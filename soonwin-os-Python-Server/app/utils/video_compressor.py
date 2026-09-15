"""Bounded video preparation for OA uploads.

This module owns the 27,000,000-byte delivery policy used for newly uploaded
videos.  It never overwrites or removes the source file.
"""

import fcntl
import json
import math
import os
import subprocess
import time
from pathlib import Path

TARGET_BYTES = 27_000_000
AUDIO_BITRATE = 96_000
MUX_RESERVE_BITRATE = 40_000
MIN_VIDEO_BITRATE = 350_000
MAX_RETRIES = 2
RETRY_BITRATE_FACTOR = 0.90
SIGNIFICANT_COMPRESSION_RATIO = 0.55
HIGH_FPS_THRESHOLD = 30.5
OUTPUT_FPS_CAP = 30.0
MAX_720_SHORT_EDGE = 720
MAX_720_LONG_EDGE = 1280


def _run(command):
    return subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def _rational_to_float(value):
    if not value or value == "0/0":
        return 0.0
    try:
        if "/" in value:
            numerator, denominator = value.split("/", 1)
            denominator = float(denominator)
            return float(numerator) / denominator if denominator else 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def probe_video(path):
    result = _run([
        "ffprobe", "-v", "error", "-show_streams", "-show_format",
        "-of", "json", str(path),
    ])
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr.strip()}")

    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    video = next((
        stream for stream in streams
        if stream.get("codec_type") == "video"
        and not stream.get("disposition", {}).get("attached_pic", 0)
    ), None)
    if not video:
        raise RuntimeError("no usable video stream")

    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    video_format = data.get("format", {})
    duration = float(video_format.get("duration") or video.get("duration") or 0)
    if duration <= 0:
        raise RuntimeError("invalid video duration")

    video_bitrate = int(video.get("bit_rate") or 0)
    if video_bitrate <= 0:
        video_bitrate = max(
            int(video_format.get("bit_rate") or 0) - int((audio or {}).get("bit_rate") or 0),
            0,
        )

    return {
        "duration": duration,
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "fps": _rational_to_float(video.get("avg_frame_rate") or video.get("r_frame_rate") or "0/1"),
        "video_bitrate": video_bitrate,
        "has_audio": audio is not None,
        "codec": video.get("codec_name"),
    }


def _output_path_for(source):
    return source.with_name(f"{source.stem}_compressed_27m.mp4")


def _cache_valid(source, output):
    if not output.is_file():
        return False
    try:
        if output.stat().st_size <= 0 or output.stat().st_size > TARGET_BYTES:
            return False
        if output.stat().st_mtime < source.stat().st_mtime:
            return False
        probe_video(output)
        return True
    except (OSError, RuntimeError, ValueError):
        return False


def _target_video_bitrate(duration, has_audio):
    reserve = MUX_RESERVE_BITRATE + (AUDIO_BITRATE if has_audio else 0)
    return max(int(TARGET_BYTES * 8 / duration - reserve), MIN_VIDEO_BITRATE)


def _build_plan(source, info):
    source_size = source.stat().st_size
    if source_size <= TARGET_BYTES:
        return {
            "action": "original",
            "source": str(source),
            "output": None,
            "source_bytes": source_size,
            "output_bytes": source_size,
            "target_bytes": TARGET_BYTES,
        }

    output = _output_path_for(source)
    if _cache_valid(source, output):
        return {
            "action": "cached",
            "source": str(source),
            "output": str(output),
            "source_bytes": source_size,
            "output_bytes": output.stat().st_size,
            "target_bytes": TARGET_BYTES,
        }

    bitrate = _target_video_bitrate(info["duration"], info["has_audio"])
    bitrate_ratio = bitrate / info["video_bitrate"] if info["video_bitrate"] > 0 else 1.0
    output_fps = info["fps"]
    scale_filter = None

    if bitrate_ratio < SIGNIFICANT_COMPRESSION_RATIO and info["fps"] > HIGH_FPS_THRESHOLD:
        output_fps = OUTPUT_FPS_CAP

    if (
        bitrate_ratio < SIGNIFICANT_COMPRESSION_RATIO
        and max(info["width"], info["height"]) > MAX_720_LONG_EDGE
        and min(info["width"], info["height"]) > MAX_720_SHORT_EDGE
    ):
        scale_filter = (
            f"scale={MAX_720_SHORT_EDGE}:-2"
            if info["height"] >= info["width"]
            else f"scale=-2:{MAX_720_SHORT_EDGE}"
        )

    return {
        "action": "compress",
        "source": str(source),
        "output": str(output),
        "source_bytes": source_size,
        "target_bytes": TARGET_BYTES,
        "video_bitrate": bitrate,
        "output_fps": output_fps,
        "scale_filter": scale_filter,
    }


def _ffmpeg_pass(source, output, pass_number, passlog, video_bitrate,
                 output_fps, source_fps, scale_filter, has_audio):
    filters = []
    if scale_filter:
        filters.append(scale_filter)
    if output_fps > 0 and source_fps > output_fps + 0.5:
        filters.append(f"fps={output_fps:g}")

    command = ["ffmpeg", "-y", "-v", "warning", "-i", str(source), "-map", "0:v:0"]
    if pass_number == 2 and has_audio:
        command += ["-map", "0:a?"]
    if filters:
        command += ["-vf", ",".join(filters)]
    command += [
        "-c:v", "libx264", "-b:v", str(video_bitrate), "-preset", "veryfast",
        "-pix_fmt", "yuv420p", "-pass", str(pass_number), "-passlogfile", str(passlog),
    ]
    if pass_number == 1:
        command += ["-an", "-f", "mp4", os.devnull]
    else:
        command += ["-c:a", "aac", "-b:a", "96k"] if has_audio else ["-an"]
        command += ["-movflags", "+faststart", str(output)]

    result = _run(command)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg pass {pass_number} failed: {result.stderr.strip()}")


def _cleanup_passlog(passlog):
    for item in passlog.parent.glob(f"{passlog.name}*"):
        try:
            item.unlink()
        except FileNotFoundError:
            pass


def prepare_video(source_path):
    """Return a validated ``original``, ``compressed``, or ``failed`` result.

    Exceptions are converted into a failed result so callers can preserve the
    original and persist an unambiguous status.
    """
    source = Path(source_path).resolve()
    if not source.is_file():
        return {"action": "failed", "error": "source file does not exist", "source": str(source)}
    if source.name.endswith("_compressed_27m.mp4"):
        return {"action": "failed", "error": "refusing compressed derivative as source", "source": str(source)}

    try:
        info = probe_video(source)
        plan = _build_plan(source, info)
        if plan["action"] in ("original", "cached"):
            plan["ok"] = True
            return plan
    except Exception as exc:
        return {"action": "failed", "error": str(exc), "source": str(source)}

    output = Path(plan["output"])
    temp = source.with_name(f"{source.stem}_compressed_27m.part.mp4")
    passlog = source.with_name(f"{source.stem}_compressed_27m.passlog")
    lock_path = source.with_name(f"{source.stem}_compressed_27m.lock")
    start = time.monotonic()

    try:
        with lock_path.open("a+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            if _cache_valid(source, output):
                return {
                    "ok": True, "action": "cached", "source": str(source),
                    "output": str(output), "source_bytes": source.stat().st_size,
                    "output_bytes": output.stat().st_size, "target_bytes": TARGET_BYTES,
                }

            bitrate = int(plan["video_bitrate"])
            last_size = None
            for attempt in range(1, MAX_RETRIES + 2):
                try:
                    temp.unlink()
                except FileNotFoundError:
                    pass
                _cleanup_passlog(passlog)

                _ffmpeg_pass(source, temp, 1, passlog, bitrate, plan["output_fps"],
                             info["fps"], plan["scale_filter"], info["has_audio"])
                _ffmpeg_pass(source, temp, 2, passlog, bitrate, plan["output_fps"],
                             info["fps"], plan["scale_filter"], info["has_audio"])
                _cleanup_passlog(passlog)

                if not temp.is_file() or temp.stat().st_size <= 0:
                    raise RuntimeError("ffmpeg completed without a non-empty output")
                last_size = temp.stat().st_size
                probe_video(temp)
                if last_size <= TARGET_BYTES:
                    os.replace(temp, output)
                    return {
                        "ok": True, "action": "compressed", "source": str(source),
                        "output": str(output), "source_bytes": source.stat().st_size,
                        "output_bytes": last_size, "target_bytes": TARGET_BYTES,
                        "attempt": attempt, "elapsed_seconds": round(time.monotonic() - start, 2),
                    }
                bitrate = max(MIN_VIDEO_BITRATE, int(bitrate * RETRY_BITRATE_FACTOR))

            raise RuntimeError(
                f"compressed output remains over target size after retries; last_size={last_size}"
            )
    except Exception as exc:
        return {"action": "failed", "error": str(exc), "source": str(source)}
    finally:
        _cleanup_passlog(passlog)
        try:
            temp.unlink()
        except FileNotFoundError:
            pass
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass

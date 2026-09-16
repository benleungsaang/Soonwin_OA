"""Bounded video preparation for OA uploads.

This module owns the 27,000,000-byte delivery policy used for newly uploaded
videos.  It never overwrites or removes the source file.
"""

import json
import math
import os
import subprocess
import time
from filelock import FileLock
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

LOGO_MARGIN_RATIO = 0.03
BASE_LOGO_HEIGHT_RATIO = 0.20
BASE_LOGO_MAX_WIDTH_RATIO = 0.32
LANDSCAPE_CORNER_MULTIPLIER = 1.50
LANDSCAPE_CENTER_MULTIPLIER = 2.00
PORTRAIT_CORNER_MULTIPLIER = 1.80
PORTRAIT_CENTER_MULTIPLIER = 2.00
CORNER_OPACITY = 1.00
CENTER_OPACITY = 0.60


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


def _display_dimensions(video):
    coded_width = int(video.get("width") or 0)
    coded_height = int(video.get("height") or 0)
    rotation = 0

    for side_data in video.get("side_data_list", []) or []:
        raw_rotation = side_data.get("rotation") if isinstance(side_data, dict) else None
        if raw_rotation in (None, "", "N/A"):
            continue
        try:
            rotation = int(round(float(raw_rotation)))
        except (TypeError, ValueError):
            continue
        break

    if abs(rotation) % 360 in (90, 270):
        return coded_height, coded_width, rotation
    return coded_width, coded_height, rotation


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

    coded_width = int(video.get("width") or 0)
    coded_height = int(video.get("height") or 0)
    display_width, display_height, rotation = _display_dimensions(video)

    video_bitrate = int(video.get("bit_rate") or 0)
    if video_bitrate <= 0:
        video_bitrate = max(
            int(video_format.get("bit_rate") or 0) - int((audio or {}).get("bit_rate") or 0),
            0,
        )

    return {
        "duration": duration,
        "width": coded_width,
        "height": coded_height,
        "coded_width": coded_width,
        "coded_height": coded_height,
        "display_width": display_width,
        "display_height": display_height,
        "rotation": rotation,
        "fps": _rational_to_float(video.get("avg_frame_rate") or video.get("r_frame_rate") or "0/1"),
        "video_bitrate": video_bitrate,
        "has_audio": audio is not None,
        "codec": video.get("codec_name"),
    }


def _runtime_backend_root():
    """Resolve the backend root from the active runtime when available."""
    try:
        from flask import has_app_context, current_app
        if has_app_context():
            return Path(current_app.root_path).parent
    except (ImportError, RuntimeError):
        pass
    return Path(__file__).resolve().parents[2]


def _logo_path():
    backend_root = _runtime_backend_root()
    return backend_root / "assets" / "Media" / "Videos" / "water-mark" / "Logo.png"


def _probe_logo(path):
    if (
        not path.is_file()
        or path.is_symlink()
        or path.stat().st_size <= 0
        or not os.access(path, os.R_OK)
    ):
        raise RuntimeError("Logo.png is not a regular non-empty file")

    result = _run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "json", str(path),
    ])
    if result.returncode != 0:
        raise RuntimeError(f"Logo ffprobe failed: {result.stderr.strip()}")

    try:
        stream = json.loads(result.stdout)["streams"][0]
        width = int(stream["width"])
        height = int(stream["height"])
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise RuntimeError("invalid Logo dimensions") from exc

    if width <= 0 or height <= 0:
        raise RuntimeError("invalid Logo dimensions")
    return width, height


def _logo_geometry(info, position):
    if position not in (1, 2, 3, 4, 5):
        raise RuntimeError("watermark position must be one of 1, 2, 3, 4, 5")

    logo = _logo_path()
    logo_width, logo_height = _probe_logo(logo)
    frame_width = info["display_width"]
    frame_height = info["display_height"]
    portrait = frame_height > frame_width
    multiplier = (
        PORTRAIT_CENTER_MULTIPLIER if position == 3 else PORTRAIT_CORNER_MULTIPLIER
        if portrait else
        LANDSCAPE_CENTER_MULTIPLIER if position == 3 else LANDSCAPE_CORNER_MULTIPLIER
    )

    scale = min(
        frame_height * BASE_LOGO_HEIGHT_RATIO / logo_height,
        frame_width * BASE_LOGO_MAX_WIDTH_RATIO / logo_width,
    ) * multiplier
    target_width = max(1, round(logo_width * scale))
    target_height = max(1, round(logo_height * scale))

    max_width = round(frame_width * 0.88)
    max_height = round(frame_height * 0.55)
    if target_width > max_width or target_height > max_height:
        safety_scale = min(max_width / target_width, max_height / target_height)
        target_width = max(1, round(target_width * safety_scale))
        target_height = max(1, round(target_height * safety_scale))

    margin = max(8, round(min(frame_width, frame_height) * LOGO_MARGIN_RATIO))
    if position in (1, 4):
        x = margin
    elif position in (2, 5):
        x = frame_width - target_width - margin
    else:
        x = (frame_width - target_width) // 2

    if position in (1, 2):
        y = margin
    elif position in (4, 5):
        y = frame_height - target_height - margin
    else:
        y = (frame_height - target_height) // 2

    return {
        "width": target_width,
        "height": target_height,
        "x": x,
        "y": y,
        "opacity": CENTER_OPACITY if position == 3 else CORNER_OPACITY,
        "logo_path": str(logo),
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


def _watermark_video_bitrate(source_size, info):
    """Choose a non-inflating baseline for watermark-only encoding."""
    source_bitrate = int(info.get("video_bitrate") or 0)
    if source_bitrate > 0:
        return source_bitrate

    # When stream bitrate metadata is absent, estimate the source's average
    # video bitrate from its own size and duration; never use TARGET_BYTES.
    duration = float(info["duration"])
    reserve = MUX_RESERVE_BITRATE + (AUDIO_BITRATE if info["has_audio"] else 0)
    estimated = int(source_size * 8 / duration - reserve)
    return max(estimated, MIN_VIDEO_BITRATE)


def _build_plan(source, info, watermark_enabled=False, watermark_position=2,
                force_target_size=False):
    source_size = source.stat().st_size
    if source_size <= TARGET_BYTES and not watermark_enabled:
        return {
            "action": "original",
            "source": str(source),
            "output": None,
            "source_bytes": source_size,
            "output_bytes": source_size,
            "target_bytes": TARGET_BYTES,
        }

    if watermark_enabled and source_size <= TARGET_BYTES and not force_target_size:
        return {
            "action": "watermark",
            "source": str(source),
            "output": str(_output_path_for(source)),
            "source_bytes": source_size,
            "target_bytes": TARGET_BYTES,
            "video_bitrate": _watermark_video_bitrate(source_size, info),
            "output_fps": info["fps"],
            "scale_filter": None,
            "watermark_enabled": True,
            "watermark_geometry": _logo_geometry(info, watermark_position),
        }

    output = _output_path_for(source)
    if not watermark_enabled and _cache_valid(source, output):
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

    plan = {
        "action": "compress",
        "source": str(source),
        "output": str(output),
        "source_bytes": source_size,
        "target_bytes": TARGET_BYTES,
        "video_bitrate": bitrate,
        "output_fps": output_fps,
        "scale_filter": scale_filter,
        "watermark_enabled": watermark_enabled,
    }
    if watermark_enabled:
        plan["watermark_geometry"] = _logo_geometry(info, watermark_position)
    return plan


def _ffmpeg_watermark_one_pass(source, output, video_bitrate,
                                output_fps, source_fps, scale_filter,
                                has_audio, watermark_geometry):
    filters = []
    if scale_filter:
        filters.append(scale_filter)
    if output_fps > 0 and source_fps > output_fps + 0.5:
        filters.append(f"fps={output_fps:g}")

    command = ["ffmpeg", "-y", "-v", "warning", "-i", str(source),
               "-loop", "1", "-i", watermark_geometry["logo_path"]]
    source_chain = ",".join(filters) if filters else "null"
    width = int(watermark_geometry["width"])
    height = int(watermark_geometry["height"])
    x = int(watermark_geometry["x"])
    y = int(watermark_geometry["y"])
    opacity = float(watermark_geometry["opacity"])
    logo_chain = (
        f"[1:v]scale={width}:{height},format=rgba,"
        f"colorchannelmixer=aa={opacity:.6f}[wm]"
        if opacity < 1.0 else
        f"[1:v]scale={width}:{height},format=rgba[wm]"
    )
    filter_complex = (
        f"[0:v]{source_chain}[base];{logo_chain};"
        f"[base][wm]overlay={x}:{y}:shortest=1:format=auto[vout]"
    )
    command += ["-filter_complex", filter_complex, "-map", "[vout]",
                "-c:v", "libx264", "-b:v", str(video_bitrate),
                "-preset", "veryfast", "-pix_fmt", "yuv420p",
                "-shortest"]
    if has_audio:
        command += ["-map", "0:a:0?", "-c:a", "aac", "-b:a", "96k"]
    else:
        command += ["-an"]
    command += ["-movflags", "+faststart", str(output)]

    result = _run(command)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg watermark one-pass failed: {result.stderr.strip()}")


def _ffmpeg_pass(source, output, pass_number, passlog, video_bitrate,
                 output_fps, source_fps, scale_filter, has_audio,
                 watermark_enabled=False, watermark_geometry=None):
    filters = []
    if scale_filter:
        filters.append(scale_filter)
    if output_fps > 0 and source_fps > output_fps + 0.5:
        filters.append(f"fps={output_fps:g}")

    command = ["ffmpeg", "-y", "-v", "warning", "-i", str(source)]
    if watermark_enabled:
        logo_path = watermark_geometry["logo_path"]
        command += ["-loop", "1", "-i", logo_path]

    if watermark_enabled:
        source_chain = ",".join(filters) if filters else "null"
        width = int(watermark_geometry["width"])
        height = int(watermark_geometry["height"])
        x = int(watermark_geometry["x"])
        y = int(watermark_geometry["y"])
        opacity = float(watermark_geometry["opacity"])
        logo_chain = (
            f"[1:v]scale={width}:{height},format=rgba,"
            f"colorchannelmixer=aa={opacity:.6f}[wm]"
            if opacity < 1.0 else
            f"[1:v]scale={width}:{height},format=rgba[wm]"
        )
        filter_complex = (
            f"[0:v]{source_chain}[base];"
            f"{logo_chain};"
            f"[base][wm]overlay={x}:{y}:shortest=1:format=auto[vout]"
        )
        command += ["-filter_complex", filter_complex, "-map", "[vout]"]
    else:
        command += ["-map", "0:v:0"]
        if filters:
            command += ["-vf", ",".join(filters)]

    if pass_number == 2 and has_audio:
        command += ["-map", "0:a:0?"]
    command += [
        "-c:v", "libx264", "-b:v", str(video_bitrate), "-preset", "veryfast",
        "-pix_fmt", "yuv420p", "-pass", str(pass_number), "-passlogfile", str(passlog),
    ]
    if watermark_enabled:
        command += ["-shortest"]
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


def prepare_video(source_path, watermark_enabled=False, watermark_position=2):
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
        plan = _build_plan(
            source,
            info,
            watermark_enabled=bool(watermark_enabled),
            watermark_position=int(watermark_position),
        )
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
        with FileLock(str(lock_path)):
            if not watermark_enabled and _cache_valid(source, output):
                return {
                    "ok": True, "action": "cached", "source": str(source),
                    "output": str(output), "source_bytes": source.stat().st_size,
                    "output_bytes": output.stat().st_size, "target_bytes": TARGET_BYTES,
                }

            if plan["action"] == "watermark":
                _ffmpeg_watermark_one_pass(
                    source, temp, plan["video_bitrate"], plan["output_fps"],
                    info["fps"], plan["scale_filter"], info["has_audio"],
                    plan["watermark_geometry"],
                )
                if not temp.is_file() or temp.stat().st_size <= 0:
                    raise RuntimeError("watermark one-pass completed without a non-empty output")
                one_pass_size = temp.stat().st_size
                probe_video(temp)
                if one_pass_size <= TARGET_BYTES:
                    os.replace(temp, output)
                    return {
                        "ok": True, "action": "compressed", "encode_mode": "watermark_one_pass",
                        "source": str(source), "output": str(output),
                        "source_bytes": source.stat().st_size, "output_bytes": one_pass_size,
                        "target_bytes": TARGET_BYTES,
                    }

                # An unexpectedly oversized one-pass result uses the existing
                # target-size two-pass plan; no new retry algorithm is added.
                _cleanup_passlog(passlog)
                plan = _build_plan(
                    source, info, watermark_enabled=True,
                    watermark_position=watermark_position, force_target_size=True,
                )

            bitrate = int(plan["video_bitrate"])
            last_size = None
            for attempt in range(1, MAX_RETRIES + 2):
                try:
                    temp.unlink()
                except FileNotFoundError:
                    pass
                _cleanup_passlog(passlog)

                _ffmpeg_pass(
                    source, temp, 1, passlog, bitrate, plan["output_fps"],
                    info["fps"], plan["scale_filter"], info["has_audio"],
                    watermark_enabled=watermark_enabled,
                    watermark_geometry=plan.get("watermark_geometry"),
                )
                _ffmpeg_pass(
                    source, temp, 2, passlog, bitrate, plan["output_fps"],
                    info["fps"], plan["scale_filter"], info["has_audio"],
                    watermark_enabled=watermark_enabled,
                    watermark_geometry=plan.get("watermark_geometry"),
                )
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

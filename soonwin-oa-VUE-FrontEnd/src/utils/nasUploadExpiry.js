// Use a monotonic clock for the client-side countdown. Wall-clock time on a
// phone can be wrong; server-side JWT verification remains authoritative.
export function createNasUploadDeadline(remainingSeconds, monotonicNow = performance.now()) {
  const seconds = Number.isFinite(remainingSeconds) ? Math.max(0, remainingSeconds) : 0;
  return monotonicNow + seconds * 1000;
}

export function nasUploadRemainingMs(deadline, monotonicNow = performance.now()) {
  return Math.max(0, deadline - monotonicNow);
}

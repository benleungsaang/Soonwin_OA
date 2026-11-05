import test from 'node:test';
import assert from 'node:assert/strict';
import { createNasUploadDeadline, nasUploadRemainingMs } from '../src/utils/nasUploadExpiry.js';

test('phone wall-clock skew does not affect server-authorized QR lifetime', () => {
  const originalDateNow = Date.now;
  const monotonic = 12_345;
  try {
    for (const wallClockOffset of [-86_400_000, 86_400_000]) {
      Date.now = () => originalDateNow() + wallClockOffset;
      const deadline = createNasUploadDeadline(30 * 60, monotonic);
      assert.equal(nasUploadRemainingMs(deadline, monotonic), 30 * 60 * 1000);
      assert.equal(nasUploadRemainingMs(deadline, monotonic + 30 * 60 * 1000), 0);
    }
  } finally {
    Date.now = originalDateNow;
  }
});

test('invalid or expired server lifetime produces no usable countdown', () => {
  assert.equal(nasUploadRemainingMs(createNasUploadDeadline(0, 100), 100), 0);
  assert.equal(createNasUploadDeadline(-1, 100), 100);
});

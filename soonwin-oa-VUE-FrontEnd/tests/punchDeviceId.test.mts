import assert from 'node:assert/strict';
import test from 'node:test';

const values = new Map<string, string>();
let cookieText = '';

globalThis.localStorage = {
  getItem: (key: string) => values.get(key) ?? null,
  setItem: (key: string, value: string) => values.set(key, value),
  removeItem: (key: string) => values.delete(key),
  clear: () => values.clear(),
  key: () => null,
  get length() { return values.size; },
} as Storage;

globalThis.document = {
  get cookie() { return cookieText; },
  set cookie(value: string) { cookieText = value; },
} as Document;

const { getOrCreatePunchDeviceId, getPunchDeviceId, savePunchDeviceId } = await import('../src/utils/punchDeviceId.ts');

test('Cookie restores an existing device ID after localStorage is cleared', () => {
  values.clear();
  cookieText = '';
  savePunchDeviceId('known-device-id');
  values.clear();

  assert.equal(getPunchDeviceId(), 'known-device-id');
  assert.equal(values.get('auth_device_id'), 'known-device-id');
});

test('clearing all browser data produces one stable candidate ID', () => {
  values.clear();
  cookieText = '';

  const candidate = getOrCreatePunchDeviceId();
  assert.match(candidate, /^[0-9a-f-]{36}$/i);
  assert.equal(getOrCreatePunchDeviceId(), candidate);
  assert.equal(values.get('auth_device_id'), candidate);
  assert.match(cookieText, new RegExp(`auth_device_id=${candidate}`));
});

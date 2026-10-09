import assert from 'node:assert/strict';
import test from 'node:test';

const { isDeviceBindingRequiredHttpError } = await import('../src/utils/punchResponse.ts');

const error = (status: number, businessStatus: string, url = '/api/device-clock-in') => ({
  config: { url },
  response: { status, data: { data: { status: businessStatus } } },
});

test('only explicit device authorization rejection from punch API gets the modal flow', () => {
  assert.equal(isDeviceBindingRequiredHttpError(error(403, 'device_binding_required')), true);
  assert.equal(isDeviceBindingRequiredHttpError(error(403, 'device_change_required')), true);
  assert.equal(isDeviceBindingRequiredHttpError(error(403, 'forbidden')), false);
  assert.equal(isDeviceBindingRequiredHttpError(error(401, 'device_binding_required')), false);
  assert.equal(isDeviceBindingRequiredHttpError(error(500, 'device_binding_required')), false);
  assert.equal(isDeviceBindingRequiredHttpError(error(403, 'device_binding_required', '/api/other')), false);
});

test('network, server, and login errors remain outside the device modal flow', () => {
  assert.equal(isDeviceBindingRequiredHttpError({ request: {} }), false);
  assert.equal(isDeviceBindingRequiredHttpError(error(500, 'internal_error')), false);
  assert.equal(isDeviceBindingRequiredHttpError(error(401, 'unauthorized')), false);
  assert.equal(isDeviceBindingRequiredHttpError(null), false);
});

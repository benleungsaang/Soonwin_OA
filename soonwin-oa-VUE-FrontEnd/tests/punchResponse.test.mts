import assert from 'node:assert/strict';
import test from 'node:test';

const { classifyPunchResponse } = await import('../src/utils/punchResponse.ts');

const validRecord = {
  record_id: 42,
  emp_id: 'EMP-1',
  name: 'Test Employee',
  punch_type: '上班打卡',
  punch_time: '2026-10-09 08:30:00',
  status: 'created',
};

test('only a complete persisted record for the logged-in employee is confirmed', () => {
  assert.equal(classifyPunchResponse(validRecord, 'EMP-1').kind, 'confirmed');
  assert.equal(classifyPunchResponse({ ...validRecord, emp_id: 'OTHER' }, 'EMP-1').kind, 'invalid');
  assert.equal(classifyPunchResponse({ ...validRecord, record_id: undefined }, 'EMP-1').kind, 'invalid');
  assert.equal(classifyPunchResponse({ ...validRecord, name: '' }, 'EMP-1').kind, 'invalid');
  assert.equal(classifyPunchResponse({ ...validRecord, punch_type: '未知类型' }, 'EMP-1').kind, 'invalid');
});

test('device authorization responses never become punch success', () => {
  assert.equal(classifyPunchResponse({ status: 'device_binding_required' }, 'EMP-1').kind, 'binding-required');
  assert.equal(classifyPunchResponse({ status: 'device_change_required' }, 'EMP-1').kind, 'binding-required');
});

test('HTTP errors, server errors, and network failures cannot be confirmed', () => {
  assert.equal(classifyPunchResponse({ response: { status: 403 } }, 'EMP-1').kind, 'invalid');
  assert.equal(classifyPunchResponse({ response: { status: 500 } }, 'EMP-1').kind, 'invalid');
  assert.equal(classifyPunchResponse({ request: {}, isAxiosError: true }, 'EMP-1').kind, 'invalid');
  assert.equal(classifyPunchResponse(null, 'EMP-1').kind, 'invalid');
});

test('an existing successful attendance record is explicit and can be shown safely', () => {
  assert.equal(classifyPunchResponse({ ...validRecord, status: 'already_punched' }, 'EMP-1').kind, 'confirmed');
});

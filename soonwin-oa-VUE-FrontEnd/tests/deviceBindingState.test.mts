import assert from 'node:assert/strict';
import test from 'node:test';
const state = await import('../src/utils/deviceBindingState.ts');
test('countdown is server expires_at based and formatted', () => { assert.equal(state.secondsToExpiry('2026-10-09T00:02:00', Date.parse('2026-10-09T00:00:01')),119); assert.equal(state.formatBindingCountdown(119),'01:59'); });
test('only final states stop polling', () => { assert.equal(state.isTerminalBindingStatus('pending'),false); assert.equal(state.isTerminalBindingStatus('scanned'),false); assert.equal(state.isTerminalBindingStatus('approved'),true); assert.equal(state.bindingStatusText.pending,'待管理员审批'); });

test('poll transport failures never become expiry', () => { assert.equal(state.isExpiredSessionResponse(500),false); assert.equal(state.isExpiredSessionResponse(undefined),false); assert.equal(state.isExpiredSessionResponse(410),true); });

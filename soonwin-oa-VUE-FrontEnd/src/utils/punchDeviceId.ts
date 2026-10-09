const DEVICE_ID_STORAGE_KEY = 'auth_device_id';
const COOKIE_MAX_AGE = 365 * 24 * 60 * 60;

const getDeviceIdFromCookie = (): string | null => {
  const prefix = `${DEVICE_ID_STORAGE_KEY}=`;
  const cookie = document.cookie.split('; ').find(item => item.startsWith(prefix));
  return cookie ? decodeURIComponent(cookie.slice(prefix.length)) : null;
};

export const getPunchDeviceId = (): string | null => {
  const localDeviceId = localStorage.getItem(DEVICE_ID_STORAGE_KEY);
  if (localDeviceId) return localDeviceId;

  const cookieDeviceId = getDeviceIdFromCookie();
  if (cookieDeviceId) localStorage.setItem(DEVICE_ID_STORAGE_KEY, cookieDeviceId);
  return cookieDeviceId;
};

export const savePunchDeviceId = (deviceId: string): void => {
  localStorage.setItem(DEVICE_ID_STORAGE_KEY, deviceId);
  document.cookie = `${DEVICE_ID_STORAGE_KEY}=${encodeURIComponent(deviceId)}; path=/; max-age=${COOKIE_MAX_AGE}`;
};

const createDeviceId = (): string => {
  if (typeof crypto.randomUUID === 'function') return crypto.randomUUID();

  const bytes = new Uint8Array(16);
  if (typeof crypto.getRandomValues === 'function') {
    crypto.getRandomValues(bytes);
  } else {
    for (let index = 0; index < bytes.length; index += 1) bytes[index] = Math.floor(Math.random() * 256);
  }
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
};

/** 已绑定员工用候选 ID 申请换机；审批后同一 ID 继续用于打卡。 */
export const getOrCreatePunchDeviceId = (): string => {
  const existingDeviceId = getPunchDeviceId();
  if (existingDeviceId) return existingDeviceId;

  const candidateDeviceId = createDeviceId();
  savePunchDeviceId(candidateDeviceId);
  return candidateDeviceId;
};

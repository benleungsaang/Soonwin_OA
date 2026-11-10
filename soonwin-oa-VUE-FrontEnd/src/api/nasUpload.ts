import axios from 'axios';
import request from '@/utils/request';

export function getNasUploadSettings() {
  return request.get('/api/nas-upload/settings');
}

export function checkNasUploadDirectory(relative_dir: string) {
  return request.post('/api/nas-upload/check', { relative_dir });
}

export function saveNasUploadDirectory(relative_dir: string) {
  return request.put('/api/nas-upload/settings', { relative_dir });
}

export function getNasUploadLogs(params: { page: number; page_size: number; keyword?: string }) {
  return request.get('/api/nas-upload/logs', { params });
}

export function deleteNasUploadLogs(ids: number[]) {
  return request.delete('/api/nas-upload/logs', { data: { ids } });
}

export function createNasUploadToken() {
  return request.post('/api/nas-upload/tokens');
}

export async function validateNasUploadToken(token: string) {
  const response = await axios.get('/api/nas-upload/public', {
    headers: {
      Authorization: `Bearer ${token}`,
      'Cache-Control': 'no-store',
      Pragma: 'no-cache',
    },
  });
  return response.data.data as { expires_at: number; remaining_seconds: number };
}

export async function getNasUploadQrStatus(token: string) {
  const response = await axios.get('/api/nas-upload/qr-status', {
    headers: { Authorization: `Bearer ${token}`, 'Cache-Control': 'no-store', Pragma: 'no-cache' },
    timeout: 10000,
  });
  return response.data.data as { scanned: boolean; expires_at: number };
}

export type NasUploadTask = { upload_id: string; upload_token: string };

export async function createNasUploadTask(qrToken: string, file: File): Promise<NasUploadTask> {
  const response = await axios.post('/api/nas-upload/sessions', { filename: file.name, file_size: file.size }, {
    headers: { Authorization: `Bearer ${qrToken}` },
  });
  return response.data.data as NasUploadTask;
}

export async function getNasUploadTaskStatus(task: NasUploadTask) {
  const response = await axios.get(`/api/nas-upload/sessions/${task.upload_id}`, {
    headers: { Authorization: `Bearer ${task.upload_token}` },
    timeout: 15000,
  });
  return response.data.data as { received_bytes: number; file_size: number; status: string; error?: string; published_filename?: string };
}

export type NasUploadTaskStatus = { upload_id: string; status: string; error?: string; published_filename?: string };

export async function getNasUploadTasksStatus(tasks: NasUploadTask[]): Promise<NasUploadTaskStatus[]> {
  const response = await axios.post('/api/nas-upload/sessions/status', {
    tasks: tasks.map(task => ({ upload_id: task.upload_id, upload_token: task.upload_token })),
  }, { timeout: 15000 });
  return response.data.data.tasks as NasUploadTaskStatus[];
}

export function acknowledgeNasUploadTask(task: NasUploadTask) {
  return axios.post(`/api/nas-upload/sessions/${task.upload_id}/ack`, {}, {
    headers: { Authorization: `Bearer ${task.upload_token}` },
    timeout: 15000,
  });
}

export function uploadNasFile(task: NasUploadTask, file: File, onProgress: (loaded: number) => void) {
  return axios.put(`/api/nas-upload/sessions/${task.upload_id}/file`, file, {
    headers: { 'Content-Type': 'application/octet-stream', Authorization: `Bearer ${task.upload_token}` },
    // A whole-file request can take a long time on mobile Wi-Fi; progress is
    // shown continuously and the status endpoint reconciles a lost response.
    timeout: 21600000,
    onUploadProgress: (event) => onProgress(Math.min(file.size, event.loaded)),
  });
}

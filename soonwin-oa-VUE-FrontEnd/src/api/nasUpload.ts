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

export type NasUploadTask = { upload_id: string; upload_token: string; chunk_size: number; next_chunk: number };

export async function createNasUploadTask(qrToken: string, file: File): Promise<NasUploadTask> {
  const response = await axios.post('/api/nas-upload/sessions', { filename: file.name, file_size: file.size }, {
    headers: { Authorization: `Bearer ${qrToken}` },
  });
  return response.data.data as NasUploadTask;
}

export async function getNasUploadTaskStatus(task: NasUploadTask) {
  const response = await axios.get(`/api/nas-upload/sessions/${task.upload_id}`, {
    headers: { Authorization: `Bearer ${task.upload_token}` },
  });
  return response.data.data as { next_chunk: number; chunk_size: number; file_size: number; status: string; error?: string; published_filename?: string };
}

export type NasUploadTaskStatus = { upload_id: string; status: string; error?: string; published_filename?: string };

export async function getNasUploadTasksStatus(tasks: NasUploadTask[]): Promise<NasUploadTaskStatus[]> {
  const response = await axios.post('/api/nas-upload/sessions/status', {
    tasks: tasks.map(task => ({ upload_id: task.upload_id, upload_token: task.upload_token })),
  }, { timeout: 15000 });
  return response.data.data.tasks as NasUploadTaskStatus[];
}

export function uploadNasChunk(task: NasUploadTask, index: number, chunk: Blob, onProgress: (loaded: number) => void) {
  return axios.put(`/api/nas-upload/sessions/${task.upload_id}/chunks/${index}`, chunk, {
    headers: { 'Content-Type': 'application/octet-stream', Authorization: `Bearer ${task.upload_token}` },
    timeout: 270000,
    onUploadProgress: (event) => onProgress(Math.min(chunk.size, event.loaded)),
  });
}

export function completeNasUploadTask(task: NasUploadTask) {
  return axios.post(`/api/nas-upload/sessions/${task.upload_id}/complete`, {}, {
    headers: { Authorization: `Bearer ${task.upload_token}` },
    timeout: 30000,
  });
}

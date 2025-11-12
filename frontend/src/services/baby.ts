import { apiFetch } from './http';
import type { Baby, Gender } from '../types/dashboard';

interface CreateBabyPayload {
  name: string;
  gender: Gender;
  birth_date: string;
}

export async function getDefaultBaby(): Promise<Baby | null> {
  try {
    return await apiFetch<Baby>('/baby/default', { method: 'GET' });
  } catch (error) {
    if (error instanceof Error && 'status' in error && (error as any).status === 404) {
      return null;
    }
    throw error;
  }
}

export function getBabyById(babyId: number) {
  return apiFetch<Baby>(`/baby/${babyId}`, { method: 'GET' });
}

export function listBabies() {
  return apiFetch<Baby[]>('/baby/', { method: 'GET' });
}

export function createBaby(payload: CreateBabyPayload) {
  return apiFetch<Baby>('/baby/createBaby', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function setDefaultBaby(babyId: number) {
  return apiFetch(`/baby/${babyId}/set-default`, { method: 'POST' });
}

export function updateBaby(babyId: number, payload: Partial<CreateBabyPayload>) {
  return apiFetch<Baby>(`/baby/${babyId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function deleteBabyWithRecords(babyId: number) {
  return apiFetch(`/baby/${babyId}/purge`, { method: 'DELETE' });
}
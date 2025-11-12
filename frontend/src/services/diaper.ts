import { apiFetch } from './http';

interface DiaperPayload {
  baby_id: number;
  diaper_type: 'wet' | 'dirty';
  timestamp: string;
  notes?: string | null;
}

export function recordDiaper(payload: DiaperPayload) {
  return apiFetch('/diaper/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
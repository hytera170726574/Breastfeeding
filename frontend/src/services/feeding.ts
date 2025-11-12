import { apiFetch } from './http';
import type { TimelineEvent, TimerState } from '../types/dashboard';

interface StopFeedingPayload {
  end_time: string;
}

interface BottlePayload {
  baby_id: number;
  volume_ml: number;
  timestamp: string;
  notes?: string | null;
}

interface PumpPayload {
  baby_id: number;
  volume_ml: number;
  start_time: string;
  end_time: string;
  notes?: string | null;
}

function unwrapStartRecord(record: any, fallbackStart: string) {
  if (record?.data) {
    return {
      recordId: record.data.id ?? record.data.recordId,
      startTime: record.data.start_time ?? record.data.startTime ?? fallbackStart,
    };
  }
  if (record?.id) {
    return {
      recordId: record.id,
      startTime: record.start_time ?? fallbackStart,
    };
  }
  throw new Error('未能解析计时记录');
}

export async function startDirectFeeding(babyId: number) {
  const start_time = new Date().toISOString();
  const record = await apiFetch<any>('/feeding/direct/start', {
    method: 'POST',
    body: JSON.stringify({ baby_id: babyId, start_time }),
  });

  return unwrapStartRecord(record, start_time);
}

export function stopDirectFeeding(recordId: number) {
  const payload: StopFeedingPayload = { end_time: new Date().toISOString() };
  return apiFetch(`/feeding/direct/${recordId}/end`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export async function startSleep(babyId: number) {
  const start_time = new Date().toISOString();
  const record = await apiFetch<any>('/sleep/start', {
    method: 'POST',
    body: JSON.stringify({ baby_id: babyId, start_time }),
  });

  return unwrapStartRecord(record, start_time);
}

export function stopSleep(recordId: number) {
  const payload: StopFeedingPayload = { end_time: new Date().toISOString() };
  return apiFetch(`/sleep/${recordId}/end`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function recordBottleFeeding(type: 'breast' | 'formula' | 'pump', payload: BottlePayload) {
  if (type === 'breast') {
    return apiFetch('/feeding/breast-bottle', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  if (type === 'pump') {
    const pumpPayload: PumpPayload = {
      baby_id: payload.baby_id,
      volume_ml: payload.volume_ml,
      start_time: payload.timestamp,
      end_time: payload.timestamp,
      notes: payload.notes,
    };
    return apiFetch('/feeding/breastToPump', {
      method: 'POST',
      body: JSON.stringify(pumpPayload),
    });
  }

  const formulaPayload = {
    baby_id: payload.baby_id,
    timestamp: payload.timestamp,
    volume_ml: payload.volume_ml,
    ...(payload.notes ? { notes: payload.notes } : {}),
  };

  return apiFetch('/feeding/formula', {
    method: 'POST',
    body: JSON.stringify(formulaPayload),
  });
}

export async function fetchActiveDirect(babyId: number) {
  const record = await apiFetch<any>(`/feeding/direct/active?baby_id=${babyId}`, {
    method: 'GET',
  });
  if (!record) return null;
  const normalized = unwrapStartRecord(record, new Date().toISOString());
  return { ...normalized, mode: 'direct' as TimerState['mode'] };
}

export async function fetchActiveSleep(babyId: number) {
  const record = await apiFetch<any>(`/sleep/active?baby_id=${babyId}`, {
    method: 'GET',
  });
  if (!record) return null;
  const normalized = unwrapStartRecord(record, new Date().toISOString());
  return { ...normalized, mode: 'sleep' as TimerState['mode'] };
}

export function fetchTodayDirectRecords(babyId: number, startIso: string, endIso: string) {
  return apiFetch<TimelineEvent[]>(
    `/feeding/direct/${babyId}?start_date=${encodeURIComponent(startIso)}&end_date=${encodeURIComponent(endIso)}`,
    {
      method: 'GET',
    }
  );
}
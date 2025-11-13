import { apiFetch } from './http';
import type { Measurement } from '../types/dashboard';

interface MeasurementResponseRaw {
  id: number;
  weight_kg?: number | null;
  height_cm?: number | null;
  measurement_date: string;
  notes?: string | null;
  baby_id: number;
}

interface MeasurementCreatePayload {
  baby_id: number;
  height_cm?: number;
  weight_kg?: number;
  measurement_date: string;
  notes?: string;
}

function transformMeasurement(raw: MeasurementResponseRaw): Measurement {
  return {
    id: raw.id,
    heightCm: raw.height_cm != null ? Number(raw.height_cm) : null,
    weightKg: raw.weight_kg != null ? Number(raw.weight_kg) : null,
    measurementDate: raw.measurement_date,
    notes: raw.notes ?? null,
  };
}

export async function fetchMeasurements(babyId: number): Promise<Measurement[]> {
  const res = await apiFetch<{ data?: MeasurementResponseRaw[] } | MeasurementResponseRaw[]>(`/measurement/${babyId}`, {
    method: 'GET',
  });

  const list = Array.isArray((res as any).data) ? ((res as any).data as MeasurementResponseRaw[]) : (res as MeasurementResponseRaw[]);
  return (list ?? []).map(transformMeasurement);
}

export async function createMeasurement(payload: MeasurementCreatePayload): Promise<Measurement> {
  const res = await apiFetch<{ data?: MeasurementResponseRaw } | MeasurementResponseRaw>(`/measurement/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  const raw = (res as any).data ?? res;
  return transformMeasurement(raw as MeasurementResponseRaw);
}

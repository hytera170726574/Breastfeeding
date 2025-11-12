import { apiFetch } from './http';
import type { TimelineEvent } from '../types/dashboard';

interface RawTimelineItem {
  id?: number;
  start_time?: string;
  end_time?: string | null;
  timestamp?: string;
  created_at?: string;
  notes?: string | null;
  volume_ml?: number;
  bottle_ml?: number;
  breast_ml?: number;
  feeding_type?: string;
  diaper_type?: 'wet' | 'dirty';
  type?: string;
}

const buildEvent = (source: RawTimelineItem, overrides: Partial<TimelineEvent>): TimelineEvent => {
  const start = source.start_time ?? source.timestamp ?? source.created_at ?? new Date().toISOString();
  const end = source.end_time ?? null;
  const volume = source.volume_ml ?? source.bottle_ml ?? source.breast_ml ?? null;
  return {
    id: source.id,
    start,
    end,
    notes: source.notes ?? null,
    volumeMl: volume,
    title: overrides.title,
    type: overrides.type,
  } as TimelineEvent;
};

export async function fetchTodayTimeline(babyId: number): Promise<TimelineEvent[]> {
  const start = new Date();
  start.setHours(0, 0, 0, 0);
  const end = new Date();

  const startIso = start.toISOString();
  const endIso = end.toISOString();

  const query = `?start_date=${encodeURIComponent(startIso)}&end_date=${encodeURIComponent(endIso)}`;

  const [
    feedings,
    directs,
    sleeps,
    bottles,
    formulas,
    pumps,
    diapers,
  ] = await Promise.all([
    apiFetch<any>(`/feeding/${babyId}${query}`, { method: 'GET' }),
    apiFetch<any>(`/feeding/direct/${babyId}${query}`, { method: 'GET' }),
    apiFetch<any>(`/sleep/${babyId}${query}`, { method: 'GET' }),
    apiFetch<any>(`/feeding/breast-bottle/${babyId}${query}`, { method: 'GET' }),
    apiFetch<any>(`/feeding/formula/${babyId}${query}`, { method: 'GET' }),
    apiFetch<any>(`/feeding/pumps/${babyId}${query}`, { method: 'GET' }),
    apiFetch<any>(`/diaper/${babyId}${query}`, { method: 'GET' }),
  ]);

  const items: TimelineEvent[] = [];

  const feedData = feedings?.data ?? feedings ?? [];
  feedData.forEach((item: RawTimelineItem) => {
    const type = item.feeding_type === 'breast' ? 'breast_generic' : 'formula';
    const title = item.feeding_type === 'breast' ? '母乳（一般）' : '配方奶';
    items.push(buildEvent(item, { type, title }));
  });

  const bottleData = bottles?.data ?? bottles ?? [];
  bottleData.forEach((item: RawTimelineItem) => {
    items.push(buildEvent(item, { type: 'bottle_breast', title: '瓶喂（母乳）' }));
  });

  const formulaData = formulas?.data ?? formulas ?? [];
  formulaData.forEach((item: RawTimelineItem) => {
    items.push(buildEvent(item, { type: 'formula', title: '瓶喂（配方）' }));
  });

  const pumpData = pumps?.data ?? pumps ?? [];
  pumpData.forEach((item: RawTimelineItem) => {
    items.push(buildEvent(item, { type: 'pump', title: '泵奶' }));
  });

  const directData = directs?.data ?? directs ?? [];
  directData.forEach((item: RawTimelineItem) => {
    items.push(buildEvent(item, { type: 'direct', title: '亲喂' }));
  });

  const sleepData = sleeps?.data ?? sleeps ?? [];
  sleepData.forEach((item: RawTimelineItem) => {
    items.push(buildEvent(item, { type: 'sleep', title: '睡眠' }));
  });

  const diaperData = diapers?.data ?? diapers ?? [];
  diaperData.forEach((item: RawTimelineItem) => {
    const isDirty = item.diaper_type === 'dirty';
    items.push(
      buildEvent(item, {
        type: isDirty ? 'diaper_dirty' : 'diaper_wet',
        title: isDirty ? '大便' : '小便',
      })
    );
  });

  return items.sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());
}
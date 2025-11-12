import { apiFetch } from './http';
import type { DailyStats, WeeklyStatsDataset } from '../types/dashboard';

interface SleepRecord {
  start_time: string;
  end_time?: string | null;
  duration_minutes?: number;
}

interface DailyCountsResponse {
  total?: number;
}

interface BottleMlResponse {
  total_ml?: number;
}

interface RemainingResponse {
  remaining_ml?: number;
}

const toIsoRange = () => {
  const start = new Date();
  start.setHours(0, 0, 0, 0);
  const end = new Date();
  return {
    startIso: start.toISOString(),
    endIso: end.toISOString(),
  };
};

export async function fetchDailyStats(babyId: number): Promise<DailyStats> {
  const { startIso, endIso } = toIsoRange();

  const [remaining, counts, bottle, sleepRecords] = await Promise.all([
    apiFetch<RemainingResponse & { data?: RemainingResponse }>(`/feeding/breast/remaining/${babyId}`, {
      method: 'GET',
    }),
    apiFetch<DailyCountsResponse & { data?: DailyCountsResponse }>(
      `/feeding/count?baby_id=${babyId}&start_date=${encodeURIComponent(startIso)}&end_date=${encodeURIComponent(endIso)}`,
      { method: 'GET' }
    ),
    apiFetch<BottleMlResponse & { data?: BottleMlResponse }>(
      `/feeding/bottle-ml?baby_id=${babyId}&start_date=${encodeURIComponent(startIso)}&end_date=${encodeURIComponent(endIso)}`,
      { method: 'GET' }
    ),
    apiFetch<{ data?: SleepRecord[] } & SleepRecord[]>(
      `/sleep/${babyId}?start_date=${encodeURIComponent(startIso)}&end_date=${encodeURIComponent(endIso)}`,
      { method: 'GET' }
    ),
  ]);

  const remainingValue = (remaining as any).remaining_ml ?? (remaining as any).data?.remaining_ml ?? 0;
  const feedCount = (counts as any).total ?? (counts as any).data?.total ?? 0;
  const bottleMl = (bottle as any).total_ml ?? (bottle as any).data?.total_ml ?? 0;
  const sleeps = ((sleepRecords as any).data ?? sleepRecords) as SleepRecord[];
  const totalMinutes = sleeps.reduce((sum, item) => {
    if (item.duration_minutes != null) {
      return sum + Number(item.duration_minutes);
    }
    if (item.start_time && item.end_time) {
      const start = new Date(item.start_time).getTime();
      const end = new Date(item.end_time).getTime();
      return sum + Math.max(0, (end - start) / 60000);
    }
    return sum;
  }, 0);

  return {
    feedCount,
    bottleMl,
    remainingMilk: remainingValue,
    sleepHours: Number((totalMinutes / 60).toFixed(1)),
  };
}

export async function fetchWeeklyStats(babyId: number): Promise<WeeklyStatsDataset> {
  const today = new Date();
  const end = new Date(today);
  end.setHours(0, 0, 0, 0);
  end.setMilliseconds(-1);
  const start = new Date(end);
  start.setDate(start.getDate() - 6);
  start.setHours(0, 0, 0, 0);

  const payload = {
    baby_id: babyId,
    start_date: start.toISOString(),
    end_date: end.toISOString(),
  };

  const data = await apiFetch<any>('/stats/weekly/overview', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  const source = data?.data ?? data;
  const labels = Array.from({ length: 7 }, (_, idx) => `${idx + 1}`);

  return {
    labels,
    directCounts: source.direct_counts ?? [],
    dirtyCounts: source.dirty_counts ?? [],
    wetCounts: source.wet_counts ?? [],
    sleepMinutes: source.sleep_minutes ?? [],
    bottleMl: source.bottle_ml ?? [],
  };
}
export type Gender = 'male' | 'female' | 'other';

export interface Baby {
  id: number;
  name: string;
  gender: Gender;
  birth_date: string | null;
  created_at?: string;
}

export interface DailyStats {
  feedCount: number;
  sleepHours: number;
  bottleMl: number;
  remainingMilk: number;
}

export interface TimelineEvent {
  id?: number | string;
  type:
    | 'direct'
    | 'sleep'
    | 'bottle_breast'
    | 'formula'
    | 'pump'
    | 'diaper_wet'
    | 'diaper_dirty'
    | 'breast_generic';
  title: string;
  start: string;
  end?: string | null;
  volumeMl?: number | null;
  notes?: string | null;
}

export interface WeeklyStatsDataset {
  labels: string[];
  directCounts: number[];
  dirtyCounts: number[];
  wetCounts: number[];
  sleepMinutes: number[];
  bottleMl: number[];
}

export interface TimerState {
  mode: 'sleep' | 'direct';
  recordId: number;
  startTime: string;
}

export interface DashboardState {
  loading: boolean;
  baby: Baby | null;
  dailyStats: DailyStats;
  timeline: TimelineEvent[];
  weeklyStats: WeeklyStatsDataset | null;
  timer: TimerState | null;
}

export const emptyDailyStats: DailyStats = {
  feedCount: 0,
  sleepHours: 0,
  bottleMl: 0,
  remainingMilk: 0,
};
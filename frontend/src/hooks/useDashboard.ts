import { useCallback, useEffect, useMemo, useState } from 'react';

import {
  emptyDailyStats,
  type Baby,
  type DashboardState,
  type DailyStats,
  type Measurement,
  type TimelineEvent,
  type TimerState,
  type WeeklyStatsDataset,
} from '../types/dashboard';
import {
  createBaby,
  deleteBabyWithRecords,
  getBabyById,
  getDefaultBaby,
  listBabies,
  setDefaultBaby,
  updateBaby,
} from '../services/baby';
import {
  fetchActiveDirect,
  fetchActiveSleep,
  recordBottleFeeding,
  startDirectFeeding,
  startSleep,
  stopDirectFeeding,
  stopSleep,
} from '../services/feeding';
import { recordDiaper } from '../services/diaper';
import { fetchDailyStats, fetchWeeklyStats } from '../services/stats';
import { fetchTodayTimeline } from '../services/timeline';
import { createMeasurement, fetchLatestMeasurement } from '../services/measurement';

type ModalKey = 'createBaby' | 'manageBabies' | 'bottleFeed' | 'diaper' | 'measurement';

interface Toast {
  type: 'success' | 'error' | 'info';
  message: string;
}

interface BottleFormValues {
  type: 'breast' | 'formula' | 'pump';
  volume: number;
  notes?: string;
}

interface CreateBabyValues {
  name: string;
  gender: Baby['gender'];
  birth_date: string;
}

interface UpdateBabyValues {
  id: number;
  name?: string;
  gender?: Baby['gender'];
  birth_date?: string;
}

interface DiaperFormValues {
  type: 'wet' | 'dirty';
  notes?: string;
}

interface MeasurementFormValues {
  heightCm?: number;
  weightKg?: number;
  measurementDate: string;
  notes?: string;
}

interface UseDashboardResult {
  state: DashboardState;
  modals: Record<ModalKey, boolean>;
  babyList: Baby[];
  toast: Toast | null;
  modalAnchor: number | null;
  timerAnchor: number | null;
  openModal: (key: ModalKey, anchor?: number) => void;
  closeModal: (key: ModalKey) => void;
  dismissToast: () => void;
  refresh: () => Promise<void>;
  actions: {
    startDirect: (anchor?: number) => Promise<void>;
    stopDirect: () => Promise<void>;
    startSleep: (anchor?: number) => Promise<void>;
    stopSleep: () => Promise<void>;
    submitBottle: (values: BottleFormValues) => Promise<void>;
    submitDiaper: (values: DiaperFormValues) => Promise<void>;
  submitMeasurement: (values: MeasurementFormValues) => Promise<void>;
    createBaby: (values: CreateBabyValues) => Promise<void>;
    updateBaby: (values: UpdateBabyValues) => Promise<void>;
    deleteBaby: (babyId: number) => Promise<void>;
    selectBaby: (babyId: number) => Promise<void>;
  };
}

const defaultState: DashboardState = {
  loading: true,
  baby: null,
  dailyStats: emptyDailyStats,
  timeline: [],
  weeklyStats: null,
  timer: null,
  latestMeasurement: null,
};

function storeActiveTimerKey(mode: TimerState['mode'], babyId: number) {
  return mode === 'direct' ? `active_direct_${babyId}` : `active_sleep_${babyId}`;
}

function persistActiveTimer(timer: TimerState | null, babyId: number) {
  if (!timer) {
    localStorage.removeItem(storeActiveTimerKey('direct', babyId));
    localStorage.removeItem(storeActiveTimerKey('sleep', babyId));
    return;
  }

  const key = storeActiveTimerKey(timer.mode, babyId);
  localStorage.setItem(key, JSON.stringify({ id: timer.recordId, start_time: timer.startTime }));
}

function restoreActiveTimer(babyId: number): TimerState | null {
  const directRaw = localStorage.getItem(storeActiveTimerKey('direct', babyId));
  if (directRaw) {
    try {
      const parsed = JSON.parse(directRaw);
      if (parsed?.id && parsed?.start_time) {
        return { mode: 'direct', recordId: parsed.id, startTime: parsed.start_time };
      }
    } catch (error) {
      console.warn('无法解析本地 direct 计时器缓存', error);
    }
  }

  const sleepRaw = localStorage.getItem(storeActiveTimerKey('sleep', babyId));
  if (sleepRaw) {
    try {
      const parsed = JSON.parse(sleepRaw);
      if (parsed?.id && parsed?.start_time) {
        return { mode: 'sleep', recordId: parsed.id, startTime: parsed.start_time };
      }
    } catch (error) {
      console.warn('无法解析本地 sleep 计时器缓存', error);
    }
  }

  return null;
}

export function useDashboard(): UseDashboardResult {
  const [state, setState] = useState<DashboardState>(defaultState);
  const [modals, setModals] = useState<Record<ModalKey, boolean>>({
    createBaby: false,
    manageBabies: false,
    bottleFeed: false,
    diaper: false,
    measurement: false,
  });
  const [babyList, setBabyList] = useState<Baby[]>([]);
  const [toast, setToast] = useState<Toast | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const [modalAnchor, setModalAnchor] = useState<number | null>(null);
  const [timerAnchor, setTimerAnchor] = useState<number | null>(null);

  const showToast = useCallback((message: string, type: Toast['type'] = 'info') => {
    setToast({ message, type });
  }, []);

  const openModal = useCallback((key: ModalKey, anchor?: number) => {
    setModalAnchor(typeof anchor === 'number' ? anchor : null);
    setModals((prev) => ({ ...prev, [key]: true }));
  }, []);

  const closeModal = useCallback((key: ModalKey) => {
    setModals((prev) => ({ ...prev, [key]: false }));
    setModalAnchor(null);
  }, []);

  const dismissToast = useCallback(() => setToast(null), []);

  useEffect(() => {
    if (!toast) return;
    // 自动在3秒后隐藏提示，避免用户手动关闭；若toast更新或组件卸载时清除定时器
    const timer = window.setTimeout(() => setToast(null), 3000);
    return () => window.clearTimeout(timer);
  }, [toast]);

  const loadBabyContext = useCallback(
    async (baby: Baby) => {
      setState((prev) => ({ ...prev, loading: true, baby }));
      localStorage.setItem('currentBabyId', String(baby.id));

      try {
        const [daily, timeline, weekly, babies, activeDirect, activeSleep, latestMeasurementRaw] =
          (await Promise.all([
            fetchDailyStats(baby.id),
            fetchTodayTimeline(baby.id),
            fetchWeeklyStats(baby.id),
            listBabies(),
            fetchActiveDirect(baby.id).catch(() => null),
            fetchActiveSleep(baby.id).catch(() => null),
            fetchLatestMeasurement(baby.id).catch(() => null as Measurement | null),
          ])) as [
            DailyStats,
            TimelineEvent[],
            WeeklyStatsDataset,
            Baby[],
            TimerState | null,
            TimerState | null,
            Measurement | null
          ];

        const timer = activeDirect ?? activeSleep ?? restoreActiveTimer(baby.id);
        const latestMeasurement = latestMeasurementRaw ?? null;

        if (babies.length) {
          setBabyList(babies);
        }

        if (timer) {
          persistActiveTimer(timer, baby.id);
        } else {
          persistActiveTimer(null, baby.id);
        }

        setState({
          loading: false,
          baby,
          dailyStats: daily,
          timeline,
          weeklyStats: weekly,
          timer,
          latestMeasurement,
        });
      } catch (error) {
        console.error('加载仪表盘数据失败', error);
        showToast(error instanceof Error ? error.message : '加载仪表盘数据失败', 'error');
        setState((prev) => ({ ...prev, loading: false }));
      }
    },
    [showToast]
  );

  const resolveInitialBaby = useCallback(async (): Promise<Baby | null> => {
    try {
      const defaultBaby = await getDefaultBaby();
      if (defaultBaby) {
        return defaultBaby;
      }
    } catch (error) {
      console.warn('获取默认宝宝失败，将尝试本地记录', error);
    }

    const storedId = Number(localStorage.getItem('currentBabyId'));
    if (storedId) {
      try {
        return await getBabyById(storedId);
      } catch (error) {
        console.warn('根据本地宝宝ID加载失败', error);
      }
    }

    try {
      const babies = await listBabies();
      setBabyList(babies);
      return babies.length ? babies[0] : null;
    } catch (error) {
      console.error('加载宝宝列表失败', error);
      return null;
    }
  }, []);

  const bootstrap = useCallback(async () => {
    if (!localStorage.getItem('authToken')) {
      setState(defaultState);
      setIsInitializing(false);
      return;
    }

    const baby = await resolveInitialBaby();
    if (!baby) {
      setState((prev) => ({ ...prev, loading: false, baby: null }));
      openModal('createBaby');
      setIsInitializing(false);
      return;
    }

    await loadBabyContext(baby);
    setIsInitializing(false);
  }, [loadBabyContext, openModal, resolveInitialBaby]);

  useEffect(() => {
    bootstrap();
  }, [bootstrap]);

  const refresh = useCallback(async () => {
    if (!state.baby) return;
    await loadBabyContext(state.baby);
  }, [loadBabyContext, state.baby]);

  const startDirect = useCallback(async (anchor?: number) => {
    if (!state.baby) {
      openModal('createBaby', anchor);
      showToast('请先创建宝宝信息', 'info');
      return;
    }
    try {
      setTimerAnchor(typeof anchor === 'number' ? anchor : null);
      const { recordId, startTime } = await startDirectFeeding(state.baby.id);
      const timer: TimerState = { mode: 'direct', recordId, startTime };
      persistActiveTimer(timer, state.baby.id);
      setState((prev) => ({ ...prev, timer }));
      showToast('亲喂计时开始', 'success');
      await refresh();
    } catch (error) {
      console.error('开始亲喂失败', error);
      setTimerAnchor(null);
      showToast(error instanceof Error ? error.message : '开始亲喂失败', 'error');
    }
  }, [openModal, refresh, showToast, state.baby]);

  const stopDirect = useCallback(async () => {
    if (!state.baby || state.timer?.mode !== 'direct') return;
    try {
      await stopDirectFeeding(state.timer.recordId);
      persistActiveTimer(null, state.baby.id);
      setState((prev) => ({ ...prev, timer: null }));
      setTimerAnchor(null);
      showToast('亲喂已结束', 'success');
      await refresh();
    } catch (error) {
      console.error('结束亲喂失败', error);
      showToast(error instanceof Error ? error.message : '结束亲喂失败', 'error');
    }
  }, [refresh, showToast, state.baby, state.timer]);

  const startSleepAction = useCallback(async (anchor?: number) => {
    if (!state.baby) {
      openModal('createBaby', anchor);
      showToast('请先创建宝宝信息', 'info');
      return;
    }
    try {
      setTimerAnchor(typeof anchor === 'number' ? anchor : null);
      const { recordId, startTime } = await startSleep(state.baby.id);
      const timer: TimerState = { mode: 'sleep', recordId, startTime };
      persistActiveTimer(timer, state.baby.id);
      setState((prev) => ({ ...prev, timer }));
      showToast('睡眠计时开始', 'success');
      await refresh();
    } catch (error) {
      console.error('开始睡眠失败', error);
      setTimerAnchor(null);
      showToast(error instanceof Error ? error.message : '开始睡眠失败', 'error');
    }
  }, [openModal, refresh, showToast, state.baby]);

  const stopSleepAction = useCallback(async () => {
    if (!state.baby || state.timer?.mode !== 'sleep') return;
    try {
      await stopSleep(state.timer.recordId);
      persistActiveTimer(null, state.baby.id);
      setState((prev) => ({ ...prev, timer: null }));
      setTimerAnchor(null);
      showToast('睡眠已结束', 'success');
      await refresh();
    } catch (error) {
      console.error('结束睡眠失败', error);
      showToast(error instanceof Error ? error.message : '结束睡眠失败', 'error');
    }
  }, [refresh, showToast, state.baby, state.timer]);

  const submitBottle = useCallback(
    async (values: BottleFormValues) => {
      if (!state.baby) {
        openModal('createBaby');
        showToast('请先创建宝宝信息', 'info');
        return;
      }
      try {
        await recordBottleFeeding(values.type, {
          baby_id: state.baby.id,
          volume_ml: values.volume,
          timestamp: new Date().toISOString(),
          notes: values.notes,
        });
        closeModal('bottleFeed');
        showToast('瓶喂记录已保存', 'success');
        await refresh();
      } catch (error) {
        console.error('记录瓶喂失败', error);
        showToast(error instanceof Error ? error.message : '记录瓶喂失败', 'error');
      }
    },
    [closeModal, openModal, refresh, showToast, state.baby]
  );

  const submitDiaper = useCallback(
    async (values: DiaperFormValues) => {
      if (!state.baby) {
        openModal('createBaby');
        showToast('请先创建宝宝信息', 'info');
        return;
      }
      try {
        await recordDiaper({
          baby_id: state.baby.id,
          diaper_type: values.type,
          timestamp: new Date().toISOString(),
          notes: values.notes,
        });
        closeModal('diaper');
        showToast('大小便记录已保存', 'success');
        await refresh();
      } catch (error) {
        console.error('记录大小便失败', error);
        showToast(error instanceof Error ? error.message : '记录大小便失败', 'error');
      }
    },
    [closeModal, openModal, refresh, showToast, state.baby]
  );

  const submitMeasurement = useCallback(
    async (values: MeasurementFormValues) => {
      if (!state.baby) {
        openModal('createBaby');
        showToast('请先创建宝宝信息', 'info');
        return;
      }
      if (values.heightCm == null && values.weightKg == null) {
        showToast('请至少填写身高或体重其中一项', 'error');
        return;
      }
      try {
        await createMeasurement({
          baby_id: state.baby.id,
          height_cm: values.heightCm,
          weight_kg: values.weightKg,
          measurement_date: values.measurementDate,
          notes: values.notes,
        });
        closeModal('measurement');
        showToast('身高体重记录已保存', 'success');
        await refresh();
      } catch (error) {
        console.error('记录身高体重失败', error);
        showToast(error instanceof Error ? error.message : '记录身高体重失败', 'error');
      }
    },
    [closeModal, openModal, refresh, showToast, state.baby]
  );

  const createBabyAction = useCallback(
    async (values: CreateBabyValues) => {
      try {
        const baby = await createBaby(values);
        await setDefaultBaby(baby.id);
        closeModal('createBaby');
        showToast('宝宝信息创建成功', 'success');
        await loadBabyContext(baby);
      } catch (error) {
        console.error('创建宝宝失败', error);
        showToast(error instanceof Error ? error.message : '创建宝宝失败', 'error');
      }
    },
    [closeModal, loadBabyContext, showToast]
  );

  const updateBabyAction = useCallback(
    async (values: UpdateBabyValues) => {
      try {
        const updated = await updateBaby(values.id, {
          name: values.name,
          gender: values.gender,
          birth_date: values.birth_date,
        });
        showToast('宝宝信息已更新', 'success');
        if (state.baby && state.baby.id === values.id) {
          await loadBabyContext(updated);
        } else {
          await refresh();
        }
      } catch (error) {
        console.error('更新宝宝失败', error);
        showToast(error instanceof Error ? error.message : '更新宝宝失败', 'error');
      }
    },
    [loadBabyContext, refresh, showToast, state.baby]
  );

  const deleteBabyAction = useCallback(
    async (babyId: number) => {
      try {
        await deleteBabyWithRecords(babyId);
        showToast('宝宝及相关记录已删除', 'success');

        if (state.baby && state.baby.id === babyId) {
          const babies = await listBabies();
          setBabyList(babies);
          if (babies.length) {
            await setDefaultBaby(babies[0].id);
            await loadBabyContext(babies[0]);
          } else {
            setState({ ...defaultState, loading: false });
            openModal('createBaby');
          }
        } else {
          await refresh();
        }
      } catch (error) {
        console.error('删除宝宝失败', error);
        showToast(error instanceof Error ? error.message : '删除宝宝失败', 'error');
      }
    },
    [loadBabyContext, openModal, refresh, showToast, state.baby]
  );

  const selectBabyAction = useCallback(
    async (babyId: number) => {
      try {
        await setDefaultBaby(babyId);
        const baby = await getBabyById(babyId);
        closeModal('manageBabies');
        showToast('默认宝宝已切换', 'success');
        await loadBabyContext(baby);
      } catch (error) {
        console.error('切换宝宝失败', error);
        showToast(error instanceof Error ? error.message : '切换宝宝失败', 'error');
      }
    },
    [closeModal, loadBabyContext, showToast]
  );

  useEffect(() => {
    if (!isInitializing && state.baby && !state.timer) {
      const restored = restoreActiveTimer(state.baby.id);
      if (restored) {
        setState((prev) => ({ ...prev, timer: restored }));
      }
    }
  }, [isInitializing, state.baby, state.timer]);

  const actions = useMemo(
    () => ({
      startDirect,
      stopDirect,
      startSleep: startSleepAction,
      stopSleep: stopSleepAction,
      submitBottle,
      submitDiaper,
      submitMeasurement,
      createBaby: createBabyAction,
      updateBaby: updateBabyAction,
      deleteBaby: deleteBabyAction,
      selectBaby: selectBabyAction,
    }),
    [
      createBabyAction,
      deleteBabyAction,
      selectBabyAction,
      startDirect,
      startSleepAction,
      stopDirect,
      stopSleepAction,
      submitBottle,
      submitDiaper,
      submitMeasurement,
      updateBabyAction,
    ]
  );

  return {
    state,
    modals,
    babyList,
    toast,
    modalAnchor,
    timerAnchor,
    openModal,
    closeModal,
    dismissToast,
    refresh,
    actions,
  };
}
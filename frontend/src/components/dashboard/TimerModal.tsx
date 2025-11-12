import { useEffect, useMemo, useState } from 'react';
import type { CSSProperties } from 'react';

import type { TimerState } from '../../types/dashboard';

interface TimerModalProps {
  timer: TimerState | null;
  anchorY?: number | null;
  onStop: () => Promise<void>;
}

function formatDuration(ms: number) {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const hours = String(Math.floor(totalSeconds / 3600)).padStart(2, '0');
  const minutes = String(Math.floor((totalSeconds % 3600) / 60)).padStart(2, '0');
  const seconds = String(totalSeconds % 60).padStart(2, '0');
  return `${hours}:${minutes}:${seconds}`;
}

export function TimerModal({ timer, anchorY, onStop }: TimerModalProps) {
  const [now, setNow] = useState(() => Date.now());
  const [stopping, setStopping] = useState(false);

  useEffect(() => {
    if (!timer) return;
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, [timer]);

  useEffect(() => {
    if (!timer) {
      setStopping(false);
    }
  }, [timer]);

  const elapsed = useMemo(() => {
    if (!timer) return '00:00:00';
    const start = new Date(timer.startTime).getTime();
    return formatDuration(now - start);
  }, [now, timer]);

  const containerStyle: CSSProperties = useMemo(() => {
    if (typeof anchorY === 'number') {
      const viewportHeight = typeof window !== 'undefined' ? window.innerHeight : 0;
      const rawTop = Math.max(anchorY - 80, 24);
      const maxTop = viewportHeight ? Math.max(viewportHeight - 280, 24) : rawTop;
      // 让计时弹框跟随按钮高度显示，同时保持在视口内
      return { top: Math.min(rawTop, maxTop) };
    }
    return { top: '20vh' };
  }, [anchorY]);

  if (!timer) return null;

  const label = timer.mode === 'direct' ? '亲喂计时中' : '睡眠计时中';

  const handleStop = async () => {
    setStopping(true);
    try {
      await onStop();
    } finally {
      setStopping(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 px-4">
      <div
        className="absolute left-1/2 -translate-x-1/2 w-full max-w-sm bg-white rounded-2xl shadow-2xl p-6 text-center space-y-4"
        style={containerStyle}
      >
        <h3 className="text-xl font-semibold text-gray-800">{label}</h3>
        <div className="text-4xl font-mono font-bold text-blue-600">{elapsed}</div>
        <button
          type="button"
          onClick={handleStop}
          className="w-full py-2 rounded-lg bg-red-500 text-white hover:bg-red-600 transition disabled:opacity-70"
          disabled={stopping}
        >
          {stopping ? '停止中…' : '停止计时'}
        </button>
      </div>
    </div>
  );
}

export default TimerModal;
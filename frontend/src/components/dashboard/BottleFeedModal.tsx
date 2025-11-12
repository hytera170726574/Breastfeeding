import { useEffect, useMemo, useState } from 'react';
import type { CSSProperties } from 'react';

interface BottleFeedModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (values: { type: 'breast' | 'formula' | 'pump'; volume: number; notes?: string }) => Promise<void>;
  anchorY?: number | null;
}

const types = [
  { value: 'breast' as const, label: '母乳' },
  { value: 'formula' as const, label: '配方奶' },
  { value: 'pump' as const, label: '泵奶（加入库存）' },
];

export function BottleFeedModal({ open, onClose, onSubmit, anchorY }: BottleFeedModalProps) {
  const [type, setType] = useState<'breast' | 'formula' | 'pump'>('breast');
  const [volume, setVolume] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (open) {
      setType('breast');
      setVolume('');
      setNotes('');
      setError(null);
    }
  }, [open]);

  const containerStyle: CSSProperties = useMemo(() => {
    if (typeof anchorY === 'number') {
      const viewportHeight = typeof window !== 'undefined' ? window.innerHeight : 0;
      const rawTop = Math.max(anchorY - 80, 24);
      const maxTop = viewportHeight ? Math.max(viewportHeight - 360, 24) : rawTop;
      // 将对话框锚定到按钮附近，同时避免超出视口底部
      return { top: Math.min(rawTop, maxTop) };
    }
    return { top: '20vh' };
  }, [anchorY]);

  if (!open) return null;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const volumeNumber = Number(volume);
    if (!Number.isFinite(volumeNumber) || volumeNumber <= 0) {
      setError('请输入有效的毫升数');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await onSubmit({ type, volume: volumeNumber, notes: notes.trim() || undefined });
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败，请稍后重试');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-40 bg-black/50 px-4">
      <div
        className="absolute left-1/2 -translate-x-1/2 w-full max-w-lg bg-white rounded-2xl shadow-xl p-6"
        style={containerStyle}
      >
        <header className="text-center mb-4">
          <h2 className="text-2xl font-bold text-gray-800">记录瓶喂</h2>
          <p className="text-gray-600 mt-2">选择类型并填写毫升与备注</p>
        </header>
        <form onSubmit={handleSubmit} className="space-y-4">
          <fieldset>
            <legend className="text-sm font-medium text-gray-700 mb-2">类型</legend>
            <div className="flex flex-wrap gap-4">
              {types.map((item) => (
                <label key={item.value} className="inline-flex items-center gap-2">
                  <input
                    type="radio"
                    name="bottle-type"
                    value={item.value}
                    checked={type === item.value}
                    onChange={() => setType(item.value)}
                    className="form-radio h-4 w-4 text-blue-600"
                  />
                  <span>{item.label}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="bottle-volume">毫升数 (ml)</label>
            <input
              id="bottle-volume"
              type="number"
              min="0"
              step="0.1"
              value={volume}
              onChange={(event) => setVolume(event.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="输入毫升数"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="bottle-notes">备注 (可选)</label>
            <input
              id="bottle-notes"
              type="text"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="例如：添加了维生素"
            />
          </div>

          {error && <p className="text-sm text-red-500 text-center">{error}</p>}

          <div className="flex space-x-4 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-200 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-300 transition"
              disabled={submitting}
            >
              取消
            </button>
            <button
              type="submit"
              className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition disabled:opacity-70"
              disabled={submitting}
            >
              {submitting ? '保存中…' : '保存'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default BottleFeedModal;
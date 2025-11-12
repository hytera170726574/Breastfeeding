import { useEffect, useMemo, useState } from 'react';
import type { CSSProperties } from 'react';

interface DiaperModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (values: { type: 'wet' | 'dirty'; notes?: string }) => Promise<void>;
  anchorY?: number | null;
}

const types = [
  { value: 'wet' as const, label: '小号' },
  { value: 'dirty' as const, label: '大号' },
];

export function DiaperModal({ open, onClose, onSubmit, anchorY }: DiaperModalProps) {
  const [type, setType] = useState<'wet' | 'dirty'>('wet');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setType('wet');
      setNotes('');
      setError(null);
    }
  }, [open]);

  const containerStyle: CSSProperties = useMemo(() => {
    if (typeof anchorY === 'number') {
      const viewportHeight = typeof window !== 'undefined' ? window.innerHeight : 0;
      const rawTop = Math.max(anchorY - 80, 24);
      const maxTop = viewportHeight ? Math.max(viewportHeight - 320, 24) : rawTop;
      // 对齐操作按钮的高度，并限制在视口范围内
      return { top: Math.min(rawTop, maxTop) };
    }
    return { top: '20vh' };
  }, [anchorY]);

  if (!open) return null;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await onSubmit({ type, notes: notes.trim() || undefined });
    } catch (err) {
      setError(err instanceof Error ? err.message : '记录失败，请稍后重试');
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
          <h2 className="text-2xl font-bold text-gray-800">记录大小便</h2>
          <p className="text-gray-600 mt-2">请选择类型并填写备注（可选）</p>
        </header>
        <form onSubmit={handleSubmit} className="space-y-4">
          <fieldset>
            <legend className="text-sm font-medium text-gray-700 mb-2">类型</legend>
            <div className="flex gap-4">
              {types.map((item) => (
                <label key={item.value} className="inline-flex items-center gap-2">
                  <input
                    type="radio"
                    value={item.value}
                    checked={type === item.value}
                    onChange={() => setType(item.value)}
                    className="form-radio h-4 w-4 text-green-600"
                  />
                  <span>{item.label}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="diaper-notes">备注 (可选)</label>
            <input
              id="diaper-notes"
              type="text"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="例如：颜色异常"
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
              className="flex-1 bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 transition disabled:opacity-70"
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

export default DiaperModal;
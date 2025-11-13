import { useEffect, useMemo, useState } from 'react';
import type { CSSProperties } from 'react';

interface MeasurementModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (values: { heightCm?: number; weightKg?: number; measurementDate: string; notes?: string }) => Promise<void>;
  anchorY?: number | null;
}

function formatDateInput(date: Date): string {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, '0');
  const day = `${date.getDate()}`.padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function MeasurementModal({ open, onClose, onSubmit, anchorY }: MeasurementModalProps) {
  const [height, setHeight] = useState('');
  const [weight, setWeight] = useState('');
  const [notes, setNotes] = useState('');
  const [date, setDate] = useState(formatDateInput(new Date()));
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (open) {
      setHeight('');
      setWeight('');
      setNotes('');
      setDate(formatDateInput(new Date()));
      setError(null);
      setSubmitting(false);
    }
  }, [open]);

  const containerStyle: CSSProperties = useMemo(() => {
    if (typeof anchorY === 'number') {
      const viewportHeight = typeof window !== 'undefined' ? window.innerHeight : 0;
      const rawTop = Math.max(anchorY - 80, 24);
      const maxTop = viewportHeight ? Math.max(viewportHeight - 360, 24) : rawTop;
      return { top: Math.min(rawTop, maxTop) };
    }
    return { top: '20vh' };
  }, [anchorY]);

  if (!open) return null;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const heightNumber = height ? Number(height) : undefined;
    const weightNumber = weight ? Number(weight) : undefined;

    if ((heightNumber == null || Number.isNaN(heightNumber)) && (weightNumber == null || Number.isNaN(weightNumber))) {
      setError('请至少填写身高或体重其中一项');
      return;
    }

    if (heightNumber != null && heightNumber <= 0) {
      setError('身高必须为正数');
      return;
    }

    if (weightNumber != null && weightNumber <= 0) {
      setError('体重必须为正数');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await onSubmit({
        heightCm: heightNumber,
        weightKg: weightNumber,
        measurementDate: date,
        notes: notes.trim() || undefined,
      });
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
          <h2 className="text-2xl font-bold text-gray-800">记录身高体重</h2>
          <p className="text-gray-600 mt-2">填写宝宝最新的身高与体重数据</p>
        </header>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="measurement-height">
                身高 (cm)
              </label>
              <input
                id="measurement-height"
                type="number"
                min="0"
                step="0.1"
                value={height}
                onChange={(event) => setHeight(event.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500"
                placeholder="例如 60.5"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="measurement-weight">
                体重 (kg)
              </label>
              <input
                id="measurement-weight"
                type="number"
                min="0"
                step="0.01"
                value={weight}
                onChange={(event) => setWeight(event.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500"
                placeholder="例如 6.35"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="measurement-date">
              测量日期
            </label>
            <input
              id="measurement-date"
              type="date"
              value={date}
              onChange={(event) => setDate(event.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="measurement-notes">
              备注 (可选)
            </label>
            <input
              id="measurement-notes"
              type="text"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500"
              placeholder="例如：晨起测量"
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
              className="flex-1 bg-pink-500 text-white py-2 px-4 rounded-lg hover:bg-pink-600 transition disabled:opacity-70"
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

export default MeasurementModal;

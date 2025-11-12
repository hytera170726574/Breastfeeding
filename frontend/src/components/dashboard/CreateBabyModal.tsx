import { useEffect, useMemo, useState } from 'react';
import type { CSSProperties } from 'react';

import type { Baby } from '../../types/dashboard';

interface CreateBabyModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (values: { name: string; gender: Baby['gender']; birth_date: string }) => Promise<void>;
  anchorY?: number | null;
}

const genders: { value: Baby['gender']; label: string }[] = [
  { value: 'male', label: '男宝宝' },
  { value: 'female', label: '女宝宝' },
  { value: 'other', label: '其他' },
];

export function CreateBabyModal({ open, onClose, onSubmit, anchorY }: CreateBabyModalProps) {
  const [name, setName] = useState('');
  const [gender, setGender] = useState<Baby['gender'] | ''>('');
  const [birthDate, setBirthDate] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setName('');
      setGender('');
      setBirthDate('');
      setError(null);
    }
  }, [open]);

  const containerStyle: CSSProperties = useMemo(() => {
    if (typeof anchorY === 'number') {
      const viewportHeight = typeof window !== 'undefined' ? window.innerHeight : 0;
      const rawTop = Math.max(anchorY - 80, 24);
      const maxTop = viewportHeight ? Math.max(viewportHeight - 400, 24) : rawTop;
      // 让“创建宝宝”对话框跟随触发按钮高度显示
      return { top: Math.min(rawTop, maxTop) };
    }
    return { top: '18vh' };
  }, [anchorY]);

  if (!open) return null;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!name.trim() || !gender || !birthDate) {
      setError('请完整填写宝宝信息');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await onSubmit({ name: name.trim(), gender, birth_date: birthDate });
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建失败，请稍后重试');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-40 bg-black/50 px-4">
      <div
        className="absolute left-1/2 -translate-x-1/2 w-full max-w-xl bg-white rounded-2xl shadow-xl p-6"
        style={containerStyle}
      >
        <div className="text-center mb-4">
          <h2 className="text-2xl font-bold text-gray-800">添加宝宝信息</h2>
          <p className="text-gray-600 mt-2">请填写宝宝的基本信息</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="create-baby-name">宝宝姓名</label>
            <input
              id="create-baby-name"
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="请输入宝宝姓名"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="create-baby-gender">宝宝性别</label>
            <select
              id="create-baby-gender"
              value={gender}
              onChange={(event) => setGender(event.target.value as Baby['gender'])}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            >
              <option value="">请选择性别</option>
              {genders.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="create-baby-birth">出生日期</label>
            <input
              id="create-baby-birth"
              type="date"
              value={birthDate}
              onChange={(event) => setBirthDate(event.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
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

export default CreateBabyModal;
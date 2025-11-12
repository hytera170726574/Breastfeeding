import type { Baby } from '../../types/dashboard';

interface BabyInfoCardProps {
  baby: Baby | null;
  onEdit: () => void;
  onLogout: () => void;
}

function formatGender(gender: Baby['gender'] | null | undefined) {
  if (!gender) return '未知';
  if (gender === 'male') return '男';
  if (gender === 'female') return '女';
  return '其他';
}

function calculateMonths(birthDate?: string | null) {
  if (!birthDate) return '-';
  const birth = new Date(birthDate);
  if (Number.isNaN(birth.getTime())) return '-';
  const now = new Date();
  const years = now.getFullYear() - birth.getFullYear();
  const months = now.getMonth() - birth.getMonth();
  const total = years * 12 + months;
  return `${Math.max(total, 0)}个月`;
}
function formatBirthDate(birthDate?: string | null) {
  if (!birthDate) return '未设置';
  const parsed = new Date(birthDate);
  if (Number.isNaN(parsed.getTime())) {
    const [datePart] = birthDate.split('T');
    return datePart || birthDate;
  }
  const year = parsed.getFullYear();
  const month = String(parsed.getMonth() + 1).padStart(2, '0');
  const day = String(parsed.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function BabyInfoCard({ baby, onEdit, onLogout }: BabyInfoCardProps) {
  return (
    <section className="bg-white rounded-xl shadow-md p-4 w-full">
      <header className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-semibold text-gray-800">我的宝宝</h3>
        <div className="flex items-center gap-3">
          <button onClick={onEdit} className="text-blue-500 hover:text-blue-700 text-sm">编辑</button>
          <button
            onClick={onLogout}
            className="inline-flex items-center px-3 py-1 border border-red-200 text-red-600 bg-white hover:bg-red-50 rounded-full text-sm font-medium transition-colors"
          >
            退出
          </button>
        </div>
      </header>
      <dl className="space-y-2 text-sm text-gray-700">
        <div className="flex justify-between">
          <dt className="text-gray-500">姓名</dt>
          <dd className="font-medium">{baby?.name ?? '未设置'}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-gray-500">性别</dt>
          <dd className="font-medium">{formatGender(baby?.gender)}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-gray-500">出生日期</dt>
          <dd className="font-medium">{formatBirthDate(baby?.birth_date)}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-gray-500">月龄</dt>
          <dd className="font-medium">{calculateMonths(baby?.birth_date)}</dd>
        </div>
      </dl>
    </section>
  );
}

export default BabyInfoCard;
import type { Baby } from '../../types/dashboard';

interface ManageBabiesModalProps {
  open: boolean;
  babies: Baby[];
  currentBabyId?: number | null;
  onClose: () => void;
  onSelect: (babyId: number) => Promise<void>;
  onDelete: (babyId: number) => Promise<void>;
  onUpdate: (payload: { id: number; name?: string; birth_date?: string; gender?: Baby['gender'] }) => Promise<void>;
  onCreate: () => void;
}

export function ManageBabiesModal({ open, babies, currentBabyId, onClose, onSelect, onDelete, onUpdate, onCreate }: ManageBabiesModalProps) {
  if (!open) return null;

  const handleEdit = async (baby: Baby) => {
    const name = window.prompt('编辑宝宝姓名', baby.name ?? '');
    if (name === null) return;
    const birth = window.prompt('编辑出生日期 (YYYY-MM-DD)', baby.birth_date ?? '');
    if (birth === null) return;
    const gender = window.prompt('编辑性别 (male|female|other)', baby.gender ?? 'other');
    if (gender === null) return;
    await onUpdate({ id: baby.id, name: name.trim(), birth_date: birth.trim(), gender: gender.trim() as Baby['gender'] });
  };

  const handleDelete = async (babyId: number) => {
    const confirmed = window.confirm('删除宝宝将移除所有关联记录。是否继续？');
    if (!confirmed) return;
    await onDelete(babyId);
  };

  return (
    <div className="fixed inset-0 z-40 flex items-start justify-center bg-black/40 p-6 pt-20 overflow-y-auto">
      <div className="w-full max-w-3xl bg-white rounded-2xl shadow-xl p-6">
        <header className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">管理宝宝</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">关闭</button>
        </header>

        {babies.length === 0 ? (
          <p className="text-sm text-gray-500">尚无宝宝，您可以创建一个新的宝宝信息。</p>
        ) : (
          <ul className="space-y-3 max-h-72 overflow-auto">
            {babies.map((baby) => {
              const isCurrent = currentBabyId === baby.id;
              return (
                <li key={baby.id} className="p-3 border rounded-lg flex items-center justify-between">
                  <div>
                    <div className="text-sm font-medium text-gray-800">{baby.name ?? '未命名宝宝'}</div>
                    <div className="text-xs text-gray-500">
                      出生: {baby.birth_date ?? '未设置'} · 性别: {baby.gender ?? '未知'}
                    </div>
                  </div>
                  <div className="flex items-center gap-3 text-sm">
                    <button
                      onClick={() => onSelect(baby.id)}
                      className={`px-3 py-1 rounded ${isCurrent ? 'bg-green-600 text-white' : 'bg-green-100 text-green-700 hover:bg-green-200'}`}
                    >
                      {isCurrent ? '当前默认' : '设为默认'}
                    </button>
                    <button
                      onClick={() => handleEdit(baby)}
                      className="px-3 py-1 rounded bg-yellow-100 text-yellow-800 hover:bg-yellow-200"
                    >
                      编辑
                    </button>
                    <button
                      onClick={() => handleDelete(baby.id)}
                      className="px-3 py-1 rounded bg-red-100 text-red-700 hover:bg-red-200"
                    >
                      删除
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}

        <footer className="flex justify-between items-center mt-6">
          <button onClick={onCreate} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
            创建新宝宝
          </button>
          <button onClick={onClose} className="px-4 py-2 bg-gray-200 rounded-lg text-gray-700 hover:bg-gray-300 transition">
            关闭
          </button>
        </footer>
      </div>
    </div>
  );
}

export default ManageBabiesModal;
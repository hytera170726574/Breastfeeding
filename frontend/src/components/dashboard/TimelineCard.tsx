import type { TimelineEvent } from '../../types/dashboard';

interface TimelineCardProps {
  items: TimelineEvent[];
}

const colorMap: Record<TimelineEvent['type'], { dot: string; border: string }> = {
  direct: { dot: 'bg-green-500', border: 'border-green-500' },
  sleep: { dot: 'bg-yellow-400', border: 'border-yellow-400' },
  pump: { dot: 'bg-purple-500', border: 'border-purple-500' },
  bottle_breast: { dot: 'bg-teal-400', border: 'border-teal-400' },
  formula: { dot: 'bg-blue-500', border: 'border-blue-500' },
  diaper_dirty: { dot: 'bg-red-500', border: 'border-red-500' },
  diaper_wet: { dot: 'bg-indigo-400', border: 'border-indigo-400' },
  breast_generic: { dot: 'bg-sky-500', border: 'border-sky-500' },
};

function formatTime(iso?: string | null) {
  if (!iso) return '';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export function TimelineCard({ items }: TimelineCardProps) {
  return (
    <section className="mt-6 bg-white rounded-xl p-4 shadow w-full">
      <p className="text-gray-600 text-sm mb-4">今日时间线</p>
      {items.length === 0 ? (
        <p className="text-sm text-gray-500">今天还没有记录</p>
      ) : (
        <div className="relative pl-12">
          <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-gray-200" />
          {items.map((item) => {
            const color = colorMap[item.type] ?? { dot: 'bg-gray-400', border: 'border-gray-400' };
            const start = formatTime(item.start);
            const end = formatTime(item.end);
            const time = end ? `${start} - ${end}` : start;
            return (
              <div key={`${item.type}-${item.start}-${item.id ?? ''}`} className="mb-4 flex items-start">
                <div className="w-10 flex flex-col items-center">
                  <div className={`w-3 h-3 rounded-full ${color.dot} mt-1`} />
                </div>
                <div className="ml-3 flex-1">
                  <div className={`bg-white border-l-4 p-3 rounded-lg shadow-sm ${color.border}`}>
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-semibold text-gray-800">{item.title}</div>
                      <div className="text-xs text-gray-500">{time}</div>
                    </div>
                    {item.volumeMl != null && item.volumeMl > 0 && (
                      <div className="text-sm text-gray-700 font-medium">{item.volumeMl} ml</div>
                    )}
                    {item.notes && <div className="text-sm text-gray-600 mt-1">{item.notes}</div>}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

export default TimelineCard;
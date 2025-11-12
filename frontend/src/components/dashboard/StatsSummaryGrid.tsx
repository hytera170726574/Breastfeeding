import type { DailyStats } from '../../types/dashboard';

interface StatsSummaryGridProps {
  stats: DailyStats;
}

const items = [
  {
    label: '今日亲喂次数',
    key: 'feedCount' as const,
    color: 'text-green-500',
    format: (value: number) => value.toString(),
  },
  {
    label: '今日睡眠时长',
    key: 'sleepHours' as const,
    color: 'text-yellow-500',
    format: (value: number) => `${value}h`,
  },
  {
    label: '剩余母乳 (ml)',
    key: 'remainingMilk' as const,
    color: 'text-pink-500',
    format: (value: number) => value.toString(),
  },
  {
    label: '今日瓶喂 (ml)',
    key: 'bottleMl' as const,
    color: 'text-blue-500',
    format: (value: number) => value.toString(),
  },
];

export function StatsSummaryGrid({ stats }: StatsSummaryGridProps) {
  return (
    <section className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4">
      {items.map((item) => (
        <article key={item.key} className="bg-white rounded-xl p-4 shadow text-center">
          <p className="text-gray-600 text-sm">{item.label}</p>
          <p className={`text-2xl font-bold ${item.color}`}>{item.format(stats[item.key])}</p>
        </article>
      ))}
    </section>
  );
}

export default StatsSummaryGrid;
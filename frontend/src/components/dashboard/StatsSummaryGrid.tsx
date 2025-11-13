import type { DailyStats, Measurement } from '../../types/dashboard';

interface StatsSummaryGridProps {
  stats: DailyStats;
  latestMeasurement?: Measurement | null;
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

export function StatsSummaryGrid({ stats, latestMeasurement }: StatsSummaryGridProps) {
  const heightValue = latestMeasurement?.heightCm != null ? `${latestMeasurement.heightCm}` : '--';
  const weightValue = latestMeasurement?.weightKg != null ? `${latestMeasurement.weightKg}` : '--';
  const measurementDate = latestMeasurement?.measurementDate
    ? new Date(latestMeasurement.measurementDate)
    : null;
  const measurementDateLabel = measurementDate
    ? new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: 'numeric', day: 'numeric' }).format(measurementDate)
    : null;
  const measurementTooltip = measurementDateLabel ? `记录日期：${measurementDateLabel}` : '暂无记录';

  return (
    <section className="mt-8 grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
      {items.map((item) => (
        <article key={item.key} className="bg-white rounded-xl p-4 shadow text-center">
          <p className="text-gray-600 text-sm">{item.label}</p>
          <p className={`text-2xl font-bold ${item.color}`}>{item.format(stats[item.key])}</p>
        </article>
      ))}
      <article className="bg-white rounded-xl p-4 shadow text-center" title={measurementTooltip} aria-label={measurementTooltip} role="note">
        <p className="text-gray-600 text-sm">身高体重</p>
        <p className="mt-3 text-lg font-semibold text-rose-500">{`${heightValue} / ${weightValue}`}</p>
        <p className="mt-1 text-[11px] text-gray-400">{measurementDateLabel ? `${measurementDateLabel}` : '尚未记录'}</p>
      </article>
    </section>
  );
}

export default StatsSummaryGrid;
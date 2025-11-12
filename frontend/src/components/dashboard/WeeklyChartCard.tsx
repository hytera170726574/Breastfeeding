import { useMemo } from 'react';
import { Bar } from 'react-chartjs-2';
import { Chart, registerables } from 'chart.js';

import type { WeeklyStatsDataset } from '../../types/dashboard';

Chart.register(...registerables);

interface WeeklyChartCardProps {
  stats: WeeklyStatsDataset | null;
}

export function WeeklyChartCard({ stats }: WeeklyChartCardProps) {
  const hasData = stats && stats.directCounts.length > 0;

  const data = useMemo(
    () => ({
      labels: stats?.labels ?? [],
      datasets: [
        {
          label: '亲喂次数',
          data: stats?.directCounts ?? [],
          backgroundColor: 'rgba(34,197,94,0.9)',
          yAxisID: 'yLeft',
        },
        {
          label: '大便次数',
          data: stats?.dirtyCounts ?? [],
          backgroundColor: 'rgba(239,68,68,0.9)',
          yAxisID: 'yLeft',
        },
        {
          label: '小便次数',
          data: stats?.wetCounts ?? [],
          backgroundColor: 'rgba(59,130,246,0.9)',
          yAxisID: 'yLeft',
        },
        {
          label: '睡眠分钟',
          data: stats?.sleepMinutes ?? [],
          backgroundColor: 'rgba(168,85,247,0.9)',
          yAxisID: 'yRight',
        },
        {
          label: '瓶喂(ml)',
          data: stats?.bottleMl ?? [],
          backgroundColor: 'rgba(14,165,233,0.9)',
          yAxisID: 'yRight',
        },
      ],
    }),
    [stats]
  );

  const options = useMemo(
    () => ({
      responsive: true,
      interaction: { mode: 'index' as const, intersect: false },
      scales: {
        yLeft: {
          type: 'linear' as const,
          position: 'left' as const,
          title: { display: true, text: '次数' },
          beginAtZero: true,
        },
        yRight: {
          type: 'linear' as const,
          position: 'right' as const,
          title: { display: true, text: '分钟 / ml' },
          beginAtZero: true,
          grid: { drawOnChartArea: false },
        },
      },
      plugins: {
        legend: { position: 'top' as const },
      },
    }),
    []
  );

  return (
    <section className="mt-6 bg-white rounded-xl p-4 shadow w-full">
      <p className="text-gray-600 text-sm mb-4">近7天统计（不含今天）</p>
      {hasData ? (
        <Bar options={options} data={data} />
      ) : (
        <p className="text-sm text-gray-500">暂无数据</p>
      )}
    </section>
  );
}

export default WeeklyChartCard;
interface ActionButtonGridProps {
  onStartDirect: (anchor: number) => void;
  onStartSleep: (anchor: number) => void;
  onOpenBottle: (anchor: number) => void;
  onOpenDiaper: (anchor: number) => void;
  onOpenMeasurement: (anchor: number) => void;
}

const buttons = [
  {
    id: 'direct',
    label: '亲喂',
    color: 'bg-green-500 hover:bg-green-600',
    onClickKey: 'onStartDirect' as const,
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
      </svg>
    ),
  },
  {
    id: 'sleep',
    label: '睡眠',
    color: 'bg-yellow-500 hover:bg-yellow-600',
    onClickKey: 'onStartSleep' as const,
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
  },
  {
    id: 'bottle',
    label: '瓶喂',
    color: 'bg-blue-500 hover:bg-blue-600',
    onClickKey: 'onOpenBottle' as const,
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
    ),
  },
  {
    id: 'diaper',
    label: '记录',
    color: 'bg-purple-500 hover:bg-purple-600',
    onClickKey: 'onOpenDiaper' as const,
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
    ),
  },
  {
    id: 'measurement',
    label: '身高体重',
    color: 'bg-pink-500 hover:bg-pink-600',
    onClickKey: 'onOpenMeasurement' as const,
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v18m9-9H3" />
      </svg>
    ),
  },
];

export function ActionButtonGrid(props: ActionButtonGridProps) {
  const handlerMap = {
    onStartDirect: props.onStartDirect,
    onStartSleep: props.onStartSleep,
    onOpenBottle: props.onOpenBottle,
    onOpenDiaper: props.onOpenDiaper,
    onOpenMeasurement: props.onOpenMeasurement,
  };

  return (
    <section className="w-full">
  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
        {buttons.map((item) => (
          <button
            key={item.id}
            onClick={(event) => {
              const rect = event.currentTarget.getBoundingClientRect();
              const anchor = rect.top + rect.height / 2;
              // 记录按钮在视口中的垂直位置，让后续弹层对齐同一高度
              void handlerMap[item.onClickKey](anchor);
            }}
            className={`w-full py-5 ${item.color} text-white font-semibold rounded-2xl text-lg flex items-center justify-center transition-all shadow-md hover:-translate-y-1`}>
            {item.icon}
            {item.label}
          </button>
        ))}
      </div>
    </section>
  );
}

export default ActionButtonGrid;
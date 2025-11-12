// src/pages/DashboardPage.tsx
import ActionButtonGrid from '../components/dashboard/ActionButtonGrid';
import BabyInfoCard from '../components/dashboard/BabyInfoCard';
import BottleFeedModal from '../components/dashboard/BottleFeedModal';
import CreateBabyModal from '../components/dashboard/CreateBabyModal';
import DiaperModal from '../components/dashboard/DiaperModal';
import ManageBabiesModal from '../components/dashboard/ManageBabiesModal';
import StatsSummaryGrid from '../components/dashboard/StatsSummaryGrid';
import TimelineCard from '../components/dashboard/TimelineCard';
import TimerModal from '../components/dashboard/TimerModal';
import Toast from '../components/dashboard/Toast';
import WeeklyChartCard from '../components/dashboard/WeeklyChartCard';
import { useDashboard } from '../hooks/useDashboard';

const DashboardPage = () => {
  const {
    state,
    modals,
    babyList,
    toast,
    modalAnchor,
    timerAnchor,
    openModal,
    closeModal,
    dismissToast,
    actions,
  } = useDashboard();

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentBabyId');
    window.location.reload();
  };

  const handleStopTimer = async () => {
    if (!state.timer) return;
    if (state.timer.mode === 'direct') {
      await actions.stopDirect();
    } else {
      await actions.stopSleep();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 to-purple-100 p-4 sm:p-6 lg:p-10 flex items-center justify-center">
      <div className="relative w-full max-w-6xl bg-white/90 backdrop-blur rounded-2xl shadow-2xl p-6 sm:p-8 lg:p-10 space-y-6">
        <div className="flex flex-col md:flex-row gap-6">
          <aside className="md:w-2/5 bg-gradient-to-br from-blue-500 to-purple-600 text-white p-8 rounded-xl flex flex-col justify-between">
            <div>
              <h1 className="text-3xl font-bold">母乳喂养记录</h1>
              <p className="mt-3 text-blue-100">记录宝宝成长的每一个珍贵时刻</p>
            </div>
            <ul className="mt-6 space-y-3 text-sm text-blue-50">
              <li className="flex items-center gap-3">
                <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-white/20">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                </span>
                记录喂养时间和时长
              </li>
              <li className="flex items-center gap-3">
                <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-white/20">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                </span>
                跟踪宝宝体重变化
              </li>
              <li className="flex items-center gap-3">
                <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-white/20">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                </span>
                生成喂养统计报告
              </li>
            </ul>
          </aside>

          <main className="md:w-3/5 space-y-6">
            <BabyInfoCard baby={state.baby} onEdit={() => openModal('manageBabies')} onLogout={handleLogout} />
            <ActionButtonGrid
              onStartDirect={(anchor: number) => {
                void actions.startDirect(anchor);
              }}
              onStartSleep={(anchor: number) => {
                void actions.startSleep(anchor);
              }}
              onOpenBottle={(anchor: number) => {
                if (!state.baby) {
                  openModal('createBaby', anchor);
                  return;
                }
                openModal('bottleFeed', anchor);
              }}
              onOpenDiaper={(anchor: number) => {
                if (!state.baby) {
                  openModal('createBaby', anchor);
                  return;
                }
                openModal('diaper', anchor);
              }}
            />
            <StatsSummaryGrid stats={state.dailyStats} />
          </main>
        </div>

        <WeeklyChartCard stats={state.weeklyStats} />
        <TimelineCard items={state.timeline} />

        {state.loading && (
          <div className="absolute inset-0 bg-white/60 backdrop-blur flex items-center justify-center rounded-2xl">
            <span className="text-gray-600 text-sm">数据加载中…</span>
          </div>
        )}

        {toast && (
          <div className="fixed top-6 right-6 z-50">
            <Toast type={toast.type} message={toast.message} onClose={dismissToast} />
          </div>
        )}

        <CreateBabyModal
          open={modals.createBaby}
          anchorY={modalAnchor}
          onClose={() => closeModal('createBaby')}
          onSubmit={actions.createBaby}
        />

        <ManageBabiesModal
          open={modals.manageBabies}
          babies={babyList}
          currentBabyId={state.baby?.id}
          onClose={() => closeModal('manageBabies')}
          onSelect={actions.selectBaby}
          onDelete={actions.deleteBaby}
          onUpdate={actions.updateBaby}
          onCreate={() => {
            closeModal('manageBabies');
            openModal('createBaby');
          }}
        />

        <BottleFeedModal
          open={modals.bottleFeed}
          anchorY={modalAnchor}
          onClose={() => closeModal('bottleFeed')}
          onSubmit={actions.submitBottle}
        />

        <DiaperModal
          open={modals.diaper}
          anchorY={modalAnchor}
          onClose={() => closeModal('diaper')}
          onSubmit={actions.submitDiaper}
        />

        <TimerModal timer={state.timer} anchorY={timerAnchor} onStop={handleStopTimer} />
      </div>
    </div>
  );
};

export default DashboardPage;

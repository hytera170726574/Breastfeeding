// Backup of timer JS: flip-clock and helpers
// Functions: formatMinutesSecondsMMMSS, updateFlipClock, openSleepTimer

function formatMinutesSecondsMMMSS(ms) {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(3, '0');
  const seconds = String(totalSeconds % 60).padStart(2, '0');
  return `${minutes}:${seconds}`;
}

function updateFlipClock(timeStr) {
  const parts = timeStr.split(':');
  const minutes = parts[0];
  const seconds = parts[1];
  const groupMin = document.querySelector('.flip-group[data-group="minutes"] .flip-card');
  const groupSec = document.querySelector('.flip-group[data-group="seconds"] .flip-card');
  if (!groupMin || !groupSec) return;

  const applyFlip = (card, newText) => {
    const top = card.querySelector('.top');
    const bottom = card.querySelector('.bottom');
    const flipTop = card.querySelector('.flip-top');
    const flipBottom = card.querySelector('.flip-bottom');
    if (!top || !bottom || !flipTop || !flipBottom) return;
    if (top.textContent !== newText) {
      flipTop.textContent = top.textContent;
      flipBottom.textContent = newText;
      card.classList.remove('flip-anim');
      void card.offsetWidth;
      card.classList.add('flip-anim');
      setTimeout(() => {
        top.textContent = newText;
        bottom.textContent = newText;
        card.classList.remove('flip-anim');
      }, 600);
    }
  };

  applyFlip(groupSec, seconds);
  applyFlip(groupMin, minutes);
}

function openSleepTimer(serverStartIso) {
  const modal = document.getElementById('sleep-timer-modal');
  if (!modal) return;
  modal.classList.remove('hidden');
  const display = document.getElementById('sleep-timer-display');
  let startMs = Date.now();
  if (serverStartIso) {
    const parsed = Date.parse(serverStartIso);
    if (!isNaN(parsed)) startMs = parsed;
  }
  if (window.sleepTimerInterval) clearInterval(window.sleepTimerInterval);
  const update = () => {
    const diff = Date.now() - startMs;
    const timeStr = formatMinutesSecondsMMMSS(diff);
    updateFlipClock(timeStr);
  };
  updateFlipClock('000:00');
  update();
  window.sleepTimerInterval = setInterval(update, 1000);
}

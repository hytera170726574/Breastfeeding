/* 3D Timer (inspired by mrahmedayyan/3D-Digital-Clock). Original minimal JS. */
(function(){
  function pad(n, w){ n = String(n); while(n.length < w) n = '0'+n; return n; }

  function createDigit(initial){
    const d = document.createElement('div');
    d.className = 'digit';
    d.innerHTML = `
      <div class="face top">00</div>
      <div class="face bottom">00</div>
      <div class="flip-top">00</div>
      <div class="flip-bottom">00</div>
    `;
    setDigit(d, initial);
    return d;
  }
  function setDigit(digitEl, text){
    const top = digitEl.querySelector('.top');
    const bottom = digitEl.querySelector('.bottom');
    const flipTop = digitEl.querySelector('.flip-top');
    const flipBottom = digitEl.querySelector('.flip-bottom');
    const current = top.textContent;
    if (current === text) return;
    flipTop.textContent = current;
    flipBottom.textContent = text;
    digitEl.classList.remove('flip');
    void digitEl.offsetWidth;
    digitEl.classList.add('flip');
    setTimeout(()=>{
      top.textContent = text;
      bottom.textContent = text;
      digitEl.classList.remove('flip');
    }, 600);
  }

  function buildClock(container){
    container.innerHTML = '';
    const wrap = document.createElement('div');
    wrap.className = 'clock3d';
    const min = createDigit('000');
    const colon = document.createElement('div'); colon.className = 'colon'; colon.textContent = ':';
    const sec = createDigit('00');
    wrap.appendChild(min); wrap.appendChild(colon); wrap.appendChild(sec);
    container.appendChild(wrap);
    return {min, sec};
  }

  function Timer3D(container){
    this.container = container;
    const parts = buildClock(container);
    this.minEl = parts.min; this.secEl = parts.sec;
    this.interval = null;
    this.startMs = null;
  }
  Timer3D.prototype.start = function(startIso){
    this.startMs = Date.now();
    if (startIso){ const p = Date.parse(startIso); if(!isNaN(p)) this.startMs = p; }
    const tick = ()=>{
      const diff = Date.now() - this.startMs;
      const totalSec = Math.floor(diff/1000);
      const m = pad(Math.floor(totalSec/60),3);
      const s = pad(totalSec%60,2);
      setDigit(this.minEl, m);
      setDigit(this.secEl, s);
    };
    tick();
    this.interval = setInterval(tick, 1000);
  };
  Timer3D.prototype.stop = function(){
    if (this.interval){ clearInterval(this.interval); this.interval = null; }
  };

  window.Timer3D = Timer3D;
})();

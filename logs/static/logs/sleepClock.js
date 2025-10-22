
(function () {
// SVG 要素を取得
const svg = document.getElementById('sleepClock');
if (!svg) return;

// --- データ属性（H:i の分解後）を取得 ---
const sH = Number(svg.dataset.sleepH);
const sM = Number(svg.dataset.sleepM);
const wH = Number(svg.dataset.wakeH);
const wM = Number(svg.dataset.wakeM);

// 値が欠けている場合は描画しない
if ([sH, sM, wH, wM].some(x => Number.isNaN(x))) return;

// ローカル日の分単位 0..1439 に変換
let sMin = sH * 60 + sM; // 入眠
let wMin = wH * 60 + wM; // 起床

// 跨日（起床が入眠より小さい）なら翌日に延長
let endMin = wMin;
if (wMin <= sMin) endMin += 1440;

// --- 描画パラメータ ---
const cx = 110, cy = 110;  // 中心
const r  = 78;             // 半径（strokeがはみ出ない程度に小さめ）
const minToRad = m => ((m / 1440) * 360 - 90) * Math.PI / 180;

// --- 目盛り（1時間ごと、3時間ごと長め） ---
try {
    const hourGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    hourGroup.setAttribute('stroke', '#9ca3af');       // gray-300
    hourGroup.setAttribute('stroke-width', '1.5');
    for (let h = 0; h < 24; h++) {
    const a  = ((h / 24) * 360 - 90) * Math.PI / 180;
    const x1 = cx + Math.cos(a) * (r + 6);
    const y1 = cy + Math.sin(a) * (r + 6);
    const x2 = cx + Math.cos(a) * (r + (h % 3 === 0 ? 14 : 10)); // 3時間ごと長く
    const y2 = cy + Math.sin(a) * (r + (h % 3 === 0 ? 14 : 10));
    const tick = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    tick.setAttribute('x1', x1); tick.setAttribute('y1', y1);
    tick.setAttribute('x2', x2); tick.setAttribute('y2', y2);
    hourGroup.appendChild(tick);
    }
    const arcEl = document.getElementById('sleepArc');
    if (arcEl && arcEl.parentNode) {
    svg.insertBefore(hourGroup, arcEl);
    } else {
    svg.appendChild(hourGroup);
    }
} catch (e) {
    console.warn('Tick draw error:', e);
}

// --- 円弧パス生成（時計回り・大円弧フラグ対応） ---
function arcPath(cx, cy, r, startRad, endRad) {
    const TAU = Math.PI * 2;
    const norm = x => ((x % TAU) + TAU) % TAU;
    const s = norm(startRad);
    let e = norm(endRad);
    while (e <= s) e += TAU;             // 時計回りになるよう調整
    const sx = cx + r * Math.cos(s), sy = cy + r * Math.sin(s);
    const ex = cx + r * Math.cos(e), ey = cy + r * Math.sin(e);
    const largeArc = (e - s) > Math.PI ? 1 : 0; // 180°超なら1
    const sweep = 1;                              // 時計回り
    return `M ${sx} ${sy} A ${r} ${r} 0 ${largeArc} ${sweep} ${ex} ${ey}`;
}

// --- 弧とドットを配置 ---
const startRad = minToRad(sMin);
const endRad   = minToRad(endMin);

const arc = document.getElementById('sleepArc');
if (arc) {
    arc.setAttribute('d', arcPath(cx, cy, r, startRad, endRad));
    // 必要なら色や太さを mood に応じて変える処理をここに追加可能
    // 例: arc.setAttribute('stroke', '#16a34a'); // 良い気分=緑
}

const setDot = (id, rad) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.setAttribute('cx', cx + r * Math.cos(rad));
    el.setAttribute('cy', cy + r * Math.sin(rad));
};

setDot('startDot', startRad);
setDot('endDot',   endRad);
})();
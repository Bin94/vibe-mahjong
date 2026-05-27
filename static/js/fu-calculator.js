/**
 * Vibe Mahjong - Fu Calculator
 */

class ParticleSystem {
    constructor(canvas) {
        this.canvas = canvas; if (!canvas) return;
        this.ctx = canvas.getContext('2d'); this.particles = []; this.mouse = { x: null, y: null };
        this.init();
    }
    init() { this.resize(); this.createParticles(); window.addEventListener('resize', () => { this.resize(); this.createParticles(); }); window.addEventListener('mousemove', (e) => { this.mouse.x = e.clientX; this.mouse.y = e.clientY; }); this.animate(); }
    resize() { this.canvas.width = window.innerWidth; this.canvas.height = window.innerHeight; }
    createParticles() { const count = Math.min(Math.floor(window.innerWidth / 15), 50); this.particles = []; const isWa = document.body.dataset.theme === 'wa'; const colors = isWa ? ['#c41e3a', '#d4a574', '#ffd700', '#8b0000'] : ['#00ff88', '#00ccff', '#ff0080', '#ffd700']; for (let i = 0; i < count; i++) { this.particles.push({ x: Math.random() * this.canvas.width, y: Math.random() * this.canvas.height, vx: (Math.random() - 0.5) * 0.3, vy: (Math.random() - 0.5) * 0.3, radius: Math.random() * 2 + 0.5, color: colors[Math.floor(Math.random() * colors.length)] }); } }
    animate() { if (!this.ctx) return; this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height); this.particles.forEach(p => { if (this.mouse.x !== null) { const dx = this.mouse.x - p.x, dy = this.mouse.y - p.y, d = Math.sqrt(dx*dx + dy*dy); if (d < 100) { const f = (100 - d) / 100; p.vx += (dx/d) * f * 0.01; p.vy += (dy/d) * f * 0.01; } } p.x += p.vx; p.y += p.vy; if (p.x < 0 || p.x > this.canvas.width) p.vx *= -1; if (p.y < 0 || p.y > this.canvas.height) p.vy *= -1; p.vx *= 0.99; p.vy *= 0.99; this.ctx.beginPath(); this.ctx.arc(p.x, p.y, p.radius, 0, Math.PI*2); this.ctx.fillStyle = p.color; this.ctx.globalAlpha = 0.5; this.ctx.fill(); this.ctx.globalAlpha = 1; }); requestAnimationFrame(() => this.animate()); }
}

class ThemeToggle {
    constructor() { this.btn = document.getElementById('theme-toggle'); this.body = document.body; if (!this.btn) return; this.cyberIcon = this.btn.querySelector('.cyber-icon'); this.waIcon = this.btn.querySelector('.wa-icon'); this.init(); }
    init() { const saved = localStorage.getItem('mahjong-theme') || 'cyber'; this.setTheme(saved); this.btn.addEventListener('click', () => { const newTheme = this.body.dataset.theme === 'cyber' ? 'wa' : 'cyber'; this.setTheme(newTheme); localStorage.setItem('mahjong-theme', newTheme); }); }
    setTheme(theme) { this.body.dataset.theme = theme; if (this.cyberIcon && this.waIcon) { this.cyberIcon.style.display = theme === 'cyber' ? 'inline' : 'none'; this.waIcon.style.display = theme === 'cyber' ? 'none' : 'inline'; } }
}

class WinAnimation {
    constructor(container) {
        this.container = container;
        this.emojis = ['🎉', '✨', '🎊', '🏆', '🎆', '🔥', '🌟', '🎇', '💎', '🥳'];
        this.confettiColors = ['#ff6b6b', '#ffd93d', '#6bcf7f', '#4d96ff', '#ff8cc8', '#a78bfa', '#00ff88', '#ffd700'];
        this.isMobile = window.innerWidth <= 768;
    }

    play(level) {
        level = level || 'normal';
        this.isMobile = window.innerWidth <= 768;
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            z-index: 9999; pointer-events: none; overflow: hidden;
        `;
        this.container.appendChild(overlay);

        // Flash
        const flash = document.createElement('div');
        let flashColors = 'rgba(255,215,0,0.4), rgba(0,255,136,0.2), transparent';
        if (level === 'yakuman') {
            flashColors = 'rgba(255,0,128,0.5), rgba(255,215,0,0.4), transparent';
        } else if (level === 'high') {
            flashColors = 'rgba(255,100,0,0.4), rgba(255,215,0,0.3), transparent';
        }
        flash.style.cssText = `
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: radial-gradient(circle at 50% 50%, ${flashColors});
            opacity: 0; animation: winFlash 1.5s ease-out forwards;
        `;
        overlay.appendChild(flash);

        // Confetti count by level (reduce on mobile)
        let confettiCount = 0, emojiCount = 0, showText = false, textHtml = '';
        const mobileFactor = this.isMobile ? 0.5 : 1;
        if (level === 'normal') {
            confettiCount = Math.floor(8 * mobileFactor);
            showText = false;
        } else if (level === 'medium') {
            confettiCount = Math.floor(30 * mobileFactor);
            emojiCount = Math.floor(10 * mobileFactor);
            showText = true;
            textHtml = '满贯！🎆';
        } else if (level === 'high') {
            confettiCount = Math.floor(55 * mobileFactor);
            emojiCount = Math.floor(18 * mobileFactor);
            showText = true;
            textHtml = '🎉 倍满 · 三倍满！🎉';
        } else if (level === 'yakuman') {
            confettiCount = Math.floor(80 * mobileFactor);
            emojiCount = Math.floor(25 * mobileFactor);
            showText = true;
            textHtml = '🔥🌟 役满！🌟🔥';
        }

        // Confetti (falling ribbons)
        for (let i = 0; i < confettiCount; i++) {
            const conf = document.createElement('div');
            const w = 5 + Math.random() * 7;
            const h = 10 + Math.random() * 18;
            const left = Math.random() * 100;
            const delay = Math.random() * 2.5;
            const duration = 2 + Math.random() * 2.5;
            const color = this.confettiColors[Math.floor(Math.random() * this.confettiColors.length)];
            const rotate = Math.random() * 360;
            conf.style.cssText = `
                position: absolute; width: ${w}px; height: ${h}px;
                background: ${color}; border-radius: 2px;
                left: ${left}%; top: -30px;
                transform: rotate(${rotate}deg);
                opacity: 0.9;
                animation: confettiFall ${duration}s linear forwards;
                animation-delay: ${delay}s;
            `;
            overlay.appendChild(conf);
        }

        // Emoji burst (only for medium/high/yakuman)
        const emojiTop = this.isMobile ? '10%' : '15%';
        for (let i = 0; i < emojiCount; i++) {
            const el = document.createElement('div');
            const emoji = this.emojis[Math.floor(Math.random() * this.emojis.length)];
            const left = 15 + Math.random() * 70;
            const delay = 0.2 + Math.random() * 0.8;
            const size = this.isMobile ? (0.8 + Math.random() * 0.7) : (1.2 + Math.random() * 1.5);
            el.textContent = emoji;
            el.style.cssText = `
                position: absolute; font-size: ${size}rem;
                left: ${left}%; top: ${emojiTop};
                animation: emojiPop 1.5s ease-out forwards;
                animation-delay: ${delay}s;
            `;
            overlay.appendChild(el);
        }

        // Main celebration text
        if (showText) {
            const text = document.createElement('div');
            text.innerHTML = textHtml;
            let fontSize = this.isMobile ? '1.2rem' : '2rem';
            if (level === 'yakuman') fontSize = this.isMobile ? '1.8rem' : '3rem';
            const textTop = this.isMobile ? '25%' : '30%';
            text.style.cssText = `
                position: absolute; top: ${textTop}; left: 50%;
                transform: translate(-50%, -50%);
                font-size: ${fontSize}; font-weight: 900;
                color: #ffd700; white-space: nowrap;
                text-shadow: 0 0 30px rgba(255, 215, 0, 0.8), 0 0 60px rgba(255, 215, 0, 0.5), 0 4px 8px rgba(0,0,0,0.5);
                animation: winText 2s ease-out forwards;
                font-family: 'Noto Sans SC', sans-serif;
            `;
            overlay.appendChild(text);
        }

        // Cleanup
        const duration = level === 'yakuman' ? 4000 : 3000;
        setTimeout(() => {
            overlay.style.transition = 'opacity 0.8s ease';
            overlay.style.opacity = '0';
            setTimeout(() => overlay.remove(), 800);
        }, duration);
    }
}

class FuCalculator {
    constructor() {
        this.hand = [];
        this.handDisplay = document.getElementById('hand-display');
        this.handCount = document.getElementById('hand-count');
        this.resultArea = document.getElementById('calc-result');
        this.msgArea = document.getElementById('message-area');
        this.params = { agari: 'tsumo', dealer: true, tsumo: true };
        this.winAnim = new WinAnimation(document.body);
        this.init();
    }
    init() {
        document.querySelectorAll('.tile-btn').forEach(btn => {
            btn.addEventListener('click', () => this.addTile(btn.dataset.tile));
        });
        document.getElementById('btn-clear').addEventListener('click', () => this.clearHand());
        document.getElementById('btn-random-tenpai').addEventListener('click', () => this.randomHand());
        document.getElementById('btn-calculate').addEventListener('click', () => this.calculate());
        document.querySelectorAll('.param-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const param = btn.dataset.param;
                const value = btn.dataset.value === 'true' ? true : (btn.dataset.value === 'false' ? false : btn.dataset.value);
                this.params[param] = value;
                document.querySelectorAll(`.param-btn[data-param="${param}"]`).forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });
        // Stepper controls
        document.querySelectorAll('.stepper-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const stepper = btn.dataset.stepper;
                const delta = parseInt(btn.dataset.delta, 10);
                const valueEl = document.getElementById(stepper + '-value');
                let val = parseInt(valueEl.textContent, 10) || 0;
                val = Math.max(0, Math.min(20, val + delta));
                valueEl.textContent = val;
            });
        });
    }
    addTile(tile) {
        if (this.hand.length >= 14) { this.showMessage('手牌已达14张上限'); return; }
        const count = this.hand.filter(t => t === tile).length;
        if (count >= 4) { this.showMessage('同一种牌最多4张'); return; }
        this.hand.push(tile); this.renderHand();
    }
    removeTile(index) { this.hand.splice(index, 1); this.renderHand(); }
    clearHand() { this.hand = []; this.renderHand(); this.resultArea.style.display = 'none'; if (this.msgArea) { this.msgArea.innerHTML = ''; this.msgArea.style.display = 'none'; } }
    randomHand() {
        const suits = ['m', 'p', 's']; const suit = suits[Math.floor(Math.random() * 3)];
        this.hand = [];
        [1, 4, 7].forEach(n => { this.hand.push(`${suit}${n}`, `${suit}${n+1}`, `${suit}${n+2}`); });
        this.hand.push(`${suit}2`, `${suit}3`, `${suit}4`, `${suit}5`, `${suit}5`);
        this.renderHand(); this.resultArea.style.display = 'none'; if (this.msgArea) { this.msgArea.innerHTML = ''; this.msgArea.style.display = 'none'; }
    }
    renderHand() {
        this.handCount.textContent = this.hand.length;
        if (this.hand.length === 0) { this.handDisplay.innerHTML = '<div class="hand-placeholder">选择14张和牌手牌...</div>'; return; }
        if (window.MahgenTiles) {
            const isMobile = window.innerWidth <= 768;
            const tileSize = isMobile ? 28 : 42;
            MahgenTiles.renderTiles(this.handDisplay, this.hand, { size: tileSize, gap: 3 });
            const imgs = this.handDisplay.querySelectorAll('.tile-png');
            imgs.forEach((img, i) => {
                img.style.cursor = 'pointer';
                img.addEventListener('click', () => this.removeTile(i));
            });
        }
    }
    async calculate() {
        if (this.msgArea) { this.msgArea.innerHTML = ''; this.msgArea.style.display = 'none'; }
        if (this.hand.length !== 14) { this.showMessage(`请选择14张牌（当前${this.hand.length}张）`); return; }
        const doraVal = document.getElementById('dora-value');
        const uraVal = document.getElementById('ura-dora-value');
        const dora = doraVal ? parseInt(doraVal.textContent, 10) || 0 : 0;
        const uraDora = uraVal ? parseInt(uraVal.textContent, 10) || 0 : 0;
        try {
            const response = await fetch('/api/calculate-fu', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    hand: this.hand, is_tsumo: this.params.tsumo,
                    is_tsumo_agari: this.params.agari === 'tsumo',
                    is_dealer: this.params.dealer,
                    dora: dora, ura_dora: uraDora
                })
            });
            const data = await response.json();
            if (data.error) { this.showMessage(data.error); return; }
            this.winAnim.play(data.anim_level || 'normal');
            this.renderResult(data);
        } catch (error) { this.showMessage('计算失败: ' + error.message); }
    }
    renderResult(data) {
        const score = data.score;
        let detailHtml = '';
        if (score.type.includes('自摸')) {
            if (score.type.includes('亲家')) {
                detailHtml = `<div class="result-detail-item"><div class="result-detail-value">${score.all || 0}</div><div class="result-detail-label">每家支付</div></div><div class="result-detail-item"><div class="result-detail-value">${score.total || 0}</div><div class="result-detail-label">合计收入</div></div>`;
            } else {
                detailHtml = `<div class="result-detail-item"><div class="result-detail-value">${score.dealer || 0}</div><div class="result-detail-label">庄家支付</div></div><div class="result-detail-item"><div class="result-detail-value">${score.others || 0}</div><div class="result-detail-label">闲家支付</div></div><div class="result-detail-item"><div class="result-detail-value">${score.total || 0}</div><div class="result-detail-label">合计收入</div></div>`;
            }
        } else {
            detailHtml = `<div class="result-detail-item"><div class="result-detail-value">${score.from_player || 0}</div><div class="result-detail-label">放铳者支付</div></div><div class="result-detail-item"><div class="result-detail-value">${score.total || 0}</div><div class="result-detail-label">合计收入</div></div>`;
        }

        let yakuHtml = '';
        if (data.yaku && data.yaku.length > 0) {
            const yakuList = data.yaku.map(y => {
                const yakumanClass = (y.han >= 13) ? 'yakuman' : '';
                return `<span class="result-yaku-item ${yakumanClass}">${y.name} ${y.han}番</span>`;
            }).join('');
            yakuHtml = `
                <div class="result-yaku-section">
                    <div class="result-yaku-title">🎯 自动识别役种 (${data.yaku.length}种)</div>
                    <div class="result-yaku-list">${yakuList}</div>
                    <div class="result-breakdown">
                        ${data.is_yakuman ? `
                            <div class="result-breakdown-item total"><span>役满</span><span>役满</span></div>
                        ` : `
                            <div class="result-breakdown-item"><span>役种</span><span>${data.auto_han}番</span></div>
                            ${data.dora > 0 ? `<div class="result-breakdown-item"><span>宝牌</span><span>+${data.dora}番</span></div>` : ''}
                            ${data.ura_dora > 0 ? `<div class="result-breakdown-item"><span>里宝牌</span><span>+${data.ura_dora}番</span></div>` : ''}
                            <div class="result-breakdown-item total"><span>总番数</span><span>${data.total_han}番</span></div>
                        `}
                    </div>
                </div>
            `;
        } else {
            yakuHtml = `
                <div class="result-yaku-section">
                    <div class="result-yaku-title">🎯 役种识别</div>
                    <div style="color:var(--text-muted);font-size:0.9rem;">未识别到役种（纯符数计算）</div>
                    ${data.dora > 0 ? `<div class="result-breakdown-item" style="margin-top:0.5rem"><span>宝牌</span><span>+${data.dora}番</span></div>` : ''}
                    ${data.ura_dora > 0 ? `<div class="result-breakdown-item"><span>里宝牌</span><span>+${data.ura_dora}番</span></div>` : ''}
                </div>
            `;
        }

        this.resultArea.innerHTML = `
            <div class="mahgen-container" id="mahgen-fu-hand" style="margin-bottom:1rem;"><span class="mahgen-loading">生成中...</span></div>
            ${yakuHtml}
            <div class="result-score">${score.total || 0} 点</div>
            <div class="result-score-label">${data.is_yakuman ? '役满 · ' + score.type : data.fu + '符 ' + data.total_han + '番 · ' + score.type}</div>
            <div class="result-details">${detailHtml}</div>
        `;
        if (window.MahgenTiles && this.hand.length > 0) {
            const isMobile = window.innerWidth <= 768;
            const resultSize = isMobile ? 24 : 38;
            const container = document.getElementById('mahgen-fu-hand');
            if (container) MahgenTiles.renderTiles(container, this.hand, { size: resultSize, gap: 3 });
        }
        this.resultArea.style.display = 'block';
        this.resultArea.scrollIntoView({ behavior: 'smooth' });
    }
    showMessage(msg) {
        if (!this.msgArea) return;
        const div = document.createElement('div');
        div.className = 'warning-message';
        div.textContent = msg;
        div.style.animation = 'fadeIn 0.3s ease';
        this.msgArea.innerHTML = '';
        this.msgArea.appendChild(div);
        this.msgArea.style.display = 'block';
        setTimeout(() => {
            div.style.opacity = '0';
            setTimeout(() => {
                div.remove();
                if (this.msgArea.children.length === 0) this.msgArea.style.display = 'none';
            }, 300);
        }, 3000);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new ParticleSystem(document.getElementById('particle-canvas'));
    new ThemeToggle();
    new FuCalculator();
});

/**
 * Vibe Mahjong - Hand Analyzer
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
        overlay.style.cssText = `position:fixed;top:0;left:0;width:100%;height:100%;z-index:9999;pointer-events:none;overflow:hidden;`;
        this.container.appendChild(overlay);
        const flash = document.createElement('div');
        let flashColors = 'rgba(255,215,0,0.4),rgba(0,255,136,0.2),transparent';
        if (level === 'yakuman') flashColors = 'rgba(255,0,128,0.5),rgba(255,215,0,0.4),transparent';
        else if (level === 'high') flashColors = 'rgba(255,100,0,0.4),rgba(255,215,0,0.3),transparent';
        flash.style.cssText = `position:absolute;top:0;left:0;width:100%;height:100%;background:radial-gradient(circle at 50% 50%,${flashColors});opacity:0;animation:winFlash 1.5s ease-out forwards;`;
        overlay.appendChild(flash);
        let confettiCount = 0, emojiCount = 0, showText = false, textHtml = '';
        const mobileFactor = this.isMobile ? 0.5 : 1;
        if (level === 'normal') { confettiCount = Math.floor(8 * mobileFactor); showText = false; }
        else if (level === 'medium') { confettiCount = Math.floor(30 * mobileFactor); emojiCount = Math.floor(10 * mobileFactor); showText = true; textHtml = '满贯！🎆'; }
        else if (level === 'high') { confettiCount = Math.floor(55 * mobileFactor); emojiCount = Math.floor(18 * mobileFactor); showText = true; textHtml = '🎉 倍满·三倍满！🎉'; }
        else if (level === 'yakuman') { confettiCount = Math.floor(80 * mobileFactor); emojiCount = Math.floor(25 * mobileFactor); showText = true; textHtml = '🔥🌟 役满！🌟🔥'; }
        for (let i = 0; i < confettiCount; i++) {
            const conf = document.createElement('div');
            const w = 5 + Math.random() * 7, h = 10 + Math.random() * 18, left = Math.random() * 100, delay = Math.random() * 2.5, duration = 2 + Math.random() * 2.5;
            const color = this.confettiColors[Math.floor(Math.random() * this.confettiColors.length)], rotate = Math.random() * 360;
            conf.style.cssText = `position:absolute;width:${w}px;height:${h}px;background:${color};border-radius:2px;left:${left}%;top:-30px;transform:rotate(${rotate}deg);opacity:0.9;animation:confettiFall ${duration}s linear forwards;animation-delay:${delay}s;`;
            overlay.appendChild(conf);
        }
        const emojiTop = this.isMobile ? '10%' : '15%';
        for (let i = 0; i < emojiCount; i++) {
            const el = document.createElement('div');
            const emoji = this.emojis[Math.floor(Math.random() * this.emojis.length)], left = 15 + Math.random() * 70, delay = 0.2 + Math.random() * 0.8;
            const size = this.isMobile ? (0.8 + Math.random() * 0.7) : (1.2 + Math.random() * 1.5);
            el.textContent = emoji;
            el.style.cssText = `position:absolute;font-size:${size}rem;left:${left}%;top:${emojiTop};animation:emojiPop 1.5s ease-out forwards;animation-delay:${delay}s;`;
            overlay.appendChild(el);
        }
        if (showText) {
            const text = document.createElement('div');
            text.innerHTML = textHtml;
            let fontSize = this.isMobile ? '1.2rem' : '2rem'; if (level === 'yakuman') fontSize = this.isMobile ? '1.8rem' : '3rem';
            const textTop = this.isMobile ? '25%' : '30%';
            text.style.cssText = `position:absolute;top:${textTop};left:50%;transform:translate(-50%,-50%);font-size:${fontSize};font-weight:900;color:#ffd700;white-space:nowrap;text-shadow:0 0 30px rgba(255,215,0,0.8),0 0 60px rgba(255,215,0,0.5),0 4px 8px rgba(0,0,0,0.5);animation:winText 2s ease-out forwards;font-family:'Noto Sans SC',sans-serif;`;
            overlay.appendChild(text);
        }
        const duration = level === 'yakuman' ? 4000 : 3000;
        setTimeout(() => { overlay.style.transition = 'opacity 0.8s ease'; overlay.style.opacity = '0'; setTimeout(() => overlay.remove(), 800); }, duration);
    }
}

class HandAnalyzer {
    constructor() {
        this.hand = [];
        this.handDisplay = document.getElementById('hand-display');
        this.handCount = document.getElementById('hand-count');
        this.resultArea = document.getElementById('analysis-result');
        this.msgArea = document.getElementById('message-area');
        this.winAnim = new WinAnimation(document.body);
        this.init();
    }
    init() {
        document.querySelectorAll('.tile-btn').forEach(btn => {
            btn.addEventListener('click', () => this.addTile(btn.dataset.tile));
        });
        document.getElementById('btn-clear').addEventListener('click', () => this.clearHand());
        document.getElementById('btn-random').addEventListener('click', () => this.randomHand());
        document.getElementById('btn-analyze').addEventListener('click', () => this.analyze());
        
        // 牌筛选按钮
        document.querySelectorAll('.tile-filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const filter = btn.dataset.filter;
                document.querySelectorAll('.tile-filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                document.querySelectorAll('#tile-selector .tile-btn').forEach(tile => {
                    if (filter === 'all' || tile.dataset.suit === filter) {
                        tile.style.display = '';
                    } else {
                        tile.style.display = 'none';
                    }
                });
            });
        });
    }
    addTile(tile) {
        if (this.hand.length >= 14) { this.showMessage('手牌已达14张上限'); return; }
        const count = this.hand.filter(t => t === tile).length;
        if (count >= 4) { this.showMessage('同一种牌最多4张'); return; }
        this.hand.push(tile);
        this.sortHand();
        this.renderHand();
    }
    sortHand() {
        const order = {
            'm1':1,'m2':2,'m3':3,'m4':4,'m5':5,'m6':6,'m7':7,'m8':8,'m9':9,
            'p1':10,'p2':11,'p3':12,'p4':13,'p5':14,'p6':15,'p7':16,'p8':17,'p9':18,
            's1':19,'s2':20,'s3':21,'s4':22,'s5':23,'s6':24,'s7':25,'s8':26,'s9':27,
            'east':28,'south':29,'west':30,'north':31,'red':32,'green':33,'white':34
        };
        this.hand.sort((a, b) => (order[a] || 99) - (order[b] || 99));
    }
    removeTile(index) { this.hand.splice(index, 1); this.renderHand(); }
    clearHand() { this.hand = []; this.renderHand(); this.resultArea.style.display = 'none'; if (this.msgArea) { this.msgArea.innerHTML = ''; this.msgArea.style.display = 'none'; } }
    randomHand() {
        const tiles = ['m1','m2','m3','m4','m5','m6','m7','m8','m9','p1','p2','p3','p4','p5','p6','p7','p8','p9','s1','s2','s3','s4','s5','s6','s7','s8','s9','east','south','west','north','white','green','red'];
        this.hand = []; const counts = {};
        while (this.hand.length < 14) { const t = tiles[Math.floor(Math.random() * tiles.length)]; counts[t] = (counts[t] || 0) + 1; if (counts[t] <= 4) this.hand.push(t); else counts[t]--; }
        this.sortHand();
        this.renderHand(); this.resultArea.style.display = 'none'; if (this.msgArea) { this.msgArea.innerHTML = ''; this.msgArea.style.display = 'none'; }
    }
    renderHand() {
        this.handCount.textContent = this.hand.length;
        if (this.hand.length === 0) { this.handDisplay.innerHTML = '<div class="hand-placeholder">点击下方牌选择手牌...</div>'; return; }
        if (window.MahgenTiles) {
            const isMobile = window.innerWidth <= 768;
            const tileSize = isMobile ? 28 : 42;
            MahgenTiles.renderTiles(this.handDisplay, this.hand, { size: tileSize, gap: 3 });
            const imgs = this.handDisplay.querySelectorAll('.tile-png');
            imgs.forEach((img, i) => { img.style.cursor = 'pointer'; img.addEventListener('click', () => this.removeTile(i)); });
        }
    }
    async analyze() {
        if (this.msgArea) { this.msgArea.innerHTML = ''; this.msgArea.style.display = 'none'; }
        if (this.hand.length === 0) { this.showMessage('请先选择手牌'); return; }
        
        // 显示加载状态
        const btn = document.getElementById('btn-analyze');
        const btnOriginalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> 计算中...';
        btn.classList.add('loading');
        
        // 显示进度条
        let progressHtml = '<div class="calc-progress"><div class="progress-bar"><div class="progress-fill" id="progress-fill"></div></div><span class="progress-text" id="progress-text">正在分析...</span></div>';
        if (this.msgArea) {
            this.msgArea.innerHTML = progressHtml;
            this.msgArea.style.display = 'block';
        }
        
        // 模拟进度
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress = Math.min(progress + Math.random() * 15, 90);
            const fill = document.getElementById('progress-fill');
            const text = document.getElementById('progress-text');
            if (fill) fill.style.width = progress + '%';
            if (text) {
                if (progress < 30) text.textContent = '正在分解手牌...';
                else if (progress < 60) text.textContent = '正在计算向听数...';
                else text.textContent = '正在分析进张...';
            }
        }, 200);
        
        try {
            const response = await fetch('/api/analyze-hand', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ hand: this.hand }) });
            const data = await response.json();
            
            clearInterval(progressInterval);
            // 完成进度
            const fill = document.getElementById('progress-fill');
            if (fill) fill.style.width = '100%';
            
            if (data.error) { 
                this.showMessage(data.error); 
                this.resetButton(btn, btnOriginalText);
                return; 
            }
            if (data.is_agari) {
                let animLevel = 'normal';
                if (data.is_yakuman) animLevel = 'yakuman';
                else if (data.total_han >= 8) animLevel = 'high';
                else if (data.total_han >= 5) animLevel = 'medium';
                this.winAnim.play(animLevel);
            }
            this.renderResult(data);
        } catch (error) { 
            clearInterval(progressInterval);
            this.showMessage('分析失败: ' + error.message); 
        }
        
        this.resetButton(btn, btnOriginalText);
    }
    
    resetButton(btn, originalText) {
        btn.disabled = false;
        btn.innerHTML = originalText;
        btn.classList.remove('loading');
        if (this.msgArea) {
            this.msgArea.innerHTML = '';
            this.msgArea.style.display = 'none';
        }
    }
    renderResult(data) {
        if (data.error) { this.showMessage(data.error); return; }
        const statusText = data.is_agari ? '和牌！' : (data.is_tenpai ? '听牌！' : '未完成');
        const statusColor = data.is_agari ? 'var(--accent-1)' : (data.is_tenpai ? '#ffd700' : 'var(--text-muted)');
        let html = `
            <div class="result-section"><div class="result-title">状态</div><div class="result-content"><span style="display:inline-block;padding:0.4rem 1rem;border-radius:50px;font-weight:600;background:${statusColor};color:var(--bg-primary);">${statusText}</span><p style="margin-top:0.5rem;color:var(--text-secondary);">${data.message}</p></div></div>
            <div class="result-section"><div class="result-title">手牌</div><div class="result-content"><div class="mahgen-container" id="mahgen-hand"><span class="mahgen-loading">生成中...</span></div></div></div>
        `;
        if (data.yaku && data.yaku.length > 0) {
            const yakuList = data.yaku.map(y => {
                const yakumanClass = (y.han >= 13) ? 'yakuman' : '';
                return `<span class="result-yaku-item ${yakumanClass}">${y.name} ${y.han}番</span>`;
            }).join('');
            if (data.is_yakuman) {
                html += `<div class="result-section"><div class="result-title">可构成役种 (${data.yaku.length}种)</div><div class="result-yaku-list">${yakuList}</div><div class="result-breakdown"><div class="result-breakdown-item total"><span>役满</span><span>役满</span></div></div></div>`;
            } else {
                html += `<div class="result-section"><div class="result-title">可构成役种 (${data.yaku.length}种)</div><div class="result-yaku-list">${yakuList}</div><div class="result-breakdown"><div class="result-breakdown-item total"><span>总番数</span><span>${data.total_han}番</span></div></div></div>`;
            }
        }
        
        // 14张非和牌时显示牌效分析建议
        if (data.efficiency && data.efficiency.length > 0 && !data.is_agari) {
            // 判断是否为进张分析（听牌分析有waiting_types，进张分析没有）
            const isTenpaiResult = data.efficiency[0] && data.efficiency[0].waiting_types && 
                Object.values(data.efficiency[0].waiting_types).some(v => v.types && v.types.includes('进张'));
            const headerText = isTenpaiResult ? '可进张牌（含役种）' : '可听的牌（含役种）';
            
            html += `<div class="result-section" id="efficiency-section"><div class="result-title">牌效分析建议（打出哪张）</div><div class="result-content">`;
            html += `<div class="efficiency-table"><div class="efficiency-header"><span>打</span><span>进张数</span><span>好型率</span><span>${headerText}</span></div>`;
            for (const eff of data.efficiency) {
                const tilesHtml = eff.waiting_tiles.map((t, i) => {
                    const types = eff.waiting_types[t] ? eff.waiting_types[t].types.join('/') : '';
                    const yakuInfo = eff.waiting_yaku && eff.waiting_yaku[t] ? eff.waiting_yaku[t] : null;
                    let yakuHtml = '';
                    if (yakuInfo && yakuInfo.yaku && yakuInfo.yaku.length > 0) {
                        const yakuTags = yakuInfo.yaku.map(y => {
                            const yakumanClass = (y.han >= 13) ? 'yakuman' : '';
                            return `<span class="eff-yaku-tag ${yakumanClass}">${y.name} ${y.han}番</span>`;
                        }).join('');
                        yakuHtml = `<span class="eff-yaku-total">${yakuInfo.total_han}番</span>`;
                        return `<span class="eff-tile"><img src="${eff.waiting_tiles_png[i]}" class="eff-tile-img" alt="${t}"><span class="eff-tile-types">${types}</span><span class="eff-tile-yaku">${yakuTags}${yakuHtml}</span></span>`;
                    } else if (types === '进张') {
                        return `<span class="eff-tile"><img src="${eff.waiting_tiles_png[i]}" class="eff-tile-img" alt="${t}"><span class="eff-tile-types">${types}</span></span>`;
                    } else {
                        yakuHtml = `<span class="eff-yaku-none">无役</span>`;
                        return `<span class="eff-tile"><img src="${eff.waiting_tiles_png[i]}" class="eff-tile-img" alt="${t}"><span class="eff-tile-types">${types}</span><span class="eff-tile-yaku">${yakuHtml}</span></span>`;
                    }
                }).join('');
                // 好型率初始显示为"计算中..."
                html += `<div class="efficiency-row" data-tile="${eff.tile}"><span class="eff-discard"><img src="${eff.tile_png}" class="eff-discard-img" alt="${eff.tile}"><span>${eff.tile_name}</span></span><span class="eff-count">${eff.count}张</span><span class="eff-rate rate-loading" id="rate-${eff.tile}">计算中...</span><span class="eff-waiting">${tilesHtml}</span></div>`;
            }
            html += `</div></div></div>`;
            
            // 异步获取好型率（方案四）
            this.fetchGoodShapeRates(data.efficiency);
        }
        
        if (data.tenpai_tiles && data.tenpai_tiles.length > 0) {
            html += `<div class="result-section"><div class="result-title">可听的牌 (${data.tenpai_tiles.length}种)</div><div class="result-content"><div class="mahgen-container" id="mahgen-tenpai"><span class="mahgen-loading">生成中...</span></div></div></div>`;
        }
        
        // 听牌形分析
        if (data.tenpai_types_display && Object.keys(data.tenpai_types_display).length > 0) {
            html += `<div class="result-section"><div class="result-title">听牌形分析</div><div class="result-content">`;
            for (const [tile, info] of Object.entries(data.tenpai_types_display)) {
                const types = info.types.join(' · ');
                let yakuHtml = '';
                if (info.yaku && info.yaku.length > 0) {
                    const yakuTags = info.yaku.map(y => {
                        const yakumanClass = (y.han >= 13) ? 'yakuman' : '';
                        return `<span class="tenpai-yaku-tag ${yakumanClass}">${y.name} ${y.han}番</span>`;
                    }).join('');
                    yakuHtml = `<div class="tenpai-yaku-list">${yakuTags}<span class="tenpai-yaku-total">${info.total_han}番</span></div>`;
                } else {
                    yakuHtml = `<div class="tenpai-yaku-list"><span class="tenpai-yaku-none">无役种</span></div>`;
                }
                html += `<div class="tenpai-type-item"><img src="${info.png}" class="tenpai-type-img" alt="${info.name}"><div class="tenpai-type-info"><div class="tenpai-type-row"><span class="tenpai-type-name">${info.name}</span><span class="tenpai-type-tags">${types}</span></div>${yakuHtml}</div></div>`;
            }
            html += `</div></div>`;
        }
        
        // 手牌效率分析（13张听牌时显示）
        if (data.is_tenpai && data.efficiency && data.efficiency.length > 0) {
            html += `<div class="result-section"><div class="result-title">手牌效率分析（建议打牌）</div><div class="result-content">`;
            html += `<div class="efficiency-table"><div class="efficiency-header"><span>打</span><span>进张数</span><span>可听的牌</span></div>`;
            for (const eff of data.efficiency) {
                const tilesHtml = eff.waiting_tiles.map((t, i) => {
                    const types = eff.waiting_types[t] ? eff.waiting_types[t].types.join('/') : '';
                    return `<span class="eff-tile"><img src="${eff.waiting_tiles_png[i]}" class="eff-tile-img" alt="${t}"><span class="eff-tile-types">${types}</span></span>`;
                }).join('');
                html += `<div class="efficiency-row"><span class="eff-discard"><img src="${eff.tile_png}" class="eff-discard-img" alt="${eff.tile}"><span>${eff.tile_name}</span></span><span class="eff-count">${eff.count}张</span><span class="eff-waiting">${tilesHtml}</span></div>`;
            }
            html += `</div></div></div>`;
        }
        
        if (data.invalid) html += `<div class="result-section"><div class="error-message">手牌中有超过4张的牌</div></div>`;
        this.resultArea.innerHTML = html; this.resultArea.style.display = 'block';
        if (window.MahgenTiles) {
            const isMobile = window.innerWidth <= 768;
            const resultSize = isMobile ? 24 : 38;
            const handContainer = document.getElementById('mahgen-hand');
            if (handContainer && data.hand) MahgenTiles.renderTiles(handContainer, data.hand, { size: resultSize, gap: 3 });
            const tenpaiContainer = document.getElementById('mahgen-tenpai');
            if (tenpaiContainer && data.tenpai_tiles) MahgenTiles.renderTiles(tenpaiContainer, data.tenpai_tiles, { size: resultSize, gap: 3 });
        }
        this.resultArea.scrollIntoView({ behavior: 'smooth' });
    }
    
    async fetchGoodShapeRates(efficiency) {
        // 异步获取好型率（方案四）
        const tiles = efficiency.map(eff => eff.tile);
        try {
            const response = await fetch('/api/good-shape', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ hand: this.hand, tiles: tiles })
            });
            const data = await response.json();
            if (data.rates) {
                for (const [tile, rate] of Object.entries(data.rates)) {
                    const rateEl = document.getElementById('rate-' + tile);
                    if (rateEl) {
                        const rateClass = rate >= 70 ? 'rate-high' : (rate >= 40 ? 'rate-mid' : 'rate-low');
                        rateEl.className = 'eff-rate ' + rateClass;
                        rateEl.textContent = rate.toFixed(1) + '%';
                    }
                }
            }
        } catch (error) {
            console.error('好型率计算失败:', error);
            // 失败时显示"--
            tiles.forEach(tile => {
                const rateEl = document.getElementById('rate-' + tile);
                if (rateEl) {
                    rateEl.className = 'eff-rate';
                    rateEl.textContent = '--';
                }
            });
        }
    }
    
    showMessage(msg) {
        if (!this.msgArea) {
            const div = document.createElement('div'); div.className = 'warning-message'; div.textContent = msg; div.style.animation = 'fadeIn 0.3s ease';
            this.resultArea.innerHTML = ''; this.resultArea.appendChild(div); this.resultArea.style.display = 'block';
            setTimeout(() => { div.style.opacity = '0'; setTimeout(() => div.remove(), 300); }, 3000);
            return;
        }
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
    new HandAnalyzer();
});
/**
 * Vibe Mahjong - Main Page (Yaku Search)
 */

class ParticleSystem {
    constructor(canvas) {
        this.canvas = canvas;
        if (!canvas) return;
        this.ctx = canvas.getContext('2d');
        this.particles = [];
        this.mouse = { x: null, y: null };
        this.init();
    }
    init() {
        this.resize();
        this.createParticles();
        window.addEventListener('resize', () => { this.resize(); this.createParticles(); });
        window.addEventListener('mousemove', (e) => { this.mouse.x = e.clientX; this.mouse.y = e.clientY; });
        this.animate();
    }
    resize() { this.canvas.width = window.innerWidth; this.canvas.height = window.innerHeight; }
    createParticles() {
        const count = Math.min(Math.floor(window.innerWidth / 15), 50);
        this.particles = [];
        const isWa = document.body.dataset.theme === 'wa';
        const colors = isWa ? ['#c41e3a', '#d4a574', '#ffd700', '#8b0000'] : ['#00ff88', '#00ccff', '#ff0080', '#ffd700'];
        for (let i = 0; i < count; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width, y: Math.random() * this.canvas.height,
                vx: (Math.random() - 0.5) * 0.3, vy: (Math.random() - 0.5) * 0.3,
                radius: Math.random() * 2 + 0.5, color: colors[Math.floor(Math.random() * colors.length)]
            });
        }
    }
    animate() {
        if (!this.ctx) return;
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.particles.forEach(p => {
            if (this.mouse.x !== null) {
                const dx = this.mouse.x - p.x, dy = this.mouse.y - p.y, d = Math.sqrt(dx*dx + dy*dy);
                if (d < 100) { const f = (100 - d) / 100; p.vx += (dx/d) * f * 0.01; p.vy += (dy/d) * f * 0.01; }
            }
            p.x += p.vx; p.y += p.vy;
            if (p.x < 0 || p.x > this.canvas.width) p.vx *= -1;
            if (p.y < 0 || p.y > this.canvas.height) p.vy *= -1;
            p.vx *= 0.99; p.vy *= 0.99;
            this.ctx.beginPath(); this.ctx.arc(p.x, p.y, p.radius, 0, Math.PI*2);
            this.ctx.fillStyle = p.color; this.ctx.globalAlpha = 0.5; this.ctx.fill(); this.ctx.globalAlpha = 1;
        });
        requestAnimationFrame(() => this.animate());
    }
}

class ThemeToggle {
    constructor() {
        this.btn = document.getElementById('theme-toggle');
        this.body = document.body;
        if (!this.btn) return;
        this.cyberIcon = this.btn.querySelector('.cyber-icon');
        this.waIcon = this.btn.querySelector('.wa-icon');
        this.init();
    }
    init() {
        const saved = localStorage.getItem('mahjong-theme') || 'cyber';
        this.setTheme(saved);
        this.btn.addEventListener('click', () => {
            const newTheme = this.body.dataset.theme === 'cyber' ? 'wa' : 'cyber';
            this.setTheme(newTheme); localStorage.setItem('mahjong-theme', newTheme);
        });
    }
    setTheme(theme) {
        this.body.dataset.theme = theme;
        if (this.cyberIcon && this.waIcon) {
            this.cyberIcon.style.display = theme === 'cyber' ? 'inline' : 'none';
            this.waIcon.style.display = theme === 'cyber' ? 'none' : 'inline';
        }
    }
}

class YakuSearch {
    constructor() {
        this.searchInput = document.getElementById('search-input');
        this.yakuGrid = document.getElementById('yaku-grid');
        this.categoryBtns = document.querySelectorAll('.category-btn');
        this.resultCount = document.getElementById('result-count');
        this.currentFilter = document.getElementById('current-filter');
        this.noResults = document.getElementById('no-results');
        this.modalOverlay = document.getElementById('modal-overlay');
        this.modalContent = document.getElementById('modal-content');
        this.modalClose = document.getElementById('modal-close');
        this.activeCategory = ''; this.searchQuery = '';
        this.init();
    }
    init() {
        this.searchInput.addEventListener('input', (e) => {
            this.searchQuery = e.target.value.toLowerCase().trim(); this.filterCards();
        });
        this.categoryBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                this.categoryBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.activeCategory = btn.dataset.category;
                this.currentFilter.textContent = this.activeCategory || '全部';
                this.filterCards();
            });
        });
        this.yakuGrid.querySelectorAll('.yaku-card').forEach(card => {
            card.addEventListener('click', () => this.openModal(card.dataset.id));
        });
        this.modalClose.addEventListener('click', () => this.closeModal());
        this.modalOverlay.addEventListener('click', (e) => { if (e.target === this.modalOverlay) this.closeModal(); });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this.closeModal();
            if (e.key === '/' && document.activeElement !== this.searchInput) { e.preventDefault(); this.searchInput.focus(); }
        });
    }
    filterCards() {
        let visibleCount = 0;
        this.yakuGrid.querySelectorAll('.yaku-card').forEach(card => {
            const category = card.dataset.category;
            const title = card.querySelector('.card-title').textContent.toLowerCase();
            const japanese = card.querySelector('.card-japanese').textContent.toLowerCase();
            const description = card.querySelector('.card-description').textContent.toLowerCase();
            const tags = Array.from(card.querySelectorAll('.tag')).map(t => t.textContent.toLowerCase());
            const matchesCategory = !this.activeCategory || category === this.activeCategory;
            const matchesSearch = !this.searchQuery || title.includes(this.searchQuery) || japanese.includes(this.searchQuery) || description.includes(this.searchQuery) || tags.some(tag => tag.includes(this.searchQuery));
            if (matchesCategory && matchesSearch) { card.classList.remove('hidden'); visibleCount++; }
            else { card.classList.add('hidden'); }
        });
        this.resultCount.textContent = visibleCount;
        this.noResults.style.display = visibleCount === 0 ? 'block' : 'none';
        this.yakuGrid.style.display = visibleCount === 0 ? 'none' : 'grid';
    }
    async openModal(yakuId) {
        try {
            const response = await fetch(`/api/yaku/${yakuId}`);
            const yaku = await response.json();
            if (yaku.error) return;
            const hanClass = yaku.category === '双倍役满' ? 'double-yakuman' : yaku.category === '役满' ? 'yakuman' : '';
            this.modalContent.innerHTML = `
                <div class="modal-header">
                    <div class="modal-han ${hanClass}">${yaku.category}</div>
                    <h2 class="modal-title">${yaku.name}</h2>
                    <p class="modal-japanese">${yaku.japanese}</p>
                </div>
                <div class="modal-tiles-section">
                    <div class="modal-tiles-label">示例牌型</div>
                    <div class="mahgen-container" id="modal-mahgen"><span class="mahgen-loading">生成中...</span></div>
                </div>
                <div class="modal-section"><div class="modal-section-title">说明</div><div class="modal-section-content highlight">${yaku.description}</div></div>
                <div class="modal-section"><div class="modal-section-title">条件</div><div class="modal-section-content">${yaku.condition}</div></div>
                <div class="modal-section"><div class="modal-section-title">类型</div><div class="modal-section-content">${yaku.type}</div></div>
                <div class="modal-tags">${yaku.tags.map(tag => `<span class="modal-tag">${tag}</span>`).join('')}</div>
            `;
            this.modalOverlay.classList.add('active'); document.body.style.overflow = 'hidden';
            // Render with local PNG tiles
            if (yaku.tiles_png && window.MahgenTiles) {
                const container = document.getElementById('modal-mahgen');
                if (container) MahgenTiles.renderTiles(container, yaku.tiles, { size: 28, gap: 2 });
            }
        } catch (error) { console.error('Error:', error); }
    }
    closeModal() {
        this.modalOverlay.classList.remove('active'); document.body.style.overflow = '';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new ParticleSystem(document.getElementById('particle-canvas'));
    new ThemeToggle();
    new YakuSearch();
});

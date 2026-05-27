/**
 * Tile Image Renderer - 使用本地 mahjong-res PNG 图片
 */

const MahgenTiles = {
    // tile代码 -> 图片文件名
    tileToFile: {
        'm1': '1m', 'm2': '2m', 'm3': '3m', 'm4': '4m', 'm5': '5m',
        'm6': '6m', 'm7': '7m', 'm8': '8m', 'm9': '9m',
        'p1': '1p', 'p2': '2p', 'p3': '3p', 'p4': '4p', 'p5': '5p',
        'p6': '6p', 'p7': '7p', 'p8': '8p', 'p9': '9p',
        's1': '1s', 's2': '2s', 's3': '3s', 's4': '4s', 's5': '5s',
        's6': '6s', 's7': '7s', 's8': '8s', 's9': '9s',
        'east': 'east', 'south': 'south', 'west': 'west', 'north': 'north',
        'white': 'white', 'green': 'green', 'red': 'red',
    },

    getImgUrl(tile) {
        const file = this.tileToFile[tile];
        return file ? `/static/images/mahjong-res/${file}.png` : '';
    },

    // 直接渲染为 <img> 标签拼接
    renderTiles(container, tiles, options = {}) {
        if (!container || !tiles || tiles.length === 0) {
            if (container) container.innerHTML = '';
            return;
        }

        const size = options.size || 40;
        const gap = options.gap || 2;
        const wrap = options.wrap !== false; // default to wrap

        container.innerHTML = `
            <div class="tile-images-row" style="display:flex;gap:${gap}px;flex-wrap:${wrap ? 'wrap' : 'nowrap'};justify-content:center;align-items:center;padding:2px 0;">
                ${tiles.map(t => {
                    const src = this.getImgUrl(t);
                    return src ? `<img src="${src}" alt="${t}" class="tile-png" style="width:${size}px;height:auto;border-radius:3px;user-select:none;flex-shrink:0;" draggable="false">` : '';
                }).join('')}
            </div>
        `;
    }
};

// 显式挂载到 window，确保跨文件可访问
window.MahgenTiles = MahgenTiles;

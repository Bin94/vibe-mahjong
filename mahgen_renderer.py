"""
Mahgen Python Renderer
基于 mahgen 项目的 res.json 和渲染逻辑，用 Pillow 实现牌型图片拼接
"""

import json
import base64
import io
from PIL import Image
from pathlib import Path

# 加载 res.json
RES_JSON_PATH = Path(__file__).parent / 'mahgen-master' / 'src' / 'res.json'
_res_data = None
_image_cache = {}

def _load_res():
    global _res_data
    if _res_data is None:
        with open(RES_JSON_PATH, 'r', encoding='utf-8') as f:
            _res_data = {item['k']: item['v'] for item in json.load(f)}
    return _res_data

def _get_image(key):
    """从缓存获取图片，如果不存在则从base64解码"""
    if key not in _image_cache:
        res_data = _load_res()
        if key not in res_data:
            return None
        img_data = base64.b64decode(res_data[key])
        _image_cache[key] = Image.open(io.BytesIO(img_data)).convert('RGBA')
    return _image_cache[key].copy()

# 解析器常量
SUIT_MAP = {'m': 'Man', 'p': 'Pin', 's': 'So', 'z': 'Char'}
STATE_MAP = {'': 'Normal', '_': 'Horizontal', '^': 'Stack', 'v': 'Diff'}
SPACE_NAME = 'space'

def parse_seq(seq, river=False):
    """
    解析 mahgen 序列字符串为 tile 列表
    例如: "123m|456p" -> [(1,'m',''), (2,'m',''), (3,'m',''), (None,'space',''), (4,'p',''), (5,'p',''), (6,'p','')]
    """
    seq = seq.replace(r'\s+', '')
    tiles = []
    i = 0

    while i < len(seq):
        # 空格
        if seq[i] == '|':
            tiles.append((None, 'space', ''))
            i += 1
            continue

        # 解析一组牌
        group = []
        while i < len(seq) and seq[i] not in 'mpsz':
            state = ''
            if seq[i] in '_^v':
                state = seq[i]
                i += 1
            if i >= len(seq) or not seq[i].isdigit():
                break
            num = int(seq[i])
            group.append((num, state))
            i += 1

        if i >= len(seq):
            break

        suit = seq[i]
        i += 1

        for num, state in group:
            tiles.append((num, suit, state))

    return tiles

def get_image_key(tile, river=False):
    """
    根据 tile 获取 res.json 中的 key
    tile: (num, suit, state)
    """
    num, suit, state = tile

    if suit == 'space':
        return SPACE_NAME

    # 处理 river 模式的 state 转换
    if river:
        if state == '^':
            state = ''
        elif state == 'v':
            state = '_'

    prefix = state  # '', '_', '^', 'v'
    key = f"{prefix}{num}{suit}"

    # 如果 key 不存在，fallback 到 Stack 状态
    res_data = _load_res()
    if key not in res_data:
        fallback_key = f"={num}{suit}"
        if fallback_key in res_data:
            return fallback_key
        # 最后的 fallback
        return f"{num}{suit}"

    return key

def render_tiles(seq, river=False):
    """
    渲染 mahgen 序列为图片，返回 base64 编码的 PNG
    """
    tiles = parse_seq(seq, river)
    if not tiles:
        return None

    # 获取所有图片
    images = []
    for tile in tiles:
        key = get_image_key(tile, river)
        img = _get_image(key)
        if img is None:
            # 跳过缺失的图片
            continue
        images.append(img)

    if not images:
        return None

    # 计算总尺寸
    total_width = sum(img.width for img in images)
    max_height = max(img.height for img in images)

    # 创建新图片
    result = Image.new('RGBA', (total_width, max_height), (0, 0, 0, 0))

    # 横向拼接
    x_offset = 0
    for img in images:
        result.paste(img, (x_offset, 0), img)
        x_offset += img.width

    # 转为 base64
    buffer = io.BytesIO()
    result.save(buffer, format='PNG')
    buffer.seek(0)
    base64_str = base64.b64encode(buffer.read()).decode('utf-8')

    return f"data:image/png;base64,{base64_str}"

# 预加载资源
_load_res()

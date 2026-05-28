"""
牌效分析模块 - 封装向听计算、进张分析、好型率计算
从 shanten.py 和 app.py 中提取的牌效分析功能
"""

from shanten import (
    calc_shanten, calc_shanten_cached, tiles_to_34, remaining_tiles,
    TILE_TO_INDEX, INDEX_TO_TILE, TILE_COUNT
)

# ========== 常量 ==========
MAX_GOOD_SHAPE_DEPTH = 3


# ========== 进张分析 ==========

def evaluate_hand(hand, shanten_cache=None):
    """评估14张手牌的切牌选择
    hand: 当前命名的牌列表 (如 ['m1', 'm2', 'm3', ...])
    shanten_cache: 可选的共享缓存字典
    返回: {tile: {improvements, count, shanten}} 按进张数排序
    """
    if shanten_cache is None:
        shanten_cache = {}
    current34 = tiles_to_34(hand)
    original_shanten = calc_shanten_cached(current34, shanten_cache)

    if original_shanten < -1:
        return {}

    rem34 = remaining_tiles(current34)
    results = {}
    processed = set()

    for tile_to_discard in hand:
        if tile_to_discard in processed:
            continue
        processed.add(tile_to_discard)

        tile_idx = TILE_TO_INDEX.get(tile_to_discard)
        if tile_idx is None:
            continue

        new34 = list(current34)
        new34[tile_idx] -= 1

        shanten_after_discard = calc_shanten_cached(tuple(new34), shanten_cache)

        # 跳过向听倒退的切牌
        if shanten_after_discard > original_shanten:
            continue

        improvements = {}
        total_count = 0

        for i in range(TILE_COUNT):
            if rem34[i] <= 0:
                continue
            new34[i] += 1
            new_shanten = calc_shanten_cached(tuple(new34), shanten_cache)
            if new_shanten < shanten_after_discard:
                imp_tile = INDEX_TO_TILE.get(i, str(i))
                improvements[imp_tile] = rem34[i]
                total_count += rem34[i]
            new34[i] -= 1

        if total_count > 0:
            results[tile_to_discard] = {
                'improvements': improvements,
                'count': total_count,
                'shanten': shanten_after_discard
            }

    # 按进张数排序
    sorted_results = sorted(results.items(), key=lambda x: (-x[1]['count'], x[0]))
    return dict(sorted_results)


def evaluate_tenpai(hand13):
    """评估13张手牌的听牌状态
    hand13: 当前命名的牌列表
    返回: {improvements, count, shanten}
    """
    shanten_cache = {}
    current34 = tiles_to_34(hand13)
    shanten = calc_shanten_cached(current34, shanten_cache)

    rem34 = remaining_tiles(current34)
    improvements = {}
    total_count = 0

    for i in range(TILE_COUNT):
        if rem34[i] <= 0:
            continue
        current34[i] += 1
        new_shanten = calc_shanten_cached(tuple(current34), shanten_cache)
        if new_shanten < shanten:
            imp_tile = INDEX_TO_TILE.get(i, str(i))
            improvements[imp_tile] = rem34[i]
            total_count += rem34[i]
        current34[i] -= 1

    return {
        'improvements': improvements,
        'count': total_count,
        'shanten': shanten
    }


# ========== 好型率计算 ==========

def calculate_good_shape_rate(hand34, rem34, shanten, depth=0, shanten_cache=None):
    """计算好型率（移植自 evaluation.js calculateGoodShapeRate34）
    好型率: 衡量听牌质量或向听前进后获得好型听牌的概率
    
    hand34: 当前手牌34数组
    rem34: 剩余牌34数组
    shanten: 当前向听数
    depth: 递归深度（用于限制计算量）
    shanten_cache: 可选的共享缓存字典
    
    返回: 0~1 的好型率
    """
    if depth > MAX_GOOD_SHAPE_DEPTH:
        return 0

    if shanten_cache is None:
        shanten_cache = {}
    current_shanten = shanten if shanten >= 0 else calc_shanten_cached(tuple(hand34), shanten_cache)

    # 听牌状态：判断是否为好型听牌
    if current_shanten == 0:
        wait_types = 0
        wait_count = 0
        for i in range(TILE_COUNT):
            if rem34[i] <= 0:
                continue
            hand34[i] += 1
            if calc_shanten_cached(tuple(hand34), shanten_cache) == -1:
                wait_types += 1
                wait_count += rem34[i]
            hand34[i] -= 1

        # 好型听牌：听牌种类 > 1 且听牌张数 > 4
        return 1.0 if (wait_types > 1 and wait_count > 4) else 0.0

    total = 0
    good = 0

    # 模拟所有可能的摸牌
    for i in range(TILE_COUNT):
        count = rem34[i]
        if count <= 0:
            continue

        hand34[i] += 1
        new_shanten = calc_shanten_cached(tuple(hand34), shanten_cache)

        if new_shanten < current_shanten:
            best_path = 0

            rem34[i] -= 1
            for d in range(TILE_COUNT):
                if hand34[d] <= 0:
                    continue
                hand34[d] -= 1
                rem34[d] += 1

                val = calculate_good_shape_rate(hand34, rem34, new_shanten, depth + 1, shanten_cache=shanten_cache)
                if val > best_path:
                    best_path = val
                    if best_path == 1.0:
                        rem34[d] -= 1
                        hand34[d] += 1
                        break

                rem34[d] -= 1
                hand34[d] += 1
            rem34[i] += 1

            total += count
            good += count * best_path

        hand34[i] -= 1

    return good / total if total > 0 else 0.0


def calculate_good_shape_for_discard(hand, discard_tile, shanten_cache=None):
    """计算打出某张牌后的好型率
    hand: 14张手牌
    discard_tile: 要打出的牌
    shanten_cache: 可选的共享缓存字典
    
    返回: 0~100 的好型率百分比
    """
    if shanten_cache is None:
        shanten_cache = {}
    
    current34 = tiles_to_34(hand)
    tile_idx = TILE_TO_INDEX.get(discard_tile)
    if tile_idx is None:
        return 0.0

    current34[tile_idx] -= 1
    rem34 = remaining_tiles(current34)

    shanten = calc_shanten_cached(tuple(current34), shanten_cache)

    rate = calculate_good_shape_rate(list(current34), list(rem34), shanten, shanten_cache=shanten_cache)
    return max(0.0, rate * 100)


def calculate_good_shape_batch(hand, tiles, shanten_cache=None):
    """批量计算多张牌的好型率（使用共享缓存加速）
    hand: 14张手牌
    tiles: 要计算的牌列表
    shanten_cache: 可选的共享缓存字典
    
    返回: {tile: rate} 字典
    """
    if shanten_cache is None:
        shanten_cache = {}
    
    results = {}
    for tile in tiles:
        results[tile] = calculate_good_shape_for_discard(hand, tile, shanten_cache)
    
    return results

from flask import Flask, render_template, jsonify, request
from collections import Counter
from shanten import calc_shanten, calc_shanten_cached, tiles_to_34, remaining_tiles, evaluate_hand, evaluate_tenpai, TILE_TO_INDEX, INDEX_TO_TILE, TILE_COUNT, calculate_good_shape_for_discard, calculate_good_shape_batch

app = Flask(__name__)

# ========== PNG Tile Helper ==========
TILE_TO_PNG = {
    'm1': '1m', 'm2': '2m', 'm3': '3m', 'm4': '4m', 'm5': '5m',
    'm6': '6m', 'm7': '7m', 'm8': '8m', 'm9': '9m',
    'p1': '1p', 'p2': '2p', 'p3': '3p', 'p4': '4p', 'p5': '5p',
    'p6': '6p', 'p7': '7p', 'p8': '8p', 'p9': '9p',
    's1': '1s', 's2': '2s', 's3': '3s', 's4': '4s', 's5': '5s',
    's6': '6s', 's7': '7s', 's8': '8s', 's9': '9s',
    'east': 'east', 'south': 'south', 'west': 'west', 'north': 'north',
    'white': 'white', 'green': 'green', 'red': 'red',
}

def tile_to_png(tcode):
    """将牌代码转为PNG URL"""
    fname = TILE_TO_PNG.get(tcode, tcode)
    return f"/static/images/mahjong-res/{fname}.png"

def tiles_to_pngs(tiles):
    """将牌代码列表转为PNG URL列表"""
    return [tile_to_png(t) for t in tiles]

# ========== 麻将牌常量 ==========
ALL_TILES = []
for i in range(1, 10):
    ALL_TILES.append(f'm{i}')
for i in range(1, 10):
    ALL_TILES.append(f'p{i}')
for i in range(1, 10):
    ALL_TILES.append(f's{i}')
ALL_TILES.extend(['east', 'south', 'west', 'north', 'white', 'green', 'red'])

TILE_NAMES = {
    'm1': '一万', 'm2': '二万', 'm3': '三万', 'm4': '四万', 'm5': '五万',
    'm6': '六万', 'm7': '七万', 'm8': '八万', 'm9': '九万',
    'p1': '一筒', 'p2': '二筒', 'p3': '三筒', 'p4': '四筒', 'p5': '五筒',
    'p6': '六筒', 'p7': '七筒', 'p8': '八筒', 'p9': '九筒',
    's1': '一条', 's2': '二条', 's3': '三条', 's4': '四条', 's5': '五条',
    's6': '六条', 's7': '七条', 's8': '八条', 's9': '九条',
    'east': '东风', 'south': '南风', 'west': '西风', 'north': '北风',
    'white': '白板', 'green': '发财', 'red': '红中',
}

def tile_suit(t):
    return t[0]  # 'm', 'p', 's', or first letter for honors

def tile_num(t):
    if len(t) == 2 and t[0] in 'mps':
        try:
            return int(t[1:])
        except ValueError:
            return None
    return None

def is_honor(t):
    return t in ['east', 'south', 'west', 'north', 'white', 'green', 'red']

def is_terminal(t):
    n = tile_num(t)
    return n is not None and (n == 1 or n == 9)

def is_yaochu(t):
    return is_honor(t) or is_terminal(t)

def is_green(t):
    return t in ['s2', 's3', 's4', 's6', 's8', 'green']

# ========== 牌命名转换 ==========
# 当前代码: m1, m9, east, south, west, north, white, green, red
# 参考代码: 1m, 9m, 1z, 2z, 3z, 4z, 5z, 6z, 7z

HONOR_TO_Z = {
    'east': '1z', 'south': '2z', 'west': '3z', 'north': '4z',
    'white': '5z', 'green': '6z', 'red': '7z'
}
Z_TO_HONOR = {v: k for k, v in HONOR_TO_Z.items()}

def tile_to_ref(tile):
    """将当前命名转为参考命名: m1 -> 1m, east -> 1z"""
    if tile in HONOR_TO_Z:
        return HONOR_TO_Z[tile]
    if len(tile) == 2 and tile[0] in 'mps' and tile[1].isdigit():
        return tile[1] + tile[0]
    return tile

def ref_to_tile(ref):
    """将参考命名转为当前命名: 1m -> m1, 1z -> east"""
    if ref in Z_TO_HONOR:
        return Z_TO_HONOR[ref]
    if len(ref) == 2 and ref[1] in 'mps' and ref[0].isdigit():
        return ref[1] + ref[0]
    return ref

# ========== 手牌分析核心逻辑 ==========
def check_standard_agari(hand_counter):
    """检查标准型4面子+1将牌"""
    tiles = []
    for t, c in hand_counter.items():
        tiles.extend([t] * c)
    if len(tiles) != 14:
        return False
    
    for pair_tile in hand_counter:
        if hand_counter[pair_tile] < 2:
            continue
        temp = Counter(hand_counter)
        temp[pair_tile] -= 2
        if temp[pair_tile] == 0:
            del temp[pair_tile]
        
        if can_form_groups(temp, 4):
            return True
    return False

def can_form_groups(counter, groups_needed):
    """递归检查是否能组成指定数量的面子"""
    if groups_needed == 0:
        return len(counter) == 0
    
    if not counter:
        return False
    
    # 取最小牌
    tile = min(counter.keys())
    
    # 尝试刻子
    if counter[tile] >= 3:
        temp = Counter(counter)
        temp[tile] -= 3
        if temp[tile] == 0:
            del temp[tile]
        if can_form_groups(temp, groups_needed - 1):
            return True
    
    # 尝试顺子（仅数牌）
    if len(tile) == 2 and tile[0] in 'mps':
        n = tile_num(tile)
        if n is not None and n <= 7:
            t2 = f"{tile[0]}{n+1}"
            t3 = f"{tile[0]}{n+2}"
            if t2 in counter and t3 in counter:
                temp = Counter(counter)
                temp[tile] -= 1
                temp[t2] -= 1
                temp[t3] -= 1
                for t in [tile, t2, t3]:
                    if temp[t] == 0:
                        del temp[t]
                if can_form_groups(temp, groups_needed - 1):
                    return True
    
    return False

def check_chiitoitsu(hand_counter):
    """检查七对子"""
    if sum(hand_counter.values()) != 14:
        return False
    pairs = sum(1 for c in hand_counter.values() if c == 2)
    quads = sum(1 for c in hand_counter.values() if c == 4)
    # 7 pairs = 7*2 = 14 cards. Allow up to 1 quad (counts as 2 pairs)
    return pairs + quads * 2 == 7 and all(c in [2, 4] for c in hand_counter.values())

def check_kokushi(hand_counter):
    """检查国士无双"""
    yaochu_tiles = ['m1', 'm9', 'p1', 'p9', 's1', 's9',
                    'east', 'south', 'west', 'north', 'white', 'green', 'red']
    if sum(hand_counter.values()) != 14:
        return False
    
    for t in yaochu_tiles:
        if t not in hand_counter:
            return False
    
    # Check one tile appears twice
    extra = sum(c - 1 for t, c in hand_counter.items() if t in yaochu_tiles)
    return extra == 1

def check_agari(hand):
    """检查和牌（返回True/False）"""
    if len(hand) != 14:
        return False
    counter = Counter(hand)
    if any(c > 4 for c in counter.values()):
        return False
    
    return check_standard_agari(counter) or check_chiitoitsu(counter) or check_kokushi(counter)

def get_tenpai_tiles(hand):
    """获取13张牌的听牌列表"""
    if len(hand) != 13:
        return []
    
    counter = Counter(hand)
    if any(c > 4 for c in counter.values()):
        return []
    
    tenpai = []
    for t in ALL_TILES:
        if counter[t] < 4:
            test_hand = list(hand) + [t]
            if check_agari(test_hand):
                tenpai.append(t)
    return tenpai

def detect_wait_type(hand, wait_tile):
    """检测听牌类型
    hand: 13张手牌
    wait_tile: 听的那张牌
    返回听牌类型列表
    """
    counter = Counter(hand)
    wait_types = []
    
    # 1. 单骑听 (Tanki): 等待的牌是将牌
    # 如果手牌中有wait_tile，且去掉这张将牌后剩下的12张能组成4个面子
    if counter[wait_tile] >= 1:
        temp = Counter(counter)
        temp[wait_tile] -= 1
        if temp[wait_tile] == 0:
            del temp[wait_tile]
        if len(temp) > 0 and sum(temp.values()) == 12:
            if can_form_groups(temp, 4):
                wait_types.append('单骑听')
    
    # 2. 双碰听 (Shanpon): 两个对子，等哪个变成刻子
    # 如果wait_tile在手牌中有2张，且去掉这对后剩下的11张能组成4个面子
    if counter[wait_tile] >= 2:
        temp = Counter(counter)
        temp[wait_tile] -= 2
        if temp[wait_tile] == 0:
            del temp[wait_tile]
        if len(temp) > 0 and sum(temp.values()) == 11:
            if can_form_groups(temp, 4):
                if '双碰听' not in wait_types:
                    wait_types.append('双碰听')
    
    # 3. 顺子系听牌 (两面/坎张/边张)
    if is_honor(wait_tile):
        return wait_types
    
    n = tile_num(wait_tile)
    suit = tile_suit(wait_tile)
    if n is None:
        return wait_types
    
    # 两面听 (Ryanmen): 34等2或5
    # 检查wait_tile是否在顺子的两端
    left = f"{suit}{n-2}"
    mid = f"{suit}{n-1}"
    right1 = f"{suit}{n+1}"
    right2 = f"{suit}{n+2}"
    
    # 顺子中wait_tile在右边: X,Y,wait_tile (如 3,4,5 中的5)
    if n >= 3:
        t1 = f"{suit}{n-2}"
        t2 = f"{suit}{n-1}"
        if counter.get(t1, 0) >= 1 and counter.get(t2, 0) >= 1:
            # 检查去掉这个顺子后，剩下的能否组成3面子+1将
            temp = Counter(counter)
            temp[t1] -= 1
            temp[t2] -= 1
            for t in [t1, t2]:
                if temp[t] == 0:
                    del temp[t]
            if sum(temp.values()) == 10:
                # 尝试每种可能的将牌
                for pt in list(temp.keys()):
                    if temp[pt] >= 2:
                        temp2 = Counter(temp)
                        temp2[pt] -= 2
                        if temp2[pt] == 0:
                            del temp2[pt]
                        if can_form_groups(temp2, 3):
                            if '两面听' not in wait_types:
                                wait_types.append('两面听')
                            break
    
    # 顺子中wait_tile在左边: wait_tile,X,Y (如 3,4,5 中的3)
    if n <= 7:
        t1 = f"{suit}{n+1}"
        t2 = f"{suit}{n+2}"
        if counter.get(t1, 0) >= 1 and counter.get(t2, 0) >= 1:
            temp = Counter(counter)
            temp[t1] -= 1
            temp[t2] -= 1
            for t in [t1, t2]:
                if temp[t] == 0:
                    del temp[t]
            if sum(temp.values()) == 10:
                for pt in list(temp.keys()):
                    if temp[pt] >= 2:
                        temp2 = Counter(temp)
                        temp2[pt] -= 2
                        if temp2[pt] == 0:
                            del temp2[pt]
                        if can_form_groups(temp2, 3):
                            if '两面听' not in wait_types:
                                wait_types.append('两面听')
                            break
    
    # 坎张听 (Kanchan): X,wait_tile,Y (如 3,5等4)
    if n >= 2 and n <= 8:
        t1 = f"{suit}{n-1}"
        t2 = f"{suit}{n+1}"
        if counter.get(t1, 0) >= 1 and counter.get(t2, 0) >= 1:
            temp = Counter(counter)
            temp[t1] -= 1
            temp[t2] -= 1
            for t in [t1, t2]:
                if temp[t] == 0:
                    del temp[t]
            if sum(temp.values()) == 10:
                for pt in list(temp.keys()):
                    if temp[pt] >= 2:
                        temp2 = Counter(temp)
                        temp2[pt] -= 2
                        if temp2[pt] == 0:
                            del temp2[pt]
                        if can_form_groups(temp2, 3):
                            if '坎张听' not in wait_types:
                                wait_types.append('坎张听')
                            break
    
    # 边张听 (Penchan): 12等3 或 89等7
    if n == 3:
        t1 = f"{suit}1"
        t2 = f"{suit}2"
        if counter.get(t1, 0) >= 1 and counter.get(t2, 0) >= 1:
            temp = Counter(counter)
            temp[t1] -= 1
            temp[t2] -= 1
            for t in [t1, t2]:
                if temp[t] == 0:
                    del temp[t]
            if sum(temp.values()) == 10:
                for pt in list(temp.keys()):
                    if temp[pt] >= 2:
                        temp2 = Counter(temp)
                        temp2[pt] -= 2
                        if temp2[pt] == 0:
                            del temp2[pt]
                        if can_form_groups(temp2, 3):
                            if '边张听' not in wait_types:
                                wait_types.append('边张听')
                            break
    elif n == 7:
        t1 = f"{suit}8"
        t2 = f"{suit}9"
        if counter.get(t1, 0) >= 1 and counter.get(t2, 0) >= 1:
            temp = Counter(counter)
            temp[t1] -= 1
            temp[t2] -= 1
            for t in [t1, t2]:
                if temp[t] == 0:
                    del temp[t]
            if sum(temp.values()) == 10:
                for pt in list(temp.keys()):
                    if temp[pt] >= 2:
                        temp2 = Counter(temp)
                        temp2[pt] -= 2
                        if temp2[pt] == 0:
                            del temp2[pt]
                        if can_form_groups(temp2, 3):
                            if '边张听' not in wait_types:
                                wait_types.append('边张听')
                            break
    
    return wait_types

def analyze_tenpai_types(hand):
    """分析13张手牌的听牌类型
    返回: {tile: [types]} 字典
    """
    tenpai_tiles = get_tenpai_tiles(hand)
    if not tenpai_tiles:
        return {}
    
    result = {}
    for tile in tenpai_tiles:
        types = detect_wait_type(hand, tile)
        result[tile] = types if types else ['听牌']
    
    return result

def calculate_shanten(hand):
    """计算向听数（简化版）
    返回: 向听数（0=听牌，-1=和牌，1+=还差几步）
    """
    if len(hand) < 13:
        return -1
    
    counter = Counter(hand)
    if any(c > 4 for c in counter.values()):
        return 8  # Invalid
    
    # 检查是否已经和牌
    if len(hand) == 14 and check_agari(hand):
        return -1
    
    # 检查是否听牌
    if len(hand) == 13:
        tenpai = get_tenpai_tiles(hand)
        if tenpai:
            return 0
    
    # 简化的向听数计算
    # 使用贪心算法估算
    tiles = sorted(hand)
    groups = 0  # 已完成的面子数
    pairs = 0   # 将牌
    partials = 0  # 搭子数
    
    temp = Counter(tiles)
    
    # 先找刻子
    for t in sorted(temp.keys()):
        while temp[t] >= 3:
            groups += 1
            temp[t] -= 3
    
    # 再找将牌
    for t in sorted(temp.keys()):
        if temp[t] >= 2:
            pairs += 1
            temp[t] -= 2
            break
    
    # 找顺子和搭子
    for suit in 'mps':
        nums = sorted([tile_num(t) for t in temp.keys() if tile_suit(t) == suit and temp[t] > 0])
        if not nums:
            continue
        i = 0
        while i < len(nums):
            n = nums[i]
            if n is None:
                i += 1
                continue
            # 尝试顺子
            if (n+1) in nums and (n+2) in nums:
                groups += 1
                temp[f"{suit}{n}"] -= 1
                temp[f"{suit}{n+1}"] -= 1
                temp[f"{suit}{n+2}"] -= 1
                nums.remove(n)
                nums.remove(n+1)
                nums.remove(n+2)
            # 尝试搭子
            elif (n+1) in nums:
                partials += 1
                temp[f"{suit}{n}"] -= 1
                temp[f"{suit}{n+1}"] -= 1
                nums.remove(n)
                nums.remove(n+1)
            elif (n+2) in nums:
                partials += 1
                temp[f"{suit}{n}"] -= 1
                temp[f"{suit}{n+2}"] -= 1
                nums.remove(n)
                nums.remove(n+2)
            else:
                i += 1
    
    # 向听数 = 4 - 面子数 - min(将牌, 1) - 搭子数(最多算到4面子)
    # 但实际上搭子也需要面子来完成
    remaining = 4 - groups
    if pairs > 0:
        remaining = max(0, remaining - 1)
    
    shanten = remaining * 2 - partials
    if shanten < 0:
        shanten = 0
    
    return max(0, shanten)

def find_improving_tiles_simple(remaining, discard_tile):
    """当HandDivider无法分解时，使用简单方法找进张
    找出能与手牌形成搭子/对子的牌
    """
    counter = Counter(remaining)
    improving = set()
    
    for tile in remaining:
        n = tile_num(tile)
        suit = tile_suit(tile)
        
        if suit in 'mps' and n is not None:
            # 找对子（雀头）
            if counter[tile] >= 1:
                improving.add(tile)
            
            # 找顺子搭子
            if n <= 7:
                t2 = f"{suit}{n+1}"
                t3 = f"{suit}{n+2}"
                if counter.get(t2, 0) > 0:
                    improving.add(t3)
                if counter.get(t3, 0) > 0:
                    improving.add(t2)
            
            # 坎张搭子
            if n >= 2 and n <= 8:
                t_prev = f"{suit}{n-1}"
                t_next = f"{suit}{n+1}"
                if counter.get(t_prev, 0) > 0:
                    improving.add(t_next)
                if counter.get(t_next, 0) > 0:
                    improving.add(t_prev)
            
            # 边张搭子
            if n == 1:
                t2 = f"{suit}2"
                t3 = f"{suit}3"
                if counter.get(t2, 0) > 0:
                    improving.add(t3)
            elif n == 9:
                t7 = f"{suit}7"
                t8 = f"{suit}8"
                if counter.get(t8, 0) > 0:
                    improving.add(t7)
        
        elif is_honor(tile):
            # 字牌找对子
            if counter[tile] >= 1:
                improving.add(tile)
    
    # 移除已经在手牌中超过4张的牌
    improving = {t for t in improving if counter.get(t, 0) < 4}
    
    return list(improving)

def analyze_hand_efficiency(hand):
    """分析手牌效率：建议打哪张牌（基于shanten.py新算法）
    hand: 13或14张手牌
    返回: [{tile, waiting_tiles, count, waiting_types}] 按进张数排序
    """
    if len(hand) < 13 or len(hand) > 14:
        return []
    
    results = []
    
    if len(hand) == 14:
        # 14张手牌：使用evaluate_hand分析
        eval_result = evaluate_hand(hand)
        
        for tile, info in eval_result.items():
            improvements = info['improvements']
            count = info['count']
            shanten = info['shanten']
            
            if count > 0:
                # 分析听牌类型
                wait_types = {}
                for w_tile in improvements:
                    if shanten == 0:
                        # 听牌状态，检测听牌类型
                        remaining = list(hand)
                        remaining.remove(tile)
                        types = detect_wait_type(remaining, w_tile)
                        wait_types[w_tile] = types if types else ['听牌']
                    else:
                        wait_types[w_tile] = ['进张']
                
                results.append({
                    'tile': tile,
                    'waiting_tiles': list(improvements.keys()),
                    'count': count,
                    'waiting_types': wait_types,
                    'shanten': shanten
                })
    
    else:
        # 13张手牌：使用evaluate_tenpai分析
        eval_result = evaluate_tenpai(hand)
        improvements = eval_result['improvements']
        count = eval_result['count']
        shanten = eval_result['shanten']
        
        if count > 0:
            wait_types = {}
            for w_tile in improvements:
                if shanten == 0:
                    types = detect_wait_type(hand, w_tile)
                    wait_types[w_tile] = types if types else ['听牌']
                else:
                    wait_types[w_tile] = ['进张']
            
            results.append({
                'tile': None,
                'waiting_tiles': list(improvements.keys()),
                'count': count,
                'waiting_types': wait_types,
                'shanten': shanten
            })
    
    # 按进张数排序（降序）
    results.sort(key=lambda x: x['count'], reverse=True)
    
    return results

def calc_shanten_from_decomp(decomp, hand_size):
    """根据分解结果计算向听数
    decomp: HandDivider分解出的面子组合
    hand_size: 手牌数量
    """
    groups = 0  # 面子数
    pairs = 0   # 将牌
    
    for meld in decomp:
        if meld['type'] in ('handshuntsu', 'handkouutsu'):
            groups += 1
        elif meld['type'] == 'handtoitsu':
            pairs += 1
    
    # 标准型向听数 = 8 - 2*面子数 - 将牌
    # 但需要考虑手牌数量
    target_groups = 4 if hand_size >= 13 else hand_size // 3
    
    shanten = target_groups * 2 - groups * 2 - (1 if pairs > 0 else 0)
    
    return max(0, shanten)

def analyze_yaku(hand, is_tsumo=False, is_riichi=False, is_ippatsu=False):
    """分析手牌可构成的役种（增强版，14张和牌状态）"""
    yaku_list = []
    counter = Counter(hand)
    
    if len(hand) != 14 or not check_agari(hand):
        return yaku_list
    
    # 基本役种判定
    # 七对子
    if check_chiitoitsu(counter):
        yaku_list.append('七对子')
    
    # 断幺九
    if not any(is_yaochu(t) for t in counter):
        yaku_list.append('断幺九')
    
    # 役牌
    honor_yaku = {
        'white': '役牌-白', 'green': '役牌-发', 'red': '役牌-中',
        'east': '自风牌/场风牌', 'south': '自风牌/场风牌',
        'west': '自风牌/场风牌', 'north': '自风牌/场风牌',
    }
    for t, name in honor_yaku.items():
        if counter[t] >= 3:
            if name not in yaku_list:
                yaku_list.append(name)
    
    # 对对和
    quads = sum(1 for c in counter.values() if c >= 3)
    if quads == 4:
        yaku_list.append('对对和')
    
    # 小三元
    san_yuan = [counter.get(t, 0) >= 3 for t in ['white', 'green', 'red']]
    san_yuan_pair = [counter.get(t, 0) >= 2 for t in ['white', 'green', 'red']]
    if sum(san_yuan) == 2 and sum(san_yuan_pair) == 3:
        yaku_list.append('小三元')
    
    # 大三元
    if all(counter.get(t, 0) >= 3 for t in ['white', 'green', 'red']):
        yaku_list.append('大三元')
    
    # 混老头
    if all(is_yaochu(t) for t in counter):
        yaku_list.append('混老头')
    
    # 清一色
    suits = set(tile_suit(t) for t in counter)
    if len(suits) == 1 and list(suits)[0] in 'mps':
        yaku_list.append('清一色')
    
    # 混一色
    elif len(suits) == 2 and any(tile_suit(t) in 'mps' for t in counter) and any(is_honor(t) for t in counter):
        yaku_list.append('混一色')
    
    # 字一色
    if all(is_honor(t) for t in counter):
        yaku_list.append('字一色')
    
    # 清老头
    if all(is_terminal(t) for t in counter) and not any(is_honor(t) for t in counter):
        yaku_list.append('清老头')
    
    # 绿一色
    if all(is_green(t) for t in counter):
        yaku_list.append('绿一色')
    
    # 国士无双
    if check_kokushi(counter):
        yaku_list.append('国士无双')
    
    # 四暗刻（简化检查）
    if sum(1 for c in counter.values() if c >= 3) == 4:
        yaku_list.append('四暗刻')
    
    # 大四喜/小四喜
    winds = ['east', 'south', 'west', 'north']
    wind_kotsu = sum(1 for w in winds if counter.get(w, 0) >= 3)
    wind_pair = sum(1 for w in winds if counter.get(w, 0) >= 2)
    if wind_kotsu == 4:
        yaku_list.append('大四喜')
    elif wind_kotsu == 3 and wind_pair == 4:
        yaku_list.append('小四喜')
    
    # 四杠子（简化）
    if sum(1 for c in counter.values() if c == 4) == 4:
        yaku_list.append('四杠子')
    
    # ===== 新增增强判定 =====
    
    # 一杯口/二杯口判定
    # 找出手牌中所有顺子，检查是否有相同的
    sequences = []
    temp_counter = Counter(counter)
    for suit in 'mps':
        for n in range(1, 8):
            t1, t2, t3 = f"{suit}{n}", f"{suit}{n+1}", f"{suit}{n+2}"
            while (temp_counter.get(t1, 0) >= 1 and 
                   temp_counter.get(t2, 0) >= 1 and 
                   temp_counter.get(t3, 0) >= 1):
                sequences.append((suit, n))
                temp_counter[t1] -= 1
                temp_counter[t2] -= 1
                temp_counter[t3] -= 1
    
    # 检查重复顺子
    seq_counts = Counter(sequences)
    pairs_of_seqs = sum(1 for c in seq_counts.values() if c >= 2)
    
    if pairs_of_seqs >= 2:
        yaku_list.append('二杯口')
    elif pairs_of_seqs >= 1:
        yaku_list.append('一杯口')
    
    # 一气通贯判定
    for suit in 'mps':
        has_123 = counter.get(f"{suit}1", 0) >= 1 and counter.get(f"{suit}2", 0) >= 1 and counter.get(f"{suit}3", 0) >= 1
        has_456 = counter.get(f"{suit}4", 0) >= 1 and counter.get(f"{suit}5", 0) >= 1 and counter.get(f"{suit}6", 0) >= 1
        has_789 = counter.get(f"{suit}7", 0) >= 1 and counter.get(f"{suit}8", 0) >= 1 and counter.get(f"{suit}9", 0) >= 1
        if has_123 and has_456 and has_789:
            yaku_list.append('一气通贯')
            break
    
    # 三色同顺判定
    for n in range(1, 8):
        m_ok = counter.get(f"m{n}", 0) >= 1 and counter.get(f"m{n+1}", 0) >= 1 and counter.get(f"m{n+2}", 0) >= 1
        p_ok = counter.get(f"p{n}", 0) >= 1 and counter.get(f"p{n+1}", 0) >= 1 and counter.get(f"p{n+2}", 0) >= 1
        s_ok = counter.get(f"s{n}", 0) >= 1 and counter.get(f"s{n+1}", 0) >= 1 and counter.get(f"s{n+2}", 0) >= 1
        if m_ok and p_ok and s_ok:
            yaku_list.append('三色同顺')
            break
    
    # 三色同刻判定
    for n in range(1, 10):
        m_ok = counter.get(f"m{n}", 0) >= 3
        p_ok = counter.get(f"p{n}", 0) >= 3
        s_ok = counter.get(f"s{n}", 0) >= 3
        if m_ok and p_ok and s_ok:
            yaku_list.append('三色同刻')
            break
    
    # 纯全带幺九/混全带幺九判定
    # 需要检查每组面子和将牌是否都包含幺九牌
    has_honor = any(is_honor(t) for t in counter)
    has_terminal = any(is_terminal(t) for t in counter)
    
    # 检查手牌中是否只有幺九牌和字牌
    all_yaochu = all(is_yaochu(t) for t in counter)
    
    if all_yaochu:
        # 如果全是幺九牌，检查是否能组成有效和牌型
        # 纯全带幺九：不含字牌，每组都有1或9
        if not has_honor and has_terminal:
            # 检查是否每组面子都含1或9
            # 启发式：如果手牌中只有1、9和少量2-8的牌
            non_terminal = [t for t in counter if tile_suit(t) in 'mps' and not is_terminal(t)]
            if not non_terminal:
                yaku_list.append('纯全带幺九')
            elif has_honor:
                yaku_list.append('混全带幺九')
        elif has_honor:
            # 有字牌，检查是否混全带幺九
            # 启发式：如果手牌中只有幺九牌和字牌
            non_yaochu = [t for t in counter if not is_yaochu(t)]
            if not non_yaochu:
                yaku_list.append('混全带幺九')
    else:
        # 更精确的检测：尝试分解手牌，检查每组是否都含幺九
        # 这里用更简单的启发式方法
        # 检查手牌中是否大部分是幺九牌
        yaochu_count = sum(c for t, c in counter.items() if is_yaochu(t))
        total_count = sum(counter.values())
        
        # 如果幺九牌占比超过70%，可能是混全带/纯全带
        if yaochu_count >= total_count * 0.7:
            if not has_honor and has_terminal:
                # 可能是纯全带幺九
                # 更精确检查：尝试找到一种分解方式使得每组都含1或9
                if check_chanta_decomposition(counter, junchan=True):
                    yaku_list.append('纯全带幺九')
            elif has_honor and has_terminal:
                # 可能是混全带幺九
                if check_chanta_decomposition(counter, junchan=False):
                    yaku_list.append('混全带幺九')
    
    # 三暗刻判定（区分暗刻/明刻）
    # 暗刻 = 没有被碰过的刻子（简化：手牌中3张相同的牌）
    concealed_koutsu = sum(1 for c in counter.values() if c >= 3)
    if concealed_koutsu >= 3:
        # 排除四暗刻（已在上面判定）
        if '四暗刻' not in yaku_list:
            yaku_list.append('三暗刻')
    
    # 平和判定
    # 条件：1) 全部是顺子（4个顺子+1将）2) 将牌不是役牌 3) 两面听
    if not any(is_honor(t) for t in counter):
        # 检查是否能分解为4个顺子+1将
        is_all_sequences = False
        for pair_tile in counter:
            if counter[pair_tile] < 2:
                continue
            temp = Counter(counter)
            temp[pair_tile] -= 2
            if temp[pair_tile] == 0:
                del temp[pair_tile]
            # 检查是否全是顺子
            if all_can_form_sequences(temp):
                is_all_sequences = True
                break
        
        if is_all_sequences:
            # 将牌不能是役牌（这里简化为不是字牌）
            # 实际平和的将牌不能是三元牌、自风牌、场风牌
            yaku_list.append('平和')
    
    # 立直系
    if is_riichi:
        yaku_list.append('立直')
        if is_ippatsu:
            yaku_list.append('一发')
        if is_tsumo:
            yaku_list.append('门前清自摸和')
    
    return yaku_list

def all_can_form_sequences(counter):
    """检查是否能全部分解为顺子"""
    if not counter:
        return True
    
    tile = min(counter.keys())
    if is_honor(tile):
        return False
    
    n = tile_num(tile)
    suit = tile_suit(tile)
    if n is None or n > 7:
        return False
    
    t2 = f"{suit}{n+1}"
    t3 = f"{suit}{n+2}"
    
    if counter.get(t2, 0) >= 1 and counter.get(t3, 0) >= 1:
        temp = Counter(counter)
        temp[tile] -= 1
        temp[t2] -= 1
        temp[t3] -= 1
        for t in [tile, t2, t3]:
            if temp[t] == 0:
                del temp[t]
        if all_can_form_sequences(temp):
            return True
    
    return False

def check_chanta_decomposition(counter, junchan=False):
    """检查手牌是否能分解为每组都含幺九牌的形式
    counter: 手牌计数器
    junchan: True=纯全带幺九（不含字牌），False=混全带幺九（含字牌）
    """
    if not counter:
        return True
    
    tiles = sorted(counter.keys())
    first_tile = tiles[0]
    
    # 将牌（必须含幺九）
    for pair_tile in tiles:
        if counter[pair_tile] < 2:
            continue
        if not is_yaochu(pair_tile):
            continue
        if junchan and is_honor(pair_tile):
            continue
        
        temp = Counter(counter)
        temp[pair_tile] -= 2
        if temp[pair_tile] == 0:
            del temp[pair_tile]
        
        # 检查剩余牌是否能分解为每组都含幺九的面子
        if check_groups_with_yaochu(temp, 4, junchan):
            return True
    
    return False

def check_groups_with_yaochu(counter, groups_needed, junchan=False):
    """检查是否能组成指定数量的面子，且每组都含幺九牌"""
    if groups_needed == 0:
        return len(counter) == 0
    
    if not counter:
        return False
    
    tile = min(counter.keys())
    
    # 尝试刻子（必须是幺九牌）
    if is_yaochu(tile) and counter[tile] >= 3:
        if not (junchan and is_honor(tile)):
            temp = Counter(counter)
            temp[tile] -= 3
            if temp[tile] == 0:
                del temp[tile]
            if check_groups_with_yaochu(temp, groups_needed - 1, junchan):
                return True
    
    # 尝试顺子（必须含幺九牌）
    if tile_suit(tile) in 'mps':
        n = tile_num(tile)
        if n is not None and n <= 7:
            t2 = f"{tile_suit(tile)}{n+1}"
            t3 = f"{tile_suit(tile)}{n+2}"
            # 顺子必须含1或9
            if (is_terminal(tile) or is_terminal(t2) or is_terminal(t3)):
                if counter.get(t2, 0) >= 1 and counter.get(t3, 0) >= 1:
                    temp = Counter(counter)
                    temp[tile] -= 1
                    temp[t2] -= 1
                    temp[t3] -= 1
                    for t in [tile, t2, t3]:
                        if temp[t] == 0:
                            del temp[t]
                    if check_groups_with_yaochu(temp, groups_needed - 1, junchan):
                        return True
    
    return False

# ========== 符数计算 ==========
def calculate_fu(hand, is_tsumo, is_tsumo_agari, dora_count=0):
    """计算符数（简化版）
    hand: 14张牌 Counter
    is_tsumo: 是否门前清
    is_tsumo_agari: 是否自摸和牌
    """
    counter = Counter(hand)
    fu = 20  # 底符
    
    # 自摸和牌+2符（非平和时）
    if is_tsumo_agari:
        fu += 2
    
    # 荣和+10符（非门前清时）
    if not is_tsumo and not is_tsumo_agari:
        fu += 10
    
    # 雀头符
    # 役牌雀头+2符
    yakuhai_heads = ['white', 'green', 'red', 'east', 'south', 'west', 'north']
    
    # 刻子/杠子符
    for tile, count in counter.items():
        if count >= 3:
            base = 2 if is_terminal(tile) or is_honor(tile) else 4
            if count == 4:
                base *= 4  # 暗杠
            elif is_tsumo:
                base *= 2  # 暗刻
            fu += base * count
    
    # 符数向上取整到10的倍数
    fu = ((fu + 9) // 10) * 10
    
    return fu

def calculate_score(fu, han, is_dealer, is_tsumo):
    """计算点数"""
    if han >= 13:
        base = 8000
    elif han >= 11:
        base = 6000
    elif han >= 8:
        base = 4000
    elif han >= 6:
        base = 3000
    elif han >= 5:
        base = 2000
    else:
        base = fu * (2 ** (han + 2))
        if base > 2000:
            base = 2000
    
    if is_dealer:
        if is_tsumo:
            return {
                'all': base * 2,
                'total': base * 2 * 3,
                'type': '自摸（亲家）'
            }
        else:
            return {
                'from_player': base * 6,
                'total': base * 6,
                'type': '荣和（亲家）'
            }
    else:
        if is_tsumo:
            return {
                'dealer': base * 2,
                'others': base,
                'total': base * 2 + base * 2,
                'type': '自摸（子家）'
            }
        else:
            return {
                'from_player': base * 4,
                'total': base * 4,
                'type': '荣和（子家）'
            }

# ========== 役种数据 ==========
YAKU_DATA = [
    {"id": 1, "name": "立直", "japanese": "立直 (リーチ)", "han": 1, "type": "门前清限定", "description": "在门前清听牌时宣告立直，支付1000点立直棒", "condition": "必须门前清状态且已听牌，宣言后支付1000点", "tiles": ['m2','m3','m4','p2','p3','p4','s6','s7','s8','s8','s8','white','white'], "category": "1番", "tags": ["立直", "门前清限定", "基础"]},
    {"id": 2, "name": "一发", "japanese": "一発 (イッパツ)", "han": 1, "type": "门前清限定", "description": "立直后，在自己摸牌前和牌", "condition": "立直后，下一巡内和牌（中间不可被其他家吃碰明杠）", "tiles": ['m1','m2','m3','p4','p5','p6','s7','s8','s9','east','east','white','white'], "category": "1番", "tags": ["立直", "一发", "门前清限定"]},
    {"id": 3, "name": "门前清自摸和", "japanese": "門前清自摸和 (メンゼンチンツモホウ)", "han": 1, "type": "门前清限定", "description": "保持门前清状态，自己摸牌和牌", "condition": "没有吃、碰、明杠，自摸和牌", "tiles": ['m2','m3','m4','p5','p6','p7','s1','s2','s3','south','south','green','green'], "category": "1番", "tags": ["自摸", "门前清限定", "基础"]},
    {"id": 4, "name": "平和", "japanese": "平和 (ピンフ)", "han": 1, "type": "门前清限定", "description": "由4个顺子+1对将牌组成，听牌为两面听，将牌不能是役牌", "condition": "全顺子、两面听、将牌为非役牌的数牌", "tiles": ['m2','m3','m4','p2','p3','p4','s6','s7','s8','s3','s4','s5','s5'], "category": "1番", "tags": ["顺子", "门前清限定", "基础"]},
    {"id": 5, "name": "断幺九", "japanese": "断幺九 (タンヤオチュウ)", "han": 1, "type": "副露可", "description": "手牌中只包含2~8的数牌，不含1、9和字牌", "condition": "所有牌都是2-8的数牌（万筒条）", "tiles": ['m2','m3','m4','p3','p4','p5','s6','s7','s8','s2','s2','m5','m5'], "category": "1番", "tags": ["幺九", "副露可", "基础"]},
    {"id": 6, "name": "役牌-白", "japanese": "役牌 - 白 (ハク)", "han": 1, "type": "副露可", "description": "手牌中有白板的刻子或杠子", "condition": "三个或四个白板", "tiles": ['white','white','white','m2','m3','m4','p5','p6','p7','s7','s8','s9','s9'], "category": "1番", "tags": ["役牌", "三元牌", "副露可"]},
    {"id": 7, "name": "役牌-发", "japanese": "役牌 - 發 (ハツ)", "han": 1, "type": "副露可", "description": "手牌中有发财的刻子或杠子", "condition": "三个或四个发财", "tiles": ['green','green','green','m1','m2','m3','p4','p5','p6','s7','s8','s9','s9'], "category": "1番", "tags": ["役牌", "三元牌", "副露可"]},
    {"id": 8, "name": "役牌-中", "japanese": "役牌 - 中 (チュン)", "han": 1, "type": "副露可", "description": "手牌中有红中的刻子或杠子", "condition": "三个或四个红中", "tiles": ['red','red','red','m2','m3','m4','p5','p6','p7','s1','s2','s3','s3'], "category": "1番", "tags": ["役牌", "三元牌", "副露可"]},
    {"id": 9, "name": "自风牌", "japanese": "自風牌 (ジカゼハイ)", "han": 1, "type": "副露可", "description": "手牌中有与自己风位相同的刻子或杠子", "condition": "三个或四个自风牌（如东家为东）", "tiles": ['east','east','east','m2','m3','m4','p5','p6','p7','s1','s2','s3','s3'], "category": "1番", "tags": ["役牌", "风牌", "副露可"]},
    {"id": 10, "name": "场风牌", "japanese": "場風牌 (バカゼハイ)", "han": 1, "type": "副露可", "description": "手牌中有与场风相同的刻子或杠子", "condition": "三个或四个场风牌（如东风圈则东为场风）", "tiles": ['east','east','east','m2','m3','m4','p5','p6','p7','s1','s2','s3','s3'], "category": "1番", "tags": ["役牌", "风牌", "副露可"]},
    {"id": 11, "name": "岭上开花", "japanese": "嶺上開花 (リンシャンカイホウ)", "han": 1, "type": "副露可", "description": "杠牌后从岭上摸牌自摸和牌", "condition": "开杠后摸岭上牌自摸和牌（包含加杠、暗杠）", "tiles": ['m1','m2','m3','p4','p5','p6','white','white','white','white','s7','s8','s9'], "category": "1番", "tags": ["杠", "自摸", "副露可"]},
    {"id": 12, "name": "抢杠", "japanese": "槍槓 (チャンカン)", "han": 1, "type": "副露可", "description": "荣别人加杠的牌", "condition": "他家碰牌后进行加杠时，荣和那张牌", "tiles": ['m1','m2','m3','p4','p5','p6','white','white','s7','s8','s9','south','south'], "category": "1番", "tags": ["杠", "荣", "副露可"]},
    {"id": 13, "name": "海底摸月", "japanese": "海底摸月 (ハイテイモウヨウ)", "han": 1, "type": "副露可", "description": "摸牌墙最后一张牌自摸和牌", "condition": "牌山剩余0张时，摸最后一张牌自摸", "tiles": ['m2','m3','m4','p5','p6','p7','s1','s2','s3','east','east','green','green'], "category": "1番", "tags": ["自摸", "最后一张", "副露可"]},
    {"id": 14, "name": "河底捞鱼", "japanese": "河底撈魚 (ホウテイラオユイ)", "han": 1, "type": "副露可", "description": "牌山摸完后，荣和最后一张打出的牌", "condition": "牌山剩余0张时，荣和他家打出的牌", "tiles": ['m2','m3','m4','p5','p6','p7','s1','s2','s3','east','east','green','green'], "category": "1番", "tags": ["荣", "最后一张", "副露可"]},
    {"id": 15, "name": "一杯口", "japanese": "一盃口 (イーペーコウ)", "han": 1, "type": "门前清限定", "description": "同种数牌有完全相同的两组顺子", "condition": "门前清限定，同一花色有两组数字相同的顺子", "tiles": ['m2','m3','m4','m2','m3','m4','p5','p6','p7','s8','s9','white','white'], "category": "1番", "tags": ["顺子", "门前清限定", "重复"]},
    {"id": 16, "name": "七对子", "japanese": "七対子 (チートイツ)", "han": 2, "type": "门前清限定", "description": "由7个对子组成的特殊和牌型", "condition": "七组不同的对子，不能有相同的四张牌", "tiles": ['m2','m2','p3','p3','s5','s5','east','east','south','south','white','white','red'], "category": "2番", "tags": ["对子", "特殊型", "门前清限定"]},
    {"id": 17, "name": "混全带幺九", "japanese": "混全帯幺九 (ホンチャンタイヤオチュウ)", "han": 2, "type": "门前清限定", "description": "每组面子（顺子/刻子）和将牌都包含幺九牌或字牌", "condition": "所有面子和将牌都含1、9或字牌", "tiles": ['m1','m2','m3','p7','p8','p9','s1','s1','s1','east','east','white','white'], "category": "2番", "tags": ["幺九", "字牌", "副露可"]},
    {"id": 18, "name": "一气通贯", "japanese": "一気通貫 (イッキツウカン)", "han": 2, "type": "门前清限定", "description": "同种花色有123、456、789三组顺子", "condition": "同一花色包含1-9的连续顺子序列", "tiles": ['m1','m2','m3','m4','m5','m6','m7','m8','m9','p2','p3','s5','s5'], "category": "2番", "tags": ["顺子", "一气", "副露可"]},
    {"id": 19, "name": "三色同顺", "japanese": "三色同順 (サンショクドウジュン)", "han": 2, "type": "门前清限定", "description": "三种花色有相同数字的顺子", "condition": "万、筒、条有同一数字的顺子", "tiles": ['m2','m3','m4','p2','p3','p4','s2','s3','s4','east','east','white','white'], "category": "2番", "tags": ["顺子", "三色", "副露可"]},
    {"id": 20, "name": "三色同刻", "japanese": "三色同刻 (サンショクドウコウ)", "han": 2, "type": "副露可", "description": "三种花色有相同数字的刻子", "condition": "万、筒、条有同一数字的刻子/杠子", "tiles": ['m5','m5','m5','p5','p5','p5','s5','s5','s5','east','east','white','white'], "category": "2番", "tags": ["刻子", "三色", "副露可"]},
    {"id": 21, "name": "对对和", "japanese": "対々和 (トイトイホウ)", "han": 2, "type": "副露可", "description": "由4个刻子/杠子+1对将牌组成", "condition": "手牌全由刻子/杠子和将牌组成，无顺子", "tiles": ['m2','m2','m2','p5','p5','p5','s8','s8','s8','east','east','east','white','white'], "category": "2番", "tags": ["刻子", "副露可"]},
    {"id": 22, "name": "三暗刻", "japanese": "三暗刻 (サンアンコウ)", "han": 2, "type": "副露可", "description": "手牌中有3个暗刻或暗杠", "condition": "三个自己摸到的刻子（非碰出），第四组可以是任意", "tiles": ['m3','m3','m3','p6','p6','p6','s9','s9','s9','east','east','white','white'], "category": "2番", "tags": ["刻子", "暗刻", "副露可"]},
    {"id": 23, "name": "小三元", "japanese": "小三元 (ショウサンゲン)", "han": 2, "type": "副露可", "description": "白、发、中三种三元牌组成2个刻子+1对将牌", "condition": "三元牌中有2个刻子/杠子和1个对子", "tiles": ['white','white','white','green','green','green','red','red','m2','m3','m4','p5','p5'], "category": "2番", "tags": ["三元牌", "副露可"]},
    {"id": 24, "name": "混老头", "japanese": "混老頭 (ホンロウトウ)", "han": 2, "type": "副露可", "description": "手牌全由幺九牌和字牌组成", "condition": "只能有1、9数牌和东南西北白发中", "tiles": ['m1','m1','m1','p9','p9','p9','s1','s1','east','east','west','west','white'], "category": "2番", "tags": ["幺九", "字牌", "副露可"]},
    {"id": 25, "name": "两立直", "japanese": "両立直 (ダブルリーチ)", "han": 2, "type": "门前清限定", "description": "第一巡（未经过任何吃碰明杠）即听牌并立直", "condition": "配牌后第一张打出即立直（门前清第一巡听牌）", "tiles": ['m2','m3','m4','p2','p3','p4','s6','s7','s8','east','east','white','white'], "category": "2番", "tags": ["立直", "门前清限定"]},
    {"id": 26, "name": "二杯口", "japanese": "二盃口 (リャンペーコウ)", "han": 3, "type": "门前清限定", "description": "同种数牌有两组完全相同的两组顺子（两个一杯口）", "condition": "门前清限定，包含两组相同的两组顺子", "tiles": ['m2','m3','m4','m2','m3','m4','p5','p6','p7','p5','p6','p7','s8','s8'], "category": "3番", "tags": ["顺子", "门前清限定", "重复"]},
    {"id": 27, "name": "纯全带幺九", "japanese": "純全帯幺九 (ジュンチャンタイヤオチュウ)", "han": 3, "type": "门前清限定", "description": "每组面子和将牌都包含1或9，不含字牌", "condition": "所有面子和将牌都含1或9，无字牌", "tiles": ['m1','m2','m3','p7','p8','p9','s1','s1','s1','m9','m9','p1','p1'], "category": "3番", "tags": ["幺九", "副露可"]},
    {"id": 28, "name": "混一色", "japanese": "混一色 (ホンイツ)", "han": 3, "type": "门前清限定", "description": "手牌由一种花色+字牌组成", "condition": "只有一种数牌+字牌", "tiles": ['m1','m2','m3','m5','m5','m5','m8','m8','m8','east','east','white','white'], "category": "3番", "tags": ["一色", "字牌", "副露可"]},
    {"id": 29, "name": "清一色", "japanese": "清一色 (チンイツ)", "han": 6, "type": "门前清限定", "description": "手牌只由一种花色的数牌组成，不含字牌", "condition": "只有万子/筒子/条子中的一种数牌", "tiles": ['m1','m2','m3','m4','m5','m6','m6','m6','m8','m8','m8','m9','m9'], "category": "6番", "tags": ["一色", "副露可"]},
    {"id": 30, "name": "流局满贯", "japanese": "流局満貫 (リュウキョクマンガン)", "han": 5, "type": "特殊", "description": "流局时听牌且手牌全为幺九或字牌，或在特定规则下达成", "condition": "根据规则，流局时满足特定条件（雀魂中部分规则场存在）", "tiles": ['m1','m1','m1','p9','p9','s1','s1','east','east','west','west','white','white'], "category": "满贯", "tags": ["流局", "特殊"]},
    {"id": 31, "name": "国士无双", "japanese": "国士無双 (コクシムソウ)", "han": 13, "type": "门前清限定", "description": "13种幺九牌各1张+其中任意1张组成", "condition": "1、9万筒条+东南西北白发中各一张，再重复其中一张", "tiles": ['m1','m9','p1','p9','s1','s9','east','south','west','north','white','green','red'], "category": "役满", "tags": ["十三幺", "门前清限定", "特殊型"]},
    {"id": 32, "name": "国士无双十三面", "japanese": "国士無双十三面待ち", "han": 26, "type": "门前清限定", "description": "国士无双听全部13种幺九牌", "condition": "门前清限定，13种幺九牌各1张，听全部13种", "tiles": ['m1','m9','p1','p9','s1','s9','east','south','west','north','white','green','red'], "category": "双倍役满", "tags": ["十三幺", "门前清限定", "特殊型"]},
    {"id": 33, "name": "大三元", "japanese": "大三元 (ダイサンゲン)", "han": 13, "type": "副露可", "description": "手牌中有白、发、中三种牌的刻子或杠子", "condition": "三元牌全部组成刻子/杠子", "tiles": ['white','white','white','green','green','green','red','red','red','m2','m3','m4','m4'], "category": "役满", "tags": ["三元牌", "副露可"]},
    {"id": 34, "name": "四暗刻", "japanese": "四暗刻 (スーアンコウ)", "han": 13, "type": "门前清限定", "description": "手牌中有4个暗刻或暗杠", "condition": "四个都是自己摸到的刻子/杠子（非碰出）", "tiles": ['m3','m3','m3','p6','p6','p6','s9','s9','s9','east','east','east','white','white'], "category": "役满", "tags": ["暗刻", "门前清限定"]},
    {"id": 35, "name": "四暗刻单骑", "japanese": "四暗刻単騎 (スーアンコウタンキ)", "han": 26, "type": "门前清限定", "description": "四暗刻且听单张将牌", "condition": "四个暗刻，将牌是单张听牌（单骑听牌）", "tiles": ['m3','m3','m3','p6','p6','p6','s9','s9','s9','east','east','east','white'], "category": "双倍役满", "tags": ["暗刻", "单骑", "门前清限定"]},
    {"id": 36, "name": "字一色", "japanese": "字一色 (ツーイーソー)", "han": 13, "type": "副露可", "description": "手牌全由字牌组成", "condition": "只有东南西北白发中", "tiles": ['east','east','east','south','south','south','west','west','west','north','north','white','white'], "category": "役满", "tags": ["字牌", "副露可"]},
    {"id": 37, "name": "清老头", "japanese": "清老頭 (チンロウトウ)", "han": 13, "type": "副露可", "description": "手牌全由1和9组成，不含字牌", "condition": "只有数字牌的1和9", "tiles": ['m1','m1','m1','m9','m9','m9','p1','p1','p1','p9','p9','s1','s1'], "category": "役满", "tags": ["幺九", "副露可"]},
    {"id": 38, "name": "九莲宝灯", "japanese": "九蓮宝燈 (チューレンポウトウ)", "han": 13, "type": "门前清限定", "description": "同种花色1112345678999+任意同花色牌", "condition": "门前清限定，同花色包含1112345678999形式", "tiles": ['m1','m1','m1','m2','m3','m4','m5','m6','m7','m8','m9','m9','m9'], "category": "役满", "tags": ["一色", "门前清限定"]},
    {"id": 39, "name": "纯正九莲宝灯", "japanese": "純正九蓮宝燈", "han": 26, "type": "门前清限定", "description": "九莲宝灯且听全部9种牌", "condition": "门前清限定，听该花色全部9种牌", "tiles": ['m1','m1','m1','m2','m3','m4','m5','m6','m7','m8','m9','m9','m9'], "category": "双倍役满", "tags": ["一色", "门前清限定"]},
    {"id": 40, "name": "绿一色", "japanese": "緑一色 (リューイーソー)", "han": 13, "type": "副露可", "description": "手牌全由绿色牌组成（23468条+发）", "condition": "只使用2、3、4、6、8条和发财", "tiles": ['s2','s2','s2','s3','s3','s3','s4','s4','s4','s6','s6','green','green'], "category": "役满", "tags": ["一色", "副露可"]},
    {"id": 41, "name": "小四喜", "japanese": "小四喜 (ショウスーシー)", "han": 13, "type": "副露可", "description": "东南西北四种风牌组成3个刻子+1对将牌", "condition": "四风牌中有3个刻子/杠子和1个对子", "tiles": ['east','east','east','south','south','south','west','west','west','north','north','m2','m2'], "category": "役满", "tags": ["风牌", "副露可"]},
    {"id": 42, "name": "大四喜", "japanese": "大四喜 (ダイスーシー)", "han": 13, "type": "副露可", "description": "东南西北四种风牌全部组成刻子或杠子", "condition": "四风牌全部组成刻子/杠子", "tiles": ['east','east','east','south','south','south','west','west','west','north','north','north','m2','m2'], "category": "役满", "tags": ["风牌", "副露可"]},
    {"id": 43, "name": "四杠子", "japanese": "四槓子 (スーカンツ)", "han": 13, "type": "副露可", "description": "手牌中有4个杠子（明暗皆可）", "condition": "四个杠子（可以是暗杠或明杠）", "tiles": ['m2','m2','m2','m2','p5','p5','p5','p5','s8','s8','s8','s8','east','east','east','east'], "category": "役满", "tags": ["杠", "副露可"]},
    {"id": 44, "name": "天和", "japanese": "天和 (テンホウ)", "han": 13, "type": "门前清限定", "description": "庄家配牌后直接和牌", "condition": "东家（庄家），配牌后第一张自摸和牌", "tiles": ['m1','m1','m1','p4','p4','p4','s7','s7','s7','east','east','white','white'], "category": "役满", "tags": ["天和", "门前清限定"]},
    {"id": 45, "name": "地和", "japanese": "地和 (チーホウ)", "han": 13, "type": "门前清限定", "description": "闲家在第一轮摸牌前和牌", "condition": "闲家，第一轮摸牌前自摸或荣和（不含暗杠）", "tiles": ['m2','m3','m4','p5','p6','p7','s8','s9','s1','south','south','white','white'], "category": "役满", "tags": ["地和", "门前清限定"]},
    {"id": 46, "name": "人和", "japanese": "人和 (レンホウ)", "han": 13, "type": "门前清限定", "description": "闲家配牌后第一轮荣和庄家打出的牌", "condition": "闲家，第一轮荣和庄家", "tiles": ['m2','m3','m4','p5','p6','p7','s8','s9','s1','south','south','white','white'], "category": "役满", "tags": ["人和", "门前清限定"]},
]

HAN_ORDER = {"1番": 1, "2番": 2, "3番": 3, "6番": 6, "满贯": 5, "役满": 13, "双倍役满": 26}

# ========== 路由 ==========

@app.route('/')
def index():
    processed = []
    for yaku in YAKU_DATA:
        yc = dict(yaku)
        if 'tiles' in yc:
            yc['tiles_png'] = tiles_to_pngs(yc['tiles'])
        processed.append(yc)
    sorted_yaku = sorted(processed, key=lambda x: HAN_ORDER.get(x["category"], 0))
    return render_template('index.html', yaku_list=sorted_yaku, categories=list(HAN_ORDER.keys()))

@app.route('/api/search')
def search():
    query = request.args.get('q', '').lower()
    category = request.args.get('category', '')
    results = YAKU_DATA
    if query:
        results = [y for y in results if query in y['name'].lower() or query in y['japanese'].lower() or query in y['description'].lower() or any(query in tag.lower() for tag in y['tags'])]
    if category:
        results = [y for y in results if y['category'] == category]
    for r in results:
        if 'tiles' in r:
            r['tiles_png'] = tiles_to_pngs(r['tiles'])
    
    return jsonify(results)

@app.route('/api/yaku/<int:yaku_id>')
def get_yaku(yaku_id):
    yaku = next((y for y in YAKU_DATA if y['id'] == yaku_id), None)
    if yaku:
        yc = dict(yaku)
        if 'tiles' in yc:
            yc['tiles_png'] = tiles_to_pngs(yc['tiles'])
        return jsonify(yc)
    return jsonify({"error": "Not found"}), 404

# ========== 符数计算器页面 ==========
@app.route('/fu-calculator')
def fu_calculator():
    return render_template('fu-calculator.html', tiles=ALL_TILES, tile_names=TILE_NAMES)

# ========== 手牌分析器页面 ==========
@app.route('/hand-analyzer')
def hand_analyzer():
    return render_template('hand-analyzer.html', tiles=ALL_TILES, tile_names=TILE_NAMES)

# ========== API: 手牌分析 ==========
@app.route('/api/analyze-hand', methods=['POST'])
def analyze_hand_api():
    data = request.get_json()
    hand = data.get('hand', [])
    
    if not hand or len(hand) > 14:
        return jsonify({"error": "手牌数量不合法"}), 400
    
    result = {
        "hand": hand,
        "hand_count": len(hand),
        "tiles_png": tiles_to_pngs(hand),
        "counter": dict(Counter(hand)),
    }
    
    # 检查非法牌（超过4张）
    counter = Counter(hand)
    invalid = {t: c for t, c in counter.items() if c > 4}
    if invalid:
        result["invalid"] = invalid
        result["message"] = "手牌中有超过4张的牌"
        return jsonify(result)
    
    if len(hand) == 14:
        # 和牌判定
        is_agari = check_agari(hand)
        result["is_agari"] = is_agari
        if is_agari:
            yaku_names = analyze_yaku(hand)
            # Build YAKU_HAN_MAP
            YAKU_HAN_MAP = {}
            for y in YAKU_DATA:
                h = y['han']
                if isinstance(h, int):
                    YAKU_HAN_MAP[y['name']] = h
                elif h == '役满':
                    YAKU_HAN_MAP[y['name']] = 13
                elif h == '双倍役满':
                    YAKU_HAN_MAP[y['name']] = 26
            yaku_details = []
            total_han = 0
            for name in yaku_names:
                han = YAKU_HAN_MAP.get(name, 0)
                total_han += han
                yaku_details.append({"name": name, "han": han})
            has_yakuman = any(y['han'] >= 13 for y in yaku_details)
            result["yaku"] = yaku_details
            result["total_han"] = total_han
            result["is_yakuman"] = has_yakuman
            result["message"] = f"和牌！可构成 {len(yaku_details)} 种役"
        else:
            result["message"] = "未和牌（牌型不成立）"
            # 14张非和牌时进行牌效分析
            efficiency = analyze_hand_efficiency(hand)
            if efficiency:
                # 构建役种番数映射
                YAKU_HAN_MAP = {}
                for y in YAKU_DATA:
                    h = y['han']
                    if isinstance(h, int):
                        YAKU_HAN_MAP[y['name']] = h
                    elif h == '役满':
                        YAKU_HAN_MAP[y['name']] = 13
                    elif h == '双倍役满':
                        YAKU_HAN_MAP[y['name']] = 26
                YAKU_HAN_MAP['自风牌/场风牌'] = 1
                YAKU_HAN_MAP['役牌-白'] = 1
                YAKU_HAN_MAP['役牌-发'] = 1
                YAKU_HAN_MAP['役牌-中'] = 1
                
                result["efficiency"] = []
                for eff in efficiency:  # 返回所有结果
                    eff_info = {
                        "tile": eff['tile'],
                        "tile_name": TILE_NAMES.get(eff['tile'], eff['tile']),
                        "tile_png": tile_to_png(eff['tile']),
                        "count": eff['count'],
                        "waiting_tiles": eff['waiting_tiles'],
                        "waiting_tiles_names": [TILE_NAMES.get(t, t) for t in eff['waiting_tiles']],
                        "waiting_tiles_png": tiles_to_pngs(eff['waiting_tiles']),
                        "waiting_types": {},
                        "waiting_yaku": {},
                        "good_shape_rate": round(eff.get('good_shape_rate', 0), 1),
                        "shanten": eff.get('shanten', 0)
                    }
                    for w_tile, w_types in eff['waiting_types'].items():
                        eff_info["waiting_types"][w_tile] = {
                            "name": TILE_NAMES.get(w_tile, w_tile),
                            "types": w_types
                        }
                        # 检测胡这张牌时的役种
                        remaining = list(hand)
                        remaining.remove(eff['tile'])
                        test_hand = remaining + [w_tile]
                        yaku_names = analyze_yaku(test_hand)
                        yaku_details = []
                        total_han = 0
                        for name in yaku_names:
                            han = YAKU_HAN_MAP.get(name, 0)
                            total_han += han
                            yaku_details.append({"name": name, "han": han})
                        eff_info["waiting_yaku"][w_tile] = {
                            "yaku": yaku_details,
                            "total_han": total_han
                        }
                    result["efficiency"].append(eff_info)
                
                # 计算打出每张牌后听哪些牌
                best = efficiency[0]
                result["suggestion"] = {
                    "discard": best['tile'],
                    "discard_name": TILE_NAMES.get(best['tile'], best['tile']),
                    "discard_png": tile_to_png(best['tile']),
                    "waiting_count": best['count'],
                    "waiting_tiles": best['waiting_tiles']
                }
                # 判断是听牌还是进张
                is_tenpai_result = any(t in best.get('waiting_types', {}) and '进张' in best['waiting_types'].get(t, []) for t in best['waiting_tiles'])
                if is_tenpai_result:
                    result["message"] = f"未和牌，建议打 {TILE_NAMES.get(best['tile'], best['tile'])}，可进张 {best['count']} 张牌"
                else:
                    result["message"] = f"未和牌，建议打 {TILE_NAMES.get(best['tile'], best['tile'])}，可听 {best['count']} 张牌"
            else:
                result["message"] = "未和牌（牌型不成立），无法给出牌效建议"
    elif len(hand) == 13:
        # 听牌判定
        tenpai_tiles = get_tenpai_tiles(hand)
        result["tenpai_tiles"] = tenpai_tiles
        result["tenpai_tiles_names"] = [TILE_NAMES.get(t, t) for t in tenpai_tiles]
        result["tenpai_tiles_png"] = tiles_to_pngs(tenpai_tiles)
        if tenpai_tiles:
            result["is_tenpai"] = True
            result["message"] = f"听牌！可和 {len(tenpai_tiles)} 种牌"
            
            # 听牌形分析
            tenpai_types = analyze_tenpai_types(hand)
            result["tenpai_types"] = tenpai_types
            tenpai_types_display = {}
            
            # 构建役种番数映射
            YAKU_HAN_MAP = {}
            for y in YAKU_DATA:
                h = y['han']
                if isinstance(h, int):
                    YAKU_HAN_MAP[y['name']] = h
                elif h == '役满':
                    YAKU_HAN_MAP[y['name']] = 13
                elif h == '双倍役满':
                    YAKU_HAN_MAP[y['name']] = 26
            # 添加役牌通用映射
            YAKU_HAN_MAP['自风牌/场风牌'] = 1
            YAKU_HAN_MAP['役牌-白'] = 1
            YAKU_HAN_MAP['役牌-发'] = 1
            YAKU_HAN_MAP['役牌-中'] = 1
            
            for tile, types in tenpai_types.items():
                # 检测胡这张牌时的役种
                test_hand = list(hand) + [tile]
                yaku_names = analyze_yaku(test_hand)
                yaku_details = []
                total_han = 0
                for name in yaku_names:
                    han = YAKU_HAN_MAP.get(name, 0)
                    total_han += han
                    yaku_details.append({"name": name, "han": han})
                
                tenpai_types_display[tile] = {
                    "name": TILE_NAMES.get(tile, tile),
                    "types": types,
                    "png": tile_to_png(tile),
                    "yaku": yaku_details,
                    "total_han": total_han
                }
            result["tenpai_types_display"] = tenpai_types_display
            
            # 手牌效率分析
            efficiency = analyze_hand_efficiency(hand)
            if efficiency:
                result["efficiency"] = []
                for eff in efficiency[:5]:  # 只返回前5个最优选择
                    eff_info = {
                        "tile": eff['tile'],
                        "tile_name": TILE_NAMES.get(eff['tile'], eff['tile']),
                        "tile_png": tile_to_png(eff['tile']),
                        "count": eff['count'],
                        "waiting_tiles": eff['waiting_tiles'],
                        "waiting_tiles_names": [TILE_NAMES.get(t, t) for t in eff['waiting_tiles']],
                        "waiting_tiles_png": tiles_to_pngs(eff['waiting_tiles']),
                        "waiting_types": {}
                    }
                    for w_tile, w_types in eff['waiting_types'].items():
                        eff_info["waiting_types"][w_tile] = {
                            "name": TILE_NAMES.get(w_tile, w_tile),
                            "types": w_types
                        }
                    result["efficiency"].append(eff_info)
        else:
            result["is_tenpai"] = False
            result["message"] = "未听牌"
    else:
        result["message"] = f"当前 {len(hand)} 张牌，还需 {14-len(hand)} 张"
    
    return jsonify(result)

# ========== API: 符数计算 ==========
@app.route('/api/calculate-fu', methods=['POST'])
def calculate_fu_api():
    data = request.get_json()
    hand = data.get('hand', [])
    is_tsumo = data.get('is_tsumo', True)
    is_tsumo_agari = data.get('is_tsumo_agari', True)
    is_dealer = data.get('is_dealer', False)
    
    if len(hand) != 14 or not check_agari(hand):
        return jsonify({"error": "手牌不合法或未和牌"}), 400
    
    # 宝牌/里宝牌
    dora = data.get('dora', 0)
    ura_dora = data.get('ura_dora', 0)
    
    # 自动算番
    yaku_names = analyze_yaku(hand, is_tsumo=is_tsumo_agari, is_riichi=False)
    
    # 创建役种名称到番数的映射
    YAKU_HAN_MAP = {}
    YAKU_HAN_LIST = []
    for y in YAKU_DATA:
        h = y['han']
        if isinstance(h, int):
            YAKU_HAN_MAP[y['name']] = h
        elif h == '役满':
            YAKU_HAN_MAP[y['name']] = 13
        elif h == '双倍役满':
            YAKU_HAN_MAP[y['name']] = 26
    
    # 构建带番数的役种列表
    yaku_details = []
    auto_han = 0
    for name in yaku_names:
        han = YAKU_HAN_MAP.get(name, 0)
        auto_han += han
        yaku_details.append({"name": name, "han": han})
    
    if auto_han == 0:
        auto_han = 1  # 最低1番
    
    # 总番数 = 役种番 + 宝牌 + 里宝牌
    total_han = auto_han + dora + ura_dora
    
    fu = calculate_fu(hand, is_tsumo, is_tsumo_agari)
    score = calculate_score(fu, total_han, is_dealer, is_tsumo_agari)
    
    # 判定动画等级 & 是否有役满
    has_yakuman = any(y['han'] >= 13 for y in yaku_details)
    anim_level = 'normal'
    if has_yakuman:
        anim_level = 'yakuman'
    elif total_han >= 8:
        anim_level = 'high'
    elif total_han >= 5:
        anim_level = 'medium'
    
    return jsonify({
        "fu": fu,
        "han": total_han,
        "auto_han": auto_han,
        "dora": dora,
        "ura_dora": ura_dora,
        "score": score,
        "tiles_png": tiles_to_pngs(hand),
        "yaku": yaku_details,
        "total_han": total_han,
        "anim_level": anim_level,
        "is_yakuman": has_yakuman,
    })

# ========== API: 异步好型率计算 ==========
@app.route('/api/good-shape', methods=['POST'])
def good_shape_api():
    """异步计算好型率（方案四）
    接收手牌和切牌列表，返回每张牌的好型率
    使用共享缓存加速计算（方案一）
    """
    data = request.get_json()
    hand = data.get('hand', [])
    tiles = data.get('tiles', [])
    
    if not hand or len(hand) != 14:
        return jsonify({"error": "手牌数量不合法"}), 400
    
    if not tiles:
        return jsonify({"error": "未指定切牌列表"}), 400
    
    # 使用共享缓存（方案一）
    shanten_cache = {}
    results = calculate_good_shape_batch(hand, tiles, shanten_cache)
    
    # 四舍五入到1位小数
    results = {tile: round(rate, 1) for tile, rate in results.items()}
    
    return jsonify({"rates": results})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

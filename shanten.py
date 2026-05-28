"""
向听数计算引擎 - 移植自 Xpilot (shanten.js + evaluation.js)
使用34张牌数组表示法进行高效递归向听计算
"""

# 牌索引: m1=0, m2=1, ..., m9=8, p1=9, ..., p9=17, s1=18, ..., s9=26
# east=27, south=28, west=29, north=30, white=31, green=32, red=33

TILE_COUNT = 34
NUMERAL_COUNT = 27
HAND_MAX_TILES = 14
MAX_SHANTEN = 8
AGARI_STATE = -1

TERMINAL_INDICES = [0, 8, 9, 17, 18, 26]
HONOR_INDICES = [27, 28, 29, 30, 31, 32, 33]
TERMINAL_HONOR_INDICES = TERMINAL_INDICES + HONOR_INDICES

# 牌名 -> 索引
TILE_TO_INDEX = {}
for i in range(9):
    TILE_TO_INDEX[f'm{i+1}'] = i
    TILE_TO_INDEX[f'p{i+1}'] = 9 + i
    TILE_TO_INDEX[f's{i+1}'] = 18 + i
TILE_TO_INDEX['east'] = 27
TILE_TO_INDEX['south'] = 28
TILE_TO_INDEX['west'] = 29
TILE_TO_INDEX['north'] = 30
TILE_TO_INDEX['white'] = 31
TILE_TO_INDEX['green'] = 32
TILE_TO_INDEX['red'] = 33

# 索引 -> 牌名
INDEX_TO_TILE = {v: k for k, v in TILE_TO_INDEX.items()}


def tiles_to_34(tiles):
    """将牌名列表转为34张牌计数数组"""
    arr = [0] * TILE_COUNT
    for t in tiles:
        idx = TILE_TO_INDEX.get(t)
        if idx is not None:
            arr[idx] += 1
    return arr


def hand_to_34(hand):
    """将手牌列表转为34张牌计数数组"""
    return tiles_to_34(hand)


class Shanten:
    """向听数计算器 - 完整移植自 shanten.js"""

    def __init__(self):
        self.tiles = []
        self.number_melds = 0
        self.number_tatsu = 0
        self.number_pairs = 0
        self.number_jidahai = 0
        self.number_characters = 0
        self.number_isolated_tiles = 0
        self.min_shanten = MAX_SHANTEN
        self._work_tiles = [0] * TILE_COUNT

    def calculate(self, tiles34, use_chiitoitsu=True, use_kokushi=True):
        """统一入口: 计算向听数
        tiles34: 长度34的计数数组
        返回: -1=和牌, 0=听牌, 1+=向听数
        """
        results = []

        if use_chiitoitsu:
            s = self._calc_chiitoitsu(tiles34)
            results.append(s)
            if s == AGARI_STATE:
                return AGARI_STATE

        if use_kokushi:
            s = self._calc_kokushi(tiles34)
            results.append(s)
            if s == AGARI_STATE:
                return AGARI_STATE

        results.append(self._calc_regular(tiles34))
        return min(results)

    def _calc_chiitoitsu(self, tiles34):
        """七对子向听数"""
        cnt2 = cnt3 = cnt4 = 0
        for i in range(TILE_COUNT):
            c = tiles34[i]
            if c == 2:
                cnt2 += 1
            elif c == 3:
                cnt3 += 1
            elif c == 4:
                cnt4 += 1
        if cnt2 == 4 and cnt3 == 2:
            return 1
        if cnt2 == 5 and cnt4 == 1:
            return 1
        if cnt2 == 7:
            return AGARI_STATE
        pairs = cnt2 + cnt3 + cnt4
        return 6 - pairs

    def _calc_kokushi(self, tiles34):
        """国士无双向听数"""
        terminals = 0
        has_pair = False
        for i in TERMINAL_HONOR_INDICES:
            c = tiles34[i]
            if c > 0:
                terminals += 1
                if not has_pair and c >= 2:
                    has_pair = True
        return 13 - terminals - (1 if has_pair else 0)

    def _calc_regular(self, tiles34):
        """一般形向听数"""
        for i in range(TILE_COUNT):
            self._work_tiles[i] = tiles34[i]
        self.tiles = self._work_tiles
        self.number_melds = 0
        self.number_tatsu = 0
        self.number_pairs = 0
        self.number_jidahai = 0
        self.number_characters = 0
        self.number_isolated_tiles = 0
        self.min_shanten = MAX_SHANTEN

        count_of_tiles = sum(tiles34)
        if count_of_tiles > HAND_MAX_TILES:
            return MAX_SHANTEN

        self._remove_character_tiles(count_of_tiles)
        init_mentsu = (14 - count_of_tiles) // 3
        self._scan(init_mentsu)

        return self.min_shanten

    def _scan(self, init_mentsu):
        self.number_characters = 0
        for i in range(NUMERAL_COUNT):
            if self.tiles[i] == 4:
                self.number_characters |= (1 << i)
        self.number_melds += init_mentsu
        self._run(0)

    def _run(self, depth):
        if self.min_shanten == AGARI_STATE:
            return
        while depth < NUMERAL_COUNT and self.tiles[depth] == 0:
            depth += 1
        if depth >= NUMERAL_COUNT:
            self._update_result()
            return

        tiles = self.tiles
        i = depth % 9
        tc = tiles[depth]
        t1 = tiles[depth + 1] if depth + 1 < TILE_COUNT else 0
        t2 = tiles[depth + 2] if depth + 2 < TILE_COUNT else 0
        t3 = tiles[depth + 3] if depth + 3 < TILE_COUNT else 0

        # 4张
        if tc == 4:
            self._inc_set(depth)
            if i < 7 and t2:
                if t1:
                    self._inc_syuntsu(depth)
                    self._run(depth + 1)
                    self._dec_syuntsu(depth)
                self._inc_tatsu_second(depth)
                self._run(depth + 1)
                self._dec_tatsu_second(depth)
            if i < 8 and t1:
                self._inc_tatsu_first(depth)
                self._run(depth + 1)
                self._dec_tatsu_first(depth)
            self._inc_isolated(depth)
            self._run(depth + 1)
            self._dec_isolated(depth)
            self._dec_set(depth)

            self._inc_pair(depth)
            if i < 7 and t2:
                if t1:
                    self._inc_syuntsu(depth)
                    self._run(depth)
                    self._dec_syuntsu(depth)
                self._inc_tatsu_second(depth)
                self._run(depth + 1)
                self._dec_tatsu_second(depth)
            if i < 8 and t1:
                self._inc_tatsu_first(depth)
                self._run(depth + 1)
                self._dec_tatsu_first(depth)
            self._dec_pair(depth)

        # 3张
        if tc == 3:
            self._inc_set(depth)
            self._run(depth + 1)
            self._dec_set(depth)

            self._inc_pair(depth)
            if i < 7 and t1 and t2:
                self._inc_syuntsu(depth)
                self._run(depth + 1)
                self._dec_syuntsu(depth)
            else:
                if i < 7 and t2:
                    self._inc_tatsu_second(depth)
                    self._run(depth + 1)
                    self._dec_tatsu_second(depth)
                if i < 8 and t1:
                    self._inc_tatsu_first(depth)
                    self._run(depth + 1)
                    self._dec_tatsu_first(depth)
            self._dec_pair(depth)

            if i < 7 and tiles[depth + 2] >= 2 and tiles[depth + 1] >= 2:
                self._inc_syuntsu(depth)
                self._inc_syuntsu(depth)
                self._run(depth)
                self._dec_syuntsu(depth)
                self._dec_syuntsu(depth)

        # 2张
        if tc == 2:
            self._inc_pair(depth)
            self._run(depth + 1)
            self._dec_pair(depth)
            if i < 7 and t2 and t1:
                self._inc_syuntsu(depth)
                self._run(depth)
                self._dec_syuntsu(depth)

        # 1张
        if tc == 1:
            if i < 6 and t1 == 1 and t2 and t3 != 4:
                self._inc_syuntsu(depth)
                self._run(depth + 2)
                self._dec_syuntsu(depth)
            else:
                self._inc_isolated(depth)
                self._run(depth + 1)
                self._dec_isolated(depth)

                if i < 7 and t2:
                    if t1:
                        self._inc_syuntsu(depth)
                        self._run(depth + 1)
                        self._dec_syuntsu(depth)
                    self._inc_tatsu_second(depth)
                    self._run(depth + 1)
                    self._dec_tatsu_second(depth)
                if i < 8 and t1:
                    self._inc_tatsu_first(depth)
                    self._run(depth + 1)
                    self._dec_tatsu_first(depth)

    def _update_result(self):
        ret = 8 - self.number_melds * 2 - self.number_tatsu - self.number_pairs
        n_mentsu_kouho = self.number_melds + self.number_tatsu

        if self.number_pairs:
            n_mentsu_kouho += self.number_pairs - 1
        elif self.number_characters and self.number_isolated_tiles:
            if (self.number_characters | self.number_isolated_tiles) == self.number_characters:
                ret += 1

        if n_mentsu_kouho > 4:
            ret += n_mentsu_kouho - 4

        if ret != AGARI_STATE and ret < self.number_jidahai:
            ret = self.number_jidahai

        if ret < self.min_shanten:
            self.min_shanten = ret

    # --- 辅助函数 ---
    def _inc_set(self, k):
        self.tiles[k] -= 3
        self.number_melds += 1

    def _dec_set(self, k):
        self.tiles[k] += 3
        self.number_melds -= 1

    def _inc_pair(self, k):
        self.tiles[k] -= 2
        self.number_pairs += 1

    def _dec_pair(self, k):
        self.tiles[k] += 2
        self.number_pairs -= 1

    def _inc_syuntsu(self, k):
        self.tiles[k] -= 1
        self.tiles[k + 1] -= 1
        self.tiles[k + 2] -= 1
        self.number_melds += 1

    def _dec_syuntsu(self, k):
        self.tiles[k] += 1
        self.tiles[k + 1] += 1
        self.tiles[k + 2] += 1
        self.number_melds -= 1

    def _inc_tatsu_first(self, k):
        self.tiles[k] -= 1
        self.tiles[k + 1] -= 1
        self.number_tatsu += 1

    def _dec_tatsu_first(self, k):
        self.tiles[k] += 1
        self.tiles[k + 1] += 1
        self.number_tatsu -= 1

    def _inc_tatsu_second(self, k):
        self.tiles[k] -= 1
        self.tiles[k + 2] -= 1
        self.number_tatsu += 1

    def _dec_tatsu_second(self, k):
        self.tiles[k] += 1
        self.tiles[k + 2] += 1
        self.number_tatsu -= 1

    def _inc_isolated(self, k):
        self.tiles[k] -= 1
        self.number_isolated_tiles |= (1 << k)

    def _dec_isolated(self, k):
        self.tiles[k] += 1
        self.number_isolated_tiles &= ~(1 << k)

    def _remove_character_tiles(self, nc):
        number = 0
        isolated = 0
        for i in range(27, 34):
            if self.tiles[i] == 4:
                self.number_melds += 1
                self.number_jidahai += 1
                number |= 1 << (i - 27)
                isolated |= 1 << (i - 27)
            if self.tiles[i] == 3:
                self.number_melds += 1
            if self.tiles[i] == 2:
                self.number_pairs += 1
            if self.tiles[i] == 1:
                isolated |= 1 << (i - 27)

        if self.number_jidahai and nc % 3 == 2:
            self.number_jidahai -= 1

        if isolated:
            self.number_isolated_tiles |= (1 << 27)
            if (number | isolated) == number:
                self.number_characters |= (1 << 27)


# 全局单例
_shanten_solver = Shanten()

def calc_shanten(tiles34):
    """计算向听数（带缓存）"""
    return _shanten_solver.calculate(tiles34)


def calc_shanten_cached(tiles34, cache):
    """带缓存的向听数计算"""
    key = tuple(tiles34)
    if key in cache:
        return cache[key]
    val = calc_shanten(tiles34)
    cache[key] = val
    return val


def remaining_tiles(hand34):
    """计算剩余牌数数组（每种牌最多4张减去手牌）"""
    rem = [0] * TILE_COUNT
    for i in range(TILE_COUNT):
        rem[i] = max(0, 4 - hand34[i])
    return rem


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
MAX_GOOD_SHAPE_DEPTH = 3


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
    """批量计算多张牌的好型率
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

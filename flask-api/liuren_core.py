#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大六壬在线排盘 · 核心计算库

完整实现：地盘/天盘/四课/三传/九宗门/贵人起例/天官排列/课体判断/断课解释
"""

import datetime
import ephem
import math

# ========== 基础数据 ==========

TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# 天干阴阳：甲丙戊庚壬=阳，乙丁己辛癸=阴
TIANGAN_YINYANG = {g: '阳' if i % 2 == 0 else '阴' for i, g in enumerate(TIANGAN)}
# 地支阴阳：子寅辰午申戌=阳，丑卯巳未酉亥=阴
DIZHI_YINYANG = {z: '阳' if i % 2 == 0 else '阴' for i, z in enumerate(DIZHI)}

# 五行
WUXING = {
    '甲乙': '木', '寅卯': '木',
    '丙丁': '火', '巳午': '火',
    '戊己': '土', '辰戌丑未': '土',
    '庚辛': '金', '申酉': '金',
    '壬癸': '水', '亥子': '水',
}

# 孟仲季
MENG_ZHONG_JI = {'寅': '孟', '巳': '孟', '申': '孟', '亥': '孟',
                 '子': '仲', '卯': '仲', '午': '仲', '酉': '仲',
                 '丑': '季', '辰': '季', '未': '季', '戌': '季'}

# 六冲
LIUCHONG = {'子': '午', '午': '子', '丑': '未', '未': '丑',
            '寅': '申', '申': '寅', '卯': '酉', '酉': '卯',
            '辰': '戌', '戌': '辰', '巳': '亥', '亥': '巳'}

# 六合
LIUHE = {'子': '丑', '丑': '子', '寅': '亥', '亥': '寅',
         '卯': '戌', '戌': '卯', '巳': '申', '申': '巳',
         '午': '未', '未': '午', '辰': '酉', '酉': '辰'}

# 三合
SANHE = {
    '申': '子', '子': '辰', '辰': '申',  # 申子辰水局
    '寅': '午', '午': '戌', '戌': '寅',  # 寅午戌火局
    '巳': '酉', '酉': '丑', '丑': '巳',  # 巳酉丑金局
    '亥': '卯', '卯': '未', '未': '亥',  # 亥卯未木局
}

# 三刑
SANXING = {
    '寅': '巳', '巳': '申', '申': '寅',  # 无恩之刑
    '丑': '戌', '戌': '未', '未': '丑',  # 恃势之刑
    '子': '卯', '卯': '子',              # 无礼之刑
    '辰': '辰', '午': '午', '酉': '酉', '亥': '亥',  # 自刑
}

# 地支序号
DIZHI_INDEX = {z: i for i, z in enumerate(DIZHI)}

# 天干序号
TIANGAN_INDEX = {g: i for i, g in enumerate(TIANGAN)}

# 干支基准：2000年1月1日 = 戊午日 (序号54)
GANZHI_BASE_2000 = 54

# 天干寄宫
JIGONG = {
    '甲': '寅', '乙': '辰',
    '丙': '巳', '丁': '未',
    '戊': '巳', '己': '未',
    '庚': '申', '辛': '戌',
    '壬': '亥', '癸': '丑',
}

# 干支序号（0-59）
def ganzhi_index(gan, zhi):
    """计算干支序号（六十甲子）"""
    gi = TIANGAN_INDEX[gan]
    zi = DIZHI_INDEX[zhi]
    for i in range(60):
        if i % 10 == gi and i % 12 == zi:
            return i
    return 0

# 月将（正月亥→十二月子）
YUEJIANG = ['亥', '戌', '酉', '申', '未', '午', '巳', '辰', '卯', '寅', '丑', '子']

# 月将名称
YUEJIANG_NAME = {
    '亥': '登明', '戌': '河魁', '酉': '从魁', '申': '传送',
    '未': '小吉', '午': '胜光', '巳': '太乙', '辰': '天罡',
    '卯': '太冲', '寅': '功曹', '丑': '大吉', '子': '神后',
}

# 十二天官顺序（天乙居中，前五后六）
TIANGUAN_SEQUENCE = [
    ('贵人', '己丑', '土', '吉', '掌吉凶之枢'),
    ('螣蛇', '丁巳', '火', '凶', '惊疑火光怪异'),
    ('朱雀', '丙午', '火', '凶', '文书口舌司讼'),
    ('六合', '乙卯', '木', '吉', '和合婚姻成就'),
    ('勾陈', '戊辰', '土', '凶', '词讼争战迟滞'),
    ('青龙', '甲寅', '木', '大吉', '财帛喜庆亨通'),
    ('天后', '壬子', '水', '中', '阴私蔽匿护卫'),
    ('太阴', '辛酉', '金', '凶', '暗昧奸邪淫乱'),
    ('玄武', '癸亥', '水', '凶', '盗贼走失遗亡'),
    ('太常', '己未', '土', '吉', '酒食衣冠印绶'),
    ('白虎', '庚申', '金', '大凶', '道路血光官灾'),
    ('天空', '戊戌', '土', '凶', '诈伪不实奏书'),
]

TIANGUAN_NAMES = [t[0] for t in TIANGUAN_SEQUENCE]

# 天官在地盘上的排列顺序（顺行）
TIANGUAN_ORDER_SHUN = ['贵人', '螣蛇', '朱雀', '六合', '勾陈', '青龙',
                        '天后', '太阴', '玄武', '太常', '白虎', '天空']

TIANGUAN_ORDER_NI = ['贵人', '天空', '白虎', '太常', '玄武', '太阴',
                      '天后', '青龙', '勾陈', '六合', '朱雀', '螣蛇']

# 天官吉凶
TIANGUAN_JIXIONG = {t[0]: (t[2], t[3], t[4]) for t in TIANGUAN_SEQUENCE}

# 昼夜贵人歌诀：甲戊庚牛羊，乙己鼠猴乡，丙丁猪鸡位，壬癸蛇兔藏，六辛逢马虎
GUI_REN_ZHOU = {
    '甲': '丑', '戊': '丑', '庚': '丑',
    '乙': '子', '己': '子',
    '丙': '亥', '丁': '亥',
    '壬': '巳', '癸': '巳',
    '辛': '午',
    '阳贵': {'甲': '丑', '戊': '丑', '庚': '丑',
              '乙': '子', '己': '子', '丙': '亥', '丁': '亥',
              '壬': '巳', '癸': '巳', '辛': '午'},
}
GUI_REN_YE = {
    '甲': '未', '戊': '未', '庚': '未',
    '乙': '申', '己': '申',
    '丙': '酉', '丁': '酉',
    '壬': '卯', '癸': '卯',
    '辛': '寅',
    '阴贵': {'甲': '未', '戊': '未', '庚': '未',
              '乙': '申', '己': '申', '丙': '酉', '丁': '酉',
              '壬': '卯', '癸': '卯', '辛': '寅'},
}


# ========== 五行生克 ==========

def wuxing_of(gan_or_zhi):
    """判断五行"""
    if gan_or_zhi in TIANGAN:
        for key, val in WUXING.items():
            if gan_or_zhi in key:
                return val
    else:
        for key, val in WUXING.items():
            if gan_or_zhi in key:
                return val
    return None

def wuxing_ke(x, y):
    """x五行克y吗？"""
    wx = WUXING_KE.get(wuxing_of(x), [])
    return wuxing_of(y) in wx

WUXING_KE = {'木': ['土'], '火': ['金'], '土': ['水'], '金': ['木'], '水': ['火']}
WUXING_SHENG = {'木': ['火'], '火': ['土'], '土': ['金'], '金': ['水'], '水': ['木']}
WUXING_SHENG_REV = {'木': ['水'], '火': ['木'], '土': ['火'], '金': ['土'], '水': ['金']}


# ========== 长生十二宫 ==========

# 十干长生位（阳干顺行，阴干逆行）
CHANGSHENG_START = {
    '甲': '亥', '丙': '寅', '戊': '寅', '庚': '巳', '壬': '申',
    '乙': '午', '丁': '酉', '己': '酉', '辛': '子', '癸': '卯',
}

CHANGSHENG_LIST = ['长生', '沐浴', '冠带', '临官', '帝旺', '衰', '病', '死', '墓', '绝', '胎', '养']

def get_changsheng(gan, zhi):
    """获取某天干下某地支的长生状态"""
    start = CHANGSHENG_START.get(gan)
    if not start:
        return ''
    
    start_idx = DIZHI_INDEX[start]
    zhi_idx = DIZHI_INDEX[zhi]
    
    # 阳干顺行，阴干逆行
    if TIANGAN_YINYANG[gan] == '阳':
        offset = (zhi_idx - start_idx) % 12
    else:
        offset = (start_idx - zhi_idx) % 12
    
    if 0 <= offset < 12:
        return CHANGSHENG_LIST[offset]
    return ''


def get_changsheng_table(ri_gan, sanchuan):
    """获取三传每个字的长生状态
    Returns: [(地支, 长生状态), ...]
    """
    result = []
    for zhi, label in sanchuan:
        if zhi:
            cs = get_changsheng(ri_gan, zhi)
            result.append((zhi, cs))
        else:
            result.append(('', ''))
    return result


# ========== 月将计算 ==========

def get_solar_terms(year):
    """获取全年24节气日期"""
    terms = {}
    for i in range(1, 25):
        d = ephem.next_vernal_equinox(str(year))
        # Use sun longitude to get solar terms
        t = ephem.Date(f"{year}/1/1") + i * 15.2  # approximate
        terms[i] = t
    return terms

def get_yuejiang(year, month, day):
    """根据阳历日期计算月将

    月将 = 太阳所在宫，每月中气过宫
    正月亥(立春→雨水)、二月戌(惊蛰→春分)...
    简化：雨水→惊蛰用亥，春分→清明用戌...
    """
    # 2026年节气日期（近似）
    jieqi_2026 = {
        1: (2, 4),   # 立春
        2: (2, 19),  # 雨水
        3: (3, 5),   # 惊蛰
        4: (3, 20),  # 春分
        5: (4, 4),   # 清明
        6: (4, 20),  # 谷雨
        7: (5, 5),   # 立夏
        8: (5, 21),  # 小满
        9: (6, 5),   # 芒种
        10: (6, 21), # 夏至
        11: (7, 7),  # 小暑
        12: (7, 22), # 大暑
        13: (8, 7),  # 立秋
        14: (8, 23), # 处暑
        15: (9, 7),  # 白露
        16: (9, 23), # 秋分
        17: (10, 8), # 寒露
        18: (10, 23),# 霜降
        19: (11, 7), # 立冬
        20: (11, 22),# 小雪
        21: (12, 7), # 大雪
        22: (12, 21),# 冬至
        23: (1, 5),  # 小寒（次年）
        24: (1, 20), # 大寒（次年）
    }

    md = month * 100 + day
    # 雨水(220)→亥将，春分(320)→戌将，...
    # 中气→月将映射（中气为月将换宫日）
    # 雨水(2/19)→亥, 春分(3/20)→戌, 谷雨(4/20)→酉,
    # 小满(5/21)→申, 夏至(6/21)→未, 大暑(7/23)→午,
    # 处暑(8/23)→巳, 秋分(9/23)→辰, 霜降(10/23)→卯,
    # 小雪(11/22)→寅, 冬至(12/22)→丑, 大寒(1/20)→子
    yuejiang_boundaries = [
        (120, '子'),  # 大寒(1月20日) → 子将
        (219, '亥'),  # 雨水(2月19日) → 亥将
        (320, '戌'),  # 春分(3月20日) → 戌将
        (420, '酉'),  # 谷雨(4月20日) → 酉将
        (521, '申'),  # 小满(5月21日) → 申将
        (621, '未'),  # 夏至(6月21日) → 未将
        (723, '午'),  # 大暑(7月23日) → 午将
        (823, '巳'),  # 处暑(8月23日) → 巳将
        (923, '辰'),  # 秋分(9月23日) → 辰将
        (1023, '卯'), # 霜降(10月23日) → 卯将
        (1122, '寅'), # 小雪(11月22日) → 寅将
        (1222, '丑'), # 冬至(12月22日) → 丑将
    ]

    # For dates before the first boundary (before 大寒 Jan 20)
    # 丑月=冬至(12/22)~大寒(1/20), so Jan 1-19 uses丑将
    if month == 1 and day < 20:
        return '丑'
    # For December after冬至
    if month == 12 and day >= 22:
        return '丑'
    
    yj = '子'  # before 雨水 falls back to子(大寒→雨水=子将)
    for bound_md, yue_jiang_char_bound in yuejiang_boundaries:
        if md < bound_md:
            return yj
        yj = yue_jiang_char_bound
    return yj  # 最后(大雪→冬至前=丑)


# ========== 时辰 ==========

SHICHEN_MAP = {
    23: '子', 0: '子', 1: '丑', 2: '丑', 3: '寅', 4: '寅',
    5: '卯', 6: '卯', 7: '辰', 8: '辰', 9: '巳', 10: '巳',
    11: '午', 12: '午', 13: '未', 14: '未', 15: '申', 16: '申',
    17: '酉', 18: '酉', 19: '戌', 20: '戌', 21: '亥', 22: '亥',
}

SHICHEN_SEQUENCE = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

def hour_to_shichen(hour):
    """小时转时辰"""
    return SHICHEN_MAP.get(hour, '子')

def is_daytime(hour):
    """判断昼夜：卯时(5-7)到酉时(17-19)为昼"""
    return 5 <= hour < 19


# ========== 地盘/天盘 ==========

def create_diban():
    """创建地盘（固定）"""
    return {
        '巳': ('辰', '午', '未', '申'),  # 顺时针一圈
    }

def get_diban_positions():
    """返回地盘十二宫位置（方格式）"""
    return {
        '巳': (0, 0), '午': (0, 1), '未': (0, 2), '申': (0, 3),
        '辰': (1, 0), '酉': (1, 3),
        '卯': (2, 0), '戌': (2, 3),
        '寅': (3, 0), '丑': (3, 1), '子': (3, 2), '亥': (3, 3),
    }

def get_tianpan(yuejiang, shichen):
    """计算天盘：月将加占时
    
    月将（天盘）所加的地盘位置 = 占时的地盘位置
    然后顺时针排列
    """
    # 月将在地盘上的位置
    yj_idx = DIZHI_INDEX[yuejiang]
    sc_idx = DIZHI_INDEX[shichen]
    
    # 偏移量：月将应该加到占时上
    offset = (yj_idx - sc_idx) % 12
    
    tianpan = {}
    for i, zhi in enumerate(DIZHI):
        # 天盘支 = 地盘支 + 偏移
        tp_zhi = DIZHI[(i + offset) % 12]
        tianpan[zhi] = tp_zhi
    
    return tianpan


# ========== 四课 ==========

def get_sike(ri_gan, ri_zhi, tianpan):
    """计算四课
    
    Returns:
        四课列表 [(课名, 简名, 底层支, 天盘神), ...]
    """
    gan_gong = JIGONG[ri_gan]
    
    sike = []
    
    # 第一课：日干寄宫上的天盘神（日阳）
    di_yi_ke_shen = tianpan[gan_gong]
    sike.append(('第一课（日阳）', f'{ri_gan}→{gan_gong}', gan_gong, di_yi_ke_shen))
    
    # 第二课：第一课上神的天盘神（日阴）
    di_er_ke_shen = tianpan[di_yi_ke_shen]
    sike.append(('第二课（日阴）', f'{di_yi_ke_shen}上', di_yi_ke_shen, di_er_ke_shen))
    
    # 第三课：日支上的天盘神（辰阳）
    di_san_ke_shen = tianpan[ri_zhi]
    sike.append(('第三课（辰阳）', f'{ri_zhi}上', ri_zhi, di_san_ke_shen))
    
    # 第四课：第三课上神的天盘神（辰阴）
    di_si_ke_shen = tianpan[di_san_ke_shen]
    sike.append(('第四课（辰阴）', f'{di_san_ke_shen}上', di_san_ke_shen, di_si_ke_shen))
    
    return sike


# ========== 九宗门 ==========




# ========== 贵人天官 ==========

def get_guiren(ri_gan, shichen_hour, shichen=None):
    """计算贵人及顺逆
    
    Returns:
        (贵人支, 顺逆)
    """
    if shichen is None:
        shichen = hour_to_shichen(shichen_hour) if isinstance(shichen_hour, int) else shichen_hour
    
    day = is_daytime(shichen_hour) if isinstance(shichen_hour, int) else (5 <= shichen_hour < 19)
    
    if day:
        guiren_gong = GUI_REN_ZHOU['阳贵'].get(ri_gan, '丑')
    else:
        guiren_gong = GUI_REN_YE['阴贵'].get(ri_gan, '未')
    
    # 贵人参照着地支
    return guiren_gong

def get_guiren_order(guiren_gong, tianpan):
    """判断贵人的排列方向（顺行还是逆行）
    
    贵人加地盘亥子丑寅卯辰 → 顺行
    贵人加地盘巳午未申酉戌 → 逆行
    """
    # 贵人所在的天盘位置对应的地盘
    # 即：贵人地支在天盘上，看它所加的地盘是什么
    # tianpan[地盘] = 天盘，反过来查
    for dp, tp in tianpan.items():
        if tp == guiren_gong:
            guiren_diban = dp
            break
    else:
        guiren_diban = guiren_gong  # 默认
    
    # 逆用地支判断
    if DIZHI_INDEX[guiren_diban] <= DIZHI_INDEX['辰']:
        return '顺行'
    else:
        return '逆行'


def get_tianguan_positions(tianpan, guiren_gong, order):
    """给天盘配天官（贵神）"""
    
    # 贵人所在的第一个位置
    for dp, tp in tianpan.items():
        if tp == guiren_gong:
            guiren_pos = dp  # 贵人所在的地盘位置
            break
    else:
        guiren_pos = guiren_gong
    
    # 从贵人开始，按顺/逆行布天官
    guiren_idx = DIZHI_INDEX[guiren_pos]
    
    tianguan_map = {}
    
    if order == '顺行':
        # 贵人在第0位，顺行：贵人→蛇→朱→六→勾→龙→后→阴→玄→常→白→空
        order_list = TIANGUAN_ORDER_SHUN
    else:
        order_list = TIANGUAN_ORDER_NI
    
    for i, tg_name in enumerate(order_list):
        # 在地盘上按顺/逆时针排列
        if order == '顺行':
            pos_idx = (guiren_idx + i) % 12
        else:
            pos_idx = (guiren_idx - i) % 12
        pos_zhi = DIZHI[pos_idx]
        tianguan_map[pos_zhi] = tg_name
    
    return tianguan_map


def get_ke_zei(sike, ri_gan, ri_zhi, tianpan, yuejiang, shichen):
    """九宗门完整判断
    四课元组: (课名, 简名, 底层支, 天盘神)
    
    Returns:
        dict with keys: keti(课名), fayong(发用), reason(原因),
        sanchuan_mode(三传模式: standard/pingxing/bieze/maoxing/fuyin/fanyin)
    """
    
    # 辅助函数：提取克贼列表
    def check_kz(sike):
        zei = []
        ke = []
        for i, (name, label, bottom_zhi, top_shen) in enumerate(sike):
            if wuxing_ke(bottom_zhi, top_shen):
                zei.append((i, bottom_zhi, top_shen))
            if wuxing_ke(top_shen, bottom_zhi):
                ke.append((i, bottom_zhi, top_shen))
        return zei, ke
    
    def biyong_selection(candidates, ri_gan):
        """比用选法"""
        yy = TIANGAN_YINYANG[ri_gan]
        for i, b, t in candidates:
            if DIZHI_YINYANG.get(t, '') == yy:
                return t
        return candidates[0][2] if candidates else ''
    
    # 检查是否伏吟（月将=占时）
    if yuejiang == shichen:
        zei, ke = check_kz(sike)
        if zei:
            # 伏吟有克取克
            if len(zei) == 1:
                return {'keti': '伏吟', 'fayong': zei[0][2], 'reason': f'伏吟有克取{zei[0][2]}',
                        'sanchuan_mode': 'fuyin', 'details': zei}
            else:
                t = biyong_selection(zei, ri_gan)
                return {'keti': '伏吟', 'fayong': t, 'reason': f'伏吟比用取{t}',
                        'sanchuan_mode': 'fuyin', 'details': zei}
        else:
            # 无克：阳日干上发传，阴日支上发传
            if TIANGAN_YINYANG[ri_gan] == '阳':
                fa = sike[0][3]  # 干上神
                return {'keti': '伏吟·任信', 'fayong': fa, 'reason': '伏吟无克阳日干上发传',
                        'sanchuan_mode': 'fuyin', 'details': []}
            else:
                fa = sike[2][3]  # 支上神
                return {'keti': '伏吟·自信', 'fayong': fa, 'reason': '伏吟无克阴日支上发传',
                        'sanchuan_mode': 'fuyin', 'details': []}
    
    # 检查是否返吟（月将=占时对冲）
    if yuejiang and shichen and LIUCHONG.get(yuejiang) == shichen:
        zei, ke = check_kz(sike)
        if zei or ke:
            # 有克贼
            if zei:
                if len(zei) == 1:
                    return {'keti': '返吟·重审', 'fayong': zei[0][2], 'reason': f'返吟有下贼上{zei[0][2]}',
                            'sanchuan_mode': 'fanyin', 'details': zei}
                else:
                    t = biyong_selection(zei, ri_gan)
                    return {'keti': '返吟', 'fayong': t, 'reason': f'返吟比用取{t}',
                            'sanchuan_mode': 'fanyin', 'details': zei}
            if len(ke) == 1:
                return {'keti': '返吟·元首', 'fayong': ke[0][2], 'reason': f'返吟上克下{ke[0][2]}',
                        'sanchuan_mode': 'fanyin', 'details': ke}
            else:
                t = biyong_selection(ke, ri_gan)
                return {'keti': '返吟', 'fayong': t, 'reason': f'返吟比用取{t}',
                        'sanchuan_mode': 'fanyin', 'details': ke}
        else:
            # 无克：井栏射（用驿马）
            # 驿马：寅午戌马居申，申子辰马居寅，巳酉丑马在亥，亥卯未马在巳
            YIMA = {'寅':'申','午':'申','戌':'申','申':'寅','子':'寅','辰':'寅',
                    '巳':'亥','酉':'亥','丑':'亥','亥':'巳','卯':'巳','未':'巳'}
            yima = YIMA.get(ri_zhi, '寅')
            fa = tianpan.get(yima, yima)
            return {'keti': '返吟·无依', 'fayong': fa, 'reason': f'返吟无克井栏射取{fa}',
                    'sanchuan_mode': 'fanyin_wuyi', 'details': []}
    
    # 检查八专（干支同位）
    if JIGONG[ri_gan] == ri_zhi:
        zei, ke = check_kz(sike)
        if zei:
            if len(zei) == 1:
                return {'keti': '八专', 'fayong': zei[0][2], 'reason': f'八专有克{zei[0][2]}',
                        'sanchuan_mode': 'bazhuan', 'details': zei}
            else:
                t = biyong_selection(zei, ri_gan)
                return {'keti': '八专', 'fayong': t, 'reason': f'八专比用取{t}',
                        'sanchuan_mode': 'bazhuan', 'details': zei}
        if ke:
            if len(ke) == 1:
                return {'keti': '八专', 'fayong': ke[0][2], 'reason': f'八专上克下{ke[0][2]}',
                        'sanchuan_mode': 'bazhuan', 'details': ke}
            else:
                t = biyong_selection(ke, ri_gan)
                return {'keti': '八专', 'fayong': t, 'reason': f'八专比用取{t}',
                        'sanchuan_mode': 'bazhuan', 'details': ke}
        # 无克：八专法
        yy = TIANGAN_YINYANG[ri_gan]
        if yy == '阳':
            fa = sike[0][3]
            return {'keti': '八专·帷簿不修', 'fayong': fa, 'reason': '八专无克阳日顺取',
                    'sanchuan_mode': 'bazhuan', 'details': []}
        else:
            fa = sike[2][3]
            return {'keti': '八专·帷簿不修', 'fayong': fa, 'reason': '八专无克阴日逆取',
                    'sanchuan_mode': 'bazhuan', 'details': []}
    
    # 标准克贼判断
    zei, ke = check_kz(sike)
    
    if zei:
        if len(zei) == 1:
            return {'keti': '重审', 'fayong': zei[0][2], 'reason': f'唯一下贼上：{zei[0][1]}贼{zei[0][2]}',
                    'sanchuan_mode': 'standard', 'details': zei}
        else:
            t = biyong_selection(zei, ri_gan)
            return {'keti': '比用（知一）', 'fayong': t, 'reason': f'多重下贼上比用取{t}',
                    'sanchuan_mode': 'standard', 'details': zei}
    
    if ke:
        if len(ke) == 1:
            return {'keti': '元首', 'fayong': ke[0][2], 'reason': f'唯一上克下{ke[0][2]}',
                    'sanchuan_mode': 'standard', 'details': ke}
        else:
            t = biyong_selection(ke, ri_gan)
            return {'keti': '比用', 'fayong': t, 'reason': f'多重上克下比用取{t}',
                    'sanchuan_mode': 'standard', 'details': ke}
    
    # 无克贼 → 遥克
    # 检查二、三、四课上神是否克日干或被日干克
    # 日干克上神 → 弹射；上神克日干 → 蒿矢
    ri_gan_zhi = JIGONG[ri_gan]  # 寄宫地支
    second_top = sike[1][3]  # 阴神
    third_top = sike[2][3]   # 辰上神
    fourth_top = sike[3][3]  # 辰阴
    
    ke_gan = []  # 上神克日干
    gan_ke = []  # 日干克上神
    
    for shen in [second_top, third_top, fourth_top]:
        if wuxing_ke(shen, ri_gan_zhi):
            ke_gan.append(shen)
        if wuxing_ke(ri_gan_zhi, shen):
            gan_ke.append(shen)
    
    if ke_gan:
        # 蒿矢
        if len(ke_gan) == 1:
            return {'keti': '蒿矢', 'fayong': ke_gan[0], 'reason': f'上神{ke_gan[0]}遥克日干',
                    'sanchuan_mode': 'standard', 'details': []}
        else:
            t = biyong_selection([(0, '', s) for s in ke_gan], ri_gan)
            return {'keti': '蒿矢', 'fayong': t, 'reason': f'多重遥克比用取{t}',
                    'sanchuan_mode': 'standard', 'details': []}
    
    if gan_ke:
        # 弹射
        if len(gan_ke) == 1:
            return {'keti': '弹射', 'fayong': gan_ke[0], 'reason': f'日干遥克上神{gan_ke[0]}',
                    'sanchuan_mode': 'standard', 'details': []}
        else:
            t = biyong_selection([(0, '', s) for s in gan_ke], ri_gan)
            return {'keti': '弹射', 'fayong': t, 'reason': f'多重弹射比用取{t}',
                    'sanchuan_mode': 'standard', 'details': []}
    
    # 无遥克 → 昴星
    # 阳日：酉上天盘发用，中传辰上，末传干上
    # 阴日：酉下地盘发用，中传干上，末传辰上
    yy = TIANGAN_YINYANG[ri_gan]
    you_top = tianpan.get('酉', '酉')
    you_bottom = '酉'
    
    if yy == '阳':
        fa = you_top
        return {'keti': '昴星·虎视', 'fayong': fa, 'reason': f'阳日昴星取{fa}',
                'sanchuan_mode': 'maoxing_yang', 'details': []}
    else:
        fa = you_bottom
        return {'keti': '昴星·冬蛇掩目', 'fayong': fa, 'reason': f'阴日昴星取酉下{fa}',
                'sanchuan_mode': 'maoxing_yin', 'details': []}


def get_sanchuan(ke_zei_result, tianpan, sike=None, ri_gan=None):
    """计算三传
    不同课体的三传规则不同
    Returns: [(地支, 标签), ...]
    """
    keti = ke_zei_result['keti']
    fayong = ke_zei_result['fayong']
    mode = ke_zei_result.get('sanchuan_mode', 'standard')
    
    if not fayong:
        return []
    
    if mode == 'standard':
        # 初传=发用，中传=初传上神，末传=中传上神
        chu = fayong
        zhong = tianpan[chu]
        mo = tianpan[zhong]
        return [(chu, '初传（发用）'), (zhong, '中传（移易）'), (mo, '末传（归结）')]
    
    elif mode == 'fuyin':
        # 伏吟：三传迤逦三刑
        chu = fayong
        xing = SANXING.get(chu)
        if xing and xing != chu:
            # 正常三刑
            zhong = xing
            mo = SANXING.get(zhong, tianpan[zhong])
            return [(chu, '初传'), (zhong, '中传'), (mo if mo != zhong else tianpan[zhong], '末传')]
        # 自刑情况
        if chu in ('辰', '午', '酉', '亥'):
            if sike:
                yy = TIANGAN_YINYANG.get(ri_gan, '阳')
                if yy == '阳':
                    zhong = sike[2][3] if len(sike) >= 3 else tianpan[chu]  # 辰上神
                else:
                    zhong = sike[0][3] if sike else tianpan[chu]  # 干上神
                mo_xing = SANXING.get(zhong)
                mo = mo_xing if mo_xing and mo_xing != zhong else tianpan[zhong]
                return [(chu, '初传'), (zhong, '中传'), (mo, '末传')]
        # 默认
        zhong = tianpan[chu] if chu else ''
        mo = tianpan[zhong] if zhong else ''
        return [(chu, '初传'), (zhong, '中传'), (mo, '末传')]
    
    elif mode == 'fanyin':
        # 返吟：初末相同冲中传
        chu = fayong
        zhong = tianpan[chu]
        mo = chu  # 初末相同
        return [(chu, '初传'), (zhong, '中传'), (mo, '末传')]
    
    elif mode == 'fanyin_wuyi':
        # 返吟无依：中传=支上，末传=干上
        if sike:
            zhong = sike[2][3] if len(sike) >= 3 else tianpan[fayong]
            mo = sike[0][3] if sike else tianpan[zhong]
        else:
            zhong = tianpan[fayong]
            mo = tianpan[zhong]
        return [(fayong, '初传'), (zhong, '中传'), (mo, '末传')]
    
    elif mode == 'maoxing_yang':
        # 阳日昴星：初=酉上神，中=辰上，末=干上
        if sike:
            zhong = sike[2][3]  # 辰上
            mo = sike[0][3]     # 干上
        else:
            zhong = tianpan[fayong]
            mo = tianpan[zhong]
        return [(fayong, '初传'), (zhong, '中传'), (mo, '末传')]
    
    elif mode == 'maoxing_yin':
        # 阴日昴星：初=酉下，中=干上，末=辰上
        if sike:
            zhong = sike[0][3]  # 干上
            mo = sike[2][3]     # 辰上
        else:
            zhong = tianpan[fayong]
            mo = tianpan[zhong]
        return [(fayong, '初传'), (zhong, '中传'), (mo, '末传')]
    
    elif mode == 'bazhuan':
        # 八专：有克同标准，无克中末干上
        # 无克：中末传干上神
        zhong = sike[0][3] if sike else tianpan[fayong]
        # 八专中末传都归干上
        mo = zhong
        return [(fayong, '初传'), (zhong, '中传'), (mo, '末传')]
    
    # 默认
    chu = fayong
    zhong = tianpan[chu]
    mo = tianpan[zhong]
    return [(chu, '初传（发用）'), (zhong, '中传（移易）'), (mo, '末传（归结）')]


# ========== 课体判断 ==========

def get_keti_description(keti, sike):
    """课体说明"""
    descriptions = {
        '元首': '唯一上克下，天地顺轨，事多顺利，百事攸宜。',
        '重审': '下贼上，先迷后利，卑下犯上，人事逆谋为不利，须详审。',
        '比用（知一）': '二克贼阴阳相争，阳得一阴爻而不知有阴。吉神将福祥双至，凶神将灾祸不单。',
        '比用': '二克贼阴阳并存，取与日干同阴阳者为用。',
        '蒿矢': '无克无遥克唯上神遥克日干者，力绵如蒿，事难成。',
        '弹射': '无克无遥克唯日干遥克上神者，力薄如弹，所卜难成。',
        '伏吟': '诸神归于本位，天地闭贤人隐，未可有为。宜静不宜动。',
        '伏吟·任信': '阳日伏吟，自任其刚。宜静不宜动。',
        '伏吟·自信': '阴日伏吟，自信其柔。宜静不宜动。',
        '返吟': '天地易位，反复呻吟，往来不一，事情多变。',
        '返吟·重审': '返吟中有下贼上，反复中仍有审慎之意。',
        '返吟·元首': '返吟中上克下，反复中见天意。',
        '返吟·无依': '返吟无克，井栏射取用。事体反复无依，往来不一。',
        '昴星·虎视': '阳日昴星，酉上取用，虎视转蓬，出外稽留难归。',
        '昴星·冬蛇掩目': '阴日昴星，酉下取用，冬蛇掩目，虚惊终不伤人。',
        '别责': '四课不备，所占罔济，不过利守而已。',
        '八专': '干支同位，有克从克，无克用八专法。',
        '八专·帷簿不修': '八专无克，帷簿不修之象，主内外不分。',
    }
    return descriptions.get(keti, f'《{keti}》课')


# ========== 断课解释 ==========

def make_judgment(keti, sike, sanchuan, tianguan_map, tianpan, ri_gan, ri_zhi, shichen, guiren_gong, guiren_order, zhan_shi=''):
    """生成完整断课解释"""
    lines = []
    lines.append('═' * 40)
    lines.append('【六壬排盘结果】')
    
    # 基本信息
    lines.append(f'日干：{ri_gan}（{wuxing_of(ri_gan)}，{TIANGAN_YINYANG[ri_gan]}）')
    lines.append(f'日支：{ri_zhi}（{wuxing_of(ri_zhi)}）')
    lines.append(f'占时：{shichen}')
    lines.append(f'贵人：{guiren_gong}（{guiren_order}）')
    lines.append(f'课体：{keti}')
    if zhan_shi:
        lines.append(f'占事：{zhan_shi}')
    
    lines.append('')
    
    # 四课显示
    lines.append('【四课】')
    for name, label, bottom_zhi, top_shen in sike:
        lines.append(f'  {name}：{label} → {top_shen}')
    
    lines.append('')
    
    # 三传
    lines.append('【三传】')
    for zhi, label in sanchuan:
        if zhi:
            tg = tianguan_map.get(zhi, '?')
            cs = get_changsheng(ri_gan, zhi)
            lines.append(f'  {label}：{zhi}（{MENG_ZHONG_JI[zhi]}，{wuxing_of(zhi)}）乘【{tg}】 长生：{cs}')
    
    lines.append('')
    
    # 课体解释
    lines.append('【课体解】')
    lines.append(f'  {get_keti_description(keti, sike)}')
    
    lines.append('')
    
    # 天官吉凶
    lines.append('【天官吉凶】')
    for zhi, label in sanchuan:
        tg = tianguan_map.get(zhi, '?')
        _, jx, desc = TIANGUAN_JIXIONG.get(tg, ('', '中', ''))
        lines.append(f'  {zhi}→{tg}：{jx} — {desc}')
    
    lines.append('')
    
    # 断语
    lines.append('【断语】')
    if sanchuan:
        chu_zhi = sanchuan[0][0] if sanchuan[0] else ''
        zhong_zhi = sanchuan[1][0] if len(sanchuan) >= 2 else ''
        mo_zhi = sanchuan[2][0] if len(sanchuan) >= 3 else ''
        
        chu_tg = tianguan_map.get(chu_zhi, '?')
        zhong_tg = tianguan_map.get(zhong_zhi, '?')
        mo_tg = tianguan_map.get(mo_zhi, '?')
        
        _, jx_chu, desc_chu = TIANGUAN_JIXIONG.get(chu_tg, ('', '中', ''))
        _, jx_zhong, desc_zhong = TIANGUAN_JIXIONG.get(zhong_tg, ('', '中', ''))
        _, jx_mo, desc_mo = TIANGUAN_JIXIONG.get(mo_tg, ('', '中', ''))
        
        lines.append(f'  初传{chu_zhi}乘{chu_tg}（{jx_chu}）→ {desc_chu}')
        lines.append(f'  中传{zhong_zhi}乘{zhong_tg}（{jx_zhong}）→ {desc_zhong}')
        lines.append(f'  末传{mo_zhi}乘{mo_tg}（{jx_mo}）→ {desc_mo}')
        lines.append('')
        
        # 三传走势
        lines.append(f'  【三传走势】{chu_tg}（{chu_zhi}）→ {zhong_tg}（{zhong_zhi}）→ {mo_tg}（{mo_zhi}）')
        
        # 四大天官基础判断
        if jx_chu in ('大吉', '吉'):
            lines.append(f'  ✓ 初传吉神，起步有利')
        else:
            lines.append(f'  ⚠ 初传凶神，起步有压力')
        
        if jx_mo in ('大吉', '吉'):
            lines.append(f'  ✓ 末传吉神，结果看好')
        else:
            lines.append(f'  ⚠ 末传凶神，结果需谨慎')
    
    lines.append('═' * 40)
    
    return '\n'.join(lines)


# ========== 主入口 ==========

def get_liuren_pan(year, month, day, hour, minute=0,
                   ri_gan=None, ri_zhi=None,
                   yuejiang=None, shichen=None,
                   zhan_shi='', auto_shi=True,
                   gr_manual='auto', sn_manual='auto'):
    """获取完整六壬排盘
    
    Args:
        year, month, day, hour, minute: 阳历日期时间
        ri_gan, ri_zhi: 日干支（可选，自动计算）
        yuejiang: 月将（可选，自动计算）
        shichen: 时辰（可选，自动计算）
        zhan_shi: 占事
        auto_shi: 是否自动时辰
        gr_manual: 贵人手动选择（auto/昼/夜）
        sn_manual: 顺逆手动选择（auto/顺行/逆行）
    
    Returns:
        排盘结果 dict
    """
    # 1. 时辰
    if shichen is None:
        shichen = hour_to_shichen(hour)
    
    # 2. 日月干支（使用计算结果）
    if ri_gan is None or ri_zhi is None:
        import datetime
        dt = datetime.date(year, month, day)
        # 简单计算日干支
        # 基准：2000-01-01 = 甲子日
        base = datetime.date(2000, 1, 1)
        diff = (dt - base).days
        idx = (diff + GANZHI_BASE_2000) % 60
        if idx < 0:
            idx += 60
        ri_gan = TIANGAN[idx % 10]
        ri_zhi = DIZHI[idx % 12]
    
    # 3. 月将
    if yuejiang is None or yuejiang == 'auto':
        yuejiang = get_yuejiang(year, month, day)
    
    # 4. 天盘
    tianpan = get_tianpan(yuejiang, shichen)
    
    # 5. 四课
    sike = get_sike(ri_gan, ri_zhi, tianpan)
    
    # 6. 九宗门定三传
    ke_zei_result = get_ke_zei(sike, ri_gan, ri_zhi, tianpan, yuejiang, shichen)
    sanchuan = get_sanchuan(ke_zei_result, tianpan, sike, ri_gan)
    
    # 7. 贵人（支持手动覆盖）
    if gr_manual == '昼':
        guiren_gong = GUI_REN_ZHOU['阳贵'].get(ri_gan, '丑')
    elif gr_manual == '夜':
        guiren_gong = GUI_REN_YE['阴贵'].get(ri_gan, '未')
    else:
        guiren_gong = get_guiren(ri_gan, hour, shichen)
    
    if sn_manual in ('顺行', '逆行'):
        guiren_order = sn_manual
    else:
        guiren_order = get_guiren_order(guiren_gong, tianpan)
    
    # 8. 天官
    tianguan_map = get_tianguan_positions(tianpan, guiren_gong, guiren_order)
    
    # 9. 断语
    judgment = make_judgment(
        ke_zei_result['keti'], sike, sanchuan, tianguan_map,
        tianpan, ri_gan, ri_zhi, shichen,
        guiren_gong, guiren_order, zhan_shi
    )
    
    result = {
        'year': year, 'month': month, 'day': day,
        'hour': hour, 'minute': minute,
        'ri_gan': ri_gan, 'ri_zhi': ri_zhi,
        'yuejiang': yuejiang,
        'yuejiang_name': YUEJIANG_NAME.get(yuejiang, ''),
        'shichen': shichen,
        'tianpan': tianpan,
        'sike': sike,
        'keti': ke_zei_result['keti'],
        'ke_zei_reason': ke_zei_result.get('reason', ''),
        'sanchuan': sanchuan,
        'changsheng': get_changsheng_table(ri_gan, sanchuan),
        'guiren_gong': guiren_gong,
        'guiren_order': guiren_order,
        'tianguan_map': tianguan_map,
        'judgment': judgment,
        'zhan_shi': zhan_shi,
    }
    
    return result


# ========== 终身论命 ==========

def get_geju(birth_zhi, tianpan, tianguan):
    """匹配二十四格（简化版）"""
    tg_names = [tianguan[z] for z in DIZHI if z in tianguan]
    # 检查关键格局
    gest = []
    # 正跨龙：本命子 临寅
    if birth_zhi == '子' and tianpan.get('寅') == '寅' and '青龙' in tg_names:
        gest.append(('正跨青龙', '极贵台阁之命'))
    # 倒跨龙：本命子 寅加子上
    if birth_zhi == '子' and tianpan.get('寅') == '子' and '青龙' in tg_names:
        gest.append(('倒跨青龙', '大贵富之命'))
    # 乘虎登天：本命午/申 临亥
    if birth_zhi in ('午','申') and tianpan.get('亥') == birth_zhi and '白虎' in tg_names:
        gest.append(('乘虎登天', '威镇边夷公侯之命'))
    # 朱雀腾辉
    if '朱雀' in tg_names and tianpan.get(birth_zhi,'') in ('寅','卯','辰','巳','午'):
        gest.append(('朱雀腾辉', '文章盖世'))
    # 朱雀束翅
    if '朱雀' in tg_names and tianpan.get(birth_zhi,'') in ('亥','子','丑'):
        gest.append(('朱雀束翅', '七步之才不得展'))
    # 司命天门
    if tianpan.get('亥') == birth_zhi and any(t in tg_names for t in ['贵人','青龙','太常','天后','六合','朱雀']):
        gest.append(('司命天门', '得君信任枢秘之职'))
    # 四墓交错
    if wuxing_of(birth_zhi) == '土' and '白虎' not in tg_names:
        gest.append(('四墓交错', '丰厚有财产'))
    if not gest:
        gest.append(('格局未显', '不入二十四格，宜详审课传'))
    return gest


def get_12gong(ri_gan, ri_zhi, tianpan, tianguan_map):
    """十二宫分析"""
    gong_map = [
        ('命宫', 0, '身命本体'),
        ('财帛', 2, '财运资产'),
        ('兄弟', 3, '手足情谊'),
        ('田宅', 4, '产业家宅'),
        ('男女', 5, '子嗣'),
        ('奴仆', 6, '下属仆役'),
        ('妻妾', 7, '配偶姻缘'),
        ('疾厄', 8, '健康'),
        ('迁移', 9, '出行变动'),
        ('官禄', 10, '功名事业'),
        ('福德', 11, '福分'),
        ('相貌', 1, '外表'),
    ]
    results = []
    ri_zhi_idx = DIZHI_INDEX[ri_zhi]
    for gong_name, offset, desc in gong_map:
        gong_zhi = DIZHI[(ri_zhi_idx + offset) % 12]
        gong_shen = tianpan.get(gong_zhi, gong_zhi)
        gong_tg = tianguan_map.get(gong_zhi, '')
        _, jx, _ = TIANGUAN_JIXIONG.get(gong_tg, ('', '中', ''))
        results.append({'宫': gong_name, '位置': gong_zhi, '天盘': gong_shen,
                       '天官': gong_tg, '吉凶': jx, '说明': desc})
    return results


def get_zhongshen(ri_gan, ri_zhi, sike, sanchuan, tianpan, tianguan_map, judgment):
    """生成终身论命结果"""
    birth_zhi = ri_zhi
    geju = get_geju(birth_zhi, tianpan, tianguan_map)
    gong = get_12gong(ri_gan, ri_zhi, tianpan, tianguan_map)
    
    # 三传三世
    shi_san = []
    for i, (zhi, label) in enumerate(sanchuan):
        if zhi:
            tg = tianguan_map.get(zhi, '')
            _, jx, _ = TIANGUAN_JIXIONG.get(tg, ('', '中', ''))
            cs = get_changsheng(ri_gan, zhi)
            stages = ['少年(初传)', '中年(中传)', '晚年(末传)']
            shi_san.append({'阶段': stages[i] if i < 3 else '', '地支': zhi,
                          '天官': tg, '吉凶': jx, '长生': cs})
    
    return {'geju': geju, 'gong': gong, 'shisan': shi_san}

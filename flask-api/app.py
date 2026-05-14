#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大六壬在线排盘 · Web应用 (Flask)
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pylib'))

from flask import Flask, render_template, request, jsonify
import datetime
import json

# 添加pylib到路径
CORE_DIR = os.path.dirname(os.path.abspath(__file__))
PYLIB_DIR = os.path.join(CORE_DIR, 'pylib')
if os.path.exists(PYLIB_DIR):
    sys.path.insert(0, PYLIB_DIR)

from liuren_core import *

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/paipan', methods=['POST'])
def api_paipan():
    data = request.get_json()
    year = int(data.get('year', 2026))
    month = int(data.get('month', 5))
    day = int(data.get('day', 12))
    hour = int(data.get('hour', 8))
    minute = int(data.get('minute', 0))
    yuejiang_sel = data.get('yuejiang', 'auto')
    zhanshi = data.get('zhanshi', '')
    grsel = data.get('guiren', 'auto')
    snsel = data.get('shunni', 'auto')

    # 计算时辰
    shichen = hour_to_shichen(hour)

    # 计算日干支
    dt = datetime.date(year, month, day)
    base = datetime.date(2000, 1, 1)
    diff = (dt - base).days
    idx = (diff + 54) % 60
    if idx < 0:
        idx += 60
    ri_gan = TIANGAN[idx % 10]
    ri_zhi = DIZHI[idx % 12]
    ri_gan = TIANGAN[idx % 10]
    ri_zhi = DIZHI[idx % 12]

    # 月将
    if yuejiang_sel == 'auto':
        yuejiang = get_yuejiang(year, month, day)
    else:
        yuejiang = yuejiang_sel

    # 排盘（贵人手动模式）
    result = get_liuren_pan(year, month, day, hour, minute,
                           ri_gan=ri_gan, ri_zhi=ri_zhi,
                           yuejiang=yuejiang, shichen=shichen,
                           zhan_shi=zhanshi,
                           gr_manual=grsel,
                           sn_manual=snsel)

    # 构建返回数据
    resp = {
        'year': year, 'month': month, 'day': day,
        'hour': hour, 'minute': minute,
        'ri_gan': ri_gan, 'ri_zhi': ri_zhi,
        'yuejiang': result.get('yuejiang', yuejiang),
        'yuejiang_name': result.get('yuejiang_name', YUEJIANG_NAME.get(yuejiang, '')),
        'shichen': shichen,
        'tianpan': result['tianpan'],
        'sike': result['sike'],
        'keti': result['keti'],
        'keti_desc': get_keti_description(result['keti'], result['sike']),
        'sanchuan': result['sanchuan'],
        'guiren_gong': result['guiren_gong'],
        'guiren_order': result['guiren_order'],
        'tianguan_map': result['tianguan_map'],
        'zhan_shi': zhanshi,
    }

    # 天官在三传上的分布
    tg_on_chuan = []
    wx_on_chuan = []
    cs_on_chuan = []
    jx_on_chuan = []
    for zhi, label in result['sanchuan']:
        if zhi:
            tg = result['tianguan_map'].get(zhi, '')
            tg_on_chuan.append(tg)
            wx_on_chuan.append(wuxing_of(zhi))
            cs_on_chuan.append(get_changsheng(result['ri_gan'], zhi))
            _, jx, _ = TIANGUAN_JIXIONG.get(tg, ('', '中', ''))
            jx_on_chuan.append(jx)
        else:
            tg_on_chuan.append(''); wx_on_chuan.append(''); cs_on_chuan.append(''); jx_on_chuan.append('')

    resp['tianguan_on_chuan'] = tg_on_chuan
    resp['wuxing_on_chuan'] = wx_on_chuan
    resp['changsheng_on_chuan'] = cs_on_chuan
    resp['jixiong_on_chuan'] = jx_on_chuan

    # 克贼详情
    ke_details = []
    for name, label, bottom_zhi, top_shen in result['sike']:
        ke_zei = wuxing_ke(top_shen, bottom_zhi)
        zei_ke = wuxing_ke(bottom_zhi, top_shen)
        ke_details.append({'ke': ke_zei, 'zei': zei_ke})
    resp['ke_details'] = ke_details

    # 断语
    resp['judgment'] = result['judgment']

    # 学习模式
    resp['learning'] = make_learning_content(result)

    return jsonify(resp)


@app.route('/api/zhongshen', methods=['POST'])
def api_zhongshen():
    """终生论命 API"""
    data = request.get_json()
    year = int(data.get('year', 2026))
    month = int(data.get('month', 5))
    day = int(data.get('day', 12))
    hour = int(data.get('hour', 8))
    minute = int(data.get('minute', 0))
    name = data.get('name', '')
    
    result = get_liuren_pan(year, month, day, hour, minute)
    zg = get_zhongshen(result['ri_gan'], result['ri_zhi'],
                       result['sike'], result['sanchuan'],
                       result['tianpan'], result['tianguan_map'],
                       result['judgment'])
    
    resp = {
        'ri_gan': result['ri_gan'],
        'ri_zhi': result['ri_zhi'],
        'shichen': result['shichen'],
        'yuejiang': result['yuejiang'],
        'keti': result['keti'],
        'keti_desc': get_keti_description(result['keti'], result['sike']),
        'sanchuan': result['sanchuan'],
        'sike': result['sike'],
        'tianpan': result['tianpan'],
        'tianguan_map': result['tianguan_map'],
        'judgment': result['judgment'],
        'geju': zg['geju'],
        'gong': zg['gong'],
        'shisan': zg['shisan'],
    }
    return jsonify(resp)


def make_learning_content(result):
    """生成学习模式内容"""
    lines = []
    lines.append('[书] 起课过程详解')
    lines.append('=' * 40)
    lines.append(f'\n① 月将：{result["yuejiang"]}（{result["yuejiang_name"]}）')
    lines.append(f'② 占时：{result["shichen"]}时')
    lines.append(f'③ 日干支：{result["ri_gan"]}{result["ri_zhi"]}')
    lines.append(f'   {result["ri_gan"]}奇宫：{JIGONG[result["ri_gan"]]}')
    lines.append(f'\n④ 四课：')
    for name, label, bz, ts in result['sike']:
        ke_wuxing = wuxing_ke(ts, bz)
        zei_wuxing = wuxing_ke(bz, ts)
        ke_str = '上克下' if ke_wuxing else ('下贼上' if zei_wuxing else '无克')
        lines.append(f'   {name}: {label} → {ts}（{ke_str}）')
    lines.append(f'\n⑤ 九宗门：{result["keti"]}')
    lines.append(f'   {result.get("ke_zei_reason", "")}')
    lines.append(f'\n⑥ 三传：')
    for zhi, label in result['sanchuan']:
        if zhi:
            tg = result['tianguan_map'].get(zhi, '')
            _, jx, _ = TIANGUAN_JIXIONG.get(tg, ('', '中', ''))
            lines.append(f'   {label}：{zhi} 乘{tg}（{jx}）')
        else:
            lines.append(f'   {label}：(空)')
    lines.append(f'\n⑦ 贵人：{result["guiren_gong"]}（{result["guiren_order"]}）')
    return '\n'.join(lines)



@app.route('/api/bazi', methods=['POST'])
def api_bazi():
    """八字排盘 API（使用天文节气数据）"""
    data = request.get_json()
    year = int(data.get('year', 1983))
    month = int(data.get('month', 1))
    day = int(data.get('day', 23))
    hour = int(data.get('hour', 13))
    gender = data.get('gender', '男')
    
    import json, os
    jq_path = os.path.join(os.path.dirname(__file__), 'jieqi.json')
    with open(jq_path) as f:
        jq = json.load(f)
    
    s = str(year)
    lc_str = jq.get(s, {}).get('315', '0204')
    lc_m, lc_d = int(lc_str[:2]), int(lc_str[2:])
    
    # 年柱（立春分界）
    if month < lc_m or (month == lc_m and day < lc_d):
        yG = (year - 5) % 10
        yZ = (year - 5) % 12
    else:
        yG = (year - 4) % 10
        yZ = (year - 4) % 12
    if yG < 0: yG += 10
    if yZ < 0: yZ += 12
    
    # 月柱：按节气确定地支
    # 节气黄经: 小寒285,立春315,惊蛰345,清明15,立夏45,芒种75,
    # 小暑105,立秋135,白露165,寒露195,立冬225,大雪255
    # 地支: 子0大雪,丑1小寒,寅2立春,卯3惊蛰,辰4清明,巳5立夏,
    # 午6芒种,未7小暑,申8立秋,酉9白露,戌10寒露,亥11立冬
    jq_list = [('285',1),('315',2),('345',3),('15',4),('45',5),('75',6),
               ('105',7),('135',8),('165',9),('195',10),('225',11),('255',0)]
    md = month * 100 + day
    # 小雪以降默认子是11月
    mZhi = 0  # default子(大雪到小寒前)
    if md < 106: mZhi = 0  # 1月6日小寒前=子
    for jq_lon, zhi_idx in jq_list:
        jq_str = jq.get(s, {}).get(jq_lon, '0101')
        jq_md = int(jq_str[:2]) * 100 + int(jq_str[2:])
        if md >= jq_md:
            mZhi = zhi_idx

    # 五虎遁月干
    ygTab = [[2,3,4,5,6,7,8,9,0,1,2,3],[4,5,6,7,8,9,0,1,2,3,4,5],
             [6,7,8,9,0,1,2,3,4,5,6,7],[8,9,0,1,2,3,4,5,6,7,8,9],
             [0,1,2,3,4,5,6,7,8,9,0,1]]
    mG = ygTab[yG % 5][(mZhi - 2 + 12) % 12]
    
    # 日柱
    base = datetime.date(2000, 1, 1)
    dt = datetime.date(year, month, day)
    diff = (dt - base).days
    idx = (diff + 54) % 60
    rG, rZ = TIANGAN[idx % 10], DIZHI[idx % 12]
    
    # 时柱
    hz = (hour + 1) // 2 % 12
    ht = {'甲':0,'乙':2,'丙':4,'丁':6,'戊':8,'己':0,'庚':2,'辛':4,'壬':6,'癸':8}
    sG = TIANGAN[(ht.get(rG, 0) + hz) % 10]
    sZ = DIZHI[hz]
    
    # 十神
    WXMAP = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
    KW = {'木':'土','火':'金','土':'水','金':'木','水':'火'}
    SW = {'木':'火','火':'土','土':'金','金':'水','水':'木'}
    
    def shishen(ri, ot):
        if ri == ot: return '比肩' if TIANGAN.index(ri) % 2 == 0 else '劫财'
        rw, ow = WXMAP[ri], WXMAP[ot]
        ry, oy = TIANGAN.index(ri) % 2, TIANGAN.index(ot) % 2
        # 我克=财
        if KW[rw] == ow:
            return '偏财' if ry == oy else '正财'
        # 我生=食伤
        if SW[rw] == ow:
            return '食神' if ry == oy else '伤官'
        # 克我=官杀
        if KW[ow] == rw:
            return '七杀' if ry == oy else '正官'
        # 生我=印
        if SW[ow] == rw:
            return '偏印' if ry == oy else '正印'
        return '比肩' if ry == oy else '劫财'
    
    ganArr = [TIANGAN[yG], TIANGAN[mG], rG, sG]
    zhiArr = [DIZHI[yZ], DIZHI[mZhi], rZ, sZ]
    ssArr = ['日主' if i == 2 else shishen(rG, ganArr[i]) for i in range(4)]
    
    # 大运
    is_male = gender == '男'
    yang_year = TIANGAN.index(TIANGAN[yG]) % 2 == 0
    shun = (is_male and yang_year) or (not is_male and not yang_year)
    
    dayun = []
    dyG, dyZ = yG, yZ
    for i in range(8):
        if shun:
            dyG = (dyG + 1) % 10
            dyZ = (dyZ + 1) % 12
        else:
            dyG = (dyG + 9) % 10
            dyZ = (dyZ + 9) % 12
        dayun.append(TIANGAN[dyG] + DIZHI[dyZ])
    
    resp = {
        'year_gan': TIANGAN[yG], 'year_zhi': DIZHI[yZ],
        'month_gan': TIANGAN[mG], 'month_zhi': DIZHI[mZhi],
        'day_gan': rG, 'day_zhi': rZ,
        'hour_gan': sG, 'hour_zhi': sZ,
        'shi_shen': ssArr,
        'dayun': dayun,
        'gender': gender,
        'year': year, 'month': month, 'day': day,
        'jieqi_lichun': f'{lc_m}月{lc_d}日',
        'jieqi_yue': '',
    }
    
    return jsonify(resp)



if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 19130))
    print(f'\n[球] 大六壬在线排盘启动')
    print(f'   访问地址：http://0.0.0.0:{port}')
    print(f'   主实例端口：19130')
    app.run(host='0.0.0.0', port=port, debug=False)

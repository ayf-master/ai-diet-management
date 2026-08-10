# -*- coding: utf-8 -*-
"""生成《AI辅助减脂饮食管理系统》答辩 PPT (16:9, python-pptx)"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- 主题 ----------
DARK   = RGBColor(0x1B, 0x5E, 0x20)   # 深绿
MAIN   = RGBColor(0x2E, 0x7D, 0x32)   # 主绿
MID    = RGBColor(0x66, 0xBB, 0x6A)   # 中绿
ACCENT = RGBColor(0xF5, 0x7C, 0x00)   # 橙色点缀
INK    = RGBColor(0x26, 0x32, 0x38)   # 正文深灰
GRAY   = RGBColor(0x60, 0x7D, 0x8B)   # 次级灰
LIGHT  = RGBColor(0xE8, 0xF5, 0xE9)   # 浅绿
BG     = RGBColor(0xFA, 0xFD, 0xF8)   # 页面底色
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
FONT   = 'Microsoft YaHei'

prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
TOTAL = 9

def set_font(run, size=14, bold=False, color=INK, name=FONT):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = name
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = rPr.makeelement(qn('a:ea'), {})
        rPr.append(ea)
    ea.set('typeface', name)

def add_rect(slide, x, y, w, h, fill, shape=MSO_SHAPE.RECTANGLE, line=None, radius=None):
    sp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    sp.fill.solid()
    sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line
        sp.line.width = Pt(0.75)
    sp.shadow.inherit = False
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            sp.adjustments[0] = radius
        except Exception:
            pass
    return sp

def add_text(slide, x, y, w, h, text, size=14, bold=False, color=INK,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line_spacing=1.15,
             space_after=0):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    first = True
    for line in text.split('\n'):
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        p.line_spacing = line_spacing
        p.space_after = Pt(space_after)
        r = p.add_run()
        r.text = line
        set_font(r, size, bold, color)
    return tb

def add_card(slide, x, y, w, h, title, body, title_color=MAIN, body_size=13,
             title_size=15, fill=WHITE, radius=0.06, line_color=None, pad=0.18):
    add_rect(slide, x, y, w, h, fill, MSO_SHAPE.ROUNDED_RECTANGLE,
             line=line_color or LIGHT, radius=radius)
    add_text(slide, x + pad, y + pad, w - 2 * pad, h - 2 * pad, title,
             size=title_size, bold=True, color=title_color, space_after=6)
    add_text(slide, x + pad, y + pad + 0.34, w - 2 * pad, h - 2 * pad - 0.34,
             body, size=body_size, color=INK, line_spacing=1.2)

def add_table(slide, x, y, w, rows_data, col_ws, header_fill=MAIN,
              font_size=12.5, row_h=0.42, header_h=0.44, align_map=None):
    rows, cols = len(rows_data), len(rows_data[0])
    gf = slide.shapes.add_table(rows, cols, Inches(x), Inches(y), Inches(w), Inches(row_h * rows))
    table = gf.table
    table.first_row = False
    table.horz_banding = False
    for c, cw in enumerate(col_ws):
        table.columns[c].width = Inches(cw)
    table.rows[0].height = Inches(header_h)
    for i in range(1, rows):
        table.rows[i].height = Inches(row_h)
    for r in range(rows):
        for c in range(cols):
            cell = table.cell(r, c)
            cell.margin_left = Inches(0.1)
            cell.margin_right = Inches(0.1)
            cell.margin_top = Inches(0.03)
            cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = header_fill if r == 0 else (WHITE if r % 2 else LIGHT)
            p = cell.text_frame.paragraphs[0]
            p.alignment = align_map[c] if align_map else PP_ALIGN.LEFT
            run = p.add_run()
            run.text = rows_data[r][c]
            if r == 0:
                set_font(run, font_size, True, WHITE)
            elif c == 0:
                set_font(run, font_size, True, INK)
            else:
                set_font(run, font_size, False, INK)
    return table

def add_arrow_chain(slide, x, y, labels, w=1.5, h=0.95, gap=0.35, color=MAIN):
    """横向流程框:labels 为 [(主行, 副行)] 列表, 框间绿色箭头
    x=None 时整条链居中; 副行自动贴在框底部, 可容纳两行小字"""
    n = len(labels)
    total = n * w + (n - 1) * gap
    cur = (13.333 - total) / 2 if x is None else x
    for i, (t1, t2) in enumerate(labels):
        add_rect(slide, cur, y, w, h, color, MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12)
        add_text(slide, cur, y + 0.06, w, 0.3, t1, size=12, bold=True,
                 color=WHITE, align=PP_ALIGN.CENTER)
        if t2:
            add_text(slide, cur, y + h - 0.42, w, 0.36, t2, size=9,
                     color=RGBColor(0xDC, 0xF0, 0xDD), align=PP_ALIGN.CENTER,
                     line_spacing=1.1)
        cur += w
        if i < n - 1:
            ar = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(cur), Inches(y + 0.15),
                                        Inches(gap), Inches(h - 0.3))
            ar.fill.solid()
            ar.fill.fore_color.rgb = ACCENT
            ar.line.fill.background()
            ar.shadow.inherit = False
            cur += gap

def new_slide(title, subtitle=None, page=None):
    s = prs.slides.add_slide(BLANK)
    add_rect(s, 0, 0, 13.333, 7.5, BG)
    add_rect(s, 0, 0, 0.18, 7.5, DARK)
    add_rect(s, 0.55, 0.42, 0.16, 0.5, ACCENT)
    add_text(s, 0.88, 0.42, 9.5, 0.6, title, size=26, bold=True, color=INK)
    if subtitle:
        add_text(s, 0.9, 1.02, 11.5, 0.32, subtitle, size=11.5, color=GRAY)
    if page:
        add_text(s, 12.35, 7.08, 0.8, 0.3, f'{page:02d} / {TOTAL}', size=10, color=GRAY,
                 align=PP_ALIGN.RIGHT)
        add_text(s, 0.6, 7.08, 6, 0.3, 'AI辅助减脂饮食管理系统 · 数据库应用开发大型实验',
                 size=9, color=RGBColor(0xA0, 0xB8, 0xA8))
    return s

# ================= P1 封面 =================
s = prs.slides.add_slide(BLANK)
add_rect(s, 0, 0, 13.333, 7.5, DARK)
add_rect(s, 0, 7.14, 13.333, 0.36, ACCENT)
for i, (w, o) in enumerate([(2.2, 0.75), (3.6, 1.10), (1.6, 1.45)]):
    add_rect(s, 13.133 - w - i * 0.25, o, w, 0.09, MAIN if i % 2 == 0 else MID)
add_text(s, 1.2, 1.05, 10.9, 0.4, '数据库应用开发 · 大型实验答辩汇报', size=15,
         color=RGBColor(0xA5, 0xD6, 0xA7))
add_text(s, 1.2, 2.15, 10.9, 1.6, 'AI 辅助减脂饮食管理系统', size=46, bold=True,
         color=WHITE)
add_text(s, 1.2, 3.45, 10.9, 0.5,
         '饮食打卡 · 热量引擎 · 慢性病禁忌 · AI 个性化减脂方案', size=16,
         color=RGBColor(0xC8, 0xE6, 0xC9))
add_rect(s, 1.22, 4.35, 3.4, 0.035, ACCENT)
add_text(s, 1.2, 5.1, 10.9, 0.9,
         '答辩人：____________　　指导老师：____________\n'
         'MySQL 8.0 · Flask · Vue 3 · DeepSeek　　2026 年 8 月',
         size=14, color=RGBColor(0xE8, 0xF5, 0xE9), line_spacing=1.6)

# ================= P2 目录 =================
s = new_slide('目录', 'CONTENTS', 2)
items = [
    ('01', '项目背景与目标', '痛点 · 系统目标'),
    ('02', '系统架构与主要功能', '技术栈 · 功能演示'),
    ('03', '数据库设计总览', '20 张表 · ER 图'),
    ('04', '设计思路与热量引擎', '领域建模 · 三专区'),
    ('05', '技术亮点', '存储过程 · 触发器 · AI'),
    ('06', '挑战与解决方案', '难点与对策'),
    ('07', '总结与致谢', '收获与展望'),
]
for i, (num, t, d) in enumerate(items):
    if i < 4:
        x = 0.9 + i * 2.96
        y = 1.5
    else:
        x = 2.38 + (i - 4) * 2.96
        y = 4.15
    add_rect(s, x, y, 2.66, 2.4, WHITE, MSO_SHAPE.ROUNDED_RECTANGLE, line=LIGHT, radius=0.08)
    add_rect(s, x + 0.22, y + 0.24, 0.66, 0.66, LIGHT, MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.22)
    add_text(s, x + 0.22, y + 0.34, 0.66, 0.46, num, size=15, bold=True,
             color=MAIN, align=PP_ALIGN.CENTER)
    add_text(s, x + 0.22, y + 1.0, 2.22, 0.7, t, size=13.5, bold=True,
             color=INK, line_spacing=1.1)
    add_text(s, x + 0.22, y + 1.76, 2.22, 0.55, d, size=9.5, color=GRAY, line_spacing=1.1)

# ================= P3 项目背景与目标 =================
s = new_slide('项目背景与目标', 'PROJECT OVERVIEW', 3)
pains = [
    ('热量估算难', '外卖与家常菜缺乏精确热量数据，凭感觉估算误差大，减脂难以量化管理'),
    ('方案千人一面', '网上的食谱不区分胖瘦、目标与身体状况，照搬执行易失败甚至伤身'),
    ('数据零散', '体重、饮食、目标散落在不同 APP，缺乏统一记录与周期性分析'),
]
for i, (t, d) in enumerate(pains):
    add_card(s, 0.9 + i * 4.1, 1.5, 3.75, 1.95, f'痛点 {i + 1}：{t}', d, title_color=ACCENT)
add_rect(s, 0.9, 3.85, 11.55, 1.1, LIGHT, MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.1)
add_text(s, 1.25, 4.05, 10.9, 0.4, '系统目标', size=16, bold=True, color=MAIN)
add_text(s, 1.25, 4.5, 10.9, 0.4,
         '构建一套「记录 → 计算 → 推荐 → 分析」的减脂闭环：科学计算热量、按目标推荐饮食、AI 生成个性化方案与健康周报',
         size=13.5, color=INK)
cards = [
    ('科学计算', 'BMR / TDEE / BMI 分级\n自动推荐每日摄入热量'),
    ('按目标推荐', '健康 / 减肥 / 健身\n三专区精准匹配食谱'),
    ('AI 个性化', '结合身体数据、打卡记录\n与疾病禁忌生成专属方案'),
    ('周期分析', '体重趋势 + 打卡汇总\nAI 周报给出调整建议'),
]
for i, (t, d) in enumerate(cards):
    add_card(s, 0.9 + i * 2.95, 5.25, 2.7, 1.55, t, d, title_size=14, body_size=11.5)

# ================= P4 系统架构与主要功能 =================
s = new_slide('系统架构与主要功能', 'ARCHITECTURE & FEATURES', 4)
add_text(s, 0.9, 1.42, 6, 0.35, '技术栈', size=14, bold=True, color=INK)
add_table(s, 0.9, 1.82, 11.55, [
    ['技术栈', '选型与职责'],
    ['前端', 'Vue 3 + Vite + Chart.js —— 页面交互 · 数据看板 · 管理后台'],
    ['后端', 'Flask + SQLAlchemy —— RESTful 接口 · 认证 · 业务逻辑'],
    ['数据库', 'MySQL 8.0 —— 20 张表 · 5 触发器 · 5 存储过程'],
    ['AI 服务', 'DeepSeek —— 按专区 / 禁忌生成方案与周报'],
], [1.2, 10.35], font_size=11.5, row_h=0.4, header_h=0.4)
add_text(s, 0.9, 3.95, 6, 0.35, '核心功能（演示内容）', size=14, bold=True, color=INK)
user_f = [
    ('注册即科学计算', '身体数据 → BMR / BMI / 推荐热量'),
    ('专区食谱 · 一餐多菜品打卡', '按目标浏览 · 打卡热量自动汇总'),
    ('数据看板', 'Chart.js 热量对比 · 体重趋势'),
    ('AI 方案与周报', '按专区 + 禁忌生成 · 周期健康分析'),
]
for i, (t, d) in enumerate(user_f):
    add_card(s, 0.9 + (i % 2) * 5.95, 4.28 + (i // 2) * 1.02, 5.7, 0.88,
             t, d, body_size=11.5, title_size=14)
add_text(s, 0.9, 6.28, 3.5, 0.3, '管理端', size=13, bold=True, color=INK)
for i, (t, d) in enumerate([
    ('食材与食谱管理', '配比 · 热量 · 专区标签'),
    ('疾病禁忌维护', '供 AI 方案过滤'),
]):
    add_card(s, 0.9 + i * 5.95, 6.55, 5.7, 0.72, t, d,
             body_size=10.5, title_size=13.5)

# ================= P5 数据库设计 =================
s = new_slide('数据库设计总览', 'DATABASE DESIGN · 20 TABLES', 5)
add_rect(s, 0.9, 1.42, 5.6, 5.35, WHITE, MSO_SHAPE.ROUNDED_RECTANGLE, line=LIGHT, radius=0.04)
add_text(s, 1.15, 1.58, 5, 0.35, '实体关系图（ER）', size=14, bold=True, color=MAIN)
s.shapes.add_picture(os.path.join(BASE, 'ER图.png'), Inches(1.15), Inches(2.0), Inches(5.1))
add_rect(s, 6.8, 1.42, 5.65, 5.35, WHITE, MSO_SHAPE.ROUNDED_RECTANGLE, line=LIGHT, radius=0.04)
add_text(s, 7.05, 1.58, 5, 0.35, '四大体系 · 关系类型', size=14, bold=True, color=MAIN)
add_table(s, 7.05, 2.05, 5.15, [
    ['体系', '核心表', '关键关系'],
    ['用户体系', 'user / weight_record / disease / user_disease', '1:N · M:N'],
    ['食材体系', 'food / nutrition / recipe / recipe_food', '1:1 · M:N'],
    ['打卡体系', 'diet_record / diet_record_detail', '主子表 1:N'],
    ['AI 体系', 'ai_diet_plan / ai_report', '柔性关联'],
], [1.0, 2.7, 1.45], font_size=11.5, row_h=0.62, header_h=0.4)
add_text(s, 7.05, 5.05, 5.2, 0.9,
         '· food → nutrition 以 UNIQUE 约束实现 1:1\n'
         '· recipe.suitable_goals 标签支撑三专区推荐\n'
         '· numbers 数字辅助表：存储过程展开日期序列',
         size=11.5, color=GRAY, line_spacing=1.45)

# ================= P6 设计思路与热量引擎 =================
s = new_slide('设计思路与热量引擎', 'DESIGN & CALORIE ENGINE', 6)
add_text(s, 0.9, 1.42, 6, 0.35, '核心建模决策', size=14, bold=True, color=INK)
add_card(s, 0.9, 1.82, 5.7, 1.32, '食材 / 食谱分层建模',
         '同一食材不同做法热量差异大：food 存原生营养（1:1 nutrition），recipe 按配比组合（recipe_food M:N），菜品热量 = Σ 营养 × 克数',
         body_size=11.5, title_size=14)
add_card(s, 6.85, 1.82, 5.7, 1.32, '打卡主子表 + 触发器',
         '一餐多菜品：diet_record 存餐次与日期，明细存菜品与克数；明细增删由触发器自动汇总主表热量',
         body_size=11.5, title_size=14)
add_text(s, 0.9, 3.32, 6, 0.35, '设计亮点：个性化热量引擎', size=14, bold=True, color=INK)
add_arrow_chain(s, None, 3.7, [
    ('Mifflin-St Jeor', '性别/年龄/身高/体重 → BMR'),
    ('活动等级系数', '1.2 / 1.375 / 1.55 / 1.725 → TDEE'),
    ('BMI 中国标准分级', '偏瘦+300 · 正常-300 · 超重-500 · 肥胖-700'),
    ('安全下限', '男 ≥ 1500 · 女 ≥ 1200 kcal'),
], w=2.75, h=0.85, gap=0.3)
add_table(s, 0.9, 4.78, 11.55, [
    ['专区', '用户目标', '食谱筛选', '热量倾向', 'AI 方案侧重'],
    ['🥗 健康饮食', '维持身材', '所有适合的食谱', '维持或温和缺口', '食材多样化，均衡营养'],
    ['🔥 减肥专区', '减脂瘦身', '低卡高纤维食谱', '较大热量缺口', '控碳控油，高蛋白饱腹'],
    ['💪 健身专区', '增肌塑形', '高蛋白食谱', '热量盈余或维持', '高蛋白配比，增肌友好'],
], [1.7, 1.6, 2.7, 2.3, 3.25], font_size=12, row_h=0.42, header_h=0.4)
add_text(s, 0.9, 6.55, 11.5, 0.4,
         '胖瘦都适用：偏瘦人群不执行“减脂逻辑”，自动转为盈余增重 —— 同一引擎覆盖三类人群。',
         size=12.5, bold=True, color=ACCENT)

# ================= P7 技术亮点 =================
s = new_slide('技术亮点', 'STORED PROCEDURES · TRIGGERS · AI', 7)
add_text(s, 0.9, 1.42, 5.5, 0.35, '存储过程 · 业务下沉数据库', size=14, bold=True, color=INK)
add_table(s, 0.9, 1.82, 5.7, [
    ['存储过程', '作用'],
    ['sp_recommend_daily_cal', 'BMR → TDEE → BMI 分级 → 推荐热量'],
    ['sp_calc_recipe_calorie', '食材配比 → 菜品总热量'],
    ['sp_calc_user_period_summary', '周期汇总（周报数据源）'],
    ['sp_record_weight', '记录体重并同步 user 表'],
], [2.35, 3.35], font_size=11.5, row_h=0.56, header_h=0.4)
add_text(s, 6.85, 1.42, 5.5, 0.35, '触发器 · 数据一致性由库层保证', size=14, bold=True, color=INK)
add_table(s, 6.85, 1.82, 5.55, [
    ['触发器', '触发场景'],
    ['trg_detail_after_insert', '打卡明细新增 → 汇总主表热量'],
    ['trg_detail_after_delete', '打卡明细删除 → 重算主表热量'],
    ['trg_nutrition_after_update', '营养更新 → 级联刷新食谱热量'],
    ['trg_recipe_food_after_*', '配比变更 → 重算菜品热量'],
], [2.3, 3.25], font_size=11.5, row_h=0.56, header_h=0.4)
add_text(s, 0.9, 4.62, 6, 0.35, 'AI 集成：个性化方案生成闭环', size=14, bold=True, color=INK)
add_arrow_chain(s, None, 4.98, [
    ('用户画像', '专区 · 身体数据 · 禁忌'),
    ('DeepSeek 生成', '按专区侧重 · 禁忌过滤'),
    ('混合存储落库', 'AI原文 + recipe_id 列表'),
    ('前端展示', '结构化卡片 + 原文可查'),
], w=2.75, h=0.8, gap=0.3)
mix = [
    ('保留 AI 原文', 'plan_content 不丢推荐细节'),
    ('结构化关联', '三餐 + 加餐 recipe_id 列表'),
    ('模糊匹配兜底', '匹配不到不影响使用'),
]
for i, (t, d) in enumerate(mix):
    add_card(s, 0.9 + i * 4.1, 5.95, 3.75, 0.85, t, d,
             body_size=10.5, title_size=13)

# ================= P8 挑战与解决方案 =================
s = new_slide('挑战与解决方案', 'CHALLENGES & SOLUTIONS', 8)
add_table(s, 0.9, 1.85, 11.55, [
    ['挑战', '解决方案'],
    ['同一食材不同做法热量差异大', '食材 / 食谱分层建模，菜品热量按配比精确计算'],
    ['一餐多菜品，汇总易错', '打卡主子表 + 触发器自动汇总，删除也能保证正确'],
    ['胖瘦人群热量策略相反', 'BMI 生成列按中国标准分级：偏瘦盈余、肥胖大缺口'],
    ['AI 输出结构化信息易丢失', '混合存储：保留原文 + recipe_id 列表，模糊匹配兜底'],
], [3.6, 7.95], font_size=12.5, row_h=0.85, header_h=0.5)
add_text(s, 0.9, 6.35, 11.5, 0.4,
         '设计取舍：把可复用的计算与一致性保证下沉到数据库层，应用层保持简洁。',
         size=13.5, bold=True, color=MAIN)

# ================= P9 总结与致谢 =================
s = new_slide('总结与致谢', 'SUMMARY', 9)
for i, (t, d) in enumerate([
    ('完整的数据建模实践', '从业务场景到 20 张表、4 类关系，完成规范化设计与 ER 模型'),
    ('数据库高级特性落地', '生成列、触发器、存储过程真正服务于业务，而非“为加分而加分”'),
    ('全栈 + AI 集成能力', 'Vue 3 / Flask / MySQL 全链路打通，AI 方案落地为可用的业务闭环'),
]):
    add_card(s, 0.9, 1.55 + i * 1.5, 11.55, 1.3, f'收获 {i + 1}：{t}', d,
             body_size=13, title_size=15.5)
add_text(s, 0.9, 6.3, 11.5, 0.9,
         '以上是本次实验的全部汇报内容，感谢各位老师的聆听与指导，欢迎批评指正！',
         size=17, bold=True, color=MAIN, align=PP_ALIGN.CENTER)

out = os.path.join(BASE, os.environ.get('PPT_OUT', '答辩PPT-AI辅助减脂饮食管理系统.pptx'))
prs.save(out)
print('saved:', out)

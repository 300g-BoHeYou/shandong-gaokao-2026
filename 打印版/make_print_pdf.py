# -*- coding: utf-8 -*-
"""生成《2026 山东高考打印版》B5 黑白 PDF（reportlab 渲染，自带校验用 PNG 预览）。

用法:
    python make_print_pdf.py              # 只生成 PDF
    python make_print_pdf.py --preview    # 同时导出抽样页 PNG 到 ./预览/
"""
import io
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from print_pdf_core import (  # noqa: E402
    D, FM, Book, Item, mkline, wrap_spans, span_w, lead, fit_text,
    CONTENT_W, COL_GAP, CONTENT_TOP, CONTENT_BOT, CONTENT_H, PAGE_W, MARGIN_X, MM,
)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PDF = os.path.join(HERE, '2026山东高考打印版.pdf')
PREVIEW_DIR = os.path.join(HERE, '预览')

TITLE = '2026年山东高考投档数据与专业排名'

BIG_FEN = '第一部分　2026年一分一段表'
BIG_CAT = '第二部分　本科专业目录（2026年）'
BIG_RK = '第三部分　软科2026中国大学专业排名'
BIG_TD = '第四部分　2026年普通类常规批第一次投档表'

SEC_FEN = '2026年一分一段表'
SEC_CAT = '本科专业目录（2026年）'
SEC_RK = '软科2026中国大学专业排名'
SEC_TD = '2026年普通类常规批第一次投档表'

RK_TOP = 50                      # 软科每专业最多列出多少名

# 字号
TD_NAME = 7.6
TD_MAJOR = 7.0
TD_NUM = 7.4
RK_NAME = 8.4
RK_ITEM = 7.6
CAT_MEN = 10.5
CAT_LEI = 8.6
CAT_MAJ = 7.4

# 投档表表格列宽 (总宽 = 2 栏时的栏宽 76.5mm)
TD_COLW = (CONTENT_W - COL_GAP) / 2
TD_NAME_W = 56.5
TD_SCORE_W = 8.0
TD_RANK_W = 12.0
TD_PAD = 1.2                     # 单元格内左留白
TD_ROWPAD = 0.45                 # 行上下留白
assert abs(TD_NAME_W + TD_SCORE_W + TD_RANK_W - TD_COLW) < 0.01


def cell_abs(x_off, w, text, fk, size):
    """把 text 居中放在 [x_off, x_off+w] 单元格里"""
    tw = FM.width(fk, text, size)
    return (x_off + max(0.0, (w - tw) / 2.0), text, fk, size)


def fit_text(text, fk, size, maxw, min_size=5.4):
    """超宽时自动缩字号, 仍放不下则截断加省略号"""
    if FM.width(fk, text, size) <= maxw:
        return text, size
    sz = size
    while sz > min_size:
        sz = round(sz - 0.2, 2)
        if FM.width(fk, text, sz) <= maxw:
            return text, sz
    while text and FM.width(fk, text + '…', sz) > maxw:
        text = text[:-1]
    return text + '…', sz


# ============================================================
# 一、一分一段表（带框线, 每栏重复表头）
# ============================================================
FEN_COLW = (CONTENT_W - 5 * COL_GAP) / 6
FEN_C1, FEN_C2 = 5.9, 11.7          # 单元格边界 (mm)
FEN_FRAC = [FEN_C1 / FEN_COLW, FEN_C2 / FEN_COLW]
FEN_LEAD = lead(6.8, 1.38)
FEN_HLEAD = lead(6.8, 1.72)


def fen_cells(score, seg, cum, fk='song', size=6.8):
    return [
        cell_abs(0.0, FEN_C1, score, 'hei', size),
        cell_abs(FEN_C1, FEN_C2 - FEN_C1, seg, fk, size),
        cell_abs(FEN_C2, FEN_COLW - FEN_C2, cum, fk, size),
    ]


def fen_col_header():
    line = mkline([], abs_=[
        cell_abs(0.0, FEN_C1, '分数', 'hei', 6.8),
        cell_abs(FEN_C1, FEN_C2 - FEN_C1, '本段', 'hei', 6.8),
        cell_abs(FEN_C2, FEN_COLW - FEN_C2, '累计位次', 'hei', 6.4),
    ], leading=FEN_HLEAD)
    return {'lines': [line], 'box': FEN_FRAC}


def build_fen():
    items = []
    for i, (score, cum) in enumerate(D.FEN):
        seg = cum - (D.FEN[i - 1][1] if i > 0 else 0)
        items.append(Item([mkline([], leading=FEN_LEAD,
                                  abs_=fen_cells('%d' % score, '%d' % seg, '%d' % cum))],
                          keep=False, box=FEN_FRAC))
    return items


# ============================================================
# 二、本科专业目录（一行一个专业）
# ============================================================
def build_catalog():
    ct = json.load(open(os.path.join(os.path.dirname(HERE), 'scripts', 'catalog_tree.json'),
                        encoding='utf-8'))
    tree = ct['tree']
    colw = (CONTENT_W - 2 * COL_GAP) / 3
    items = []
    first = True
    for men in ct['men_order']:
        leis = tree.get(men)
        if not leis:
            continue
        if not first:
            items.append(Item([mkline([], leading=1.8)], keep=False))
        first = False
        n_maj = sum(len(v) for v in leis.values())
        items.append(Item([mkline([(men, 'hei', CAT_MEN)], leading=lead(CAT_MEN, 1.5))], keep=False))
        items.append(Item([mkline([('%d个专业类 / %d个专业' % (len(leis), n_maj), 'song', 6.6, )],
                                  leading=lead(6.6, 1.5))], keep=False))
        for lei, majors in leis.items():
            if not majors:
                continue
            items.append(Item([mkline([], leading=0.9)], keep=False))
            items.append(Item([mkline([(lei, 'hei', CAT_LEI), ('（%d）' % len(majors), 'song', 6.6)],
                                      indent=1.5, leading=lead(CAT_LEI, 1.4))], keep=False))
            for code, name in majors:
                items.append(Item([mkline([(code, 'song', 6.6, ), (' ', 'song', CAT_MAJ),
                                           (name, 'song', CAT_MAJ)],
                                          indent=3.5, leading=lead(CAT_MAJ, 1.36))], keep=False))
    return items


# ============================================================
# 三、软科排名（每专业最多 50 名，一行一条）
# ============================================================
def build_ruanke():
    RK, META, SD = D.RK, D.META, D.SD_SCHOOLS
    colw = (CONTENT_W - 2 * COL_GAP) / 3
    items = []
    shown = 0
    capped = 0
    for men in D.MEN_ORDER:
        leis = RK.get(men)
        if not leis:
            continue
        items.append(Item([mkline([], leading=2.2)], keep=False))
        items.append(Item([mkline([(men, 'hei', 10.5)], leading=lead(10.5, 1.5))], keep=False))
        for lei in D.LEI_ORDER:
            majs = leis.get(lei)
            if not majs:
                continue
            items.append(Item([mkline([(lei, 'hei', 8.6)], indent=1.5,
                                      leading=lead(8.6, 1.45))], keep=False))
            order = [k for k in D.LEI2MAJOR.get(lei, []) if k in majs]
            for k in majs:
                if k not in order:
                    order.append(k)
            for key in order:
                ranks = majs[key]
                meta = META.get(key, {})
                name = meta.get('name', key)
                code = key.split(' ', 1)[0]
                schools = sorted(((r, s) for s, r in ranks.items() if s in SD),
                                 key=lambda x: (x[0], x[1]))
                head = [(name, 'hei', RK_NAME)]
                if code and code != name:
                    head.append(('  %s' % code, 'song', 6.6))
                for sp in wrap_spans(head, colw - 3.0, indent=3.0, cont_indent=5.5):
                    items.append(Item([mkline(sp, indent=3.0, leading=lead(RK_NAME, 1.35))],
                                      keep=False))
                if key in D.SPECIAL:
                    sub = '特色专业（开设%d校，不排名）' % len(ranks)
                else:
                    sub = '上榜%d校' % meta.get('count', len(ranks))
                    if len(schools) != len(ranks):
                        sub += ' · 山东投档%d校' % len(schools)
                items.append(Item([mkline([(sub, 'song', 6.6)], indent=5.5,
                                          leading=lead(6.6, 1.4))], keep=False))
                if not schools:
                    items.append(Item([mkline([('（山东无投档院校上榜）', 'song', 6.8)], indent=6.5,
                                              leading=lead(6.8, 1.4))], keep=False))
                    continue
                use = schools[:RK_TOP]
                shown += len(use)
                if len(schools) > RK_TOP:
                    capped += 1
                for r, s in use:
                    rs = '%d' % r
                    nm, nsz = fit_text(s, 'song', RK_ITEM, colw - 13.5)
                    items.append(Item([mkline([], indent=6.5, leading=lead(RK_ITEM, 1.34), abs_=[
                        (6.5 + 6.2 - FM.width('song', rs, 6.9), rs, 'song', 6.9),
                        (6.5 + 7.0, nm, 'song', nsz),
                    ])], keep=False))
                if len(schools) > RK_TOP:
                    items.append(Item([mkline([('（仅列前%d名，其余%d所未列出）' % (RK_TOP, len(schools) - RK_TOP),
                                               'song', 6.5)], indent=6.5,
                                              leading=lead(6.5, 1.4))], keep=False))
    return items, shown, capped


# ============================================================
# 四、投档表（一行一条志愿类，带表格框线）
# ============================================================
def build_toudang():
    colw = TD_COLW
    frac = [TD_NAME_W / colw, (TD_NAME_W + TD_SCORE_W) / colw]
    name_max = TD_NAME_W - 1.2 - TD_PAD
    major_max = TD_NAME_W - 2.6 - TD_PAD
    MAJ_INDENT = 2.6
    rows = sorted(D.TD, key=lambda r: (r[6] if r[6] is not None else 10 ** 9, r[1]))
    items = []
    for r in rows:
        school, core, typ, rank, score = r[1], r[2], r[7], r[6], r[5]
        rks = D.sch(school)
        majors = D.row_majors(r)
        single = (len(majors) == 1 and D.key_name(majors[0]) == core)

        head = [(school, 'hei', TD_NAME, True), ('  ', 'song', TD_NAME)]
        core_txt = core
        if single:
            rk = D.rank_of(majors[0], rks)
            if rk:
                core_txt = '%s(#%d)' % (core, rk)
        head.append((core_txt, 'song', TD_NAME, True))
        if typ and typ != '普通':
            head.append(('  ', 'song', 6.4))
            head.append(('[%s]' % typ, 'song', 6.4, True))
        head_lines = wrap_spans(head, name_max)
        lead_h = lead(TD_NAME, 1.36)
        lines = [mkline(head_lines[0], indent=TD_PAD, leading=lead_h, abs_=[
            cell_abs(TD_NAME_W, TD_SCORE_W, '%d' % score, 'hei', TD_NUM),
            cell_abs(TD_NAME_W + TD_SCORE_W, TD_RANK_W, '%d' % rank, 'hei', TD_NUM),
        ])]
        for sp in head_lines[1:]:
            lines.append(mkline(sp, indent=TD_PAD, leading=lead_h))

        if not single:
            note = None
            syb = r[8]
            if not majors:
                if syb and syb.get('mode') == 'renxuan':
                    d = (syb.get('dir') or '').strip()
                    note = '（在本大类内任选：%s）' % d if d and d != '任选' else '（在本大类内任选）'
                elif syb and syb.get('mode') == 'notfound':
                    note = '（具体专业未公开，待查证）'
            elif r[9] is None and core in D.LEI2MAJOR:
                note = '（目录口径，未按该校实际开设筛减）'
            if note:
                lines.append(mkline([(note, 'song', 6.6)], indent=MAJ_INDENT, leading=lead(6.6, 1.34)))
            if majors:
                bs = []
                for mk in majors:
                    nm = D.key_name(mk)
                    rk = D.rank_of(mk, rks)
                    if bs:
                        bs.append(('   ', 'song', TD_MAJOR))
                    bs.append((nm + ('(#%d)' % rk if rk else ''), 'song', TD_MAJOR, True))
                for sp in wrap_spans(bs, major_max, indent=MAJ_INDENT):
                    lines.append(mkline(sp, indent=MAJ_INDENT, leading=lead(TD_MAJOR, 1.34)))

        height = 2 * TD_ROWPAD + sum(l['leading'] for l in lines)
        first_line = mkline([], leading=TD_ROWPAD)
        last_line = mkline([], leading=TD_ROWPAD)
        items.append(Item([first_line] + lines + [last_line], keep=True,
                          meta={'rank': rank}, box=frac))
    return items


# ============================================================
# 前置页: 标题页 / 目录 / 说明
# ============================================================
def draw_title_page(book):
    b = book
    size = 27.0
    while FM.width('hei', TITLE, size) > CONTENT_W - 6 and size > 16:
        size -= 0.5
    w = FM.width('hei', TITLE, size)
    b.text((PAGE_W - w) / 2.0, 92.0, TITLE, 'hei', size)
    b.line(MARGIN_X + 30, 106, PAGE_W - MARGIN_X - 30, 106, 1.0, 0.15)


TOC_SIZE = 11.0


def draw_toc(book, sections):
    b = book
    w = FM.width('hei', '目    录', 15)
    b.text((PAGE_W - w) / 2.0, 24, '目    录', 'hei', 15)
    y = 52.0
    for title, pg in [('标题页', 1), ('目录', 2), ('说明', 3)] + list(sections):
        b.text(MARGIN_X + 6, y, title, 'hei', TOC_SIZE)
        s = str(pg)
        b.text(PAGE_W - MARGIN_X - 6 - FM.width('hei', s, TOC_SIZE), y, s, 'hei', TOC_SIZE)
        y += 11.0


NOTICE = [
    ('本册内容', 'hei', 10.5),
    ('① 2026年一分一段表（分数与位次换算，含本段人数）', 'song', 8.2),
    ('② 《普通高等学校本科专业目录（2026年）》三级结构：门类 → 专业类 → 专业', 'song', 8.2),
    ('③ 软科2026中国大学专业排名（每个专业最多列前50名）', 'song', 8.2),
    ('④ 2026年山东省普通类常规批第一次志愿投档表（全部23,853个志愿类）', 'song', 8.2),
    ('', 'song', 4.5),
    ('数据来源与口径', 'hei', 10.5),
    ('· 投档表：山东省2026年普通类常规批第1次志愿投档表，共 23,853 个志愿类，含最低分与最低位次。', 'song', 7.8),
    ('· 软科排名：软科2026中国大学专业排名，发布 838 个专业，仅上榜全国前 50% 的院校；开设院校少于 4 所的', 'song', 7.8),
    ('   专业列为「特色专业」，只公布开设名单、不计算名次。', 'song', 7.8),
    ('· 一分一段表：2026年山东省高考一分一段表，「本段」人数由相邻累计位次相减得出。', 'song', 7.8),
    ('· 专业目录：《普通高等学校本科专业目录（2026年）》，14个学科门类 / 93个专业类 / 883个专业。', 'song', 7.8),
    ('· 括号中的名次为该校该专业在软科2026的全国排名，例如「理论与应用力学(#12)」；软科未上榜、', 'song', 7.8),
    ('   特色专业或该校未被软科收录时，不标注任何内容。', 'song', 7.8),
    ('', 'song', 4.5),
    ('阅读说明', 'hei', 10.5),
    ('· 投档表按最低位次升序排列，每个志愿类占表格一行（带框线），上行为院校与专业类，下行为该专业类', 'song', 7.8),
    ('   实际开设的具体专业及其软科排名；仅以具体专业招生的志愿类，名次直接标在专业名后。', 'song', 7.8),
    ('· 投档表每页页眉标出该页的位次范围，可按分数/位次直接翻查。表格最右两列依次为最低分、最低位次。', 'song', 7.8),
    ('· 招生类型为特殊计划时，在专业类名后以「[中外合作办学]」等形式标出；普通类不另标注。', 'song', 7.8),
    ('· 选科要求未收录于本册，请以山东省教育招生考试院及各院校当年公布信息为准。', 'song', 7.8),
    ('', 'song', 4.5),
    ('免责声明', 'hei', 10.5),
    ('· 本册基于 2026 年录取数据整理，仅供 2027 届考生了解院校、专业层级与分数/位次量级，不构成填报建议，', 'song', 7.8),
    ('   亦不是对 2027 年的预测。位次每年随考生人数与招生计划变化。', 'song', 7.8),
    ('· 大类/试验班的包含专业为推断或人工查证口径，可能与院校实际招生专业不完全一致，务必以院校当年招生', 'song', 7.8),
    ('   简章为准。', 'song', 7.8),
]


def draw_notice(book):
    b = book
    b.text(MARGIN_X, 24.0, '说　明', 'hei', 15)
    b.line(MARGIN_X, 36.0, PAGE_W - MARGIN_X, 36.0, 0.9, 0.15)
    y = 44.0
    for s, fk, size in NOTICE:
        if s:
            b.text(MARGIN_X + 2, y, s, fk, size)
        y += size * 25.4 / 72.0 * 1.62


# ============================================================
# 主流程
# ============================================================
def main():
    t0 = time.time()
    print('构建各章节 ...', flush=True)
    it_fen = build_fen()
    it_cat = build_catalog()
    it_rk, rk_shown, rk_capped = build_ruanke()
    print('  软科: 列出名次 %d 条，其中 %d 个专业超过前%d名已加备注' % (rk_shown, rk_capped, RK_TOP), flush=True)
    it_td = build_toudang()
    print('  投档表: %d 个志愿类' % len(it_td), flush=True)

    sections = [
        (SEC_FEN, 6, BIG_FEN, it_fen, fen_col_header()),
        (SEC_CAT, 3, BIG_CAT, it_cat, None),
        (SEC_RK, 3, BIG_RK, it_rk, None),
        (SEC_TD, 2, BIG_TD, it_td, None),
    ]

    # 第一遍: 只分页, 得到目录页码
    print('预排分页 ...', flush=True)
    dummy = Book(path=None)
    for _ in range(3):                    # 标题页 / 目录 / 说明
        dummy.new_page()
    for title, ncols, big, items, ch in sections:
        dummy.start_section(title, ncols, big=big, col_header=ch)
        for it in items:
            dummy.place_item(it)
    total = dummy.finish()

    toc_items = [(t, dummy.section_start[t]) for t, _, _, _, _ in sections]
    print('总页数 %d' % total, flush=True)
    for t, p in toc_items:
        print('   %s -> P%d' % (t, p), flush=True)

    previews = set()
    if '--preview' in sys.argv:
        previews = {1, 2, 3, 4}
        previews |= {p for _, p in toc_items}
        previews |= {p + 1 for _, p in toc_items}
        previews.add(total)

    print('生成 PDF ...', flush=True)
    book = Book(path=OUT_PDF, previews=previews, preview_dir=PREVIEW_DIR)
    book.new_page()
    draw_title_page(book)
    book.new_page()
    draw_toc(book, toc_items)
    book.new_page()
    draw_notice(book)
    for title, ncols, big, items, ch in sections:
        book.start_section(title, ncols, big=big, col_header=ch)
        for it in items:
            book.place_item(it)
    n = book.finish()
    assert n == total, '页数不一致: %d vs %d' % (n, total)
    print('完成: %s  (%d 页, %.1f 秒)' % (OUT_PDF, n, time.time() - t0), flush=True)


if __name__ == '__main__':
    main()

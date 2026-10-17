# -*- coding: utf-8 -*-
"""B5 打印版 PDF 排版引擎。

输出用 reportlab 绘制矢量 PDF；同一套绘制指令可再用 matplotlib 渲染成 PNG 供人工核对。
分页由本模块自己按精确字形宽度计算，因此不会出现截断或溢出。
"""
import io
import json
import math
import os
import re

from fontTools.ttLib import TTFont
from reportlab.pdfgen import canvas as rl_canvas

MM = 72.0 / 25.4                      # mm -> pt

# ---------------- 页面几何 (mm) ----------------
PAGE_W, PAGE_H = 176.0, 250.0         # B5
MARGIN_X = 9.0
HEADER_Y = 7.5
CONTENT_TOP = 17.0
CONTENT_BOT = 237.5
FOOTER_Y = 241.5
COL_GAP = 5.0
CONTENT_W = PAGE_W - 2 * MARGIN_X
CONTENT_H = CONTENT_BOT - CONTENT_TOP

FONT_FILES = {
    'song': (r'C:\Windows\Fonts\simsun.ttc', 0),
    'hei': (r'C:\Windows\Fonts\simhei.ttf', None),
}
RL_FONT = {'song': 'SimSun', 'hei': 'SimHei'}
BACKEND_BASE = os.path.dirname(os.path.abspath(__file__))


def lead(size, k=1.34):
    """由字号(pt)得到行高(mm)"""
    return size * 25.4 / 72.0 * k


# ---------------- 字形宽度 ----------------
class Metrics(object):
    def __init__(self):
        self.fp = {}
        self.w = {}
        self.upm = {}
        for k, (path, idx) in FONT_FILES.items():
            tt = TTFont(path, fontNumber=idx, lazy=True) if idx is not None else TTFont(path, lazy=True)
            upm = tt['head'].unitsPerEm
            cmap = tt.getBestCmap()
            hmtx = tt['hmtx']
            d = {}
            for code, gname in cmap.items():
                try:
                    d[code] = hmtx[gname][0]
                except Exception:
                    pass
            self.w[k] = d
            self.upm[k] = upm
            tt.close()

    def ch(self, fk, c):
        d = self.w[fk]
        v = d.get(ord(c))
        if v is None:
            v = d.get(ord('?'), self.upm[fk] * 0.5)
        return v / float(self.upm[fk])

    def width(self, fk, text, size):
        """文本宽度, mm"""
        return sum(self.ch(fk, c) for c in text) * size * 25.4 / 72.0


FM = Metrics()


def register_fonts():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont as RLTTFont
    for k, (path, idx) in FONT_FILES.items():
        if idx is not None:
            f = RLTTFont(RL_FONT[k], path, subfontIndex=idx)
        else:
            f = RLTTFont(RL_FONT[k], path)
        pdfmetrics.registerFont(f)


# ---------------- 折行 ----------------
ASCII_RUN = re.compile(r'[0-9A-Za-z#()./%+\-]+')
_CJK = re.compile(r'[\u2e80-\u9fff\u3000-\u303f\uff00-\uffef]')
NO_START = set('，。、；：）】》”’！？…,.;:)]}')


def tokenize(text):
    out = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == '[' and ']' in text[i:]:
            j = text.index(']', i)
            if j - i <= 14:
                out.append(text[i:j + 1])
                i = j + 1
                continue
        if _CJK.match(c):
            out.append(c)
            i += 1
        elif ASCII_RUN.match(c):
            m = ASCII_RUN.match(text, i)
            out.append(m.group(0))
            i = m.end()
        else:
            out.append(c)
            i += 1
    return out


def wrap_spans(spans, maxw, indent=0.0, cont_indent=None):
    """把 [(text,fontkey,size[,atomic])] 折行到宽度 maxw(mm)。返回 [[片段,...], ...]"""
    if cont_indent is None:
        cont_indent = indent
    avail_min = maxw - max(indent, cont_indent)
    flat = []
    for sp in spans:
        text, fk, size = sp[0], sp[1], sp[2]
        atomic = len(sp) > 3 and sp[3]
        if atomic and FM.width(fk, text, size) <= avail_min:
            flat.append((text, fk, size))
        else:
            for tok in tokenize(text):
                flat.append((tok, fk, size))
    merged = []
    for tok, fk, size in flat:
        if merged and tok and tok[0] in NO_START:
            pt, pf, ps = merged[-1]
            merged[-1] = (pt + tok, pf, ps)
        else:
            merged.append((tok, fk, size))

    lines = []
    cur = []
    curw = 0.0
    first = True

    def base():
        return indent if first else cont_indent

    for tok, fk, size in merged:
        if not cur and tok.strip() == '':
            continue
        tw = FM.width(fk, tok, size)
        if cur and curw + tw > maxw - base() + 1e-6:
            lines.append(cur)
            cur = []
            curw = 0.0
            first = False
        cur.append((tok, fk, size))
        curw += tw
    if cur:
        lines.append(cur)
    return lines or [[]]


def span_w(spans):
    return sum(FM.width(sp[1], sp[0], sp[2]) for sp in spans)


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


def mkline(spans, indent=0.0, leading=None, right=None, abs_=None):
    sz = max([sp[2] for sp in spans] + ([sp[2] for sp in right] if right else []) + [0])
    return {'spans': spans, 'indent': indent, 'right': right,
            'leading': leading if leading else lead(sz), 'abs': abs_ or []}


class Item(object):
    __slots__ = ('lines', 'keep', 'meta', 'box')

    def __init__(self, lines, keep=True, meta=None, box=None):
        self.lines = lines
        self.keep = keep
        self.meta = meta or {}
        self.box = box          # None, 或 [列分隔线位置(占栏宽比例)]


# ---------------- 书本 ----------------
class Book(object):
    def __init__(self, path=None, previews=None, preview_dir=None):
        self.dry = path is None
        self.path = path
        self.c = None
        if not self.dry:
            register_fonts()
            self.c = rl_canvas.Canvas(path, pagesize=(PAGE_W * MM, PAGE_H * MM))
            self.c.setTitle('2026山东高考打印版')
        self.previews = set(previews or [])
        self.preview_dir = preview_dir
        self.ops = []
        self.page_no = 0
        self.section = ''
        self.ncols = 3
        self.colw = 0
        self.col = 0
        self.y = CONTENT_TOP
        self.content_top = CONTENT_TOP
        self.col_header = None       # {'lines': [...], 'box': [...]} 每栏顶部重复的表头
        self.pending_big = None
        self.first_meta = None
        self.last_meta = None
        self.section_start = {}
        self.page_first = {}
        self.page_last = {}
        self._layout()

    def _layout(self):
        self.colw = (CONTENT_W - (self.ncols - 1) * COL_GAP) / self.ncols

    def col_x(self, i):
        return MARGIN_X + i * (self.colw + COL_GAP)

    # ---- 绘制指令 ----
    def text(self, x, y_top, s, fk, size, gray=0.0):
        if s and not self.dry:
            self.ops.append(('T', x, y_top, s, fk, size, gray))

    def line(self, x1, y1, x2, y2, w=0.3, gray=0.45):
        if not self.dry:
            self.ops.append(('L', x1, y1, x2, y2, w, gray))

    def rect(self, x, y, w, h, lw=0.3, gray=0.45):
        if not self.dry:
            self.ops.append(('R', x, y, w, h, lw, gray))

    # ---- 页面 ----
    def start_section(self, title, ncols, big=None, col_header=None):
        self.ncols = ncols
        self._layout()
        self.col_header = col_header
        self.pending_big = big
        self.new_page(title)
        self.section_start.setdefault(title, self.page_no)

    def new_page(self, section=None):
        self.flush_page()
        if section is not None:
            self.section = section
        self.page_no += 1
        self.col = 0
        self.content_top = CONTENT_TOP
        self.first_meta = None
        self.last_meta = None
        self.ops = []
        if not self.pending_big:
            self.draw_header()
        self.draw_footer()
        if self.pending_big:
            self.draw_big_title(self.pending_big)
            self.pending_big = None
        self._reset_column()

    def draw_big_title(self, s):
        s, _sz = fit_text(s, 'hei', 18.0, CONTENT_W, 13.0)
        self.text(MARGIN_X, CONTENT_TOP, s, 'hei', _sz)
        y = CONTENT_TOP + 12.6
        self.line(MARGIN_X, y, PAGE_W - MARGIN_X, y, 0.9, 0.15)
        self.content_top = CONTENT_TOP + 16.5

    def _reset_column(self):
        self.y = self.content_top
        self.draw_col_header()

    def draw_col_header(self):
        if not self.col_header or self.page_no <= 3:
            return
        x = self.col_x(self.col)
        y0 = self.y
        for ln in self.col_header['lines']:
            self.draw_line(ln, x, self.y)
            self.y += ln['leading']
        box = self.col_header.get('box')
        if box is not None:
            self.rect(x, y0, self.colw, self.y - y0, 0.35, 0.4)
            for frac in box:
                xs = x + self.colw * frac
                self.line(xs, y0, xs, self.y, 0.35, 0.4)

    def flush_page(self):
        if self.dry or self.page_no == 0:
            self.ops = []
            return
        self.draw_header_meta()
        if self.page_no in self.previews:
            self.render_png(self.page_no)
        self.render_pdf_page()
        self.ops = []

    def finish(self):
        self.flush_page()
        if not self.dry:
            self.c.save()
        return self.page_no

    def draw_header(self):
        if self.page_no <= 3:
            return
        self.line(MARGIN_X, HEADER_Y + 4.0, PAGE_W - MARGIN_X, HEADER_Y + 4.0, 0.5, 0.3)
        self.text(MARGIN_X, HEADER_Y, self.section, 'hei', 9.0)

    def draw_header_meta(self):
        if self.page_no <= 3 or self.first_meta is None:
            return
        s = '本页位次 %s ~ %s' % (self.first_meta, self.last_meta)
        w = FM.width('song', s, 7.0)
        self.text(PAGE_W - MARGIN_X - w, HEADER_Y + 0.8, s, 'song', 7.0)

    def draw_footer(self):
        if self.page_no <= 1:
            return
        s = '— %d —' % self.page_no
        w = FM.width('song', s, 7.5)
        self.text((PAGE_W - w) / 2.0, FOOTER_Y, s, 'song', 7.5)

    # ---- 排版 ----
    def place_item(self, item):
        lines = item.lines
        if item.keep:
            tot = sum(l['leading'] for l in lines)
            if self.y + tot > CONTENT_BOT + 1e-6 and self.y > self.content_top + 1e-6:
                self.next_col()
        if not lines:
            return
        # 首行可能因放不下而换栏; 必须在换栏之后再记录框线的起点, 否则新栏首行会丢框
        if self.y + lines[0]['leading'] > CONTENT_BOT + 1e-6:
            self.next_col()
        col0 = self.col
        y0 = self.y
        for i, ln in enumerate(lines):
            if i > 0 and self.y + ln['leading'] > CONTENT_BOT + 1e-6:
                self.next_col()
            self.draw_line(ln, self.col_x(self.col), self.y)
            self.y += ln['leading']
        if item.box is not None and self.col == col0:
            x = self.col_x(col0)
            self.rect(x, y0, self.colw, self.y - y0, 0.35, 0.4)
            for frac in item.box:
                xs = x + self.colw * frac
                self.line(xs, y0, xs, self.y, 0.35, 0.4)
        m = item.meta.get('rank')
        if m is not None:
            if self.first_meta is None:
                self.first_meta = m
            self.last_meta = m

    def draw_line(self, ln, x, y):
        cx = x + ln['indent']
        for sp in ln['spans']:
            t, fk, s = sp[0], sp[1], sp[2]
            if t:
                self.text(cx, y, t, fk, s)
                cx += FM.width(fk, t, s)
        for pos, t, fk, s in ln.get('abs', []):
            if t:
                self.text(x + pos, y, t, fk, s)
        if ln['right']:
            rw = span_w(ln['right'])
            rx = x + self.colw - rw
            for t, fk, s in ln['right']:
                if t:
                    self.text(rx, y, t, fk, s)
                    rx += FM.width(fk, t, s)

    def next_col(self):
        if self.col + 1 < self.ncols:
            self.col += 1
            self.y = self.content_top
            self.draw_col_header()
        else:
            self.new_page()

    # ---- 输出 ----
    def render_pdf_page(self):
        c = self.c
        for op in self.ops:
            if op[0] == 'T':
                _, x, y, s, fk, size, g = op
                size_mm = size * 25.4 / 72.0
                c.setFont(RL_FONT[fk], size)
                c.setFillGray(g)
                c.drawString(x * MM, (PAGE_H - (y + 0.86 * size_mm)) * MM, s)
            elif op[0] == 'L':
                _, x1, y1, x2, y2, w, g = op
                c.setStrokeGray(g)
                c.setLineWidth(w)
                c.line(x1 * MM, (PAGE_H - y1) * MM, x2 * MM, (PAGE_H - y2) * MM)
            elif op[0] == 'R':
                _, x, y, w, h, lw, g = op
                c.setStrokeGray(g)
                c.setLineWidth(lw)
                c.rect(x * MM, (PAGE_H - (y + h)) * MM, w * MM, h * MM, stroke=1, fill=0)
        c.showPage()

    def render_png(self, page_no):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.font_manager import FontProperties
        fps = {k: FontProperties(fname=v[0]) for k, v in FONT_FILES.items()}
        fig = plt.figure(figsize=(PAGE_W / 25.4, PAGE_H / 25.4))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, PAGE_W)
        ax.set_ylim(PAGE_H, 0)
        ax.axis('off')
        for op in self.ops:
            if op[0] == 'T':
                _, x, y, s, fk, size, g = op
                ax.text(x, y, s, fontproperties=fps[fk], fontsize=size, va='top', ha='left',
                        color=str(g))
            elif op[0] == 'L':
                _, x1, y1, x2, y2, w, g = op
                ax.plot([x1, x2], [y1, y2], color=str(g), linewidth=w)
            elif op[0] == 'R':
                _, x, y, w, h, lw, g = op
                ax.add_patch(plt.Rectangle((x, y), w, h, fill=False, edgecolor=str(g),
                                           linewidth=lw))
        d = self.preview_dir or '.'
        os.makedirs(d, exist_ok=True)
        fig.savefig(os.path.join(d, 'p%03d.png' % page_no), dpi=170)
        plt.close(fig)


# ---------------- 数据 ----------------
def _find_base():
    for cand in (BACKEND_BASE, os.path.dirname(BACKEND_BASE)):
        if os.path.exists(os.path.join(cand, 'data_toudang.js')):
            return cand
    return os.path.dirname(BACKEND_BASE)


BASE = _find_base()


def load_js(fn, var):
    s = io.open(os.path.join(BASE, fn), encoding='utf-8').read()
    m = re.search(r'window\.' + var + r'\s*=\s*(.*?);\s*(?:/\*|window\.|$)', s, re.S)
    return json.loads(m.group(1))


class Data(object):
    def __init__(self):
        self.TD = load_js('data_toudang.js', 'TD2026')
        self.SCHOOL_RK = load_js('data_toudang.js', 'TD_SCHOOL_RK')
        self.RK = load_js('data_ruanke.js', 'RK2026')
        self.META = load_js('data_ruanke.js', 'RK_META')
        self.LEI2MAJOR = load_js('data_ruanke.js', 'RK_LEI2MAJOR')
        self.MEN_ORDER = load_js('data_ruanke.js', 'RK_MEN_ORDER')
        self.LEI_ORDER = load_js('data_ruanke.js', 'RK_LEI_ORDER')
        self.SPECIAL = load_js('data_ruanke.js', 'RK_SPECIAL')
        self.FEN = load_js('data_fen.js', 'FEN2026')
        self.KEY2NAME = {k: v['name'] for k, v in self.META.items()}
        self.NAME2KEY = {}
        for k, v in self.META.items():
            self.NAME2KEY.setdefault(v['name'], k)
        self.SD_SCHOOLS = set(v for v in self.SCHOOL_RK.values() if v)
        self._sc = {}

    def sch(self, name):
        if name not in self._sc:
            self._sc[name] = self.SCHOOL_RK.get(name, '')
        return self._sc[name]

    def rank_of(self, key, rk_school):
        if key in self.SPECIAL or not rk_school:
            return None
        meta = self.META.get(key)
        if not meta:
            return None
        rks = self.RK.get(meta['men'], {}).get(meta['lei'], {}).get(key)
        if not rks:
            return None
        return rks.get(rk_school)

    def contained(self, core):
        if core in self.LEI2MAJOR:
            return list(self.LEI2MAJOR[core])
        if '试验班' in core or '实验班' in core:
            return []
        if core in self.NAME2KEY:
            return [self.NAME2KEY[core]]
        return [core]

    def row_majors(self, r):
        if r[9]:
            return r[9]
        keys = self.contained(r[2])
        if keys:
            return keys
        syb = r[8]
        if syb and syb.get('mode') == 'list':
            return [self.NAME2KEY.get(n, n) for n in syb['majors']]
        return []

    def key_name(self, key):
        return self.KEY2NAME.get(key, key.split(' ', 1)[-1] if ' ' in key else key)


D = Data()

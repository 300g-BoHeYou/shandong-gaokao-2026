# -*- coding: utf-8 -*-
"""排版自检: 逐行核对是否有文字越过栏边界。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_print_pdf as M
from print_pdf_core import Book, FM, MARGIN_X, CONTENT_W, PAGE_W, CONTENT_TOP, CONTENT_BOT


class QABook(Book):
    def __init__(self):
        Book.__init__(self, path=None)
        self.bad = []
        self.max_over = 0.0
        self.nlines = 0
        self.sec = ''

    def start_section(self, title, ncols, big=None, col_header=None):
        self.sec = title
        Book.start_section(self, title, ncols, big=big, col_header=col_header)

    def draw_line(self, ln, x, y):
        right_edge = x + self.colw
        cx = x + ln['indent']
        for sp in ln['spans']:
            t, fk, s = sp[0], sp[1], sp[2]
            if t:
                w = FM.width(fk, t, s)
                self.nlines += 1
                over = (cx + w) - right_edge
                if over > 0.05 or cx < MARGIN_X - 0.05 or (cx + w) > (PAGE_W - MARGIN_X + 0.05):
                    self.bad.append('[%s] p? 越界 %.2fmm: %r' % (self.sec, over, t[:30]))
                self.max_over = max(self.max_over, over)
                cx += w
        for pos, t, fk, s in ln.get('abs', []):
            if t:
                w = FM.width(fk, t, s)
                self.nlines += 1
                if x + pos + w > right_edge + 0.05:
                    self.bad.append('[%s] abs 越界: %r' % (self.sec, t[:30]))
                self.max_over = max(self.max_over, x + pos + w - right_edge)
        if ln['right']:
            for t, fk, s in ln['right']:
                if t:
                    self.nlines += 1


def main():
    print('构建 ...', flush=True)
    sections = [
        (M.SEC_FEN, 6, M.BIG_FEN, M.build_fen(), M.fen_col_header()),
        (M.SEC_CAT, 3, M.BIG_CAT, M.build_catalog(), None),
        (M.SEC_RK, 3, M.BIG_RK, M.build_ruanke()[0], None),
        (M.SEC_TD, 2, M.BIG_TD, M.build_toudang(), None),
    ]
    b = QABook()
    for _ in range(3):
        b.new_page()
    for title, ncols, big, items, ch in sections:
        b.start_section(title, ncols, big=big, col_header=ch)
        for it in items:
            b.place_item(it)
    total = b.finish()
    out = ['总页数 %d' % total,
           '文本片段 %d, 越界 %d, 最大越界 %.3fmm' % (b.nlines, len(b.bad), b.max_over)]
    out += b.bad[:40]
    print('\n'.join(out))
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qa.txt'), 'w',
         encoding='utf-8').write('\n'.join(out))


if __name__ == '__main__':
    main()

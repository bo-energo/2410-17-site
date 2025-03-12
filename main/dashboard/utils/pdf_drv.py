import logging
from fpdf import FPDF

from main.settings import STATIC_ROOT


logger = logging.getLogger(__name__)


class PDF(FPDF):
    koeff_unit = {
        'pt': 1,
        'mm': 72/25.4,
        'cm': 72/2.54,
        'in': 72.
    }

    def add_my_fonts(self):
        self.add_font(
            'NotoSerif', '',
            STATIC_ROOT.joinpath('fonts').joinpath('NotoSerif-Regular.ttf'), uni=True
        )
        self.add_font(
            'NotoSerif', 'B',
            STATIC_ROOT.joinpath('fonts').joinpath('NotoSerif-Bold.ttf'), uni=True
        )
        self.add_font(
            'NotoSerif', 'I',
            STATIC_ROOT.joinpath('fonts').joinpath('NotoSerif-Italic.ttf'), uni=True
        )
        self.add_font(
            'NotoSans', '',
            STATIC_ROOT.joinpath('fonts').joinpath('NotoSans-Regular.ttf'), uni=True
        )
        self.add_font(
            'NotoSans', 'B',
            STATIC_ROOT.joinpath('fonts').joinpath('NotoSans-Bold.ttf'), uni=True
        )
        self.add_font(
            'NotoSans', 'I',
            STATIC_ROOT.joinpath('fonts').joinpath('NotoSans-Italic.ttf'), uni=True
        )

    def text_min_h_in_mm(self):
        self.font_size

    def set_header(self, header_list: list):
        self.header_list = header_list


class DataExportPdf(PDF):
    def footer(self):
        # Go to 1.5 cm from bottom
        self.set_y(-15)
        # Select font
        footer_font_size = (self.font_size * self.k) - 2
        self.set_font(self.font_family, 'I', footer_font_size)
        # Print centered page number
        self.cell(0, 10, f'{self.page_no()}', 0, 0, 'C')

    def header(self):
        for line in self.header_list:
            # Set line header params
            words = line.get('data', '')
            w_cell = line.get('w', 0)
            h_cell = line.get('h', self.font_size)
            style = line.get('style', '')
            if style not in ('B', 'I', 'BI',):
                style = ''
            align = line.get('align', 'L')
            if align not in ('C', 'R'):
                align = 'L'
            border = line.get('border', 0)
            if isinstance(border, int) and border not in (0, 1):
                border = 0
            # Set font params
            self.set_font('', style,)
            # Print line header
            if type(words) in (tuple, list, set):
                with self.table() as table:
                    row = table.row()
                    for word in words:
                        row.cell(word)
            else:
                self.multi_cell(w_cell, h_cell, words, border, align=align)
            self.ln(h_cell)

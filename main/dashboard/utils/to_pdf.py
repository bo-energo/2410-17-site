import logging
from fpdf import Align
from fpdf.fonts import FontFace
from tablib import Dataset

from .pdf_drv import DataExportPdf


logger = logging.getLogger(__name__)


def create_signal_value_file(data: Dataset, name: str):
    font_size = 12
    margin_p = {'l': 25, 'r': 15, 't': 10}
    a4_page = {"w": 210, "h": 297}
    pdf = DataExportPdf()
    pdf.add_my_fonts()
    pdf.set_font("NotoSerif", "", font_size)
    pdf.set_margins(left=margin_p["l"], top=margin_p["t"], right=margin_p["r"])
    work_h = a4_page["w"] - margin_p["l"] - margin_p["r"]
    header_page = [
            {
                'data': name.split('.')[0],
                'style': 'I',
                'align': 'L',
                'border': 0
            },
        ]
    pdf.set_header(header_page)

    col1_width = pdf.get_string_width("2222-22-22 22_22_22") + 6
    col2_width = pdf.get_string_width("222222.22") + 6
    col_widths = [col1_width]
    col_widths.extend((col2_width,)*(len(data.headers) - 1))
    number_values_columns = int((work_h - col1_width) // col2_width)
    slice_a = 1
    slice_b = slice_a + number_values_columns
    while slice_a < len(data.headers):
        pdf.add_page()
        part_col_widths = col_widths[:1]
        part_col_widths.extend(col_widths[slice_a:slice_b])
        table_width = sum(part_col_widths)
        with pdf.table(width=table_width, col_widths=part_col_widths, align="L") as table:
            row = table.row()
            row.cell(data.headers[0])
            for cell_data in data.headers[slice_a:slice_b]:
                row.cell(cell_data)
            for line in data:
                row = table.row()
                row.cell(line[0])
                for cell_data in line[slice_a:slice_b]:
                    row.cell(cell_data)
        slice_a = slice_b
        slice_b += number_values_columns

    formatting_data = pdf.output(dest='S')
    return formatting_data


def create_diag_message_file(data: Dataset, name: str):
    font_size = 10
    margin_p = {'l': 25, 'r': 15, 't': 10}
    a4_page = {"w": 210, "h": 297}
    pdf = DataExportPdf()
    pdf.add_my_fonts()
    pdf.set_font("NotoSerif", "", font_size)
    pdf.set_margins(left=margin_p["l"], top=margin_p["t"], right=margin_p["r"])
    work_h = a4_page["w"] - margin_p["l"] - margin_p["r"]
    header_page = [
            {
                'data': name.split('.')[0],
                'style': 'I',
                'align': 'L',
                'border': 0
            },
        ]
    pdf.set_header(header_page)

    col1_width = pdf.get_string_width("2222-22-22 22_22_22") + 6
    col2_width = pdf.get_string_width("Оборудование    ") + 3
    col4_width = pdf.get_string_width("Критичность") + 3
    col3_width = work_h - col1_width - col2_width - col4_width
    col_widths = [col1_width, col2_width, col3_width, col4_width]
    pdf.add_page()
    table_width = sum(col_widths)
    l_height = pdf.font_size + 1
    with pdf.table(width=table_width, col_widths=col_widths, line_height=l_height, align="L") as table:
        row = table.row()
        for cell_data in data.headers:
            row.cell(cell_data)
        for line in data:
            row = table.row()
            for cell_data in line:
                row.cell(str(cell_data))

    formatting_data = pdf.output(dest='S')
    return formatting_data


def create_diag_config_data_file(data: dict, name: str):
    title_key = "title"
    title_page_data_key = "title_page"
    font_size = 10
    margin_p = {'l': 25, 'r': 15, 't': 10}
    a4_page = {"w": 210, "h": 297}
    pdf = DataExportPdf()
    pdf.add_my_fonts()
    pdf.set_text_color(0, 50, 116)
    pdf.set_font("NotoSerif", "", font_size)
    pdf.set_margins(left=margin_p["l"], top=margin_p["t"], right=margin_p["r"])
    work_h = a4_page["w"] - margin_p["l"] - margin_p["r"]
    pdf.set_header([])
    face_bold_cell = FontFace(emphasis="BOLD")
    pdf.add_page()

    pdf.set_font(None, "B", 14)
    pdf.cell(
        0, pdf.font_size, data.get(title_key, ""), align=Align.C, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(None, "", font_size)
    pdf.ln(pdf.font_size)

    l_height = pdf.font_size + 1

    title_page_data: list[dict] = data.get(title_page_data_key, [])
    for line in title_page_data:
        param_name = f"{line.get('name', '')}: "
        value = line.get("value", "")

        col1_width = pdf.get_string_width(param_name) + 3
        col2_width = work_h - col1_width - 10
        col_widths = [col1_width, col2_width]

        with pdf.table(
                width=sum(col_widths), col_widths=col_widths, line_height=l_height, align="L",
                first_row_as_headings=False, borders_layout="NONE") as table:
            row = table.row()
            row.cell(param_name, padding=(2, 0), style=face_bold_cell)
            row.cell(str(value), padding=(2, 0))

    col2_width = pdf.get_string_width("Очень длинное значение параметра") + 3
    col1_width = work_h - col2_width - 20
    col_widths = [col1_width, col2_width]
    cats_data: list[dict] = data.get("categories", [])
    if not isinstance(cats_data, (list, tuple)):
        return None

    pdf.set_draw_color(179, 208, 235)
    for table_data in cats_data:
        pdf.ln(pdf.font_size)
        pdf.ln(pdf.font_size)
        table_name = table_data.get("title")
        values = table_data.get("values")
        with pdf.table(
                width=sum(col_widths), col_widths=col_widths,
                line_height=l_height, align="C", text_align="C") as table:
            row = table.row()
            row.cell(table_name, colspan=2, align=Align.C, border="BOTTOM", padding=(4, 0))
            for line in values:
                row = table.row()
                param_name = [str(line.get("signal"))]
                if unit := line.get("unit"):
                    param_name.append(unit)
                row.cell(", ".join(param_name))
                row.cell(str(line.get('value')))

    formatting_data = pdf.output(dest='S')
    return formatting_data

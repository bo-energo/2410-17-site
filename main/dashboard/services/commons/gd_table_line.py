class GDTableLine:
    """Класс строки таблицы по методике РД"""
    def __init__(self, number: int, defect_label: str, example_label: str):
        self._number = number
        self._defect_label = defect_label
        self._defect_name = defect_label
        self._example_label = example_label
        self._example_name = example_label


GD_TABLE_LINES = [
    GDTableLine(1, "gdTblDefect1", "gdTblExampl1"),
    GDTableLine(2, "gdTblDefect2", "gdTblExampl2"),
    GDTableLine(3, "gdTblDefect3", "gdTblExampl3"),
    GDTableLine(4, "gdTblDefect4", "gdTblExampl4"),
    GDTableLine(5, "gdTblDefect5", "gdTblExampl5"),
    GDTableLine(6, "gdTblDefect6", "gdTblExampl6"),
    GDTableLine(7, "gdTblDefect7", "gdTblExampl7"),
    GDTableLine(8, "gdTblDefect8", "gdTblExampl8"),
    GDTableLine(9, "gdTblDefect9", "gdTblExampl9"),
]

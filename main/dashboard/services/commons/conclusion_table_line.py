class ConclusTableLine:
    """Класс строки таблицы заключений"""
    def __init__(self, number: int, conclusion_label: str, requirement_label: str):
        self._number = number
        self._conclusion_label = conclusion_label
        self._conclusion_name = conclusion_label
        self._requirement_label = requirement_label
        self._requirement_name = requirement_label


CONCLUS_TABLE_LINES = [
    ConclusTableLine(1, "conclusTblConclus1", "conclusTblRequir1"),
    ConclusTableLine(2, "conclusTblConclus2", "conclusTblRequir2"),
    ConclusTableLine(3, "conclusTblConclus3", "conclusTblRequir3"),
    ConclusTableLine(4, "conclusTblConclus4", "conclusTblRequir4"),
    ConclusTableLine(5, "conclusTblConclus4", "conclusTblRequir5"),
    ConclusTableLine(6, "conclusTblConclus5", "conclusTblRequir6"),
    ConclusTableLine(7, "conclusTblConclus5", "conclusTblRequir6"),
    ConclusTableLine(8, "conclusTblConclus5", "conclusTblRequir8"),
    ConclusTableLine(9, "conclusTblConclus3", "conclusTblRequir9"),
    ConclusTableLine(10, "conclusTblConclus6", "conclusTblRequir10"),
    ConclusTableLine(11, "conclusTblConclus6", "conclusTblRequir11"),
    ConclusTableLine(12, "conclusTblConclus7", "conclusTblRequir12"),
    ConclusTableLine(13, "conclusTblConclus6", "conclusTblRequir13"),
    ConclusTableLine(14, "conclusTblConclus6", "conclusTblRequir14"),
    ConclusTableLine(15, "conclusTblConclus8", "conclusTblRequir15"),
    ConclusTableLine(16, "conclusTblConclus9", "conclusTblRequir16"),
]

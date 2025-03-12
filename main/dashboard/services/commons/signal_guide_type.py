# Типы описаний сигналов,
# также являются названиями таблиц хранения сигналов в ClickHouse.
_SIGNAL = "signals"
_PDATA = "pdata"
_LIMITS = "dictionaries"
_CONSTANTS = "constants"
_DIAG = "diag"
_DIAG_MESS = "diag_messages"

_param_types = {
    _PDATA: "Паспортное значение",
    _LIMITS: "Лимит",
    _CONSTANTS: "Константа",
}

TYPE_CHOICES = [
    (_SIGNAL, "Сигнал"),
    (_PDATA, "Паспортное значение"),
    (_LIMITS, "Лимит"),
    (_CONSTANTS, "Константа"),
    (_DIAG, "Диагностическое значение"),
    (_DIAG_MESS, "Диагностическое сообщение"),
]

import logging

from dataclasses import dataclass

from config_ui.models import PassportSignals
from dashboard.models import SignalsGuide


logger = logging.getLogger(__name__)


@dataclass
class PCategory:
    """Класс категории сигналов паспорта"""
    code: str
    name: str
    order: int


@dataclass
class SgnUnit:
    """Класс единицы измерения сигнала паспорта"""
    code: str
    name: str


@dataclass
class PSignal:
    """Класс сигнала паспорта"""
    code: str
    order: int
    category: PCategory
    name: str = None
    unit: SgnUnit = None
    category: PCategory = None


class PaspManager:
    """Класс менеджера паспортных сигналов"""
    def __init__(self):
        self._p_category: dict[str, PCategory] = {}
        self._p_signals: dict[str, PSignal] = {}
        self.__set_data()

    def __set_data(self):
        """Инициализирует множества категорий и сигналов"""
        for p_sgn in PassportSignals.objects.select_related("pdata_category").all():
            if p_sgn.pdata_category:
                if p_category := self._p_category.get(p_sgn.pdata_category.code):
                    pass
                else:
                    p_category = PCategory(
                        code=p_sgn.pdata_category.code,
                        name=p_sgn.pdata_category.name,
                        order=p_sgn.pdata_category.order)
                    self._p_category[p_category.code] = p_category
            else:
                continue
            p_signal = PSignal(
                code=p_sgn.code,
                order=p_sgn.order,
                category=p_category)
            self._p_signals[p_signal.code] = p_signal

        sgn_guides = (
            SignalsGuide.objects.
            filter(code__in=set(self._p_signals.keys())).
            select_related("unit").
            only("code", "name", "unit"))
        for sgn in sgn_guides:
            if p_sgn := self._p_signals.get(sgn.code):
                p_sgn.name = sgn.name
                if sgn_unit := sgn.unit:
                    p_sgn.unit = SgnUnit(code=sgn_unit.code, name=sgn.name)

    def get_signals(self):
        return list(self._p_signals.values())

    def get_signals_codes(self):
        return set(self._p_signals.keys())

    def add_psignals_from_dict(self, p_sgns_configs: dict[dict]):
        """
        Добавляет паспортные сигналы на основе словаря

        Parameters
        ---
        p_sgns_configs имеет вид:
        {
            signal_code: {  # код сигнала
                "order": int,  # порядковый номер сигнала
                "category": str,  # код паспортной категории сигнала
                "name": str,  # название сигнала
                "unit_code": str,  # код единицы измерения
                "unit_name": str,  # название единицы измерения
            }
        }
        """
        for code, configs in p_sgns_configs.items():
            code_cat = configs.get("category")
            if (cat := self._p_category.get(code_cat)):
                if (order := configs.get("order")) is None:
                    order = 2000000000
                if (unit_code := configs.get("unit_code")) and (unit_name := configs.get("unit_name")):
                    unit = SgnUnit(unit_code, unit_name)
                else:
                    unit = None
                self._p_signals[code] = PSignal(
                    code=code,
                    order=order,
                    category=cat,
                    name=configs.get("name"),
                    unit=unit)

from typing import Dict, List, Iterable, Union
from copy import deepcopy

from main.settings import ROUND_NDIGIT
from dashboard.models import SignalsGuide, SignalsChartTabs


class SignalDesc:
    _diag_storage_code = "diag"
    _dict_storage_code = "dictionaries"

    """Класс сигналов для запросов с фронта"""
    def __init__(self, id: int, code: str, name: str, unit_code: str, unit_name: str,
                 storage: str, category_id: int = None, category: str = None,
                 last_val_table=None,
                 lim0_code: str = None, lim1_code: str = None,
                 precision: int = ROUND_NDIGIT,
                 visible: bool = False):
        """
        Parameters
        - precision: int - точность значения сигнала;
        - visible: bool - (default False) отображение графика сигнала
        при первом открытии страницы графиков.
        ---
        """
        self._id = id
        self._code = code
        self._status_code = f"diag_{code}"
        self._name = name
        self._unit_code = unit_code
        self._unit_name = unit_name
        self._storage = storage
        self._category_id = category_id
        self._category_name = category
        self._last_val_table = last_val_table
        self._lim0_code = lim0_code
        self._lim1_code = lim1_code
        self._precision = abs(precision) if precision is not None else ROUND_NDIGIT
        self._visible = visible

    def __str__(self):
        return (
            f"id={self._id}, code={self._code}, storage={self._storage}, "
            f"status_code={self._status_code}, "
            f"lim0_code={self._lim0_code}, lim1_code={self._lim1_code}")

    def __repr__(self):
        return f"id={self._id}, code={self._code}, storage={self._storage}"

    def get_limit_codes(self):
        return [code for code in (self._lim0_code, self._lim1_code) if code]

    def get_status_code(self):
        return self._status_code

    def get_storage_match_to_code(self):
        return {self._storage: self._code}

    @classmethod
    def __get_signals(cls, sgn_guides: Iterable[SignalsGuide], visible: bool = False):
        """Получить список 'SignalDesc' из списка 'SignalsGuide'"""
        return [cls(id=sgn_guide.id,
                    code=sgn_guide.code,
                    name=sgn_guide.name,
                    unit_code=sgn_guide.unit.code if sgn_guide.unit else None,
                    unit_name=sgn_guide.unit.name if sgn_guide.unit else "",
                    storage=sgn_guide.dynamic_storage.name if sgn_guide.dynamic_storage else "",
                    category_id=sgn_guide.category.id if sgn_guide.category else None,
                    category=sgn_guide.category.name if sgn_guide.category else "",
                    last_val_table=getattr(sgn_guide, "last_val_table", None),
                    lim0_code=sgn_guide.lim0_code,
                    lim1_code=sgn_guide.lim1_code,
                    precision=sgn_guide.precision,
                    visible=visible)
                for sgn_guide in sgn_guides]

    @classmethod
    def _get_sg_guide(cls, codes: Iterable[str]):
        """Получить список 'SignalsGuide' из списка кодов"""
        if codes and isinstance(codes, Iterable):
            return (SignalsGuide.objects
                    .select_related("unit", "category", "dynamic_storage")
                    .filter(code__in=codes)
                    .only("id", "code", "name", "unit__code", "unit__name", "dynamic_storage__name",
                          "category__id", "category__name", "lim0_code", "lim1_code", "precision"))
        else:
            return []

    @classmethod
    def _get_sg_guide_for_chart_tab(cls, asset_id: int, chart_tab: str):
        """Получить список 'SignalsGuide' из списка кодов"""
        if not isinstance(chart_tab, str):
            chart_tab = str(chart_tab)
        return (elem.code for elem in
                SignalsChartTabs.objects
                    .select_related("code", "code__sg_type", "code__unit",
                                    "code__category", "code__group",
                                    "code__data_type", "code__plot_type",
                                    "code__databus_source", "code__dynamic_storage")
                    .filter(asset__pk=asset_id, chart_tab__chart_tab__code=chart_tab).only("code"))

    @classmethod
    def get_limits_for_signals(cls, signals: Iterable['SignalDesc']):
        """Получить список 'SignalDesc' лимитов для входного списка сигналов."""
        lim_codes = []
        for sgn in signals:
            lim_codes.extend(sgn.get_limit_codes())
        return cls.get_signals_from_codes(lim_codes)

    @classmethod
    def get_pdata_signals(cls):
        """Получить список 'SignalDesc' сигналов паспортных значений"""
        sgn_guides = (SignalsGuide.objects
                      .select_related("sg_type", "unit", "category", "group",
                                      "data_type", "plot_type",
                                      "databus_source", "dynamic_storage")
                      .filter(dynamic_storage__name="pdata"))
        return cls.__get_signals(sgn_guides)

    @classmethod
    def get_separated_by_chart_groups(cls, signals: Iterable['SignalDesc']):
        """
        Получить списки сигналов разделенные по группам графиков

        Returns:
        ---
        - signals: list[SignalDesc], offline_signals: list[SignalDesc],
          forecast_sgns: list[SignalDesc]
        """
        forecast_sgns = list(filter(lambda x: "_forecast" in x._code, signals))
        signals = list(filter(lambda x: "_forecast" not in x._code, signals))
        # TODO заменить '_off' на '_offline' после сигнала от аналитиков, что
        # они навели порядок в именовании оффлайн сигналов
        offline_signals = list(filter(lambda x: "_off" in x._code, signals))
        signals = list(filter(lambda x: "_off" not in x._code, signals))
        signals = list(filter(lambda x: "_lim" not in x._code, signals))
        return signals, offline_signals, forecast_sgns

    @classmethod
    def get_signals_for_type(cls, type: str, codes: list = None):
        """Получить список 'SignalDesc' сигналов для данного типа и кодов"""
        sgn_guides = (SignalsGuide.objects
                      .select_related("sg_type", "unit", "category", "group",
                                      "data_type", "plot_type",
                                      "databus_source", "dynamic_storage")
                      .filter(sg_type__code=type))
        if codes and isinstance(codes, (list, tuple)):
            sgn_guides = sgn_guides.filter(code__in=codes)
            sgn_guides = sgn_guides.only("id", "code", "name", "unit__code", "unit__name",
                                         "dynamic_storage__name", "category__id",
                                         "category__name", "lim0_code", "lim1_code", "precision")
        return cls.__get_signals(sgn_guides)

    @classmethod
    def get_signals_for_charts(cls, asset_id: int, tab: str):
        """
        Получить списки сигналов и лимитов 'SignalDesc' для графиков

        Returns:
        ---
        - signals: list[SignalDesc], offline_signals: list[SignalDesc],
          limits: list[SignalDesc], forecast_sgns: list[SignalDesc]
        """
        signals = cls.get_signals_for_tab(asset_id, tab)
        signals, offline_signals, forecast_sgns = cls.get_separated_by_chart_groups(signals)
        limits = cls.get_limits_for_signals(signals)
        return signals, offline_signals, limits, forecast_sgns

    @classmethod
    def get_signals_for_charts_from_diag_mess(cls, input_codes: list[str]):
        """
        Получить списки сигналов и лимитов 'SignalDesc' для графиков

        Returns:
        ---
        - signals: list[SignalDesc], offline_signals: list[SignalDesc],
          limits: list[SignalDesc], forecast_sgns: list[SignalDesc]
        """
        signals = SignalDesc.get_signals_from_codes(input_codes, visible=True)
        signals, offline_signals, forecast_sgns = cls.get_separated_by_chart_groups(signals)
        limits = SignalDesc.get_limits_for_signals(signals)
        return signals, offline_signals, limits, forecast_sgns

    @classmethod
    def get_signals_for_charts_with_diag_message_signals(
            cls, asset_id: int, tab: str, input_codes: list[str]):
        """
        Получить списки сигналов и лимитов 'SignalDesc' для графиков
        c учетом сигналов из диаг. сообщения

        Returns:
        ---
        - signals: list[SignalDesc], offline_signals: list[SignalDesc],
          limits: list[SignalDesc], forecast_sgns: list[SignalDesc]
        """
        input_signals = cls.get_signals_from_codes(input_codes, visible=True)
        signals = cls.get_signals_for_tab(asset_id, tab)
        dict_signals = {sgn._code: sgn for sgn in signals}
        for sgn in input_signals:
            dict_signals[sgn._code] = sgn
        signals = list(dict_signals.values())
        signals, offline_signals, forecast_sgns = cls.get_separated_by_chart_groups(signals)
        limits = cls.get_limits_for_signals(signals)
        return signals, offline_signals, limits, forecast_sgns

    @classmethod
    def get_signals_from_codes(
            cls, codes: Union[str, Iterable[str], Iterable[Iterable[str]]], visible: bool = False):
        """Получить список 'SignalDesc' из списка кодов"""
        all_codes = []
        codes_sets = []
        result = []
        if all(isinstance(c, str) for c in codes):
            return cls.__get_signals(cls._get_sg_guide(codes), visible)
        else:
            all_codes = []
            codes_sets = []
            result = []
            for elem in codes:
                if isinstance(elem, (list, tuple, set)):
                    all_codes.extend(elem)
                    codes_sets.append(set(elem))
                    result.append([])
                else:
                    all_codes.append(elem)
                    codes_sets.append(set((elem,)))
                    result.append(None)
            for sgn in cls.__get_signals(cls._get_sg_guide(all_codes), visible):
                for i, codes_set in enumerate(codes_sets):
                    if sgn._code in codes_set:
                        if isinstance(result[i], list):
                            result[i].append(sgn)
                        else:
                            result[i] = sgn
            return result

    @classmethod
    def get_signals_for_tab(cls, asset_id: int, tab: str):
        """Получить список 'SignalDesc' для вкладки графиков"""
        return cls.__get_signals(cls._get_sg_guide_for_chart_tab(asset_id, tab))

    @classmethod
    def get_codes(cls, signals: Iterable[Iterable['SignalDesc']], add_statuses: bool = True):
        """Получить множество кодов сигналов"""
        result = set()
        for sgns in signals:
            if isinstance(sgns, SignalDesc):
                result.add(sgns._code)
                if add_statuses:
                    result.add(sgns._status_code)
                continue
            if isinstance(sgns, Iterable):
                for signal in sgns:
                    if not isinstance(signal, SignalDesc):
                        continue
                    result.add(signal._code)
                    if add_statuses:
                        result.add(signal._status_code)
        return result

    @classmethod
    def get_codes_by_source(cls, signals: List['SignalDesc'], add_statuses: bool = True):
        """Получить словарь соответствия источников спискам кодов сигналов"""
        result: dict[str, set] = {}
        if add_statuses:
            result[cls._diag_storage_code] = set()
        for signal in signals:
            if signal._storage not in result:
                result[signal._storage] = set()
            result[signal._storage].add(signal._code)
            if add_statuses:
                result[cls._diag_storage_code].add(signal._status_code)
        return result

    @classmethod
    def get_union_codes_by_source(cls, codes_by_source1: Dict[str, set],
                                  *args: List[Dict[str, set]]):
        result = deepcopy(codes_by_source1)
        for codes_by_source in args:
            for key, value in codes_by_source.items():
                if key not in result:
                    result[key] = set()
                else:
                    if not isinstance(result[key], set):
                        if isinstance(result[key], str):
                            result[key] = set((result[key]))
                        else:
                            result[key] = set(result[key])
                if isinstance(value, str):
                    result[key].add(value)
                else:
                    result[key].update(value)
        return result

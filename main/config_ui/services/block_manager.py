import logging

from dataclasses import dataclass

from config_ui.models import AssetPage, PageBlock
from dashboard.utils.number import Numeric


logger = logging.getLogger(__name__)


TAG_LAST_DATA = "last_data"
TAG_PERIOD_DATA = "period_data"
TAG_MEASURE_UNIT = "unit"
TAG_BACK_LABEL = "back_label"


@dataclass
class DataLink:
    """
    Класс ссылки на сигнал в визуальных блоках.

    link_type - ожидается из множества ('last_data', 'period_data')

    interval_mask - ожидается в формате '{x}{Unit}', где x - число типа int,
    U - код единицы измерения.

    Допустимые значения U:
    - 'Y' - год (946080000 сек.)
    - 'm' - месяц (2592000 сек.)
    - 'd' - день
    - 'H' - час
    - 'M' - минута
    - 'S' - секунда
    """
    link_type: str
    code: str
    interval_mask: str = ""
    period: float = 0
    last_date: float = 0

    def __post_init__(self):
        self.period = self.__get_period_to_sec()

    @classmethod
    def __get_period_increase(cls, time_unit: str, unit_value: int):
        """Получить прибавку к периоду."""
        if time_unit == "Y":
            return unit_value * 946080000
        elif time_unit == "m":
            return unit_value * 2592000
        elif time_unit == "d":
            return unit_value * 86400
        elif time_unit == "H":
            return unit_value * 3600
        elif time_unit == "M":
            return unit_value * 60
        elif time_unit == "S":
            return unit_value
        else:
            return 0

    def __get_period_to_sec(self):
        """Рассчитать период запроса данных в секундах."""
        period = 0
        if not self.is_period():
            return period
        if not isinstance(self.interval_mask, str):
            return period
        for chank in self.interval_mask.split("_"):
            if len(chank) < 2:
                continue
            unit_value = chank[:-1]
            time_unit = chank[-1]
            try:
                unit_value = int(unit_value)
            except Exception as ex:
                logger.error(
                    f"Datalink.code = {self.code}. Ошибка конвертации {unit_value} из '{chank}' "
                    f"в секунды периода запроса. {ex}")
                continue
            else:
                period += self.__get_period_increase(time_unit, unit_value)
        return period

    def __hash__(self):
        return hash((self.link_type, self.code, self.interval_mask, self.period))

    def is_period(self):
        if self.link_type == TAG_PERIOD_DATA:
            return True
        else:
            return False

    def is_last(self):
        if self.link_type == TAG_LAST_DATA:
            return True
        else:
            return False

    def is_unit(self):
        if self.link_type == TAG_MEASURE_UNIT:
            return True
        else:
            return False

    def is_back_label(self):
        if self.link_type == TAG_BACK_LABEL:
            return True
        else:
            return False

    def is_asset(self):
        if self.link_type == "asset":
            return True
        else:
            return False

    def get_period_to_sec(self):
        """Возвращает период запроса данных в секундах."""
        return self.period


class DataLinks:

    def __init__(self, link: DataLink = None):
        self.links: set[DataLink] = set()
        self.add_link(link)

    def add_link(self, link: DataLink = None):
        if link is None or not isinstance(link, DataLink):
            return
        self.links.add(link)

    def get_codes(self):
        return set(link.code for link in self.links)

    def get_dict_by_codes(self):
        return {link.code: link for link in self.links}

    def get_dict_by_periods(self):
        result: dict[float, set[DataLink]] = dict()
        for link in self.links:
            if link.period not in result:
                result[link.period] = set()
            result[link.period].add(link)
        result.pop(None, None)
        result.pop(0, None)
        return result

    def set_last_date(self, last_timestamp_by_codes: dict[str, float]):
        for link in self.links:
            if timestamp := last_timestamp_by_codes.get(link.code):
                link.last_date = int(timestamp)
                    


class BlockManager:
    """Класс менеджера визуальных блоков данных"""
    def __init__(self, asset_id: int, page_type: str):
        pages = (AssetPage.objects.filter(asset__id=asset_id, page__type__code=page_type)
                 .values_list("page__id", flat=True))
        if len(pages):
            self.__blocks = (PageBlock.objects.select_related('page', 'block')
                             .filter(page__id=pages[0]))
        else:
            self.__blocks = []
        self.last_data_links = DataLinks()
        self.period_data_links = DataLinks()
        self.units = DataLinks()
        self.back_labels = DataLinks()
        self.__set_links_from_blocks()

    @classmethod
    def __get_data_link(cls, template_element: str):
        """Получить ссылку из элемента шаблона"""
        val_parts = template_element.split(".")
        if len(val_parts) > 1:
            return DataLink(*val_parts[:3])
        else:
            return None

    def __set_links_from_blocks(self):
        """Установить ссылки из блоков"""
        for page_block in self.__blocks:
            self.__set_links_from_template(page_block.block.template)

    def __set_links_from_template(self, template):
        """Установить ссылки из шаблона"""
        if isinstance(template, str):
            if link := self.__get_data_link(template):
                self.add_link(link)
        elif isinstance(template, (tuple, list)):
            for elem in template:
                self.__set_links_from_template(elem)
        elif isinstance(template, dict):
            for elem in template.values():
                self.__set_links_from_template(elem)

    def add_link(self, link: DataLink = None):
        if link is None or not isinstance(link, DataLink):
            return
        if link.is_last():
            self.last_data_links.add_link(link)
        elif link.is_period():

            self.period_data_links.add_link(link)
        elif link.is_unit():
            self.units.add_link(link)
        elif link.is_back_label():
            self.back_labels.add_link(link)

    def get_blocks(self):
        return self.__blocks

    def add_data(self, signals_precision: dict,
                 last_data: dict = None, period_data: dict = None,
                 asset: dict = None, units: dict = None, back_labels: dict = None):
        """Добавить данные в шаблоны блоков"""
        if not isinstance(last_data, dict):
            last_data = {}
        if not isinstance(period_data, dict):
            period_data = {}
        if not isinstance(asset, dict):
            asset = {}
        if not isinstance(units, dict):
            units = {}
        if not isinstance(back_labels, dict):
            back_labels = {}
        for block in self.__blocks:
            block.block.template = self.get_template_with_data(
                block.block.template,
                signals_precision,
                last_data,
                period_data,
                asset,
                units,
                back_labels)

    def get_template_with_data(self, template, signals_precision: dict,
                               last_data: dict, period_data: dict,
                               asset: dict, units: dict, back_labels: dict):
        """Получить шаблон с данными"""
        result = template
        if isinstance(template, str):
            if link := self.__get_data_link(template):
                if link.is_last():
                    result = Numeric.form_float(
                        last_data.get(link.code), signals_precision.get(link.code, 2))
                elif link.is_period():
                    result = period_data.get(link.code, {}).get(link.period, [])
                elif link.is_unit():
                    result = units.get(link.code, template)
                elif link.is_back_label():
                    result = back_labels.get(link.code, template)
                elif link.is_asset():
                    result = asset.get(link.code, template)
        elif isinstance(template, (tuple, list)):
            result = []
            for elem in template:
                result.append(self.get_template_with_data(elem, signals_precision,
                                                          last_data, period_data,
                                                          asset, units, back_labels))
        elif isinstance(template, dict):
            for key in template.keys():
                template[key] = self.get_template_with_data(template[key], signals_precision,
                                                            last_data, period_data,
                                                            asset, units, back_labels)
            result = template
        return result

    def get_data_to_page(self, signals_precision: dict,
                         last_data: dict = None, period_data: dict = None,
                         asset: dict = None, units: dict = None, back_labels: dict = None):
        self.add_data(signals_precision, last_data, period_data, asset, units, back_labels)
        result = []
        for block in self.__blocks:
            block_data = block.block.template
            block_data["id"] = block.id
            block_data["gridParams"] = {
                "w": block.w,
                "h": block.h,
                "x": block.x,
                "y": block.y,
                "minW": block.min_w,
                "minH": block.min_h,
            }
            result.append(block_data)
        return result

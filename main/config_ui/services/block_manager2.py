import logging

from dataclasses import dataclass
from typing import Iterable

from config_ui.models import (
    AssetPage, Page, PagePanel, PanelBlock, PagePanelLocation, PageBlockLocation)
from config_ui.services import formatters
from dashboard.utils.time_func import runtime_in_log
from dashboard.utils.number import Numeric


logger = logging.getLogger(__name__)


TAG_LAST_DATA = "last_data"
TAG_PERIOD_DATA = "period_data"
TAG_MEASURE_UNIT = "unit"
TAG_BACK_LABEL = "back_label"


@dataclass
class BlockDesc:
    id: int
    panel_id: int
    location_id: int
    template: dict
    block_type: str
    x: float
    y: float
    w: float
    h: float

    def format_template(self):
        """Возвращает отформатированный шаблон с данными"""
        if self.block_type == "triangleChart":
            self.template["values"] = formatters.to_duval_triangle(
                self.template.get("values"))
        if self.block_type == "pentagonChart":
            self.template["values"] = formatters.to_duval_pentagon(
                self.template.get("values"))
        elif self.block_type == "boxChart":
            self.template["values"] = formatters.to_box_chart(
                self.template.get("values"))
        elif self.block_type == "textField":
            signals = self.template.pop("signals", {})
            self.template["values"] = formatters.to_text_field(
                self.template.get("values"), signals)
        return self.template


@dataclass
class PanelDesc:
    id: int
    location_id: int
    template: dict
    x: float
    y: float
    w: float
    h: float


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
                try:
                    link.last_date = int(timestamp)
                except ValueError as ex:
                    logger.error(f"Ошибка установки времени последнего измерения {link.code}. {ex}")


class BlockManager2:
    """Класс менеджера визуальных блоков данных"""
    @runtime_in_log
    def __init__(self, asset_id: int, page_type: str):
        self._page = self._get_page(asset_id, page_type)
        if self._page is not None:
            self.__panels = self._get_panels(self._page)
            self.__blocks = self._get_blocks(self._page, self._get_panel_ids(self.__panels))
        else:
            self.__panels = []
            self.__blocks = []
        self.last_data_links = DataLinks()
        self.period_data_links = DataLinks()
        self.units = DataLinks()
        self.back_labels = DataLinks()
        self.__set_links_from_blocks()
        self.__set_links_from_panels()

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
            block.template = self.get_template_with_data(
                block.template,
                signals_precision,
                last_data,
                period_data,
                asset,
                units,
                back_labels)
        for panel in self.__panels:
            panel.template = self.get_template_with_data(
                panel.template,
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

    @runtime_in_log
    def get_data_to_page(self, signals_precision: dict,
                         last_data: dict = None, period_data: dict = None,
                         asset: dict = None, units: dict = None, back_labels: dict = None):
        """Получить отформатированные данные"""
        self.add_data(signals_precision, last_data, period_data, asset, units, back_labels)
        result = {}
        outer_locations = []
        for panel in self.__panels:
            outer_locations.append(
                {
                    "i": str(panel.location_id),
                    "x": panel.x, "y": panel.y,
                    "w": panel.w, "h": panel.h
                }
            )
        inner_locations = []
        for block in self.__blocks:
            inner_locations.append(
                {
                    "i": str(block.location_id),
                    "x": block.x, "y": block.y,
                    "w": block.w, "h": block.h
                }
            )
        blocks_by_panel_id: dict[int, list[BlockDesc]] = {}
        for block in self.__blocks:
            panel_id = block.panel_id
            if panel_id not in blocks_by_panel_id:
                blocks_by_panel_id[panel_id] = []
            blocks_by_panel_id[panel_id].append(block)

        data = []
        for panel in self.__panels:
            panel_data = panel.template
            panel_data["id"] = panel.location_id
            panel_blocks = blocks_by_panel_id.get(panel.id, [])
            if panel_blocks:
                panel_data["parts"] = []
                for block in panel_blocks:
                    block_data = block.format_template()
                    block_data["id"] = block.location_id
                    panel_data["parts"].append(block_data)
            data.append(panel_data)

        result["outter"] = outer_locations
        result["inner"] = inner_locations
        result["data"] = data
        return result

    def _get_page(self, asset_id: int, page_type: str):
        try:
            return (
                AssetPage.objects.select_related("asset", "page")
                .filter(asset__id=asset_id, page__type__code=page_type).only("asset__id", "page")[0].page)
        except Exception as ex:
            logger.error(f"Ошибка запроса страницы виджетов. {ex}")
            return None

    def _get_blocks(self, page: Page, panel_ids: Iterable[int]):
        q_blocks = (PanelBlock.objects.select_related('panel', 'block')
                    .filter(panel__id__in=panel_ids))

        q_block_locs = (PageBlockLocation.objects.select_related('page', 'panel', 'block')
                        .filter(page__id=page.id, panel__id__in=panel_ids)
                        .only("id", "page_id", "panel_id", "block_id", "x", "y", "w", "h"))
        block_locs = {(loc.page.id, loc.panel.id, loc.block.id): loc for loc in q_block_locs}
        result: list[BlockDesc] = []
        for b in q_blocks:
            b_loc = block_locs.get((page.id, b.panel.id, b.block.id))
            if not b_loc:
                b_loc = self._get_new_block_loc(page, b)
            result.append(
                BlockDesc(
                    id=b.block.id,
                    panel_id=b.panel.id,
                    location_id=b_loc.id,
                    template=b.block.template,
                    block_type=b.block.type.code,
                    x=b_loc.x,
                    y=b_loc.y,
                    w=b_loc.w,
                    h=b_loc.h)
            )
        return result

    def _get_panels(self, page: Page):
        panels = PagePanel.objects.select_related('page', 'panel').filter(page__id=page.id)

        q_panel_locs = (PagePanelLocation.objects.select_related('page', 'panel')
                        .filter(page__id=page.id)
                        .only("id", "page_id", "panel_id", "x", "y", "w", "h"))
        panel_locs = {(loc.page.id, loc.panel.id): loc for loc in q_panel_locs}
        result: list[PanelDesc] = []
        for p in panels:
            p_loc = panel_locs.get((page.id, p.panel.id))
            if not p_loc:
                p_loc = self._get_new_panel_loc(p)
            result.append(
                PanelDesc(
                    id=p.panel.id,
                    location_id=p_loc.id,
                    template=p.panel.template,
                    x=p_loc.x,
                    y=p_loc.y,
                    w=p_loc.w,
                    h=p_loc.h)
            )
        return result

    def _get_panel_ids(self, panels: Iterable[PanelDesc]):
        try:
            return tuple(p.id for p in panels)
        except Exception:
            return tuple()

    def _get_new_block_loc(self, page: Page, panel_block: PanelBlock):
        loc = PageBlockLocation(
            page=page, panel=panel_block.panel, block=panel_block.block,
            x=panel_block.x, y=panel_block.y, w=panel_block.w, h=panel_block.h)
        loc.save()
        return loc

    def _get_new_panel_loc(self, page_panel: PagePanel):
        loc = PagePanelLocation(
            page=page_panel.page, panel=page_panel.panel,
            x=page_panel.x, y=page_panel.y, w=page_panel.w, h=page_panel.h)
        loc.save()
        return loc

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
        for block in self.__blocks:
            self.__set_links_from_template(block.template)

    def __set_links_from_panels(self):
        """Установить ссылки из блоков"""
        for panel in self.__panels:
            self.__set_links_from_template(panel.template)

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

import logging
from typing import List

from dashboard.services.commons.signal_desc import SignalDesc
from dashboard.utils.time_func import runtime_in_log
from localization.models import (SignalsGuideTranslts, SignalsCategoriesTranslts,
                                 MeasureUnitsTranslts, APILabelsTranslts)


logger = logging.getLogger(__name__)


class SignalDescTralslation:
    """Класс локализации экземпляров SignalDesc"""
    @classmethod
    @runtime_in_log
    def translate_collections(cls, signals: List[List[SignalDesc]], lang: str,
                              localized_properties: set = {"sg_name", "category", "unit", "api_label"}):
        if not isinstance(localized_properties, set):
            localized_properties = set()
        sguide_ids = set()
        category_ids = set()
        unit_codes = set()
        api_labels = set()
        for signals1 in signals:
            for sgn in signals1:
                if "sg_name" in localized_properties:
                    sguide_ids.add(sgn._id)
                if sgn._category_id and "category" in localized_properties:
                    category_ids.add(sgn._category_id)
                if sgn._unit_code and "unit" in localized_properties:
                    unit_codes.add(sgn._unit_code)
                if hasattr(sgn, "_last_val_table") and sgn._last_val_table and "api_label" in localized_properties:
                    api_labels.add(sgn._last_val_table.code)

        if sguide_ids:
            sguide_translts = cls.get_sgn_guide_translations(sguide_ids, lang)
        else:
            sguide_translts = {}
        if category_ids:
            category_translts = cls.get_sgn_category_translations(category_ids, lang)
        else:
            category_translts = {}
        if unit_codes:
            unit_translts = cls.get_unit_translations(unit_codes, lang)
        else:
            unit_translts = {}
        if api_labels:
            api_labels = cls.get_api_labels_translations(api_labels, lang)
        else:
            api_labels = {}

        for signals1 in signals:
            for sgn in signals1:
                cls.update(
                    sgn,
                    sguide_translts,
                    category_translts,
                    unit_translts,
                    api_labels,
                )

    @classmethod
    def update(cls, signal: SignalDesc, sguide_translts: dict[id, str],
               category_translts: dict[id, str], unit_translts: dict[id, str],
               api_labels: dict[str, str]):
        if sguide_name := sguide_translts.get(signal._id):
            signal._name = sguide_name
        if category_name := category_translts.get(signal._category_id):
            signal._category_name = category_name
        if unit_name := unit_translts.get(signal._unit_code):
            signal._unit_name = unit_name
        if hasattr(signal, "_last_val_table") and signal._last_val_table:
            if last_val_table_name := api_labels.get(signal._last_val_table.code):
                signal._last_val_table.name = last_val_table_name

    @classmethod
    def get_sgn_guide_translations(cls, sguide_ids: set[int], lang: str):
        return {
            inst.sgn_guide.id: inst.content
            for inst in SignalsGuideTranslts.objects
            .select_related("sgn_guide", "lang")
            .filter(sgn_guide__id__in=list(sguide_ids), lang__code=lang)
            .only("sgn_guide__id", "content", "lang__code")
        }

    @classmethod
    def get_sgn_category_translations(cls, category_ids: set[int], lang: str):
        return {
            inst.category.id: inst.content
            for inst in SignalsCategoriesTranslts.objects
            .select_related("category", "lang")
            .filter(category__id__in=list(category_ids), lang__code=lang)
            .only("category__id", "content", "lang__code")
        }

    @classmethod
    @runtime_in_log
    def get_unit_translations(cls, unit_codes: set[int], lang: str):
        return {
            inst.unit.code: inst.content
            for inst in MeasureUnitsTranslts.objects
            .select_related("unit", "lang")
            .filter(unit__code__in=list(unit_codes), lang__code=lang)
            .only("unit__code", "content", "lang__code")
        }

    @classmethod
    def get_api_labels_translations(cls, api_labels: set[str], lang: str):
        return {
            inst.label.code: inst.content
            for inst in APILabelsTranslts.objects
            .select_related("label", "lang")
            .filter(label__code__in=list(api_labels), lang__code=lang)
            .only("label__code", "content", "lang__code")
        }

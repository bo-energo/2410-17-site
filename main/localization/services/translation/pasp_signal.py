import logging
from typing import List

from config_ui.services.pasp_manager import PSignal
from dashboard.utils.time_func import runtime_in_log
from localization.models import PassportCategoriesTranslts

logger = logging.getLogger(__name__)


class PaspSignalTralslation:
    """Класс локализации экземпляров PSignal"""
    @classmethod
    @runtime_in_log
    def translate_collections(cls, p_signals: List[PSignal], lang: str,
                              localized_properties: set = {"category"}):
        if not isinstance(localized_properties, set):
            localized_properties = set()
        category_codes = set()
        for sgn in p_signals:

            if sgn.category and "category" in localized_properties:
                category_codes.add(sgn.category.code)

        if category_codes:
            category_translts = cls.get_sgn_category_translations(category_codes, lang)
        else:
            category_translts = {}

        for sgn in p_signals:
            cls.update(
                sgn,
                category_translts,
            )

    @classmethod
    def update(cls, signal: PSignal, category_translts: dict[id, str]):
        if (category := signal.category):
            if category_name := category_translts.get(category.code):
                category.name = category_name

    @classmethod
    def get_sgn_category_translations(cls, category_codes: set[int], lang: str):
        return {
            inst.code: inst.content
            for inst in PassportCategoriesTranslts.objects
            .filter(lang__code=lang, code__in=list(category_codes))
            .only("code", "content")
        }

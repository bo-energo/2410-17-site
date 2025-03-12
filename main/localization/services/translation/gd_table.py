import logging
from typing import List

from dashboard.services.commons.gd_table_line import GDTableLine
from localization.models import APILabelsTranslts


logger = logging.getLogger(__name__)


class GDTableLineTralslation:
    """Класс локализации таблицы по методике РД"""
    @classmethod
    def translate_collections(cls, table_lines: List[GDTableLine], lang: str):
        api_labels = set()
        for line in table_lines:
            api_labels.add(line._defect_label)
            api_labels.add(line._example_label)

        for line in table_lines:
            cls.update(
                line,
                cls.get_api_labels_translations(api_labels, lang),
            )

    @classmethod
    def update(cls, line: GDTableLine, line_translts: dict[str, str]):
        if defect_name := line_translts.get(line._defect_label):
            line._defect_name = defect_name
        if example_name := line_translts.get(line._example_label):
            line._example_name = example_name

    @classmethod
    def get_api_labels_translations(cls, api_labels: set[str], lang: str):
        return {
            inst.label.code: inst.content
            for inst in APILabelsTranslts.objects
            .select_related("label", "lang")
            .filter(label__code__in=list(api_labels), lang__code=lang)
            .only("label__code", "content", "lang__code")
        }

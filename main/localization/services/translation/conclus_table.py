import logging
from typing import List

from dashboard.services.commons.conclusion_table_line import ConclusTableLine
from localization.models import APILabelsTranslts


logger = logging.getLogger(__name__)


class ConclusTableLineTralslation:
    """Класс локализации таблицы по методике РД"""
    @classmethod
    def translate_collections(cls, table_lines: List[ConclusTableLine], lang: str):
        api_labels = set()
        for line in table_lines:
            api_labels.add(line._conclusion_label)
            api_labels.add(line._requirement_label)

        api_labels_translations = cls.get_api_labels_translations(api_labels, lang)
        for line in table_lines:
            cls.update(
                line,
                api_labels_translations,
            )

    @classmethod
    def update(cls, line: ConclusTableLine, line_translts: dict[str, str]):
        if conclusion_name := line_translts.get(line._conclusion_label):
            line._conclusion_name = conclusion_name
        if requirement_name := line_translts.get(line._requirement_label):
            line._requirement_name = requirement_name

    @classmethod
    def get_api_labels_translations(cls, api_labels: set[str], lang: str):
        return {
            inst.label.code: inst.content
            for inst in APILabelsTranslts.objects
            .select_related("label", "lang")
            .filter(label__code__in=list(api_labels), lang__code=lang)
            .only("label__code", "content", "lang__code")
        }

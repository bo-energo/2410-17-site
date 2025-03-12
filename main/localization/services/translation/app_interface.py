import logging

from localization.models import APILabelsTranslts, Langs


logger = logging.getLogger(__name__)


class APITralslation:
    """Класс предоставления перевода для меток используемых backend"""
    __translation_source = APILabelsTranslts

    @classmethod
    def get_all_translts(cls, lang: str):
        data = (
            cls.__translation_source.objects
            .filter(lang__code=lang)
            .select_related("label")
            .only("label", "content")
        )
        return {rec.label.code: rec.content for rec in data}

    @classmethod
    def get_all_langs(cls):
        return Langs.objects.all()

    @classmethod
    def get_translts(cls, labels: list, lang: str):
        data = (
            cls.__translation_source.objects
            .select_related("label")
            .filter(
                lang__code=lang,
                label__code__in=labels,
            )
            .only("label", "content")
        )
        return {rec.label.code: rec.content for rec in data}

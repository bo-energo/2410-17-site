import logging

from localization.models import Interfacelabels, InterfaceTranslts, Langs


logger = logging.getLogger(__name__)


class InterfaceTralslation:
    __label_source = Interfacelabels
    __translation_source = InterfaceTranslts

    @classmethod
    def get_all_translts(cls, lang: str):
        data = (cls.__translation_source.objects.select_related("label")
                .filter(lang__code=lang).only("label", "content"))
        return {rec.label.code: rec.content for rec in data}

    @classmethod
    def get_all_langs(cls):
        return Langs.objects.all()

import logging
from typing import List

from dashboard.services.commons.asset_desc import AssetDesc
from localization.models import AssetsTypeTranslts


logger = logging.getLogger(__name__)


class AssetDescTralslation:
    """Класс локализации экземпляров AssetDesc"""
    @classmethod
    def translate_collections(cls, assets: List[List[AssetDesc]], lang: str):
        type_codes = set()
        for assets1 in assets:
            for asset in assets1:
                if asset.type_code:
                    type_codes.add(asset.type_code)

        type_translts = cls.get_asset_type_translations(type_codes, lang)

        for assets1 in assets:
            for asset in assets1:
                cls.update(asset, type_translts)

    @classmethod
    def update(cls, asset: AssetDesc, type_translts: dict[id, str]):
        if type_name := type_translts.get(asset.type_code):
            asset.type_name = type_name

    @classmethod
    def get_asset_type_translations(cls, type_codes: set[str], lang: str):
        return {
            inst.a_type.code: inst.content
            for inst in AssetsTypeTranslts.objects
            .select_related("a_type", "lang")
            .filter(a_type__code__in=list(type_codes), lang__code=lang)
            .only("a_type__code", "content", "lang")
        }

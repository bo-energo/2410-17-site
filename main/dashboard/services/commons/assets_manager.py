import logging
from typing import Iterable

from dashboard.models import Assets
from .asset_desc import AssetDesc


logger = logger = logging.getLogger(__name__)


class AssetsManager:
    """Менеджер активов (оборудования)"""
    __source = Assets
    __filter_query_begin = __source.objects.select_related("type", "substation")

    @classmethod
    def from_model_instance(cls, asset: Assets):
        """Получить актив из экземпляра 'Assets'"""
        return AssetDesc(
            id=asset.id,
            guid=asset.guid,
            name=asset.name,
            type_name=getattr(asset.type, "name", None),
            type_code=getattr(asset.type, "code", None),
            model=asset.model,
            subst_id=getattr(asset.substation, "id", None),
            subst_name=getattr(asset.substation, "name", None),
            image=asset.image.url if asset.image else "",
            scheme_image=asset.scheme_image.url if asset.scheme_image else "",
            subst_scheme_image=cls.__get_subst_scheme_url(asset),
            on_scheme_x=cls.__get_coord_on_scheme_x(asset),
            on_scheme_y=cls.__get_coord_on_scheme_y(asset))

    @classmethod
    def get_assets_guid(cls, assets: Iterable[AssetDesc]):
        return [asset.guid for asset in assets]

    @classmethod
    def get_assets_name(cls, assets: Iterable[AssetDesc]):
        return [asset.name for asset in assets]

    @classmethod
    def __get_coord_on_scheme_x(cls, asset: Assets):
        if asset.on_scheme_x is not None:
            return asset.on_scheme_x
        else:
            return 0

    @classmethod
    def __get_coord_on_scheme_y(cls, asset: Assets):
        if asset.on_scheme_y is not None:
            return asset.on_scheme_y
        else:
            return 0

    @classmethod
    def get_subst_id_name(cls, assets: Iterable[AssetDesc]):
        """
        Получить id и название подстанции из первого актива
        имеющего не пустой id подстанции
        """
        for asset in assets:
            if asset.subst_id:
                return asset.subst_id, asset.subst_name
        return None, None

    @classmethod
    def __get_subst_scheme_url(cls, asset: Assets):
        """
        Получить URL изображения схемы подстанции
        """
        if asset.substation and asset.substation.scheme_image:
            return asset.substation.scheme_image.url
        else:
            return None

    @classmethod
    def get_all(cls):
        """Получить все активы"""
        assets = cls.__filter_query_begin.all()
        return [cls.from_model_instance(asset) for asset in assets]

    @classmethod
    def get_by_id(cls, id: int):
        """Получить актив с id = id"""
        try:
            return cls.from_model_instance(
                cls.__source.objects
                .select_related("type", "substation")
                .get(pk=id))
        except Exception:
            logger.exception(f"ERROR get asset with {id = }")
            return None

    @classmethod
    def get_by_guids(cls, guids: Iterable[str]):
        """Получить активы с guid из списка guids"""
        assets = (cls.__filter_query_begin
                  .filter(guid__in=tuple(guids)))
        return [cls.from_model_instance(asset) for asset in assets]

    @classmethod
    def get_by_subst(cls, subst_id: int):
        """Получить список активов для подстанции с id = subst_id"""
        assets = (cls.__filter_query_begin
                  .filter(substation__pk=subst_id))
        return [cls.from_model_instance(asset) for asset in assets]

    @classmethod
    def dict_by_guid(cls, assets: Iterable[AssetDesc]):
        """Получить словарь активов сгурппированных по guid"""
        return {asset.guid: asset for asset in assets}

    @classmethod
    def dict_by_name(cls, assets: Iterable[AssetDesc]):
        """Получить словарь активов сгурппированных по name"""
        return {asset.name: asset for asset in assets}

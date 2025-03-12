from dashboard.models import Assets, SignalsGuide
from .mms_sguide import SgGuide


class MMSAssetManager:
    @classmethod
    def _get_sguide(cls, excluded_codes: list):
        return SignalsGuide.objects.exclude(
            code__in=excluded_codes).filter(
            mms_logical_node__isnull=False,
            mms_data_object__isnull=False,
            mms_class__isnull=False,
            ).only("code", "name", "mms_logical_node", "mms_data_object", "mms_class")

    @classmethod
    def _get_sguides_for_asset(cls, excluded_codes: list):
        return [
            SgGuide(sguide.code, sguide.name, sguide.mms_logical_node,
                    sguide.mms_data_object, sguide.mms_class).get_formatted_for_mms_config()
            for sguide in cls._get_sguide(excluded_codes)
        ]

    @classmethod
    def get_formatted_for_mms_config(cls, excluded_codes: list):
        sguides = cls._get_sguides_for_asset(excluded_codes)
        return [
            {
                "id": asset.id,
                "asset": asset.guid,
                "device": None,
                "name": asset.name,
                "logical_device": asset.mms_logical_device,
                "signals": sguides
            }
            for asset in Assets.objects.filter(
                guid__isnull=False,
                mms_logical_device__isnull=False
                ).only("id", "guid", "name", "mms_logical_device")
        ]

import json
import logging

from dashboard.models import GeoMap, GeoMapSetting
from dashboard.utils import hash


logger = logging.getLogger(__name__)


def __loads(in_str: str, default=None):
    if default is None:
        default = {}
    try:
        return json.loads(in_str)
    except Exception as ex:
        logger.error("Не удалось преобразовать в объект свойство GEO-объекта."
                     f"{ex}")
        return default


def __get(value, default=None):
    if value is None:
        return default
    return value


def get_property(geo_elem: GeoMap):
    if geo_elem.linked_obj and isinstance(geo_elem.properties, dict):
        geo_elem.properties["subst_id"] = geo_elem.linked_obj.pk
    return geo_elem.properties


@hash.hash_result_with_status(db_tables=(GeoMap._meta.db_table, GeoMapSetting._meta.db_table))
def get_geomap():
    """Получить гео данные для отображения карты"""
    feature_colections = {
        code: {
            "type": "FeatureCollection",
            "name": code,
            "features": []}
        for code in ("Areas", "Lines", "Substations")
    }
    for rec in GeoMap.objects.select_related("linked_obj"):
        if rec.collection_code not in feature_colections:
            feature_colections[rec.collection_code] = {
                "type": "FeatureCollection",
                "name": rec.collection_code,
                "features": []
            }
        feature_colections[rec.collection_code]["features"].append(
            {
                "type": "Feature",
                "properties": get_property(rec),
                "geometry": rec.geometry,
            }
        )
    map_setting = GeoMapSetting.objects.all()
    default_setting = GeoMapSetting()
    if len(map_setting):
        map_setting = map_setting[0]
    else:
        map_setting = default_setting
        map_setting.save()
    return {
        "data": list(feature_colections.values()),
        "settings": {
            "zoom": __get(map_setting.default_zoom, default_setting.default_zoom),
            "min_zoom": __get(map_setting.min_zoom, default_setting.min_zoom),
            "max_zoom": __get(map_setting.max_zoom, default_setting.max_zoom),
            "rotation": __get(map_setting.rotation, default_setting.rotation),
            "center": [__get(map_setting.center_x, default_setting.center_x),
                       __get(map_setting.center_y, default_setting.center_y)],
        }
    }, True

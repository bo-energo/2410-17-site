import logging

from dashboard.models import AccessPoints, Assets, Devices, Signals
from dashboard.services.signal_stats.utils import dictfetchall
from django.db import connection
from django.db.models import F, Subquery
from django.forms.models import model_to_dict

logger = logging.getLogger(__name__)


def get_signal_stats(
    asset_guid: str,
    signal: str,
    start_timestamp: int,
    end_timestamp: int,
    only_bad: bool = False,
) -> list[tuple] | None:
    """Получить статусы считывания сигналов для ассета.

    Args:
        asset_guid (str): Asset's GUID
        signal (str): Signal's code
        start_timestamp (int): Start timestamp of selected data
        end_timestamp (int): End timestamp of selected data
        only_bad (bool): If True - select only bad signal stats
    """

    query = f"""
        SELECT timestamp, status, message FROM (
          SELECT
            ROW_NUMBER() OVER (PARTITION BY asset, signal ORDER BY timestamp) AS r,
            t.*
          FROM dyn_signals_stats t
          WHERE asset = %(asset_guid)s
                AND signal = %(signal)s
                AND timestamp >= %(start_timestamp)s
                AND timestamp < %(end_timestamp)s
                {"AND status = 'false'" if only_bad else ""}
        ) x
    """

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                {
                    "asset_guid": asset_guid,
                    "signal": signal,
                    "start_timestamp": start_timestamp,
                    "end_timestamp": end_timestamp,
                },
            )
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Can't get last signals_stats for {asset_guid=}. {e}")
        return None


def get_asset_devices(asset_guid: str) -> list[dict] | None:
    """Запрос на получение устройств, которые считывают хотя бы один сигнал для ассета.

    Args:
        asset_guid (str): Asset's GUID
    """

    asset_ids = Assets.objects.filter(guid=asset_guid).values("id")
    devices_queryset = (
        Devices.objects.select_related("protocol", "access_point")
        .filter(id__in=Subquery(
            Signals.objects
            .filter(asset__id__in=Subquery(asset_ids))
            .distinct("device__id")
            .values("device__id")
        ))
        .exclude(name='Manual input')
        .exclude(name='ASMD')
        .order_by("name")
    )
    result = [
        {
            **model_to_dict(d),
            "access_point": None if d.access_point is None else model_to_dict(d.access_point),
            "protocol": None if d.protocol is None else model_to_dict(d.protocol),
        }
        for d in list(devices_queryset)
    ]

    return result


def get_signals_stats(
    asset_guid: str,
    device_ids: list,
    start_timestamp: int,
    end_timestamp: int,
) -> list[tuple] | None:
    """Получить статистику по сигналам устройств.

    Args:
        asset_guid (str): Asset's GUID
        device_ids (list): Devices' identifiers
        start_timestamp (int): Start timestamp of selected data
        end_timestamp (int): End timestamp of selected data
    """

    query = """
        WITH
        last_signal_stats AS (
            SELECT timestamp, signal, status, message FROM (
                SELECT timestamp, signal, status, message, ROW_NUMBER() OVER (PARTITION BY signal ORDER BY timestamp DESC) row_numb
                FROM dyn_signals_stats
                WHERE
                    asset = %(asset_guid)s
                    AND timestamp >= %(start_timestamp)s
                    AND timestamp <= %(end_timestamp)s
            ) last_statuses
            WHERE row_numb = 1
        ),
        signal_status_counters AS (
            SELECT dss.signal, dss.status, count(*) AS total_statuses
            FROM dyn_signals_stats dss
            WHERE
                dss.asset = %(asset_guid)s
                AND dss."timestamp" >= %(start_timestamp)s
                AND dss."timestamp" <= %(end_timestamp)s
            GROUP BY (dss.signal, dss.status)
        )
        SELECT
            sg.code,
            sg.name,
            s.enabled,
            s.device,
            lags.status as last_status,
            lags.timestamp as last_timestamp,
            lags.message as last_message,
            (select total_statuses from signal_status_counters where status = 'true' and signal = sg.code) as success_statuses,
            (select total_statuses from signal_status_counters where status = 'false' and signal = sg.code) as fail_statuses
        FROM signals_guide sg
        JOIN signals s ON sg.id = s.code
        LEFT OUTER JOIN last_signal_stats lags ON sg.code = lags.signal
        WHERE s.device IN %(device_ids)s AND s.asset = (SELECT a.id FROM assets a WHERE a.guid = %(asset_guid)s)
        ORDER BY s.device, sg.code
    """

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                {
                    "asset_guid": asset_guid,
                    "start_timestamp": start_timestamp,
                    "end_timestamp": end_timestamp,
                    "device_ids": tuple(device_ids),
                },
            )
            return dictfetchall(cursor)
    except Exception as e:
        logger.error(f"Can't get good signals counter for {asset_guid=}, {device_ids=}, {start_timestamp=}, {end_timestamp=}. {e}")
        return None


def get_substation_assets() -> list[dict] | None:
    """Запрос на получение всех ассетов с инфо о подстанции."""

    assets_queryset = (
        Assets.objects
        .select_related("substation")
        .annotate(
            asset_id=F("id"),
            asset_guid=F("guid"),
            asset_name=F("name"),
            asset_model=F("model"),
            substation_name=F("substation__name")
        )
        .order_by("substation_name", "asset_name")
        .values("asset_id", "asset_guid", "asset_name", "asset_model", "substation_id", "substation_name")
    )
    return list(assets_queryset)


def get_models_stats(
    asset_guid: str,
    start_timestamp: int,
    end_timestamp: int,
) -> list[dict] | None:
    """Получить статистику по запуску моделей ассета за период.

    Args:
        asset_guid (str): Asset's GUID
        start_timestamp (int): Start timestamp of selected data
        end_timestamp (int): End timestamp of selected data
    """

    statuses_per_model = 1
    query = f"""
        SELECT asset, diagnostic, timestamp, message, model_start, model_end, model_duration
        FROM (
            SELECT
                asset,
                diagnostic,
                timestamp,
                message,
                model_start,
                model_end,
                model_duration,
                ROW_NUMBER() OVER (PARTITION BY asset, diagnostic order by timestamp DESC) AS row_numb
            FROM dyn_models_stats
            WHERE timestamp >= %(start_timestamp)s AND timestamp < %(end_timestamp)s AND asset = %(asset_guid)s
            ORDER BY asset, diagnostic, timestamp DESC
        ) last_statuses
        WHERE row_numb <= {statuses_per_model}
    """

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                {
                    "asset_guid": asset_guid,
                    "start_timestamp": start_timestamp,
                    "end_timestamp": end_timestamp,
                }
            )
            return dictfetchall(cursor)
    except Exception as e:
        logger.error(f"Can't get models stats info. {e}")
        return None


def get_model_stats(
    asset_guid: str,
    model_code: str,
    start_timestamp: int,
    end_timestamp: int,
) -> list[dict] | None:
    """Получить подробную статистику по запуску модели ассета за период.

    Args:
        asset_guid (str): Asset's GUID
        model_code (str): Model's code
        start_timestamp (int): Start timestamp of selected data
        end_timestamp (int): End timestamp of selected data
    """

    query = """
        SELECT timestamp, model_start, model_duration, message
        FROM dyn_models_stats
        WHERE
            asset = %(asset_guid)s
            AND diagnostic = %(model_code)s
            AND timestamp >= %(start_timestamp)s
            AND timestamp < %(end_timestamp)s
        ORDER BY timestamp DESC;
    """

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                {
                    "asset_guid": asset_guid,
                    "model_code": model_code,
                    "start_timestamp": start_timestamp,
                    "end_timestamp": end_timestamp,
                },
            )
            return dictfetchall(cursor)
    except Exception as e:
        logger.error(f"Can't get model stats info. {e}")
        return None


def update_access_point(
    access_point_id: int,
    access_point: dict,
) -> int | None:
    """Обновить access_point.

    Args:
        access_point_id (itn): Access point's id
        access_point (dict): new access point data
    """

    try:
        edited_access_point = (
            AccessPoints.objects.filter(pk=access_point_id)
            .update(**access_point)
        )
        return edited_access_point
    except Exception as e:
        logger.error(f"{e}. Can't update access point {access_point_id} with data = {access_point}.")
    return None

import logging
from datetime import datetime

from main.settings import TIME_ZONE
from dashboard.utils.SqlManager import SqlManager
from .select_configs import SelectDiagMessConfig


logger = logger = logging.getLogger(__name__)


class SQLDiagMsgManager:
    """SQL менеджер диагностических сообщений"""
    __source = SqlManager
    __config = SelectDiagMessConfig

    @classmethod
    def per_interval(cls, obj_id: int, date_start: datetime, date_end: datetime,
                     is_subst: bool = True, query_params: dict = None):
        """
        Возвращает диагностические сообщения для
        актива в интервале [date_start, date_end]

        Parameters:
        ---
        - obj_id: int - идентификатор объекта, для которого выбираются сообщения;
        - is_subst: bool = True - если True, то сообщения выбираются
        для подстанции, если False, то для актива.
        """
        if not query_params:
            query_params = {}
        lang = lng if (lng := query_params.get("lang")) else "ru"
        fields = cls.get_main_fields(lang, cls.get_use_template(query_params))
        config = cls.__config(fields, query_params)

        sql_parts = []
        sql_parts.extend(
            (
                "SELECT "
                "a.id, a.code, a.name,",
                f"timezone('{TIME_ZONE}', to_timestamp(timestamp)),",
                f"{fields.get('message')},",
                "dm.group, dml.name, dmlt.content, dm.id_tab, dm.signals",
                "FROM dyn_diag_messages as dm,",
                "(select a.id, a.guid, a.name, at.code from assets as a, assets_type as at",
                f"where {cls._get_condition_select_assets(obj_id, is_subst)}",
                "and a.type_id = at.id) as a,",
                "diag_msg_level as dml, diag_msg_level_translts as dmlt",
                "WHERE a.guid = dm.asset",
                "and COALESCE(dm.level, 1000) = dml.code",
                "and COALESCE(dm.level, 1000) = dmlt.level",
                f"and dmlt.lang_id = '{lang}'"
            )
        )
        sql_parts.extend(
            config.get_additional_filtering(date_start, date_end))
        sql_parts.append(config.get_ordering())
        sql_parts.append(config.get_slicing())

        query = " ".join(sql_parts)
        return cls.__source().execute(query)

    @classmethod
    def count_per_interval(cls, obj_id: int, date_start: datetime, date_end: datetime,
                           is_subst: bool = True, query_params: dict = None):
        """
        Возвращает количество диагностических сообщений для
        объекта с id = obj_id в интервале [date_start, date_end]
        без учета лимита сообщений.

        Parameters:
        ---
        - obj_id: int - идентификатор объекта, для которого выбираются сообщения;
        - is_subst: bool = True - если True, то сообщения выбираются
        для подстанции, если False, то для актива.
        """
        if not query_params:
            query_params = {}
        lang = lng if (lng := query_params.get("lang")) else "ru"
        fields = cls.get_main_fields(lang, cls.get_use_template(query_params))
        config = cls.__config(fields, query_params)

        sql_parts = []
        sql_parts.extend(
            (
                "SELECT",
                "timestamp",
                "FROM dyn_diag_messages as dm,",
                "(select a.id, a.guid, a.name, at.code from assets as a, assets_type as at",
                f"where {cls._get_condition_select_assets(obj_id, is_subst)}",
                "and a.type_id = at.id) as a,",
                "diag_msg_level as dml, diag_msg_level_translts as dmlt",
                "WHERE a.guid = dm.asset",
                "and COALESCE(dm.level, 1000) = dml.code",
                "and COALESCE(dm.level, 1000) = dmlt.level",
                f"and dmlt.lang_id = '{lang}'"
            )
        )
        sql_parts.extend(
            config.get_additional_filtering(date_start, date_end))

        query = " ".join(sql_parts)
        return cls.__source().execute(f"select count(*) from ({query}) as dmc")

    @classmethod
    def get_main_fields(cls, lang: str, use_template: bool):
        return {
            "asset": "a.name",
            "timestamp": "timestamp",
            "message": (
                "diag_msg_format(dm.param_groups, "
                "array(SELECT content FROM diagmsg_translts, "
                "(select regexp_split_to_table(regexp_replace(dm.message_ids, '\[|\]| ', '', 'g'), ',') as id) as msg "
                "WHERE cast(msg_id as text) = msg.id "
                f"AND lang_id = '{lang}'))") if use_template else "dm.message"
        }

    @classmethod
    def get_use_template(cls, query_params: dict):
        if isinstance(use_template := query_params.get("use_template"), bool):
            return use_template
        else:
            return True

    @classmethod
    def _get_condition_select_assets(cls, obj_id: int, is_subst: bool = True):
        """Возвращает условие отбора активов при запросе диаг. сообщений."""
        if is_subst is True:
            return f"a.substation_id = {obj_id}"
        else:
            return f"a.id = {obj_id}"

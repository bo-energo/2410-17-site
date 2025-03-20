import logging
from json import loads
from typing import List, Iterable

from localization.models import DiagMsgTranslts


logger = logging.getLogger(__name__)


class DiagMsgTralslation:
    def __init__(self, msg_tmp_codes: Iterable, lang: str):
        if len(msg_tmp_codes):
            diag_msgs = (
                DiagMsgTranslts.objects
                .select_related("msg")
                .filter(msg__num_code__in=msg_tmp_codes, lang__code=lang))
        else:
            diag_msgs = (
                DiagMsgTranslts.objects
                .select_related("msg")
                .filter(lang__code=lang))
        self._templates = {
                diagmsg.msg.num_code: diagmsg.content
                for diagmsg in diag_msgs}

    @classmethod
    def from_diag_msg(cls, diag_msg: List[dict], lang: str):
        msg_tmp_codes = set()
        for msg in diag_msg:
            try:
                codes = loads(msg.get("message_ids"))
            except Exception as ex:
                logger.error(f"Не удалось получить коды диаг. сообщений. {ex}")
                continue
            msg_tmp_codes.update(codes)
        return cls(msg_tmp_codes, lang)

    def get_translation(self, template_ids: str, params: str):
        result = []
        if template_ids:
            try:
                template_ids = loads(template_ids)
            except Exception as ex:
                logger.error(f"Не удалось десериализовать коды диаг. сообщений при локализации. {ex}")
                return ""
            if params:
                try:
                    params = loads(params)
                except Exception as ex:
                    logger.error(
                        f"Не удалось десериализовать параметры форматирования диаг. сообщений при локализации. {ex}")
                    params = []
            if isinstance(template_ids, Iterable):
                for i, id in enumerate(template_ids):
                    template = self._get_formatted_template(
                        self._get_template(id),
                        self._get_template_params(params, i))
                    if template:
                        result.append(template)
        return " ".join(result)

    @classmethod
    def _get_formatted_template(cls, template: str, template_params: list | tuple):
        if template_params and template:
            try:
                template = template.format(
                    **{f"param{i}": value for i, value in enumerate(template_params, 1)})
            except Exception as ex:
                logger.error(
                    f"Не удалось подставить параметры {template_params} "
                    f"в шаблон (id: {id}, content: '{template}') при формировании диаг сообщения. {ex}")
        return template

    @classmethod
    def _get_template_params(cls, all_params: list[list], index: int):
        if isinstance(all_params, list | tuple) and 0 <= index < len(all_params):
            params = all_params[index]
            if not isinstance(params, list | tuple):
                params = [params,]
        else:
            params = None
        return params

    def _get_template(self, id: int):
        template = self._templates.get(id)
        if not isinstance(template, str):
            template = None
        return template

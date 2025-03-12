import logging
from itertools import zip_longest
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
                .filter(msg__num_code__in=msg_tmp_codes, lang__code=lang)
            )
            self._templates = {
                diagmsg.msg.num_code: diagmsg.content
                for diagmsg in diag_msgs
            }
        else:
            self._templates = {}

    @classmethod
    def from_diag_msg(cls, diag_msg: List[dict], lang: str):
        msg_tmp_codes = set()
        for msg in diag_msg:
            try:
                codes = loads(msg.get("message_ids"))
            except Exception:
                logger.exception("Не удалось получить коды диаг. сообщений.")
                continue
            msg_tmp_codes.update(codes)
        return cls(msg_tmp_codes, lang)

    def get_translation(self, template_ids: str, params: str):
        try:
            template_ids = loads(template_ids)
        except Exception:
            logger.exception("Не удалось получить коды диаг. сообщений для формирования диаг сообщения.")
            return ""
        try:
            params = loads(params)
        except Exception:
            logger.exception("Не удалось получить параметры для формирования диаг сообщения.")
            params = []
        result = []
        for id, template_param in zip_longest(template_ids, params, fillvalue=[]):
            template = self._templates.get(id)
            if template_param and isinstance(template, str):
                try:
                    template = template.format(**{f"param{i}": value
                                                  for i, value in enumerate(template_param, 1)})
                except Exception:
                    logger.exception(f"Не удалось подставить параметры {template_param} "
                                     f"в шаблон (id: {id}, content: '{template}') "
                                     "при формировании диаг сообщения.")
                    continue
            if template:
                result.append(template)
        return " ".join(result)

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Union

import requests
import shortuuid
from dashboard.services.commons.asset_desc import AssetDesc
from dashboard.utils.time_func import runtime_in_log, normalize_date, safe_str_to_date

from main.settings import VM_ADDRESS, VM_PREFIX, VML_ADDRESS, VML_PROJECT_ID


logger = logging.getLogger(__name__)


class MeteringsManager:
    @classmethod
    @runtime_in_log
    def _query_prometheus(cls, query: str, step: str = '10y'):
        on_time = datetime.now() - timedelta(days=0)
        req_query = VM_ADDRESS + '/api/v1/query?query=' + \
            query + '&time='+str(on_time.timestamp()*1000)
        if step:
            req_query = req_query + '&step=' + step
        response = requests.get(req_query)
        return response.json()

    @classmethod
    @runtime_in_log
    def _query_prometheus_range(cls, query: str, start: int, end: int, step: str = '10y'):
        req_query = VM_ADDRESS + '/prometheus/api/v1/query_range?query=' + \
            query
        if start is not None:
            req_query = req_query + '&start=' + str(int(start*1000))
        if end is not None:
            req_query = req_query + '&end=' + str(int(end*1000))
        if step is not None:
            req_query = req_query + '&step=' + step
        response = requests.get(req_query)
        return response.json()

    @classmethod
    def _get_msg_hash(cls, asset, signal, ts):
        msg_id = asset+":"+signal+":"+str(int(float(ts)))
        msg_hash = shortuuid.uuid(name=msg_id)
        return msg_hash

    @classmethod
    @runtime_in_log
    def get_last_meterings(cls, asset: Union[AssetDesc, List[AssetDesc]],
                           codes: Iterable):
        """
        Получить список последних значений сигналов  и статусов сигналов.

        Parametrs
        ---
        - asset - актив (оборудование) дял которого будут получены значения;
        - 'codes' - список кодов сигналов;

        Значения сигналов возвращаются как [['asset', 'signal_code', 'value', 'timestamp'], ...].
        """
        if not codes:
            return [], True
        elif not isinstance(codes, Iterable):
            return [], False
        meterings = []
        res_status = True

        asset_list = []
        if isinstance(asset, AssetDesc):
            asset_list.append(asset)
        else:
            asset_list.extend(asset)

        asset_filter = ""
        if asset_list:
            asset_filter = f'asset=~"{"|".join([str(el.guid) for el in asset_list])}"'

        signal_filter = ""
        if codes:
            signal_filter = f'signal=~"{"|".join(codes)}"'

        table_prefix = ''
        if VM_PREFIX:
            table_prefix = VM_PREFIX + '_'

        filter_str = f'{{{asset_filter},{signal_filter}}}'
        query = 'WITH (f_str='+filter_str + \
            ',ts_q(d,p)=alias(tlast_over_time(d{f_str}[10y]),p),val_q(d,p)=alias(last_over_time(d{f_str}[10y]),p),idx_q(d)=(ts_q(d,"i_ts"),val_q(d, "i_vl")),val_blk_q(d)=(ts_q(d,"v_ts"),val_q(d,"v_vl"))) '\
                'union(idx_q('+table_prefix+'indexes_value),val_blk_q('+table_prefix+'signals_value))'
        result = cls._query_prometheus(query)

        meterings_dict = {}
        for metric in result['data']['result']:
            key = (metric['metric']['asset'], metric['metric']['signal'])
            if key not in meterings_dict:
                meterings_dict[key] = {}
            meterings_dict[key][metric['metric']['__name__']] = metric['value'][1]
        meterings = []

        indexes_dict = []
        for metric_key, metric_val in meterings_dict.items():
            if 'i_vl' in metric_val and 'v_vl' in metric_val:
                # Если есть значения в обеих базах - брать последнее
                if metric_val['i_ts'] > metric_val['v_ts']:
                    indexes_dict.append([metric_key[0], metric_key[1], metric_val['i_vl'], metric_val['i_ts']])
                else:
                    meterings.append([metric_key[0], metric_key[1], metric_val['v_vl'], metric_val['v_ts']])
            elif 'i_vl' in metric_val:
                # Если есть только в logs - записать значение, чтобы в дальнейшем получить значение
                indexes_dict.append([metric_key[0], metric_key[1], metric_val['i_vl'], metric_val['i_ts']])
            else:
                # Иначе - просто взять значение
                meterings.append([metric_key[0], metric_key[1], metric_val['v_vl'], metric_val['v_ts']])

        if indexes_dict:
            headers = {'projectid': VML_PROJECT_ID or 0}
            query_logs = "message_id:in("+','.join(cls._get_msg_hash(el[0], el[1], el[3])
                                                   for el in indexes_dict)+") | fields asset,signal,_msg,_time"
            query_dict = {"query": query_logs, "limit": 500, "start": 0, "end": datetime.now().timestamp()}
            res = requests.post(VML_ADDRESS + '/select/logsql/query', headers=headers, data=query_dict)
            for data in res.iter_lines():
                row_data = json.loads(data)
                if (time := safe_str_to_date(row_data['_time'])):
                    meterings.append(
                        [row_data['asset'], row_data['signal'], row_data['_msg'], time.timestamp()])

        return meterings, res_status

    @classmethod
    def check_code_by_sources(cls, code_by_sources: dict):
        if not code_by_sources:
            return False, True
        if not isinstance(code_by_sources, dict):
            logger.exception("code_by_sources dict type is expected, "
                             f"{type(code_by_sources)} is received.")
            return False, False
        return True, True

    @classmethod
    @runtime_in_log
    def get_meterings(
            cls,
            asset_id: str,
            code_by_sources: Dict[str, Iterable],
            date_start,
            date_end,
            is_reduced: bool = False,
            count_points: int = 2048):
        """
        Получить список значений сигналов за период [date_start, date_end].

        Parametrs
        ---
        - asset - актив (оборудование) для которого будут получены значения;
        - 'code_by_sources' - словарь соответствия источников значений сигналов
        кодам сигналов;
        - is_reduced: bool - если True - делается запрос с оптимизацией кол-ва точек.
        False (по умолчанию) - запрос всех данных для временного интервала.
        """
        meterings = []
        res_status = True
        check_status, return_status = cls.check_code_by_sources(code_by_sources)
        if not check_status:
            return meterings, return_status

        table_prefix = ''
        if VM_PREFIX:
            table_prefix = VM_PREFIX + '_'

        with_section = 'WITH (q='+table_prefix+'signals_value{'+f'asset="{asset_id}", signal=~"' + \
            '|'.join(['|'.join(codes) for codes in code_by_sources.values()]) + '"})'

        functions = [("max_over_time", "max"), ("min_over_time", "min"),
                     ("tmax_over_time", "tmax"), ("tmin_over_time", "tmin"),]
        if is_reduced:
            period = int((date_end - date_start)/count_points)
        else:
            period = 60

        alias_str = ",".join(
            ['alias('+fnc[0]+'(q['+str(period)+'s]),"'+fnc[1]+'")' for fnc in functions])
        query = with_section + ' union('+alias_str+')'

        json_parsed = cls._query_prometheus_range(query, date_start, date_end, str(period) + 's')

        result = {}
        for metric in json_parsed["data"]["result"]:
            signal = metric["metric"]["signal"]
            name = metric["metric"]["__name__"]
            values = metric["values"]

            if signal not in result:
                result[signal] = {"tmax": [], "tmin": [], "max": [], "min": []}

            result[signal][name] = values

        for signal, metrics in result.items():
            tmax_values = metrics["tmax"]
            tmin_values = metrics["tmin"]
            max_values = metrics["max"]
            min_values = metrics["min"]

            combined_values = list(zip([int(v[1]) for v in tmax_values], [float(v[1]) for v in max_values])) + \
                list(zip([int(v[1]) for v in tmin_values], [float(v[1]) for v in min_values]))

            combined_values = filter(lambda x: x[0] >= float(date_start) and x[0] <= float(date_end), combined_values)

            meterings.extend([(signal, timestamp, value)
                             for timestamp, value in sorted(combined_values, key=lambda x: x[0])])

        return meterings, res_status

    @classmethod
    def get_last_meterings_by_codes(cls, last_data: list[list], only_value: bool = False):
        """
        Получить словарь соответствия кодов сигналов их последним значениям.
        """
        if only_value:
            return {code: value for _, code, value, _ in last_data}
        return {code: {"value": value, "timestamp": timestamp}
                for _, code, value, timestamp in last_data}

    @classmethod
    def get_last_meterings_by_codes_sync(
            cls,
            asset: AssetDesc,
            codes: Iterable,
            only_value: bool = False):
        """
        Получить словарь соответствия кодов сигналов их последним значениям.
        """
        meterings, status = cls.get_last_meterings(asset, codes)
        if only_value:
            return {code: value for _, code, value, _ in meterings}, status
        return {code: {"value": value, "timestamp": timestamp}
                for _, code, value, timestamp in meterings}, status

    @classmethod
    def get_last_meterings_timestamp_by_codes(cls, last_data: list[list]):
        """
        Получить словарь соответствия кодов сигналов
        временным меткам их последних значений.
        """
        return {code: timestamp for _, code, _, timestamp in last_data}

    @classmethod
    def get_last_messages(
            cls, asset_id: str, group: str, count: int, fields: List[str] = [], type_str: str = ""):
        asset_filter = ""
        type_filter = ""
        fields_filter = ""

        if asset_id:
            asset_filter = 'asset:"'+asset_id+'"|'
        if type_str:
            type_filter = 'type:"'+type_str+'"|'

        if fields:
            fields_list = list(set(fields))
            if "timestamp" in fields_list:
                fields_list.remove("timestamp")
                fields_list.append("_time")
            fields_filter = '| fields ' + ",".join(fields_list)

        data = {"query": asset_filter + type_filter + 'group:'+group+fields_filter+'|sort by (_time) desc',
                "limit": count,
                "start": 0,
                "end": datetime.now().timestamp()}

        req_query = VML_ADDRESS + '/select/logsql/query'
        result = []
        headers = {'projectid': VML_PROJECT_ID or 0}
        res = requests.post(req_query, headers=headers, data=data)
        for record in res.iter_lines():
            row_data = json.loads(record)
            row_data["timestamp"] = normalize_date(row_data.pop("_time")).timestamp()
            result.append(row_data)
        return result

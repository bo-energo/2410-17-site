import logging
from typing import List
from datetime import datetime
from django.db import models
from django.db import connection
from django.db.models import Prefetch
from django.db.models import QuerySet
from django.db.models import F
from django.utils import timezone

from dashboard.data.assistmodel import AssistMixin
from dashboard.services.django_models.use_cases import (
    get_asset_image_path, get_substation_image_path, get_asset_scheme_image_path)


logger = logging.getLogger(__name__)


class AccessPoints(AssistMixin, models.Model):
    PARITY = [
        ('Even', 'Even'),
        ('No', 'No'),
        ('Mark', 'Mark'),
        ('Odd', 'Odd'),
        ('Space', 'Space'),
    ]
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=100, verbose_name='Код',)
    ip = models.CharField(
        max_length=30, blank=True, null=True, verbose_name='IP-адрес',)
    port = models.IntegerField(blank=True, null=True, verbose_name='Порт',)
    url = models.CharField(
        max_length=200, blank=True, null=True, verbose_name='URL',)
    com_port = models.CharField(
        max_length=20, blank=True, null=True, verbose_name='COM-порт',)
    baud_rate = models.IntegerField(
        blank=True, null=True, verbose_name='Бит/сек',)
    data_bits = models.IntegerField(
        blank=True, null=True, verbose_name='Биты данных',)
    # Прояснить смену типа на float или char
    stop_bits = models.CharField(
        max_length=20, blank=True, null=True, verbose_name='Стоповые биты',)
    parity = models.CharField(
        max_length=15, blank=True, null=True, choices=PARITY, default=None,
        verbose_name='Четность',)
    flow_control = models.BooleanField(
        blank=True, null=True, verbose_name='Управление потоком')
    username = models.CharField(
        max_length=30,
        blank=True, null=True, verbose_name='Имя пользователя',)
    password = models.CharField(
        max_length=30,
        blank=True, null=True, verbose_name='Пароль',)

    class Meta:
        managed = True
        db_table = 'access_points'
        verbose_name = 'Точка доступа'
        verbose_name_plural = 'Точки доступа'

    def __str__(self) -> str:
        if self.com_port:
            adress = self.com_port
        elif self.url:
            adress = self.url
        else:
            adress = f"{self.ip}:{self.port}"
        return f"{self.code}, {adress}"


class Assets(models.Model):
    id = models.BigAutoField(primary_key=True)
    guid = models.CharField(
        max_length=200, blank=True, null=True,
        verbose_name='Уникальный идентификатор',
    )
    type = models.ForeignKey(
        'AssetsType', models.DO_NOTHING,
        blank=True, null=True, verbose_name='Категория')
    name = models.CharField(
        max_length=200, blank=True, null=True, verbose_name='Диспетчерское наименование')
    disp_number = models.IntegerField(
        blank=True, null=True, verbose_name='Диспетчерский номер')
    model = models.CharField(
        max_length=200, blank=True, null=True, verbose_name='Тип',)
    image = models.ImageField(
        blank=True, null=True, upload_to=get_asset_image_path,
        verbose_name='Изображение')
    scheme_image = models.ImageField(
        blank=True, null=True, upload_to=get_asset_scheme_image_path,
        verbose_name='Визуальная схема')
    substation = models.ForeignKey(
        'Substations', models.SET_NULL, limit_choices_to={'type': 'end_node'},
        blank=True, null=True, verbose_name='Подстанция')
    mms_logical_device = models.CharField(
        max_length=20, blank=True, null=True, verbose_name='Логическое устройство mms',)
    on_scheme_x = models.FloatField(
        blank=True, null=True, verbose_name='Позиция на схеме, х')
    on_scheme_y = models.FloatField(
        blank=True, null=True, verbose_name='Позиция на схеме, y')

    class Meta:
        managed = True
        db_table = 'assets'
        verbose_name = 'Оборудование'
        verbose_name_plural = 'Оборудование'

    def __str__(self) -> str:
        guid = f", ...{self.guid[-5:]}" if self.guid else ""
        return f"{str(self.substation)}, {self.name}{guid}"

    @classmethod
    def get_guid(cls, id: int):
        try:
            return cls.objects.get(pk=id).guid, True
        except Exception:
            logger.exception("")
            return None, False

    @classmethod
    def get_for_kafka(cls) -> list[dict] | None:
        try:
            return list(
                cls.objects.annotate(
                    asset_type=F("type__code"),
                    substation_name=F("substation__name"),
                ).values("guid", "name", "asset_type", "substation_name")
            )
        except Exception:
            return None


class AssetsType(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=30, verbose_name='Код')
    name = models.CharField(max_length=200, verbose_name='Наименование')

    class Meta:
        managed = True
        db_table = 'assets_type'
        verbose_name = 'Категория оборудования'
        verbose_name_plural = 'Категории оборудования'

    def __str__(self) -> str:
        return str(self.name)


class DatabusSources(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=30, verbose_name='Наименование')

    class Meta:
        managed = True
        db_table = 'databus_sources'
        verbose_name_plural = 'Сигналы. Очереди шины данных'
        verbose_name = 'Очередь шины данных'

    def __str__(self) -> str:
        return str(self.name)


class DeviceModels(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=50, verbose_name='Код',)
    name = models.CharField(
        max_length=200, blank=True, null=True, verbose_name='Наименование',)
    device_type = models.ForeignKey(
        'DeviceTypes', models.DO_NOTHING, blank=True, null=True, verbose_name='Тип',)
    manufacturer = models.CharField(
        max_length=200, blank=True, null=True, verbose_name='Производитель',)
    measuring_range = models.CharField(
        max_length=50, blank=True, null=True, verbose_name='Диапазон измерений',)
    accuracy = models.CharField(
        max_length=100, blank=True, null=True, verbose_name='Точность измерений',)
    register_no = models.CharField(
        max_length=50, blank=True, null=True, verbose_name='Номер сертификата',)

    class Meta:
        managed = True
        db_table = 'device_models'
        verbose_name = 'Модель прибора мониторинга'
        verbose_name_plural = 'Модели приборов мониторинга'

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class DeviceTypes(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=50, verbose_name='Код',)
    name = models.CharField(
        max_length=200, blank=True, null=True, verbose_name='Наименование',)

    class Meta:
        managed = True
        db_table = 'device_types'
        verbose_name = 'Тип прибора мониторинга'
        verbose_name_plural = 'Типы приборов мониторинга'

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class Devices(AssistMixin, models.Model):
    ENABLED = [
        (True, 'Да'),
        (False, 'Нет'),
    ]
    ORDER = [
        (True, 'Big'),
        (False, 'Little'),
    ]
    modbus_funcs = [
        (1, '01 - Read coils'),
        (2, '02 - Read contacts'),
        (3, '03 - Read holding registers'),
        (4, '04 - Read input registers'),
        (24, '24 - Read FIFO queue'),
    ]
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=400, verbose_name='Наименование',)
    model = models.ForeignKey(
        DeviceModels, models.DO_NOTHING, blank=True, null=True, verbose_name='Тип',)
    access_point = models.ForeignKey(
        AccessPoints, models.DO_NOTHING, blank=True, null=True, verbose_name='Точка доступа',)
    schedule = models.ForeignKey(
        'Schedules', models.DO_NOTHING, blank=True, null=True,
        db_column='schedule', verbose_name='Расписание',)
    # должны отправляться в Kafka
    # В это поле переносится информация из data_model.devices.common_address
    common_address = models.CharField(
        max_length=100, blank=True, null=True, verbose_name='Общий адрес')
    wordorder = models.BooleanField(
        blank=True, null=True, choices=ORDER, default=False,
        verbose_name='Порядок слов')
    # должны отправляться в Kafka
    byteorder = models.BooleanField(
        blank=True, null=True, choices=ORDER, default=False,
        verbose_name='Порядок байт')
    enabled = models.BooleanField(
        blank=True, null=True, choices=ENABLED, default=True,
        verbose_name='Включен',)
    protocol = models.ForeignKey(
        'Protocols', models.DO_NOTHING, db_column='protocol',
        blank=True, null=True, verbose_name='Протокол',)
    modbus_function = models.PositiveSmallIntegerField(
        choices=modbus_funcs, default=None,
        blank=True, null=True, verbose_name='Функция чтения modbus',)
    mms_logical_device = models.CharField(
        max_length=20, blank=True, null=True, verbose_name='Логическое устройство mms',)

    class Meta:
        managed = True
        db_table = 'devices'
        verbose_name = 'Источник данных'
        verbose_name_plural = 'Источники данных'

    def __str__(self) -> str:
        return f"{self.name} - ({self.protocol}, {self.access_point})"

    @classmethod
    def get_enable_devices(cls, prefetch: Prefetch) -> QuerySet:
        """Возвращает список включенных приборов. """
        return cls.objects.prefetch_related(
                prefetch
            ).select_related("schedule", "protocol", "access_point").filter(
                enabled=True)

    @classmethod
    def dict_filter_devices(cls, devices: QuerySet,
                            listener: bool = False) -> list:
        """Возвращает список приборов удовлетворяющих
        переданным аргументам.
        Приборы представлены в виде словарей их атрибутов.
        listener: отбор приборов с
        тип роли (True - Listener, False- Reader)."""
        del_attr_device = (
            "signs", "_prefetched_objects_cache", "access_point_id",
            "common_address", "schedule_id", "model_id")
        del_attr_signal = (
            "code_id", "asset_id", "device_id", "value_type_id", "schedule_id")
        rename_attr_signal = (("id", "signal_id"), ("enabled", "signal_enabled"),)
        del_attr_acc_point = ("id", "code")
        rename_attr_acc_point = (("ip", "host"),)
        protocols_common_address = {
            "modbus_rtu", "modbus_tcp", "iec60870_5_104", "60870-5-101", "60870-5-104",
            "60870-5-104_udp"}
        protocols_bytes_to_address = {"modbus_rtu", "modbus_tcp"}
        protocols_ioa_to_address = {
            "iec60870_5_104", "60870-5-101", "60870-5-104", "60870-5-104_udp"}
        result = []
        if listener is not None:
            filt_devices = devices.filter(protocol__listener=listener)
        else:
            filt_devices = devices
        for device in filt_devices:
            for signal in device.signs:
                dict_device = device.get_dict(del_attr=del_attr_device)
                dict_device["additional"] = {}
                # создание словаря параметров точки доступа
                if device.access_point:
                    dict_acc_point = device.access_point.get_dict(
                        del_attr=del_attr_acc_point, rename_attr=rename_attr_acc_point)
                # обновление словаря прибора словарем точки доступа
                dict_device.update(dict_acc_point)

                # создание словаря параметров сигнала
                dict_signal = signal.get_dict(del_attr=del_attr_signal,
                                              rename_attr=rename_attr_signal)
                # обновление словаря прибора словарем сигнала
                dict_device.update(dict_signal)

                # изменение словаря прибора в зависимости от протокола
                if device.protocol:
                    if device.protocol.code in protocols_bytes_to_address:
                        if signal.address is not None:
                            try:
                                bytes = int(signal.address)
                                dict_device["bytes"] = bytes
                            except Exception:
                                pass
                    elif device.protocol.code in protocols_ioa_to_address:
                        if signal.address is not None:
                            try:
                                ioa = int(signal.address)
                                dict_device["ioa"] = ioa
                            except Exception:
                                pass
                    if device.protocol.code in protocols_common_address:
                        dict_device["address"] = device.common_address
                    else:
                        dict_device["common_address"] = device.common_address

                try:
                    dict_device["protocol"] = device.protocol.code
                except Exception:
                    pass
                if signal.schedule:
                    dict_device["period"] = signal.schedule.interval_seconds
                elif device.schedule:
                    dict_device["period"] = device.schedule.interval_seconds
                try:
                    dict_device["signal"] = signal.code.code
                    dict_device["additional"]["signal_name"] = signal.code.name
                except Exception:
                    pass
                try:
                    dict_device["additional"]["device_id"] = device.id
                except Exception:
                    pass
                try:
                    dict_device["formula"] = signal.formula.expression
                except Exception:
                    pass
                try:
                    dict_device["asset"] = signal.asset.guid
                except Exception:
                    pass
                try:
                    dict_device["output_type"] = signal.value_type.code
                except Exception:
                    pass

                [dict_device.pop(key, None)
                 for key in tuple(dict_device.keys()) if dict_device[key] is None]

                result.append(dict_device)
        return result

    @classmethod
    def changes_for_kafka(cls, signal: type,
                          debug_level: int = 1) -> tuple[List[dict]]:
        """Возвращает (readers: list[tuple], listeners: list[tuple])
        приборов в виде подготовленом для отправки в Kafka.
        debug_level:
        - 0 - нет сообщений
        - 1 - сообщение о времени исполнения и кол-ве SQL запросов
        - 2 - дополнительно к 1 уровню список SQL запросов"""
        start_time = datetime.utcnow().timestamp()
        start = len(connection.queries)
        signals_choices = signal.objects.select_related(
                "asset", "code", "formula").filter(enabled=True)
        prefetch = Prefetch("signals_set", queryset=signals_choices,
                            to_attr="signs")
        devices = cls.get_enable_devices(prefetch)

        readers = cls.dict_filter_devices(devices)
        listeners = cls.dict_filter_devices(devices, listener=True)

        diff = len(connection.queries) - start
        if debug_level >= 1:
            logger.info(f"Count of query after Devices.changes_for_kafka: {diff}")
            logger.debug("Time execute Devices.changes_for_kafka = "
                         f"{datetime.utcnow().timestamp() - start_time}")
        if debug_level >= 2:
            for q in connection.queries[-diff:]:
                logger.debug(q)
        return readers, listeners


class DynamicStorages(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=30, verbose_name='Наименование')

    class Meta:
        managed = True
        db_table = 'dynamic_storages'
        verbose_name_plural = 'Сигналы. Таблицы хранения значений'
        verbose_name = 'Таблица хранения значений'

    def __str__(self) -> str:
        return str(self.name)


class ResultHashes(models.Model):
    tables = models.CharField(max_length=1000, verbose_name='Таблицы БД')
    func = models.CharField(max_length=50, verbose_name='Функция')
    input_args = models.BinaryField(blank=True, null=True, verbose_name='Входные аргументы')
    hash = models.CharField(max_length=512, blank=True, null=True, verbose_name='Хеш')

    class Meta:
        managed = True
        db_table = 'result_hashes'
        verbose_name = 'Хеш данных'
        verbose_name_plural = 'Хеши данных'
        constraints = [
            models.UniqueConstraint(fields=['tables', 'func', 'input_args'], name='unique_resulthashes')
        ]

    def __str__(self) -> str:
        return f"{self.func} {self.hash}"


class Formulas(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200, verbose_name='Наименование')
    expression = models.CharField(
        max_length=200, blank=True, null=True, verbose_name='Выражение')

    class Meta:
        managed = True
        db_table = 'formulas'
        verbose_name = 'Формула'
        verbose_name_plural = 'Формулы'

    def __str__(self) -> str:
        return f"{self.name} {self.expression}"


class ModbusTypes(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=100, verbose_name='Код')
    name = models.CharField(
        max_length=200, blank=True, null=True, verbose_name='Наименование')

    class Meta:
        managed = True
        db_table = 'modbus_types'
        verbose_name_plural = 'Типы данных modbus'
        verbose_name = 'Тип данных modbus'

    def __str__(self) -> str:
        return str(self.code)


class Params(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.ForeignKey(
        'SignalsGuide', models.DO_NOTHING, db_column='code',
        verbose_name='Код')
    asset = models.ForeignKey(
        Assets, models.DO_NOTHING, db_column='asset',
        blank=True, null=True, verbose_name='Оборудование')
    timestamp = models.DateTimeField(
        auto_now=False, auto_now_add=False,
        default=timezone.now, verbose_name='Время задания')
    value = models.CharField(
        max_length=400, blank=True, null=True, verbose_name='Значение')

    class Meta:
        managed = True
        db_table = 'params'
        verbose_name = 'Параметр'
        verbose_name_plural = 'Параметры. Значения'

    def __str__(self) -> str:
        asset_name = self.asset.name if self.asset else None
        return f"{self.code.code} - {self.code.name} - {asset_name}: ({self.value}, {self.timestamp})"


class PlotTypes(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=100, verbose_name='Код')
    name = models.CharField(
        max_length=200, blank=True, null=True, verbose_name='Наименование')

    class Meta:
        managed = True
        db_table = 'plot_types'
        verbose_name_plural = 'Типы графиков'
        verbose_name = 'Тип графика'

    def __str__(self) -> str:
        return str(self.code)


class Protocols(models.Model):
    Role = [
        (True, 'Listener'),
        (False, 'Reader'),
    ]
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=100, verbose_name='Код')
    name = models.CharField(
        max_length=200, blank=True, null=True, verbose_name='Наименование')
    listener = models.BooleanField(
        blank=True, null=True, default=False,
        choices=Role, verbose_name='Метод взаимодействия')

    class Meta:
        managed = True
        db_table = 'protocols'
        verbose_name_plural = 'Протоколы'
        verbose_name = 'Протокол'

    def __str__(self) -> str:
        return f'{self.code} - {"listener" if self.listener else "reader"}'


class Schedules(AssistMixin, models.Model):
    id = models.BigAutoField(primary_key=True)
    interval_seconds = models.IntegerField(verbose_name='Интервал (сек)')
    name = models.CharField(
        max_length=200, blank=True, null=True, verbose_name='Наименование')

    class Meta:
        managed = True
        db_table = 'schedules'
        verbose_name_plural = 'Расписания'
        verbose_name = 'Расписание'

    def __str__(self) -> str:
        return f"{self.name}: {self.interval_seconds}"


class Signals(AssistMixin, models.Model):
    ENABLED = [
        (True, 'Да'),
        (False, 'Нет'),
    ]
    modbus_funcs = [
        (1, '01 - Read coils'),
        (2, '02 - Read contacts'),
        (3, '03 - Read holding registers'),
        (4, '04 - Read input registers'),
        (24, '24 - Read FIFO queue'),
    ]
    id = models.BigAutoField(primary_key=True)
    enabled = models.BooleanField(
        blank=True, null=True, choices=ENABLED, default=True,
        verbose_name='Включен',)
    code = models.ForeignKey(
        'SignalsGuide', models.DO_NOTHING, db_column='code',
        blank=True, null=True, verbose_name='Код')
    asset = models.ForeignKey(
        Assets, models.DO_NOTHING, db_column='asset',
        blank=True, null=True, verbose_name='Оборудование')
    device = models.ForeignKey(
        Devices, models.DO_NOTHING, db_column='device',
        verbose_name='Прибор мониторинга')
    # это поле становится уиниверсальным для всех протоколов (объединяет прежние поля 'bytes', 'ioa')
    # в него переносится информация из data_model.signals.address
    address = models.CharField(
        max_length=100, blank=True, null=True, verbose_name='Адрес')
    bit = models.IntegerField(
        blank=True, null=True, verbose_name='Бит в регистре')
    value_type = models.ForeignKey(
        'ModbusTypes', models.DO_NOTHING,
        blank=True, null=True, verbose_name='Тип данных modbus')
    modbus_function = models.PositiveSmallIntegerField(
        choices=modbus_funcs, default=None,
        blank=True, null=True, verbose_name='Функция чтения modbus',)
    unit_source = models.ForeignKey(
        'MeasureUnits', models.DO_NOTHING,
        blank=True, null=True, verbose_name='Ед. измер. источника')
    deveui = models.CharField(
        max_length=200, blank=True, null=True,
        verbose_name='Адрес LoRa устройства')
    func_constr = models.CharField(
        max_length=100, blank=True, null=True, verbose_name='FC MMS')
    value_path = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name='Путь к значению сигнала')
    quality_path = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name='Путь к значению качества')
    timestamp_path = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name='Путь к временной метке')
    fields_path = models.CharField(
        max_length=1000, blank=True, null=True,
        verbose_name='Найденные пути MMS')
    # Определиться с необходимостью этого поля
    input_port = models.IntegerField(
        blank=True, null=True, verbose_name='Входящий порт')
    check_method = models.CharField(
        max_length=20, blank=True, null=True, verbose_name='Метод проверки')
    # ping_period = 60 сек по умолчанию
    ping_period = models.CharField(
        max_length=10, blank=True, null=True,
        verbose_name='Период проверки соединения')
    schedule = models.ForeignKey(
        'Schedules', models.DO_NOTHING, blank=True, null=True,
        db_column='schedule', verbose_name='Расписание')
    formula = models.ForeignKey(
        'Formulas', models.DO_NOTHING, db_column='formula',
        blank=True, null=True, verbose_name='Формула')

    class Meta:
        managed = True
        db_table = 'signals'
        verbose_name_plural = 'Сигналы'
        verbose_name = 'Сигнал'

    def __str__(self) -> str:
        code = self.code.code if self.code else None
        name = self.code.name if self.code else None
        asset = self.asset.name if self.asset else None
        return (f"{code} - {name} - {asset} - {self.device.name}")


class SignalСategories(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=100, verbose_name='Код')
    name = models.CharField(max_length=200, verbose_name='Наименование')

    class Meta:
        managed = True
        db_table = 'signal_categories'
        verbose_name_plural = 'Сигналы. Категории'
        verbose_name = 'Категория сигнала'

    def __str__(self) -> str:
        return str(self.name)


class SignalGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=100, verbose_name='Код')
    name = models.CharField(
        max_length=200, blank=True, null=True, verbose_name='Наименование')

    class Meta:
        managed = True
        db_table = 'signal_groups'
        verbose_name_plural = 'Сигналы. Группы'
        verbose_name = 'Группа сигнала'

    def __str__(self) -> str:
        return str(self.code)


class SignalsGuide(AssistMixin, models.Model):
    ENABLED = [
        (True, 'Да'),
        (False, 'Нет'),
    ]

    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=100, verbose_name='Код')
    name = models.CharField(max_length=300, verbose_name='Наименование')
    sg_type = models.ForeignKey(
        'SignalTypes', models.DO_NOTHING, verbose_name='Тип сигнала')
    unit = models.ForeignKey(
        'MeasureUnits', models.DO_NOTHING,
        blank=True, null=True, verbose_name='Единица измерения')
    category = models.ForeignKey(
        'SignalСategories', models.DO_NOTHING,
        blank=True, null=True, verbose_name='Категория сигнала')
    group = models.ForeignKey(
        'SignalGroups', models.DO_NOTHING,
        blank=True, null=True, verbose_name='Группа сигнала')
    relevance_span = models.IntegerField(
        blank=True, null=True, verbose_name='Актуальность сигнала')
    freeze_span = models.IntegerField(
        blank=True, null=True, verbose_name='Достоверность сигнала')
    lim0_code = models.CharField(
        max_length=100, blank=True, null=True, verbose_name='Код сигнала lim0')
    lim1_code = models.CharField(
        max_length=100, blank=True, null=True, verbose_name='Код сигнала lim1')
    diag_code = models.CharField(
        max_length=100, blank=True, null=True, verbose_name='Код сигнала статуса')
    natural_range_from = models.FloatField(
        blank=True, null=True,
        verbose_name='Нижнее значение естественного диапазона')
    natural_range_to = models.FloatField(
        blank=True, null=True,
        verbose_name='Верхнее значение естественного диапазона')
    speed_limit = models.FloatField(
        blank=True, null=True,
        verbose_name='Лимит по скорости изменения')
    mms_data_object = models.CharField(
        max_length=50, blank=True, null=True, verbose_name='Объект данных mms')
    mms_logical_node = models.CharField(
        max_length=20, blank=True, null=True, verbose_name='Логический узел mms')
    mms_class = models.CharField(
        max_length=20, blank=True, null=True, verbose_name='Класс данных mms')
    opc_label = models.CharField(
        max_length=50, blank=True, null=True, verbose_name='Метка OPC')
    data_type = models.ForeignKey(
        'DataTypes', models.DO_NOTHING,
        blank=True, null=True, verbose_name='Тип данных')
    precision = models.IntegerField(
        blank=True, null=True, verbose_name='Точность значения')
    in_plot = models.BooleanField(
        blank=True, null=True, choices=ENABLED, default=False,
        verbose_name='На график',)
    plot_type = models.ForeignKey(
        'PlotTypes', models.DO_NOTHING,
        blank=True, null=True, verbose_name='Тип графика')
    databus_source = models.ForeignKey(
        'DatabusSources', models.DO_NOTHING,
        blank=True, null=True, verbose_name='Очередь шины данных')
    dynamic_storage = models.ForeignKey(
        'DynamicStorages', models.DO_NOTHING,
        blank=True, null=True, verbose_name='Таблица хранения значений')

    class Meta:
        managed = True
        db_table = 'signals_guide'
        verbose_name_plural = 'Сигналы. Коды'
        verbose_name = 'Код сигнала'

    def __str__(self) -> str:
        if self.relevance_span is None:
            relevance_span = 0
        else:
            relevance_span = self.relevance_span
        return f"{self.code} {self.name} ({self.sg_type}) {relevance_span} сек"

    def get_for_kafka(self):
        return {
            "code": self.code,
            "name": self.name,
            "period": self.relevance_span,
            "range_from": self.natural_range_from,
            "range_to": self.natural_range_to,
            "speed_limit": self.speed_limit,
            "lim0": self.lim0_code,
            "lim1": self.lim1_code
        }


class SignalsGuideFront(SignalsGuide):
    class Meta:
        proxy = True
        verbose_name_plural = 'Сигналы. Коды. Интерфейс'
        verbose_name = 'Код сигнала'


class ChartTabs(models.Model):
    code = models.CharField(max_length=50, verbose_name='Код')
    name = models.CharField(max_length=200, blank=True, null=True, verbose_name='Наименование')

    class Meta:
        managed = True
        db_table = 'chart_tabs'
        verbose_name_plural = 'Вкладки графиков'
        verbose_name = 'Вкладка графиков'

    def __str__(self) -> str:
        return self.name if self.name else self.code


class AssetsTypeChartTabs(models.Model):
    code = models.CharField(max_length=50, verbose_name='Код')
    chart_tab = models.ForeignKey(
        'ChartTabs', models.DO_NOTHING, db_column='chart_tab',
        verbose_name='Вкладка графиков')
    asset_type = models.ForeignKey(
        'AssetsType', models.DO_NOTHING, verbose_name='Категория оборудования')

    class Meta:
        managed = True
        db_table = 'assets_type_chart_tabs'
        verbose_name_plural = 'Категории оборудования.Вкладки графиков'
        verbose_name = 'Вкладка графиков категории оборудования'

    def __str__(self) -> str:
        return f"{self.asset_type.name}-{self.chart_tab.name}"


class SignalsChartTabs(models.Model):
    code = models.ForeignKey(
        SignalsGuide, models.CASCADE, db_column='code',
        verbose_name='Код сигнала')
    chart_tab = models.ForeignKey(
        AssetsTypeChartTabs, models.DO_NOTHING, db_column='chart_tab',
        verbose_name='Вкладка графиков')
    asset = models.ForeignKey(
        Assets, models.CASCADE, db_column='asset',
        blank=True, null=True, verbose_name='Оборудование')

    class Meta:
        managed = True
        db_table = 'signals_chart_tabs'
        verbose_name_plural = 'Сигналы. Вкладки графиков'
        verbose_name = 'Вкладка графиков сигнала'

    def __str__(self) -> str:
        return (f"{str(self.asset) if self.asset else ''}{',' if self.asset else ''}"
                f"  {self.code.code}: {self.chart_tab.code}")


class SignalTypes(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=100, verbose_name='Код')
    name = models.CharField(
        max_length=200, blank=True, null=True, verbose_name='Наименование')

    class Meta:
        managed = True
        db_table = 'signal_types'
        verbose_name_plural = 'Типы сигналов'
        verbose_name = 'Тип сигнала'

    def __str__(self) -> str:
        return str(self.code)


class Substations(models.Model):
    NODE_TYPE = [
        ('node', 'Организация'),
        ('end_node', 'Подстанция'),
    ]
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(
        max_length=400, blank=True, null=True, verbose_name='Название')
    type = models.CharField(choices=NODE_TYPE, default='node',
                            max_length=10, verbose_name='Тип')
    parent = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True,
                               limit_choices_to={'type': 'node'},
                               verbose_name='Входит в')
    scheme_image = models.ImageField(
        blank=True, null=True, upload_to=get_substation_image_path,
        verbose_name='Схема')

    class Meta:
        managed = True
        db_table = 'substations'
        verbose_name = 'Элемент организационной структуры'
        verbose_name_plural = 'Организационная структура'

    def __str__(self):
        return f"{self.name}"


class ManualMeasurements(models.Model):
    id = models.BigAutoField(primary_key=True)
    signal = models.ForeignKey(
        Signals, models.DO_NOTHING, db_column='signal_id',
        verbose_name='Сигнал')
    timestamp = models.DateTimeField(
        auto_now=False, auto_now_add=False,
        default=timezone.now, verbose_name='Время замера')
    value = models.FloatField(verbose_name='Значение')

    class Meta:
        managed = True
        db_table = 'manual_measurements'
        verbose_name_plural = 'Сигналы. Ручные замеры'
        verbose_name = 'Ручной замер'

    def __str__(self) -> str:
        return f"{self.signal}: ({self.value}, {self.timestamp})"


class MeasureUnits(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=50, verbose_name='Код')
    name = models.CharField(max_length=50, verbose_name='Наименование')

    class Meta:
        managed = True
        db_table = 'measure_units'
        verbose_name_plural = 'Сигналы. Единицы измерения'
        verbose_name = 'Единица измерения'

    def __str__(self) -> str:
        return str(self.name)


class DataTypes(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=100, verbose_name='Код')
    name = models.CharField(
        max_length=200, blank=True, null=True, verbose_name='Наименование')

    class Meta:
        managed = True
        db_table = 'data_types'
        verbose_name_plural = 'Типы данных'
        verbose_name = 'Тип данных'

    def __str__(self) -> str:
        return str(self.code)


class MsgToPlot(models.Model):
    id = models.BigAutoField(primary_key=True)
    diag_model = models.CharField(max_length=100, verbose_name='Диагностическая модель')
    signal = models.CharField(max_length=100, verbose_name='Сигнал группы графиков')
    value = models.CharField(max_length=100, verbose_name='Значение')

    class Meta:
        managed = True
        db_table = 'msg_to_plot'
        verbose_name_plural = 'Привязки диаг. сообщений к группам графиков'
        verbose_name = 'Привязка диаг. сообщения к группе графиков'

    def __str__(self) -> str:
        return f"{self.diag_model} ({self.signal}, {self.value})"


class DiagMsgLevel(models.Model):
    code = models.IntegerField(primary_key=True, verbose_name='Числовой код')
    name = models.CharField(max_length=100, verbose_name='Строковый код')

    class Meta:
        managed = True
        db_table = 'diag_msg_level'
        verbose_name_plural = 'Уровни критичности диаг. сообщений'
        verbose_name = 'Уровень критичности диаг. сообщений'

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class GeoMap(AssistMixin, models.Model):
    COLLECTION_TYPES = [
        ("Areas", "Areas"),
        ("Lines", "Lines"),
        ("Substations", "Substations"),
        ]
    id = models.BigAutoField(primary_key=True)
    collection_code = models.CharField(max_length=50, choices=COLLECTION_TYPES, verbose_name='Код коллекции')
    geometry = models.JSONField(verbose_name='Геометрия')
    properties = models.JSONField(verbose_name='Дополнительные свойства')
    linked_obj = models.ForeignKey(
        Substations, models.SET_NULL, blank=True, null=True, verbose_name='Связанный объект')
    description = models.CharField(
        max_length=200, verbose_name='Описание', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'geo_map'
        verbose_name = 'Элемент карты'
        verbose_name_plural = 'Географическая карта'

    def __str__(self) -> str:
        linked_obj = f" - {str(self.linked_obj)}" if self.linked_obj else ""
        return f"{self.collection_code}, {self.description} {linked_obj}"


class GeoMapSetting(AssistMixin, models.Model):
    id = models.BigAutoField(primary_key=True)
    default_zoom = models.FloatField(default=5, verbose_name='Масштаб по умолчанию')
    min_zoom = models.FloatField(default=4, verbose_name='Минимальный масштаб')
    max_zoom = models.FloatField(default=12, verbose_name='Максимальный масштаб')
    rotation = models.FloatField(default=0, verbose_name='Поворот')
    center_x = models.FloatField(default=-3124977.271710, verbose_name='Координата X центра')
    center_y = models.FloatField(default=3694888.906869, verbose_name='Координата Y центра')
    description = models.CharField(
        max_length=200, verbose_name='Описание', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'geo_map_setting'
        verbose_name = 'Настройка карты'
        verbose_name_plural = 'Географическая карта. Настройка'

    def __str__(self) -> str:
        return f"{self.default_zoom}, [{self.center_x}, {self.center_y}] {self.description}"

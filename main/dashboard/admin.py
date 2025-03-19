import logging  # noqa
import requests
from json import loads, dumps
from os import getenv
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.core.cache import caches
from django.http import HttpRequest
from django.http import HttpResponseRedirect
from django.urls import path
from django.db.models import Q

from main.settings import URl_SIGNAL_TEST, GEOMAP_CACHE
from .models import *
from .admin_form import (MyManualMeasurementsAdminForm, MyParamsAdminForm,
                         ChangeCategoryForm, ChangeGroupForm, ChangeUnitForm,
                         ChangeDatabusSourceForm, ChangeDynamicStorageForm,
                         ChangeDeviceForm, ChangeAccPointForm, ChangeScheduleForm,
                         ChangeChartTabForm, ChangeAssetForm)
from .utils import guid
from .utils import hash
from .services.kafka import use_cases as kafka_use_cases
from .services.django_models.use_cases import change_field
from .services.kafka.use_cases import send_assets


logger = logging.getLogger(__name__)


def _send_signals_to_kafka(model_admin: admin.ModelAdmin, request, modified_entity: str = ""):
    """
    Производит попытку отправки настроек сигналов в разрезе приборов в Kafka.
    Отправляет сообщение пользователю о результате.
    """
    result, mess = kafka_use_cases.send_devices(modified_entity)
    if result:
        for message in mess:
            model_admin.message_user(request, message, messages.SUCCESS)
    else:
        for message in mess:
            model_admin.message_user(request, message, messages.ERROR)


class AccessPointsAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'code', 'ip', 'port', 'url', 'com_port',
        'baud_rate', 'data_bits', 'parity', 'stop_bits', 'flow_control',
        'username', 'password',
    )
    list_display_links = (
        'id', 'code', 'ip', 'port', 'url', 'com_port',
        'baud_rate', 'data_bits', 'parity', 'stop_bits', 'flow_control',
        'username', 'password',
    )
    search_fields = (
        'id', 'code', 'ip', 'port', 'url', 'com_port',
        'baud_rate', 'data_bits', 'parity', 'stop_bits', 'flow_control',
        'username', 'password',
    )
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'code',
                    ('ip', 'port'),
                    'url',
                    ('com_port', 'baud_rate',),
                    ('data_bits', 'parity', 'stop_bits', 'flow_control'),
                    ('username', 'password'),
                    )
            }
        ),
    )


class AssetsTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name',)
    list_display_links = ('id', 'code', 'name')
    search_fields = ('id',  'code', 'name',)


class AssetsAdmin(admin.ModelAdmin):
    list_display = ('id', 'guid', 'type', 'name', 'model',
                    'substation', 'mms_logical_device', 'image',
                    'scheme_image', 'on_scheme_x', 'on_scheme_y')
    list_display_links = ('id', 'guid', 'type', 'name', 'model',
                          'substation', 'mms_logical_device', 'image',
                          'scheme_image', 'on_scheme_x', 'on_scheme_y')
    search_fields = ('id', 'guid', 'type__name', 'name', 'model',
                     'substation__name', 'mms_logical_device')
    readonly_fields = ('guid',)
    list_select_related = ('type', 'substation',)
    list_filter = ['type', 'substation',]
    exclude = ['disp_number']

    def assets_to_kafka(self, request):
        """Обработчик для кнопки 'Отправить оборудования в Kafka' в админке."""

        send_assets(self, request)
        return HttpResponseRedirect("../")

    def save_model(self, request, obj: Assets, form, change):
        if not obj.pk or not obj.guid:
            obj.guid = guid.generate()
        super().save_model(request, obj, form, change)
        send_assets(self, request)

    def delete_model(self, request: HttpRequest, obj: Devices) -> None:
        response = super().delete_model(request, obj)
        send_assets(self, request)
        return response

    def delete_queryset(self, request, queryset) -> None:
        response = super().delete_queryset(request, queryset)
        send_assets(self, request)
        return response

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path("assets_to_kafka/", self.admin_site.admin_view(self.assets_to_kafka)),
        ]
        return my_urls + urls


class DatabusSourcesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    list_display_links = ('id', 'name',)
    search_fields = ('id', 'name',)


class DeviceModelsTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name', 'device_type', 'manufacturer',
                    'measuring_range', 'accuracy', 'register_no')
    list_display_links = ('id', 'code', 'name', 'device_type', 'manufacturer',
                          'measuring_range', 'accuracy', 'register_no')
    search_fields = ('id', 'code', 'name', 'device_type__code',
                     'device_type__name', 'manufacturer',
                     'measuring_range', 'accuracy', 'register_no')
    list_select_related = ('device_type',)


class DeviceTypesAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name')
    list_display_links = ('id', 'code', 'name')
    search_fields = ('id', 'code', 'name')


class DevicesAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'model', 'schedule', 'access_point', 'common_address',
        'wordorder', 'byteorder', 'enabled', 'protocol', 'modbus_function',
        'mms_logical_device',
    )
    list_display_links = (
        'id', 'name', 'model', 'schedule', 'access_point', 'common_address',
        'wordorder', 'byteorder', 'enabled', 'protocol', 'modbus_function',
        'mms_logical_device',
    )
    search_fields = (
        'id', 'name', 'model__name',  'access_point__code', 'schedule__name',
        'common_address', 'wordorder', 'byteorder', 'enabled', 'protocol__name',
        'modbus_function', 'mms_logical_device',
    )
    list_select_related = ('access_point', 'model', 'schedule', 'protocol')
    list_filter = ('access_point',)
    fieldsets = (
        (
            None,
            {
                'fields': (
                    ('name', 'enabled'),
                    'model', 'schedule',
                    'access_point', 'common_address',
                    ('wordorder', 'byteorder',),
                    ('protocol', 'modbus_function'),
                    'mms_logical_device',
                    )
            }
        ),
    )
    actions = ['change_acc_point',]

    @admin.action(description="ИЗМЕНИТЬ точку доступа")
    def change_acc_point(self, request, queryset):
        result = change_field(self, request, queryset, "change_acc_point",
                              ChangeAccPointForm, "access_point",
                              "change_field.html", Devices._meta.verbose_name_plural,
                              {"common": "Точка доступа", "genitive": "точки доступа"})
        if "apply" in request.POST:
            _send_signals_to_kafka(self, request, "Devices")
        return result

    def save_model(self, request, obj: Devices, form, change):
        if obj.is_changed():
            super().save_model(request, obj, form, change)
            _send_signals_to_kafka(self, request, "Devices")

    def delete_model(self, request: HttpRequest, obj: Devices) -> None:
        response = super().delete_model(request, obj)
        _send_signals_to_kafka(self, request, "Devices")
        return response

    def delete_queryset(self, request, queryset) -> None:
        response = super().delete_queryset(request, queryset)
        _send_signals_to_kafka(self, request, "Devices")
        return response


class DynamicStoragesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    list_display_links = ('id', 'name',)
    search_fields = ('id', 'name',)


class FormulasAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'expression')
    list_display_links = ('id', 'name', 'expression')
    search_fields = ('id', 'name', 'expression')


class ModbusTypesAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name',)
    list_display_links = ('id', 'code', 'name',)
    search_fields = ('id', 'code', 'name',)


class ParamsAdmin(admin.ModelAdmin):
    form = MyParamsAdminForm

    list_display = ('id', 'code', 'asset', 'timestamp', 'value')
    list_display_links = ('id', 'code', 'asset', 'timestamp', 'value')
    search_fields = ('id', 'code__code', 'code__name', 'asset__name',
                     'asset__guid', 'value')
    autocomplete_fields = ('code',)
    exclude = ('timestamp',)
    list_select_related = ('code', 'asset')
    list_filter = ('asset', 'code__sg_type')

    def has_delete_permission(self, request, obj=None):
        return False


class PlotTypesAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name',)
    list_display_links = ('id', 'code', 'name',)
    search_fields = ('id', 'code', 'name',)


class ProtocolsAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name', 'listener')
    list_display_links = ('id', 'code', 'name', 'listener')
    search_fields = ('id', 'code', 'name', 'listener')


class SchedulesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'interval_seconds',)
    list_display_links = ('id', 'name', 'interval_seconds',)
    search_fields = ('id', 'name', 'interval_seconds',)

    def save_model(self, request, obj: Schedules, form, change):
        if obj.is_changed():
            super().save_model(request, obj, form, change)
            _send_signals_to_kafka(self, request, "Schedules")


class SignalsAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = (
        'id', 'enabled', 'code', 'asset', 'device',
        'address', 'bit', 'value_type', 'modbus_function', 'unit_source',
        'deveui',
        'func_constr', 'value_path', 'quality_path', 'timestamp_path', 'fields_path',
        'input_port', 'check_method', 'ping_period', 'schedule', 'formula',
    )
    list_display_links = (
        'id', 'enabled', 'code', 'asset', 'device',
        'address', 'bit', 'value_type',  'modbus_function', 'unit_source',
        'deveui',
        'func_constr', 'value_path', 'quality_path', 'timestamp_path', 'fields_path',
        'check_method', 'input_port', 'ping_period', 'schedule', 'formula',
    )
    search_fields = (
        'id', 'code__name', 'code__code', 'asset__name', 'device__name',
        'address', 'deveui', 'func_constr', 'value_path',
        'quality_path', 'timestamp_path', 'fields_path', 'check_method',
        'input_port', 'ping_period', 'schedule__interval_seconds', 'formula__name',
    )
    list_select_related = ('asset', 'device', 'code', 'code__category', 'code__sg_type',
                           'device__protocol', 'value_type', 'unit_source',
                           'schedule', 'formula')
    list_filter = ('enabled', 'asset', 'device', 'code__category',
                   'formula', 'value_type')
    autocomplete_fields = ('code',)

    fieldsets = (
        (
            None,
            {
                'fields': (
                    ('enabled',), 'code', 'asset', 'device',
                    ('address', 'bit', 'modbus_function', 'value_type'),
                    'unit_source', 'deveui',)
            }
        ),
        (
            None,
            {
                'fields': (
                    ('func_constr', 'value_path', 'quality_path', 'timestamp_path'),)
            }
        ),
        (
            None,
            {
                'fields': ('fields_path',),
                'classes': ('wide',),
            }
        ),
        (
            None,
            {'fields': (('input_port', 'check_method', 'ping_period', 'schedule'),)}
        ),
        (None, {'fields': (('formula',),)}),
    )

    actions = ['signals_to_Kafka', 'enabled_true', 'enabled_false', 'change_device',
               'change_schedule']

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path("send_to_kafka/", self.admin_site.admin_view(self.signals_to_kafka)),
            path("mms_data_to_kafka/", self.admin_site.admin_view(self.mms_data_to_kafka)),
            path("<path:object_id>/change/send_to_test/", self.admin_site.admin_view(self.signals_to_test)),
        ]
        return my_urls + urls

    def signals_to_test(self, request, object_id):
        """Отправить данные для тестирования настроек"""
        mess_for_user = []
        try:
            obj = self.model.objects.get(id=object_id)
        except Exception:
            mess_for_user.append(f"Не найден сигнал с ID = {object_id}. "
                                 "Попробуйте сохранить настройки сигнала и провести тест снова.")
        else:
            device = obj.device
            device.signs = [obj]
            test_data = Devices.dict_filter_devices([device], listener=None)
            for device in test_data:
                print(f"{device = }")
            try:
                resp = requests.post(URl_SIGNAL_TEST, json=test_data)
            except Exception:
                mess_for_user.append("Не удалось протестировать сигнал. "
                                     "Проверьте настройки URL сервиса тестирования или его доступность.")
                resp = None
            if resp is not None:
                try:
                    resp_data = loads(resp.text)
                except Exception:
                    mess_for_user.append("Ошибка разбора результата тестирования сигнала. "
                                         "Сообщите об ошибке разработчикам.")
                    resp_data = {}
            else:
                resp_data = {}
            if (one_mess := resp_data.get("message")) is not None:
                mess_for_user.append(one_mess)
            for rec in resp_data.get("messages", []):
                if (one_mess := rec.get("message")) is not None:
                    mess_for_user.append(one_mess)
            for rec in resp_data.get("detail", []):
                dict_for_mess = {}
                if (rec_loc := rec.get("loc")) is not None:
                    dict_for_mess["loc"] = rec_loc
                if (rec_msg := rec.get("msg")) is not None:
                    dict_for_mess["msg"] = rec_msg
                if dict_for_mess:
                    mess_for_user.append(dumps(dict_for_mess))
        if mess_for_user:
            message_level = messages.ERROR
        else:
            message_level = messages.SUCCESS
            mess_for_user.append("Тест пройден!")
        for mess in mess_for_user:
            self.message_user(request, mess, message_level)
        return HttpResponseRedirect("../")

    def signals_to_kafka(self, request):
        """Отправить все включенные сигналы для всех включенных источников в Kafka"""
        _send_signals_to_kafka(self, request, "Signals")
        return HttpResponseRedirect("../")

    def mms_data_to_kafka(self, request):
        """Отправить данные для конфигурации MMS сервера в Kafka"""
        result, message = kafka_use_cases.send_mms_config()
        if result:
            self.message_user(request, message, messages.SUCCESS)
        else:
            self.message_user(request, message, messages.ERROR)
        return HttpResponseRedirect("../")

    @admin.action(description="ВКЛЮЧИТЬ выбранные сигналы")
    def enabled_true(self, request, queryset):
        """Для выбранных сигналов 'enabled' делается True."""
        try:
            count = queryset.filter(enabled=False).update(enabled=True)
        except Exception:
            self.message_user(request, 'ОШИБКА включения сигналов. Проверьте данные.',
                              level=messages.ERROR)
        else:
            if count:
                _send_signals_to_kafka(self, request, "Signals")
            self.message_user(request, 'ВКЛЮЧЕНЫ %s cигналов.' % count)

    @admin.action(description="ОТКЛЮЧИТЬ выбранные сигналы")
    def enabled_false(self, request, queryset):
        """Для выбранных сигналов 'enabled' делается False."""
        try:
            count = queryset.filter(enabled=True).update(enabled=False)
        except Exception:
            self.message_user(request, 'ОШИБКА отключения сигналов. Проверьте данные.',
                              level=messages.ERROR)
        else:
            if count:
                _send_signals_to_kafka(self, request, "Signals")
            self.message_user(request, 'ОТКЛЮЧЕНЫ %s cигналов.' % count)

    @admin.action(description="ИЗМЕНИТЬ источник данных")
    def change_device(self, request, queryset):
        result = change_field(self, request, queryset, "change_device",
                              ChangeDeviceForm, "device",
                              "change_field.html", Signals._meta.verbose_name_plural,
                              {"common": "Источник данных", "genitive": "источника данных"})
        if "apply" in request.POST:
            _send_signals_to_kafka(self, request, "Signals")
        return result

    @admin.action(description="ИЗМЕНИТЬ расписание")
    def change_schedule(self, request, queryset):
        result = change_field(self, request, queryset, "change_schedule",
                              ChangeScheduleForm, "schedule",
                              "change_field.html", Signals._meta.verbose_name_plural,
                              {"common": "Расписание", "genitive": "расписания"})
        if "apply" in request.POST:
            _send_signals_to_kafka(self, request, "Signals")
        return result

    def save_model(self, request, obj: Signals, form, change, debug=True):
        need_send_reader_listener = False
        if obj.is_changed():
            need_send_reader_listener = True
        super().save_model(request, obj, form, change)
        # если существующий сигнал изменился, то отправляем в Kafka
        # все сигналы в разрезе роли прибора (reader/listener)
        if need_send_reader_listener:
            _send_signals_to_kafka(self, request, "Signals")

    def delete_model(self, request: HttpRequest, obj: Devices) -> None:
        response = super().delete_model(request, obj)
        _send_signals_to_kafka(self, request, "Signals")
        return response

    def delete_queryset(self, request, queryset) -> None:
        response = super().delete_queryset(request, queryset)
        _send_signals_to_kafka(self, request, "Signals")
        return response


class SignalСategoriesAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name')
    list_display_links = ('id', 'code', 'name')
    search_fields = ('id', 'code', 'name',)


class SignalGroupsAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name')
    list_display_links = ('id', 'code', 'name')
    search_fields = ('id', 'code', 'name')


class SignalsGuideAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = (
        'id', 'code', 'name', 'sg_type', 'unit', 'category', 'group',
        'relevance_span', 'freeze_span', 'lim0_code', 'lim1_code', 'diag_code',
        'natural_range_from', 'natural_range_to', 'speed_limit',
        'mms_data_object', 'mms_logical_node', 'mms_class', 'opc_label',
        'data_type', 'databus_source', 'dynamic_storage', 'precision')
    list_display_links = (
        'id', 'code', 'name', 'sg_type', 'unit', 'category', 'group',
        'relevance_span', 'freeze_span', 'lim0_code', 'lim1_code', 'diag_code',
        'natural_range_from', 'natural_range_to', 'speed_limit',
        'mms_data_object', 'mms_logical_node', 'mms_class', 'opc_label',
        'data_type', 'databus_source', 'dynamic_storage', 'precision')
    search_fields = (
        'id', 'code', 'name', 'sg_type__code', 'unit__name', 'category__name',
        'group__code', 'relevance_span', 'freeze_span',
        'lim0_code', 'lim1_code', 'diag_code', 'natural_range_from',
        'natural_range_to', 'speed_limit',
        'mms_data_object', 'mms_logical_node', 'mms_class', 'opc_label',
        'data_type__code', 'plot_type__code',
        'databus_source__name', 'dynamic_storage__name', 'precision')
    list_select_related = ('sg_type', 'unit', 'category', 'group', 'data_type',
                           'plot_type', 'databus_source', 'dynamic_storage')
    list_filter = ('sg_type', 'unit', 'category', 'group',
                   'databus_source', 'dynamic_storage', 'data_type',
                   'in_plot', 'plot_type')
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'code', 'name',
                    ('sg_type', 'unit'),
                    ('category', 'group'),
                    ('relevance_span', 'freeze_span'),
                    ('lim0_code', 'lim1_code', 'diag_code'),
                    ('natural_range_from', 'natural_range_to'),
                    'speed_limit',
                    ('mms_data_object', 'mms_logical_node', 'mms_class'),
                    'opc_label',
                    ('data_type', 'precision'),
                    ('in_plot', 'plot_type'),
                    ('databus_source', 'dynamic_storage'))
            }
        ),
    )
    actions = ['enabled_true', 'enabled_false', 'change_category',
               'change_group', 'change_unit',
               'change_databus_source', 'change_dynamic_storage']

    @admin.action(description="ВКЛЮЧИТЬ вывод на график выбранных сигналов")
    def enabled_true(self, request, queryset):
        """Для выбранных сигналов 'enabled' делается True."""
        try:
            count = queryset.filter(Q(in_plot=False) | Q(in_plot=None)).update(in_plot=True)
        except Exception:
            self.message_user(request, 'ОШИБКА включения вывода на график сигналов. Проверьте данные.',
                              level=messages.ERROR)
        else:
            self.message_user(request, 'ВКЛЮЧЕН вывод на график %s cигналов.' % count)

    @admin.action(description="ОТКЛЮЧИТЬ вывод на график выбранных сигналов")
    def enabled_false(self, request, queryset):
        """Для выбранных сигналов 'enabled' делается False."""
        try:
            count = queryset.filter(in_plot=True).update(in_plot=False)
        except Exception:
            self.message_user(request, 'ОШИБКА отключения вывода на графиксигналов. Проверьте данные.',
                              level=messages.ERROR)
        else:
            self.message_user(request, 'ОТКЛЮЧЕН вывод на график %s cигналов.' % count)

    @admin.action(description="ИЗМЕНИТЬ категорию")
    def change_category(self, request, queryset):
        return change_field(self, request, queryset, "change_category",
                            ChangeCategoryForm, "category",
                            "change_field.html", SignalsGuide._meta.verbose_name_plural,
                            {"common": "Категория", "genitive": "категории"})

    @admin.action(description="ИЗМЕНИТЬ группу")
    def change_group(self, request, queryset):
        return change_field(self, request, queryset, "change_group",
                            ChangeGroupForm, "group",
                            "change_field.html", SignalsGuide._meta.verbose_name_plural,
                            {"common": "Группа", "genitive": "группы сигналов"})

    @admin.action(description="ИЗМЕНИТЬ единицу измерения")
    def change_unit(self, request, queryset):
        return change_field(self, request, queryset, "change_unit",
                            ChangeUnitForm, "unit",
                            "change_field.html", SignalsGuide._meta.verbose_name_plural,
                            {"common": "Единица измерения", "genitive": "единицы измерения"})

    @admin.action(description="ИЗМЕНИТЬ шину данных")
    def change_databus_source(self, request, queryset):
        return change_field(self, request, queryset, "change_databus_source",
                            ChangeDatabusSourceForm, "databus_source",
                            "change_field.html", SignalsGuide._meta.verbose_name_plural,
                            {"common": "Шина данных", "genitive": "шины данных"})

    @admin.action(description="ИЗМЕНИТЬ таблицу хранения значений")
    def change_dynamic_storage(self, request, queryset):
        return change_field(self, request, queryset, "change_dynamic_storage",
                            ChangeDynamicStorageForm, "dynamic_storage",
                            "change_field.html", SignalsGuide._meta.verbose_name_plural,
                            {"common": "Таблица хранения значений", "genitive": "таблицы хранения значений"})

    def save_model(self, request, obj: SignalsGuide, form, change):
        if obj.is_changed():
            super().save_model(request, obj, form, change)
            result, message = kafka_use_cases.send_sg_guide(obj)
            if result:
                self.message_user(request, message, messages.SUCCESS)
            else:
                self.message_user(request, message, messages.ERROR)


class ChartTabsAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name')
    list_display_links = ('id', 'code', 'name')
    search_fields = ('id', 'code', 'name')


class AssetsTypeChartTabsAdmin(admin.ModelAdmin):
    list_display = ('id', 'chart_tab', 'asset_type')
    list_display_links = ('id', 'chart_tab', 'asset_type')
    list_filter = ['chart_tab', 'asset_type']
    search_fields = ('id', 'code', 'chart_tab__code', 'asset_type__code')
    list_select_related = ('chart_tab', 'asset_type')


class SignalsChartTabsAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'chart_tab', 'asset')
    list_display_links = ('id', 'code', 'chart_tab', 'asset')
    list_filter = ['chart_tab', 'asset']
    list_select_related = ('asset', 'asset__substation', 'chart_tab',
                           'code', 'code__sg_type')
    autocomplete_fields = ('code',)
    search_fields = ('id', 'code__code', 'code__name', 'chart_tab__code')

    actions = ['change_chart_tab', 'change_asset',]

    @admin.action(description="ИЗМЕНИТЬ вкладку графиков")
    def change_chart_tab(self, request, queryset):
        return change_field(self, request, queryset, "change_chart_tab",
                            ChangeChartTabForm, "chart_tab",
                            "change_field.html",
                            SignalsChartTabs._meta.verbose_name_plural,
                            {"common": "Вкладка графиков",
                             "genitive": "вкладки графиков"})

    @admin.action(description="ИЗМЕНИТЬ оборудование")
    def change_asset(self, request, queryset):
        return change_field(self, request, queryset, "change_asset",
                            ChangeAssetForm, "asset",
                            "change_field.html",
                            SignalsChartTabs._meta.verbose_name_plural,
                            {"common": "Оборудование",
                             "genitive": "оборудования"})


class SignalsChartTabsInLine(admin.TabularInline):
    model = SignalsChartTabs
    extra = 1


class SignalsGuideFrontAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = (
        'id', 'code', 'name', 'sg_type', 'in_plot', 'plot_type',
        'gases_tab', 'power_tab', 'humidity_tab', 'temp_tab', 'bush_tab',
        'wear_tab', 'its_tab')
    list_display_links = (
        'id', 'code', 'name', 'sg_type', 'in_plot', 'plot_type',
        'gases_tab', 'power_tab', 'humidity_tab', 'temp_tab', 'bush_tab',
        'wear_tab', 'its_tab')
    readonly_fields = ['code', 'name', 'sg_type']
    fieldsets = (
        (
            None,
            {
                'fields': (
                    ('code', 'sg_type'),
                    'name',
                    ('in_plot', 'plot_type'),
                )
            }
        ),
    )
    search_fields = ('id', 'code', 'name')
    list_select_related = ('sg_type', 'unit', 'category', 'group', 'data_type',
                           'plot_type', 'databus_source', 'dynamic_storage')
    list_filter = ['sg_type', 'unit', 'category', 'group',
                   'databus_source', 'dynamic_storage', 'data_type',
                   'in_plot', 'plot_type']
    inlines = [SignalsChartTabsInLine]
    actions = ['enabled_true', 'enabled_false']

    @admin.display(description="Вкладка Газы", boolean=True)
    def gases_tab(self, obj):
        sgn_chartab_pk = SignalsChartTabs.objects.filter(
            code=obj, chart_tab__code="gases"
        ).values_list('pk', flat=True).first()
        return bool(sgn_chartab_pk)

    @admin.display(description="Вкладка Состояние вводов", boolean=True)
    def bush_tab(self, obj):
        sgn_chartab_pk = SignalsChartTabs.objects.filter(
            code=obj, chart_tab__code="bushing"
        ).values_list('pk', flat=True).first()
        return bool(sgn_chartab_pk)

    @admin.display(description="Вкладка Мощность", boolean=True)
    def power_tab(self, obj):
        sgn_chartab_pk = SignalsChartTabs.objects.filter(
            code=obj, chart_tab__code="power"
        ).values_list('pk', flat=True).first()
        return bool(sgn_chartab_pk)

    @admin.display(description="Вкладка Температура", boolean=True)
    def temp_tab(self, obj):
        sgn_chartab_pk = SignalsChartTabs.objects.filter(
            code=obj, chart_tab__code="temperature"
        ).values_list('pk', flat=True).first()
        return bool(sgn_chartab_pk)

    @admin.display(description="Вкладка Влагосодержание", boolean=True)
    def humidity_tab(self, obj):
        sgn_chartab_pk = SignalsChartTabs.objects.filter(
            code=obj, chart_tab__code="humidity"
        ).values_list('pk', flat=True).first()
        return bool(sgn_chartab_pk)

    @admin.display(description="Вкладка Износ", boolean=True)
    def wear_tab(self, obj):
        sgn_chartab_pk = SignalsChartTabs.objects.filter(
            code=obj, chart_tab__code="wear"
        ).values_list('pk', flat=True).first()
        return bool(sgn_chartab_pk)

    @admin.display(description="Вкладка ИТС", boolean=True)
    def its_tab(self, obj):
        sgn_chartab_pk = SignalsChartTabs.objects.filter(
            code=obj, chart_tab__code="its"
        ).values_list('pk', flat=True).first()
        return bool(sgn_chartab_pk)

    @admin.action(description="ВКЛЮЧИТЬ вывод на график выбранных сигналов")
    def enabled_true(self, request, queryset):
        """Для выбранных сигналов 'enabled' делается True."""
        try:
            count = queryset.filter(Q(in_plot=False) | Q(in_plot=None)).update(in_plot=True)
        except Exception:
            self.message_user(request, 'ОШИБКА включения вывода на график сигналов. Проверьте данные.',
                              level=messages.ERROR)
        else:
            self.message_user(request, 'ВКЛЮЧЕН вывод на график %s cигналов.' % count)

    @admin.action(description="ОТКЛЮЧИТЬ вывод на график выбранных сигналов")
    def enabled_false(self, request, queryset):
        """Для выбранных сигналов 'enabled' делается False."""
        try:
            count = queryset.filter(in_plot=True).update(in_plot=False)
        except Exception:
            self.message_user(request, 'ОШИБКА отключения вывода на графиксигналов. Проверьте данные.',
                              level=messages.ERROR)
        else:
            self.message_user(request, 'ОТКЛЮЧЕН вывод на график %s cигналов.' % count)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class SignalTypesAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name')
    list_display_links = ('id', 'code', 'name')
    search_fields = ('id', 'code', 'name')


class SubstationsAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'parent', 'name', 'scheme_image')
    list_display_links = ('id', 'type', 'parent', 'name', 'scheme_image')
    search_fields = ('id', 'name', 'parent__name')
    list_filter = ('type',)


class ManualMeasurementsAdmin(admin.ModelAdmin):
    form = MyManualMeasurementsAdminForm

    list_display = ('signal', 'timestamp', 'value')
    list_display_links = ('signal', 'timestamp', 'value')
    search_fields = ('signal__code__code', 'signal__code__name', 'timestamp', 'value')
    autocomplete_fields = ('signal',)
    list_select_related = ['signal', 'signal__code', 'signal__asset', 'signal__device']

    def has_delete_permission(self, request, obj=None):
        return False


class MeasureUnitsAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name')
    list_display_links = ('id', 'code', 'name')
    search_fields = ('id', 'code', 'name',)


class DataTypesAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name')
    list_display_links = ('id', 'code', 'name')
    search_fields = ('id', 'code', 'name',)


class MsgToPlotAdmin(admin.ModelAdmin):
    list_display = ('id', 'diag_model', 'signal', 'value')
    list_display_links = ('id', 'diag_model', 'signal', 'value')
    search_fields = ('diag_model', 'signal', 'value')


class DiagMsgLevelAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')


class GeoMapAdmin(admin.ModelAdmin):
    list_display = ('id', 'collection_code', 'properties', 'linked_obj', 'description')
    list_display_links = ('id', 'collection_code', 'properties', 'linked_obj', 'description')
    search_fields = ('geometry', 'collection_code', 'properties', 'linked_obj__name', 'description')
    list_filter = ('collection_code',)

    def save_model(self, request, obj: GeoMap, form, change):
        if obj.is_changed():
            super().save_model(request, obj, form, change)
            caches[GEOMAP_CACHE].clear()
            hash.clear_hash_in_db(GeoMap._meta.db_table)

    def delete_model(self, request: HttpRequest, obj: GeoMap) -> None:
        response = super().delete_model(request, obj)
        caches[GEOMAP_CACHE].clear()
        hash.clear_hash_in_db(GeoMap._meta.db_table)
        return response

    def delete_queryset(self, request, queryset) -> None:
        response = super().delete_queryset(request, queryset)
        caches[GEOMAP_CACHE].clear()
        hash.clear_hash_in_db(GeoMap._meta.db_table)
        return response


class GeoMapSettingAdmin(admin.ModelAdmin):
    list_display = ('id', 'default_zoom', 'min_zoom', 'max_zoom', 'rotation',
                    'center_x', 'center_y', 'description')
    list_display_links = ('id', 'default_zoom', 'min_zoom', 'max_zoom', 'rotation',
                          'center_x', 'center_y', 'description')
    search_fields = ('default_zoom', 'min_zoom', 'max_zoom', 'rotation',
                     'center_x', 'center_y', 'description')

    def save_model(self, request, obj: GeoMapSetting, form, change):
        if obj.is_changed():
            super().save_model(request, obj, form, change)
            caches[GEOMAP_CACHE].clear()
            hash.clear_hash_in_db(GeoMapSetting._meta.db_table)

    def delete_model(self, request: HttpRequest, obj: GeoMap) -> None:
        response = super().delete_model(request, obj)
        caches[GEOMAP_CACHE].clear()
        hash.clear_hash_in_db(GeoMapSetting._meta.db_table)
        return response

    def delete_queryset(self, request, queryset) -> None:
        response = super().delete_queryset(request, queryset)
        caches[GEOMAP_CACHE].clear()
        hash.clear_hash_in_db(GeoMapSetting._meta.db_table)
        return response


admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.register(AccessPoints, AccessPointsAdmin)
admin.site.register(AssetsType, AssetsTypeAdmin)
admin.site.register(Assets, AssetsAdmin)
admin.site.register(DatabusSources, DatabusSourcesAdmin)
admin.site.register(DeviceModels, DeviceModelsTypeAdmin)
admin.site.register(DeviceTypes, DeviceTypesAdmin)
admin.site.register(Devices, DevicesAdmin)
admin.site.register(DynamicStorages, DynamicStoragesAdmin)
admin.site.register(Formulas, FormulasAdmin)
admin.site.register(ModbusTypes, ModbusTypesAdmin)
admin.site.register(Params, ParamsAdmin)
admin.site.register(PlotTypes, PlotTypesAdmin)
admin.site.register(Protocols, ProtocolsAdmin)
admin.site.register(Schedules, SchedulesAdmin)
admin.site.register(Signals, SignalsAdmin)
admin.site.register(SignalСategories, SignalСategoriesAdmin)
admin.site.register(SignalGroups, SignalGroupsAdmin)
admin.site.register(SignalsGuide, SignalsGuideAdmin)
admin.site.register(SignalsGuideFront, SignalsGuideFrontAdmin)
admin.site.register(ChartTabs, ChartTabsAdmin)
admin.site.register(AssetsTypeChartTabs, AssetsTypeChartTabsAdmin)
admin.site.register(SignalsChartTabs, SignalsChartTabsAdmin)
admin.site.register(SignalTypes, SignalTypesAdmin)
admin.site.register(Substations, SubstationsAdmin)
admin.site.register(ManualMeasurements, ManualMeasurementsAdmin)
admin.site.register(MeasureUnits, MeasureUnitsAdmin)
admin.site.register(DataTypes, DataTypesAdmin)
admin.site.register(MsgToPlot, MsgToPlotAdmin)
admin.site.register(DiagMsgLevel, DiagMsgLevelAdmin)
admin.site.register(GeoMap, GeoMapAdmin)
admin.site.register(GeoMapSetting, GeoMapSettingAdmin)

admin.site.site_title = getenv("ADMIN_SITE_HEADER")
admin.site.site_header = getenv("ADMIN_SITE_HEADER")
admin.site.index_title = "Администрирование"

import logging
from datetime import datetime

from django import forms
from django.core.exceptions import ValidationError

from dashboard.models import (AccessPoints, SignalСategories, SignalGroups,
                              MeasureUnits, DatabusSources, DynamicStorages,
                              Devices, Schedules, ChartTabs, Assets)
from .utils import kafka_drv
from .utils.number import Numeric
from .services.commons.signal_guide_type import _param_types, _SIGNAL


logger = logging.getLogger(__name__)


class MyManualMeasurementsAdminForm(forms.ModelForm):
    def clean(self):
        if self.instance.pk:
            raise ValidationError(
                "Нельзя изменять существующие записи ручных измерений!",
                code="You cannot change existing ManualMeasurements records!",
                params={"params.id": self.instance.pk}
            )

        super().clean()
        signal = self.cleaned_data.get("signal")
        timestamp = self.cleaned_data.get("timestamp")
        value = self.cleaned_data.get("value")

        if not hasattr(signal, "code"):
            raise ValidationError(
                "Значение поля 'Cигнал' не является сигналом",
                code="The value of the 'Signal' field is not a signal",
                params={"timestamp": timestamp, "signal": signal,
                        "value": value},
            )
        if not signal.code:
            raise ValidationError(
                "Выбранный сигнал не имеет связанного кода",
                code="The signal has no associated code",
                params={"timestamp": timestamp, "signal": signal,
                        "value": value},
            )
        if not signal.code.code:
            raise ValidationError(
                "Код выбранного сигнала должен иметь не пустое поле 'Код'",
                code="The code of the selected signal must have a non-empty 'Code' field",
                params={"timestamp": timestamp, "signal": signal,
                        "value": value},
            )
        if not isinstance(timestamp, datetime):
            raise ValidationError(
                "Некорректно заполнено поле 'Время замера'",
                code="The value of the 'Signal' field is not a datetime",
                params={"timestamp": timestamp, "signal": signal,
                        "value": value},
            )

        data = {
            "asset": signal.asset.guid if signal.asset else None,
            "signal": signal.code.code if signal.code else None,
            "value": Numeric.convert_manual_value(value),
            "timestamp": timestamp.timestamp()
        }
        topic = signal.code.databus_source.name if signal.code.databus_source else _SIGNAL

        send_kafka_result = kafka_drv.KafkaProd.send_signal_value(topic, [data,])
        if not send_kafka_result:
            sgn_code = signal.code.code if signal.code else None
            raise ValidationError(
                f"ОШИБКА! Не удалось отправить ручное измерение сигнала {sgn_code} в Kafka.",
                code=f"Failed to send ManualMeasurements {sgn_code} value to Kafka",
                params={"code": sgn_code, "asset": signal.asset, "timestamp": timestamp,
                        "value": value},
            )


class MyParamsAdminForm(forms.ModelForm):
    def clean(self):
        if self.instance.pk:
            raise ValidationError(
                "Нельзя изменять существующие записи значений параметров!",
                code="You cannot change existing parameter value records!",
                params={"params.id": self.instance.pk}
            )

        super().clean()
        code = self.cleaned_data.get("code")
        asset = self.cleaned_data.get("asset")
        value = self.cleaned_data.get("value")
        timestamp = self.instance.timestamp
        if code is None:
            raise ValidationError(
                "Выберите значение в поле 'Код'",
                code="The 'code' field is empty",
                params={"code": code, "asset": asset, "timestamp": timestamp,
                        "value": value},
            )
        if not isinstance(timestamp, datetime):
            raise ValidationError(
                "Ошибка определения момента времени",
                code="The 'timestamp' field is not a datetime type",
                params={"code": code, "asset": asset, "timestamp": timestamp,
                        "value": value},
            )
        if code.sg_type.code not in _param_types:
            raise ValidationError(
                f"Вручную задать значение можно ТОЛЬКО для сигналов с типами: {tuple(_param_types.values())}.",
                code="Incorrectly filled in the form fields",
                params={"code": code, "code.type": code.sg_type, "asset": asset,
                        "timestamp": timestamp, "value": value},
            )
        if not code.databus_source:
            raise ValidationError(
                f"В сигнале {code} не указан топик для отправки значений.",
                code="There is an empty 'databus_source' field in signal_guide",
                params={"code": code, "asset": asset,
                        "timestamp": timestamp, "value": value},
            )

        data = {
            "asset": asset.guid if asset else None,
            "signal": code.code,
            "value": Numeric.convert_manual_value(value),
            "timestamp": timestamp.timestamp()
        }
        topic = code.databus_source.name

        send_kafka_result = kafka_drv.KafkaProd.send_signal_value(topic, [data,])
        if not send_kafka_result:
            raise ValidationError(
                f"ОШИБКА! Не удалось отправить значение параметра {code.code} в Kafka.",
                code=f"Failed to send parameter {code.code} value to Kafka",
                params={"code": code, "asset": asset, "timestamp": timestamp,
                        "value": value},
            )


class ChangeCategoryForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    field = forms.ModelChoiceField(queryset=SignalСategories.objects.all(),
                                   required=False, label='Категория')


class ChangeGroupForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    field = forms.ModelChoiceField(queryset=SignalGroups.objects.all(),
                                   required=False, label='Группа сигналов')


class ChangeUnitForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    field = forms.ModelChoiceField(queryset=MeasureUnits.objects.all(),
                                   required=False, label='Единица измерения')


class ChangeDatabusSourceForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    field = forms.ModelChoiceField(queryset=DatabusSources.objects.all(),
                                   required=False, label='Шина данных')


class ChangeDynamicStorageForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    field = forms.ModelChoiceField(queryset=DynamicStorages.objects.all(),
                                   required=False, label='Таблица хранения значений')


class ChangeDeviceForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    field = forms.ModelChoiceField(queryset=Devices.objects.filter(enabled=True),
                                   label='Источник данных')


class ChangeAccPointForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    field = forms.ModelChoiceField(queryset=AccessPoints.objects.all(),
                                   label='Источник данных')


class ChangeAddressForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    field = forms.CharField(required=False, label='Общий адрес')


class ChangeScheduleForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    field = forms.ModelChoiceField(queryset=Schedules.objects.all(),
                                   label='Расписание')


class ChangeAssetForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    field = forms.ModelChoiceField(queryset=Assets.objects.all(),
                                   required=False, label='Оборудование')


class ChangeChartTabForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    field = forms.ModelChoiceField(queryset=ChartTabs.objects.all(),
                                   required=False, label='Вкладка графиков')

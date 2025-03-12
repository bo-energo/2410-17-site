import logging

from django import forms
from django.core.exceptions import ValidationError


logger = logging.getLogger(__name__)


class MyUiSettingsAdminForm(forms.ModelForm):
    def clean(self):
        super().clean()
        code = self.cleaned_data.get("code")
        value_type = self.cleaned_data.get("value_type")
        value = self.cleaned_data.get("value")

        if value_type == "int":
            try:
                _ = int(value)
            except Exception:
                raise ValidationError(
                    f"Значение {value} не является целым числом",
                    code="The value is not an integer",
                    params={"code": code, "value_type": value_type, "value": value},
                )
        elif value_type == "float":
            try:
                _ = float(value)
            except Exception:
                raise ValidationError(
                    f"Значение {value} не является вещественным числом",
                    code="The value is not an float",
                    params={"code": code, "value_type": value_type, "value": value},
                )

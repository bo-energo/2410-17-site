from typing import Dict
from django.contrib import admin
from django.forms import Form
from django.http import HttpResponseRedirect
from django.shortcuts import render


def change_field(model_admin: admin.ModelAdmin, request, queryset,
                 action: str, form: Form, field: str,
                 page: str, db_model_verbose_name: str,
                 field_verbose_names: Dict[str, str], ):
    """
    Функция изменения значения поля для элементов queryset

    Parameters
    --
    - model_admin - экземпляр типа 'admin.ModelAdmin';
    - queryset - множество изменяемых объектов;
    - action - название метода групповой операции;
    - form - форма изменения значения поля;
    - field - название изменяемого поля, берется из модели элементов 'queryset';
    - page - имя страницы html представляющей форму изменения поля;
    - db_model_verbose_name - имя модели элементов 'queryset' на русском языке;
    - field_verbose_names - словарь названий поля на русском в именительном (ключ common');
    и родительском (ключ 'genitive') падежах.
    """
    _form = None
    if "apply" in request.POST:
        _form = form(request.POST)

        if _form.is_valid():
            field_value = _form.cleaned_data["field"]
            count = 0
            for item in queryset:
                setattr(item, field, field_value)
                item.save()
                count += 1

            model_admin.message_user(request, f"{field_verbose_names.get('common')} {field_value} задана у {count} объектов.")
            return HttpResponseRedirect(request.get_full_path())

    if not _form:
        _form = form(initial={"_selected_action": queryset.values_list("id", flat=True)})
    response = render(request,
                      page,
                      {"items": tuple((el, getattr(el, field, None)) for el in queryset),
                       "form": _form,
                       "action": action,
                       "title": f"{db_model_verbose_name}. Изменение {field_verbose_names.get('genitive')}"})
    return response


def get_asset_image_path(instance, filename):
    """
    Возвращает измененный относительный путь загружаемого изображения актива.
    Новый путь: {path}/{asset_id}_{upload_filename}
    """
    return f"asset_images/{instance.id}_{filename}"


def get_substation_image_path(instance, filename):
    """
    Возвращает измененный относительный путь загружаемой схемы подстанции.
    Новый путь: {path}/{subst_id}_{upload_filename}
    """
    return f"substation_schemes/{instance.id}_{filename}"


def get_asset_scheme_image_path(instance, filename):
    """
    Возвращает измененный относительный путь загружаемой схемы актива.
    Новый путь: {path}/{subst_id}_{upload_filename}
    """
    return f"asset_schemes/{instance.id}_{filename}"

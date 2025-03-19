from django.contrib import admin

from .models import *


class LoadedDataAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'status', 'asset_guid', 'asset_name', 'date_start', 'date_end',
        'data_date_start', 'data_date_end')
    list_display_links = (
        'id', 'status', 'asset_guid', 'asset_name', 'date_start', 'date_end',
        'data_date_start', 'data_date_end')
    search_fields = (
        'id', 'status', 'asset_guid', 'asset_name', 'date_start', 'date_end',
        'data_date_start', 'data_date_end')
    exclude = [
        'timestamp_start', 'timestamp_end', 'data_timestamp_start',
        'data_timestamp_end']
    readonly_fields = (
        'status', 'asset_guid', 'asset_name', 'date_start', 'date_end',
        'data_date_start', 'data_date_end')
    # readonly_fields = ('date_start', 'date_end', 'data_date_start', 'data_date_end')
    list_filter = ('asset_name', 'status')
    actions = None  # Отключает действия, включая удаление
    show_delete_button = False  # Скрывает кнопку удаления

    def has_delete_permission(self, request, obj=None):
        # Запрет удаления
        return False

    def has_add_permission(self, request):
        # Запрет добавления
        return False

    def save_model(self, request, obj, form, change):
        # При нажатии 'Сохранить' изменения не будут сохранены
        pass


admin.site.register(LoadedData, LoadedDataAdmin)

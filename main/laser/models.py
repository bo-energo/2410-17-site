from django.db import models
from django.contrib import admin

from dashboard.utils import time_func


class LoadedData(models.Model):
    statuses = [
        (1, 'Загружены в шину'),
        (2, 'В обработке'),
        (3, 'Обработаны'),
        (4, 'Нет данных'),
        (5, 'Ошибка при обработке'),
    ]
    id = models.BigAutoField(primary_key=True)
    asset_guid = models.CharField(
        max_length=200, verbose_name='GUID оборудования')
    asset_name = models.CharField(
        max_length=200, blank=True, null=True, verbose_name='Наименование оборудования')
    timestamp_start = models.PositiveIntegerField(verbose_name='Начальная метка времени загрузки')
    timestamp_end = models.PositiveIntegerField(verbose_name='Конечная метка времени загрузки')
    data_timestamp_start = models.PositiveIntegerField(
        blank=True, null=True, verbose_name='Начальная метка времени данных')
    data_timestamp_end = models.PositiveIntegerField(
        blank=True, null=True, verbose_name='Конечная метка времени данных')
    status = models.PositiveSmallIntegerField(
        choices=statuses, default=None,
        blank=True, null=True, verbose_name='Статус')

    class Meta:
        managed = True
        db_table = 'loaded_data'
        verbose_name_plural = 'Загрузки данных с приборов'
        verbose_name = 'Загрузка данных'

    def __str__(self) -> str:
        return f"{self.asset_guid} [{self.date_start}, {self.date_end}] {self.status}"

    @property
    @admin.display(description="Начальная дата загрузки")
    def date_start(self):
        if self.timestamp_start is not None:
            return str(time_func.timestamp_to_server_datestr(self.timestamp_start))

    @property
    @admin.display(description="Конечная дата загрузки")
    def date_end(self):
        if self.timestamp_end is not None:
            return str(time_func.timestamp_to_server_datestr(self.timestamp_end))

    @property
    @admin.display(description="Начальная дата данных")
    def data_date_start(self):
        if self.data_timestamp_start is not None:
            return str(time_func.timestamp_to_server_datestr(self.data_timestamp_start))

    @property
    @admin.display(description="Конечная дата данных")
    def data_date_end(self):
        if self.data_timestamp_end is not None:
            return str(time_func.timestamp_to_server_datestr(self.data_timestamp_end))

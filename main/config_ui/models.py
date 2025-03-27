from django.db import models

from dashboard.models import Assets


class UiSettings(models.Model):
    value_types = [
        ("str", "Текст"),
        ("int", "Целое число"),
        ("float", "Вещественное число"),
    ]
    code = models.CharField(primary_key=True, max_length=200, verbose_name='Код')
    name = models.CharField(
        max_length=200, blank=True, null=True, verbose_name='Наименование')
    value_type = models.CharField(
        choices=value_types, default="str",
        verbose_name='Тип значения',)
    value = models.CharField(max_length=1000, verbose_name='Значение')

    class Meta:
        managed = True
        db_table = 'app_settings'
        verbose_name_plural = 'Настройки пользовательского интерфейса'
        verbose_name = 'Настройка пользовательского интерфейса'

    def __str__(self) -> str:
        return f"{self.code}, {self.name}: {self.value}"


# К удалению в будущем
class BlockType(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=50, verbose_name='Код')
    name = models.CharField(max_length=70, blank=True, null=True, verbose_name='Название')

    class Meta:
        managed = True
        db_table = 'block_type'
        verbose_name = 'Тип визуального блока'
        verbose_name_plural = 'Визуальные блоки. Типы'

    def __str__(self) -> str:
        return self.code


class Block(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=50, verbose_name='Код')
    type = models.ForeignKey(BlockType, models.PROTECT, blank=True, null=True, verbose_name='Тип')
    template = models.JSONField(verbose_name='Шаблон')
    description = models.CharField(max_length=150, blank=True, null=True, verbose_name='Описание')

    class Meta:
        managed = True
        db_table = 'block'
        verbose_name = 'Визуальный блок'
        verbose_name_plural = 'Визуальные блоки'

    def __str__(self) -> str:
        if self.type:
            return f"({self.type}) {self.code}"
        else:
            return self.code


class Panel(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=50, verbose_name='Код')
    template = models.JSONField(verbose_name='Шаблон')
    description = models.CharField(max_length=150, blank=True, null=True, verbose_name='Описание')

    class Meta:
        managed = True
        db_table = 'panel'
        verbose_name = 'Панель'
        verbose_name_plural = 'Панели'

    def __str__(self) -> str:
        return self.code


class PanelBlock(models.Model):
    id = models.BigAutoField(primary_key=True)
    panel = models.ForeignKey(
        Panel, models.PROTECT, verbose_name='Панель')
    block = models.ForeignKey(
        Block, models.CASCADE, blank=True, null=True, verbose_name='Блок')
    x = models.PositiveIntegerField(default=1, verbose_name='Левый верхний угол. Х')
    y = models.PositiveIntegerField(default=1, verbose_name='Левый верхний угол. Y')
    w = models.PositiveIntegerField(default=1, verbose_name='Ширина')
    h = models.PositiveIntegerField(default=1, verbose_name='Высота')
    min_w = models.PositiveIntegerField(blank=True, null=True, verbose_name='Минимальная ширина')
    min_h = models.PositiveIntegerField(blank=True, null=True, verbose_name='Минимальная высота')

    class Meta:
        managed = True
        db_table = 'panel_block'
        constraints = [
            models.UniqueConstraint(fields=['panel', 'block'], name='unique_panelblock')
        ]
        verbose_name = 'Блок панели'
        verbose_name_plural = 'Панели. Блоки'

    def __str__(self) -> str:
        return f"{self.panel}, {self.block}"


class PageType(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=50, verbose_name='Код')
    name = models.CharField(max_length=70, blank=True, null=True, verbose_name='Название')

    class Meta:
        managed = True
        db_table = 'page_type'
        verbose_name = 'Тип страницы'
        verbose_name_plural = 'Страницы пользовательского интерфейса. Типы'

    def __str__(self) -> str:
        return self.code


class Page(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=50, verbose_name='Код')
    type = models.ForeignKey(PageType, models.PROTECT, verbose_name='Тип')
    description = models.CharField(max_length=150, blank=True, null=True, verbose_name='Описание')

    class Meta:
        managed = True
        db_table = 'page'
        verbose_name = 'Cтраница пользовательского интерфейса'
        verbose_name_plural = 'Страницы пользовательского интерфейса'

    def __str__(self) -> str:
        return f"({self.type}) {self.code}"


class PagePanel(models.Model):
    id = models.BigAutoField(primary_key=True)
    page = models.ForeignKey(
        Page, models.PROTECT, verbose_name='Страница')
    panel = models.ForeignKey(
        Panel, models.CASCADE, verbose_name='Панель')
    x = models.PositiveIntegerField(default=1, verbose_name='Левый верхний угол. Х')
    y = models.PositiveIntegerField(default=1, verbose_name='Левый верхний угол. Y')
    w = models.PositiveIntegerField(default=1, verbose_name='Ширина')
    h = models.PositiveIntegerField(default=1, verbose_name='Высота')
    min_w = models.PositiveIntegerField(blank=True, null=True, verbose_name='Минимальная ширина')
    min_h = models.PositiveIntegerField(blank=True, null=True, verbose_name='Минимальная высота')

    class Meta:
        managed = True
        db_table = 'page_panel'
        constraints = [
            models.UniqueConstraint(fields=['page', 'panel'], name='unique_pagepanel')
        ]
        verbose_name = 'Панель страницы'
        verbose_name_plural = 'Страницы пользовательского интерфейса. Панели'

    def __str__(self) -> str:
        return f"{self.page}, {self.panel}"


class PageBlockLocation(models.Model):
    id = models.BigAutoField(primary_key=True)
    page = models.ForeignKey(
        Page, models.CASCADE, verbose_name='Страница')
    panel = models.ForeignKey(
        Panel, models.CASCADE, verbose_name='Панель')
    block = models.ForeignKey(
        Block, models.CASCADE, verbose_name='Блок')
    x = models.PositiveIntegerField(default=1, verbose_name='Левый верхний угол. Х')
    y = models.PositiveIntegerField(default=1, verbose_name='Левый верхний угол. Y')
    w = models.PositiveIntegerField(default=1, verbose_name='Ширина')
    h = models.PositiveIntegerField(default=1, verbose_name='Высота')
    min_w = models.PositiveIntegerField(blank=True, null=True, verbose_name='Минимальная ширина')
    min_h = models.PositiveIntegerField(blank=True, null=True, verbose_name='Минимальная высота')

    class Meta:
        managed = True
        db_table = 'page_block_location'
        verbose_name = 'Расположение блока страницы'
        verbose_name_plural = 'Страницы пользовательского интерфейса. Блоки. Расположение'

    def __str__(self) -> str:
        return f"{self.page}, {self.panel}, {self.block}"


class PagePanelLocation(models.Model):
    id = models.BigAutoField(primary_key=True)
    page = models.ForeignKey(
        Page, models.CASCADE, verbose_name='Страница')
    panel = models.ForeignKey(
        Panel, models.CASCADE, verbose_name='Панель')
    x = models.PositiveIntegerField(default=1, verbose_name='Левый верхний угол. Х')
    y = models.PositiveIntegerField(default=1, verbose_name='Левый верхний угол. Y')
    w = models.PositiveIntegerField(default=1, verbose_name='Ширина')
    h = models.PositiveIntegerField(default=1, verbose_name='Высота')
    min_w = models.PositiveIntegerField(blank=True, null=True, verbose_name='Минимальная ширина')
    min_h = models.PositiveIntegerField(blank=True, null=True, verbose_name='Минимальная высота')

    class Meta:
        managed = True
        db_table = 'page_panel_location'
        verbose_name = 'Расположение панели страницы'
        verbose_name_plural = 'Страницы пользовательского интерфейса. Панели. Расположение'

    def __str__(self) -> str:
        return f"{self.page}, {self.panel}"


class AssetPage(models.Model):
    id = models.BigAutoField(primary_key=True)
    asset = models.ForeignKey(
        Assets, models.CASCADE, verbose_name='Оборудование')
    page = models.ForeignKey(
        Page, models.PROTECT, verbose_name='Страница')

    class Meta:
        managed = True
        db_table = 'asset_page'
        verbose_name = 'Оборудование. Страница пользовательского интерфейса'
        verbose_name_plural = 'Оборудование. Страницы пользовательского интерфейса'
        constraints = [
            models.UniqueConstraint(fields=['asset', 'page'], name='unique_assetpage')
        ]

    def __str__(self) -> str:
        return f"{self.asset} - {self.page}"


class PassportCategories(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=100, verbose_name='Код')
    name = models.CharField(max_length=300, verbose_name='Наименование')
    order = models.IntegerField(default=2000000000, verbose_name='Порядковый номер')

    class Meta:
        managed = True
        db_table = 'passport_categories'
        verbose_name_plural = 'Паспорт. Категории данных'
        verbose_name = 'Категория паспортных данных'

    def __str__(self) -> str:
        return self.name


class PassportSignals(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=100, verbose_name='Код сигнала')
    pdata_category = models.ForeignKey(
        PassportCategories, models.PROTECT, verbose_name='Категория паспортных данных')
    order = models.IntegerField(default=2000000000, verbose_name='Порядковый номер')

    class Meta:
        managed = True
        db_table = 'passport_signals'
        verbose_name_plural = 'Паспорт. Используемые коды сигналов'
        verbose_name = 'Код сигнала паспорта'

    def __str__(self) -> str:
        return f"{self.code}, {str(self.pdata_category)}"

import logging
from django.db import models
from dashboard.models import (DiagMsgLevel, SignalsGuide, SignalСategories,
                              MeasureUnits, AssetsType)


logger = logging.getLogger(__name__)


class Langs(models.Model):
    code = models.CharField(primary_key=True, max_length=100, verbose_name='Код')
    name = models.CharField(
        max_length=200, verbose_name='Наименование')

    class Meta:
        managed = True
        db_table = 'langs'
        verbose_name_plural = 'Языки интерфейса'
        verbose_name = 'Язык интерфейса'

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class DiagMsgTemplates(models.Model):
    num_code = models.PositiveBigIntegerField(primary_key=True, verbose_name='Код')
    code = models.CharField(
        max_length=200, verbose_name='Строковый код')

    class Meta:
        managed = True
        db_table = 'diagmsg_templates'
        verbose_name_plural = 'Шаблоны диагностических сообщений. Коды'
        verbose_name = 'Код шаблона диагностического сообщения'

    def __str__(self) -> str:
        return f"{self.num_code} - {self.code}"


class DiagMsgTranslts(models.Model):
    id = models.BigAutoField(primary_key=True)
    msg = models.ForeignKey(
        DiagMsgTemplates, models.DO_NOTHING, db_column='msg_id', verbose_name='Шаблон диаг. сообщения')
    lang = models.ForeignKey(
        Langs, models.DO_NOTHING, db_column='lang_id', verbose_name='Язык')
    content = models.CharField(
        max_length=1500, verbose_name='Содержание')

    class Meta:
        managed = True
        db_table = 'diagmsg_translts'
        verbose_name_plural = 'Шаблоны диагностических сообщений. Переводы'
        verbose_name = 'Перевод шаблона диагностического сообщения'
        constraints = [
            models.UniqueConstraint(fields=['msg', 'lang'], name='unique_diagmsgtranslts')
        ]

    def __str__(self) -> str:
        return f"{self.msg} - {self.lang}: {self.content}"


class APILabels(models.Model):
    code = models.CharField(primary_key=True, max_length=200, verbose_name='Метка')

    class Meta:
        managed = True
        db_table = 'api_labels'
        verbose_name_plural = 'API. Метки'
        verbose_name = 'Метка API'

    def __str__(self) -> str:
        return self.code


class APILabelsTranslts(models.Model):
    id = models.BigAutoField(primary_key=True)
    label = models.ForeignKey(
        APILabels, models.DO_NOTHING, db_column='label',
        verbose_name='Метка API')
    lang = models.ForeignKey(
        Langs, models.DO_NOTHING, db_column='lang_id', verbose_name='Язык')
    content = models.CharField(
        max_length=500, verbose_name='Содержание')

    class Meta:
        managed = True
        db_table = 'api_labels_translts'
        verbose_name_plural = 'API. Метки. Переводы меток'
        verbose_name = 'Перевод метки API'
        constraints = [
            models.UniqueConstraint(fields=['label', 'lang'], name='unique_apilabelstranslts')
        ]

    def __str__(self) -> str:
        return f"{self.label} - {self.lang}: {self.content}"


class Interfacelabels(models.Model):
    code = models.CharField(primary_key=True, max_length=200, verbose_name='Метка')

    class Meta:
        managed = True
        db_table = 'interface_labels'
        verbose_name_plural = 'Пользовательский интерфейс. Метки'
        verbose_name = 'Метка пользовательского интерфейса'

    def __str__(self) -> str:
        return self.code


class InterfaceTranslts(models.Model):
    id = models.BigAutoField(primary_key=True)
    label = models.ForeignKey(
        Interfacelabels, models.DO_NOTHING, db_column='label',
        verbose_name='Метка польз. интерфейса')
    lang = models.ForeignKey(
        Langs, models.DO_NOTHING, db_column='lang_id', verbose_name='Язык')
    content = models.CharField(
        max_length=500, verbose_name='Содержание')

    class Meta:
        managed = True
        db_table = 'interface_translts'
        verbose_name_plural = 'Пользовательский интерфейс. Переводы меток'
        verbose_name = 'Перевод метки пользовательского интерфейса'
        constraints = [
            models.UniqueConstraint(fields=['label', 'lang'], name='unique_interfacetranslts')
        ]

    def __str__(self) -> str:
        return f"{self.label} - {self.lang}: {self.content}"


class DiagMsgLevelTranslts(models.Model):
    id = models.BigAutoField(primary_key=True)
    level = models.ForeignKey(
        DiagMsgLevel, models.DO_NOTHING, db_column='level',
        verbose_name='Уровень критичности')
    lang = models.ForeignKey(
        Langs, models.DO_NOTHING, db_column='lang_id', verbose_name='Язык')
    content = models.CharField(
        max_length=500, verbose_name='Содержание')

    class Meta:
        managed = True
        db_table = 'diag_msg_level_translts'
        verbose_name_plural = 'Уровни критичности диаг. сообщений. Переводы'
        verbose_name = 'Перевод уровня критичности диаг. сообщений'
        constraints = [
            models.UniqueConstraint(fields=['level', 'lang'], name='unique_diagmsgleveltranslts')
        ]

    def __str__(self) -> str:
        return f"{self.level} - {self.lang}: {self.content}"


class SignalsGuideTranslts(models.Model):
    id = models.BigAutoField(primary_key=True)
    sgn_guide = models.ForeignKey(
        SignalsGuide, models.DO_NOTHING, db_column='sgn_guide',
        verbose_name='Код сигнала')
    lang = models.ForeignKey(
        Langs, models.DO_NOTHING, db_column='lang_id', verbose_name='Язык')
    content = models.CharField(
        max_length=500, verbose_name='Содержание')

    class Meta:
        managed = True
        db_table = 'signals_guide_translts'
        verbose_name_plural = 'Сигналы. Коды. Переводы'
        verbose_name = 'Перевод названия кода сигнала'
        constraints = [
            models.UniqueConstraint(fields=['sgn_guide', 'lang'], name='unique_signalsguidetranslts')
        ]

    def __str__(self) -> str:
        return f"{self.sgn_guide.code} - {self.lang}: {self.content}"


class SignalsCategoriesTranslts(models.Model):
    id = models.BigAutoField(primary_key=True)
    category = models.ForeignKey(
        SignalСategories, models.DO_NOTHING, db_column='category',
        verbose_name='Категория сигнала')
    lang = models.ForeignKey(
        Langs, models.DO_NOTHING, db_column='lang_id', verbose_name='Язык')
    content = models.CharField(
        max_length=500, verbose_name='Содержание')

    class Meta:
        managed = True
        db_table = 'signals_categories_translts'
        verbose_name_plural = 'Сигналы. Категории. Переводы'
        verbose_name = 'Перевод названия категории сигнала'
        constraints = [
            models.UniqueConstraint(fields=['category', 'lang'], name='unique_signalscategoriestranslts')
        ]

    def __str__(self) -> str:
        return f"{self.category.name} - {self.lang}: {self.content}"


class PassportCategoriesTranslts(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=100, verbose_name='Код категории')
    lang = models.ForeignKey(
        Langs, models.DO_NOTHING, db_column='lang_id', verbose_name='Язык')
    content = models.CharField(
        max_length=500, verbose_name='Содержание')

    class Meta:
        managed = True
        db_table = 'passport_categories_translts'
        verbose_name_plural = 'Паспорт. Категории данных. Переводы'
        verbose_name = 'Перевод категории паспортных данных'
        constraints = [
            models.UniqueConstraint(fields=['code', 'lang'], name='unique_passportcategoriestranslts')
        ]

    def __str__(self) -> str:
        return f"{self.code} - {self.lang}: {self.content}"


class MeasureUnitsTranslts(models.Model):
    id = models.BigAutoField(primary_key=True)
    unit = models.ForeignKey(
        MeasureUnits, models.DO_NOTHING, db_column='unit',
        verbose_name='Единица измерения')
    lang = models.ForeignKey(
        Langs, models.DO_NOTHING, db_column='lang_id', verbose_name='Язык')
    content = models.CharField(
        max_length=500, verbose_name='Содержание')

    class Meta:
        managed = True
        db_table = 'measure_units_translts'
        verbose_name_plural = 'Сигналы. Единицы измерения. Переводы'
        verbose_name = 'Перевод названия единицы измерения'
        constraints = [
            models.UniqueConstraint(fields=['unit', 'lang'], name='unique_measureunitstranslts')
        ]

    def __str__(self) -> str:
        return f"{self.unit.code} - {self.lang}: {self.content}"


class AssetsTypeTranslts(models.Model):
    id = models.BigAutoField(primary_key=True)
    a_type = models.ForeignKey(
        AssetsType, models.DO_NOTHING, db_column='a_type',
        verbose_name='Категория оборудования')
    lang = models.ForeignKey(
        Langs, models.DO_NOTHING, db_column='lang_id', verbose_name='Язык')
    content = models.CharField(
        max_length=500, verbose_name='Содержание')

    class Meta:
        managed = True
        db_table = 'asset_type_translts'
        verbose_name_plural = 'Категории оборудования. Переводы'
        verbose_name = 'Перевод категории оборудования'
        constraints = [
            models.UniqueConstraint(fields=['a_type', 'lang'], name='unique_assetstypetranslts')
        ]

    def __str__(self) -> str:
        return f"{self.a_type.code} - {self.lang}: {self.content}"

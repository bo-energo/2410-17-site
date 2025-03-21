# Generated by Django 4.2.19 on 2025-03-05 10:48

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LoadedData',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('asset_guid', models.CharField(max_length=200, verbose_name='GUID оборудования')),
                ('asset_name', models.CharField(blank=True, max_length=200, null=True, verbose_name='Наименование оборудования')),
                ('timestamp_start', models.PositiveIntegerField(verbose_name='Начальная метка времени загрузки')),
                ('timestamp_end', models.PositiveIntegerField(verbose_name='Конечная метка времени загрузки')),
                ('data_timestamp_start', models.PositiveIntegerField(blank=True, null=True, verbose_name='Начальная метка времени данных')),
                ('data_timestamp_end', models.PositiveIntegerField(blank=True, null=True, verbose_name='Конечная метка времени данных')),
                ('status', models.PositiveSmallIntegerField(blank=True, choices=[(1, 'Загружены в шину'), (2, 'В обработке'), (3, 'Обработаны'), (4, 'Ошибка при обработке')], default=None, null=True, verbose_name='Статус')),
            ],
            options={
                'verbose_name': 'Загрузка данных',
                'verbose_name_plural': 'Загрузки данных с приборов',
                'db_table': 'loaded_data',
                'managed': True,
            },
        ),
    ]

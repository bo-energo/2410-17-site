from django.urls import path

from . import views


urlpatterns = [
    path('', views.index, name='home'),
    # оборудование с статусами в разрезе подстанций
    path('substations', views.substations, name='substations'),
    # информация о подстанции
    path('substation/<int:objId>', views.substation_info, name='substation_info'),
    # последние диаг. сообщения системы
    path('diag-messages/last', views.get_diagmsg_last, name='get_diagmsg_last'),

    # диагностические сообщения для одного актива
    path('asset/<int:objId>/diagmess', views.asset_diag_mess, name='asset_diag_mess'),
    # последние значения сигналов для актива
    path('asset/<int:assetId>/meterings/last', views.last_meterings, name='last_meterings'),
    # значения сигналов за диапазон времени для актива для графиков
    path('asset/<int:assetId>/meterings/<str:tab>/charts', views.meterings_for_charts, name='meterings_for_charts'),
    # значения сигналов за диапазон времени для актива для графика гистерезиса
    path('asset/<int:assetId>/meterings/<str:tab>/hysteresis', views.hysteresis, name='hysteresis'),
    # статусы превышения лимитов отношений газов по методике РД
    path('asset/<int:assetId>/meterings/gases/rdTable', views.rd_table, name='rd_table'),
    # отношения концентраций газов по методу треугольника Дюваля
    path('asset/<int:assetId>/meterings/gases/triangle', views.duval_triangle, name='duval_triangle'),
    # координаты точки статуса концентраций газов для пятиугольника Дюваля
    path('asset/<int:assetId>/meterings/gases/pentagon', views.duval_pentagon, name='duval_pentagon'),
    # данные диагностики по методу номограм
    path('asset/<int:assetId>/meterings/gases/rdnomogram', views.rd_nomogram, name='rd_nomogram'),
    # данные 3D прогноза концентраций
    path('asset/<int:assetId>/3dforecast', views.forecast_3d, name='forecast_3d'),
    # cоздание файла экспорта диаг. сообщений
    path('asset/<int:objId>/diagmsg/export/create', views.diag_mess_to_file, name='diag_mess_to_file'),
    # cоздание файла экспорта паспорта
    path('asset/<int:assetId>/passport/export/create', views.passport_to_file, name='passport_to_file'),
    # cоздание файла экспорта лимитов и констант
    path('asset/<int:assetId>/diag_settings/export/create', views.diag_settings_to_file, name='diag_settings_to_file'),
    # оборудование в разрезе подстанций (без статусов)
    path('assets', views.get_assets, name='assets'),
    # устройства ассета и статистика по ним
    path('asset/<str:assetGuid>/devicesStats', views.devices_stats, name='devices'),
    # статистика считывания сигнала
    path('signalStats', views.signal_stats, name='signal_stats'),
    # статистика запуска моделей
    path('modelsStats', views.get_models_stats_view, name='models_stats'),
    # подробная статистика запуска модели
    path('modelStats', views.get_model_stats_view, name='model_stats'),
    path('access_points/<int:access_point_id>', views.update_access_point, name='update_access_point'),

    # Получение файла экспорта
    path('export/file', views.get_export_file, name='get_export_file'),

    # карта
    path('geomap', views.geomap, name='geomap'),
    # организационная структура объектов
    path('org-struct', views.get_org_struct, name='get_org_struct'),
    # справочник уведомлений системы
    path('notification-guide', views.get_notification_guide, name='get_notification_guide'),
    # список вкладок графиков в разрезе типов оборудования
    path('tabs-list', views.get_tabs_list, name='get_tabs_list'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('laser/online', views.online, name='online'),
    path('laser/read-data', views.read_data, name='read_data'),
    path('laser/loadings-info', views.get_all_loaded_data_info, name='get_all_loaded_data_info'),
    path('laser/loaded-data', views.get_loaded_data_info, name='get_loaded_data_info'),
    path('check-diag-settings', views.check_diag_settings, name='check_diag_settings'),
]

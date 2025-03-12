from django.urls import path
from . import views

urlpatterns = [
    path('blocks/info', views.update_blocks_info, name='update_blocks_info'),
    path('ui/settings', views.ui_settings, name='ui_settings'),
]

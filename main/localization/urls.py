from django.urls import path
from . import views

urlpatterns = [
    path('langs', views.get_langs, name='langs'),
    path('translation/<str:lng>', views.get_translated_interface, name='translated_interface')
]

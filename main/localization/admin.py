import logging
from os import getenv
from django.contrib import admin

from .models import *


logger = logging.getLogger(__name__)


class LangsAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    list_display_links = ('code', 'name')
    search_fields = ('code', 'name')


class DiagMsgTemplatesAdmin(admin.ModelAdmin):
    list_display = ('num_code', 'code')
    list_display_links = ('num_code', 'code')
    search_fields = ('num_code', 'code')


class DiagMsgTransltsAdmin(admin.ModelAdmin):
    list_display = ('msg', 'lang', 'content')
    list_display_links = ('msg', 'lang', 'content')
    search_fields = ('msg__num_code', 'msg__code', 'lang__code', 'lang__name', 'content')
    list_select_related = ['msg', 'lang']
    autocomplete_fields = ('msg',)
    list_filter = ('lang', 'msg')


class DiagMsgLevelTransltsAdmin(admin.ModelAdmin):
    list_display = ('level', 'lang', 'content')
    list_display_links = ('level', 'lang', 'content')
    search_fields = ('level__level', 'lang__code', 'lang__name', 'content')
    list_select_related = ['level', 'lang']
    autocomplete_fields = ('level',)
    list_filter = ('lang', 'level')


class APILabelsAdmin(admin.ModelAdmin):
    list_display = ('code',)
    search_fields = ('code',)


class APILabelsTransltsAdmin(admin.ModelAdmin):
    list_display = ('label', 'lang', 'content')
    list_display_links = ('label', 'lang', 'content')
    search_fields = ('label__code', 'lang__code', 'lang__name', 'content')
    list_select_related = ['label', 'lang']
    autocomplete_fields = ('label',)
    list_filter = ('lang', 'label')


class InterfacelabelsAdmin(admin.ModelAdmin):
    list_display = ('code',)
    search_fields = ('code',)


class InterfaceTransltsAdmin(admin.ModelAdmin):
    list_display = ('label', 'lang', 'content')
    list_display_links = ('label', 'lang', 'content')
    search_fields = ('label__code', 'lang__code', 'lang__name', 'content')
    list_select_related = ['label', 'lang']
    autocomplete_fields = ('label',)
    list_filter = ('lang', 'label')


class SignalsGuideTransltsAdmin(admin.ModelAdmin):
    list_display = ('sgn_guide', 'lang', 'content')
    list_display_links = ('sgn_guide', 'lang', 'content')
    search_fields = ('sgn_guide__code', 'sgn_guide__name', 'lang__code', 'lang__name', 'content')
    list_select_related = ['lang', 'sgn_guide', 'sgn_guide__sg_type', 'sgn_guide__category']
    autocomplete_fields = ('sgn_guide',)
    list_filter = ('lang', 'sgn_guide__in_plot', 'sgn_guide__sg_type', 'sgn_guide__category')


class SignalsCategoriesTransltsAdmin(admin.ModelAdmin):
    list_display = ('category', 'lang', 'content')
    list_display_links = ('category', 'lang', 'content')
    search_fields = ('category__name', 'lang__code', 'lang__name', 'content')
    list_select_related = ['lang', 'category']
    list_filter = ('lang', 'category')


class MeasureUnitsTransltsAdmin(admin.ModelAdmin):
    list_display = ('unit', 'lang', 'content')
    list_display_links = ('unit', 'lang', 'content')
    search_fields = ('unit__name', 'unit__code', 'lang__code', 'lang__name', 'content')
    list_select_related = ['lang', 'unit']
    list_filter = ('lang', 'unit')


class AssetsTypeTransltsAdmin(admin.ModelAdmin):
    list_display = ('a_type', 'lang', 'content')
    list_display_links = ('a_type', 'lang', 'content')
    search_fields = ('a_type__name', 'a_type__code', 'lang__code', 'lang__name', 'content')
    list_select_related = ['lang', 'a_type']
    list_filter = ('lang', 'a_type')


admin.site.register(Langs, LangsAdmin)
admin.site.register(DiagMsgTemplates, DiagMsgTemplatesAdmin)
admin.site.register(DiagMsgTranslts, DiagMsgTransltsAdmin)
admin.site.register(DiagMsgLevelTranslts, DiagMsgLevelTransltsAdmin)
admin.site.register(APILabels, APILabelsAdmin)
admin.site.register(APILabelsTranslts, APILabelsTransltsAdmin)
admin.site.register(Interfacelabels, InterfacelabelsAdmin)
admin.site.register(InterfaceTranslts, InterfaceTransltsAdmin)
admin.site.register(SignalsGuideTranslts, SignalsGuideTransltsAdmin)
admin.site.register(SignalsCategoriesTranslts, SignalsCategoriesTransltsAdmin)
admin.site.register(MeasureUnitsTranslts, MeasureUnitsTransltsAdmin)
admin.site.register(AssetsTypeTranslts, AssetsTypeTransltsAdmin)

admin.site.site_title = getenv("ADMIN_SITE_HEADER")
admin.site.site_header = getenv("ADMIN_SITE_HEADER")

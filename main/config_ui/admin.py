from django.contrib import admin

from .models import *
from .admin_form import MyUiSettingsAdminForm


class UiSettingsAdmin(admin.ModelAdmin):
    form = MyUiSettingsAdminForm
    list_display = ('code', 'name', 'value_type', 'value')
    list_display_links = ('code', 'name', 'value_type', 'value')
    search_fields = ('code', 'name', 'value_type', 'value')


# К удалению в будущем
class BlockTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name')
    list_display_links = ('id', 'code', 'name')
    search_fields = ('id', 'code', 'name')


class BlockAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'type', 'template', 'description')
    list_display_links = ('id', 'code', 'type', 'template', 'description')
    search_fields = ('id', 'code', 'type__code', 'template', 'description')
    list_select_related = ('type',)
    list_filter = ['type',]


class PanelAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'template', 'description')
    list_display_links = ('id', 'code', 'template', 'description')
    search_fields = ('id', 'code', 'template', 'description')


class PanelBlockAdmin(admin.ModelAdmin):
    list_display = ('id', 'panel', 'block', 'x', 'y', 'w', 'h', 'min_w', 'min_h')
    list_display_links = ('id', 'panel', 'block', 'x', 'y', 'w', 'h', 'min_w', 'min_h')
    search_fields = ('id', 'panel_code', 'block_code', 'x', 'y', 'w', 'h', 'min_w', 'min_h')
    list_select_related = ('panel', 'block', 'block__type')
    list_filter = ['panel']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "panel":
            kwargs["queryset"] = Panel.objects.order_by('code')
        elif db_field.name == "block":
            kwargs["queryset"] = Block.objects.select_related("type").order_by('type__code', 'code')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class PageTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name')
    list_display_links = ('id', 'code', 'name')
    search_fields = ('id', 'code', 'name')


class PageAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'type', 'description')
    list_display_links = ('id', 'code', 'type', 'description')
    search_fields = ('id', 'code', 'type_code', 'type_name', 'description')
    list_select_related = ('type',)
    list_filter = ['type',]


# К удалению в будущем
class PageBlockAdmin(admin.ModelAdmin):
    list_display = ('id', 'page', 'block', 'x', 'y', 'w', 'h', 'min_w', 'min_h')
    list_display_links = ('id', 'page', 'block', 'x', 'y', 'w', 'h', 'min_w', 'min_h')
    search_fields = ('id', 'page_code', 'block_code', 'x', 'y', 'w', 'h', 'min_w', 'min_h')
    list_select_related = ('page', 'block')
    list_filter = ['page', 'block']


class PagePanelAdmin(admin.ModelAdmin):
    list_display = ('id', 'page', 'panel', 'x', 'y', 'w', 'h', 'min_w', 'min_h')
    list_display_links = ('id', 'page', 'panel', 'x', 'y', 'w', 'h', 'min_w', 'min_h')
    search_fields = ('id', 'page_code', 'panel_code', 'x', 'y', 'w', 'h', 'min_w', 'min_h')
    list_select_related = ('page', 'panel')
    list_filter = ['page', 'panel']


class PageBlockLocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'page', 'panel', 'block', 'x', 'y', 'w', 'h', 'min_w', 'min_h')
    list_display_links = ('id', 'page', 'panel', 'block', 'x', 'y', 'w', 'h', 'min_w', 'min_h')
    search_fields = ('id', 'page_code', 'panel_code', 'block__code', 'x', 'y', 'w', 'h', 'min_w', 'min_h')
    list_select_related = ('page', 'panel', 'block')
    list_filter = ['page', 'panel']


class PagePanelLocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'page', 'panel',  'x', 'y', 'w', 'h', 'min_w', 'min_h')
    list_display_links = ('id', 'page', 'panel', 'x', 'y', 'w', 'h', 'min_w', 'min_h')
    search_fields = ('id', 'page_code', 'panel_code', 'x', 'y', 'w', 'h', 'min_w', 'min_h')
    list_select_related = ('page', 'panel')
    list_filter = ['page', 'panel']


class AssetPageAdmin(admin.ModelAdmin):
    list_display = ('id', 'asset', 'page')
    list_display_links = ('id', 'asset', 'page')
    search_fields = ('id', 'asset_guid', 'asset_name', 'page_code')
    list_select_related = ('asset', 'page')
    list_filter = ['asset', 'page']


admin.site.register(UiSettings, UiSettingsAdmin)
admin.site.register(BlockType, BlockTypeAdmin)
admin.site.register(Block, BlockAdmin)
admin.site.register(Panel, PanelAdmin)
admin.site.register(PanelBlock, PanelBlockAdmin)
admin.site.register(PageType, PageTypeAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(PageBlock, PageBlockAdmin)
admin.site.register(PagePanel, PagePanelAdmin)
admin.site.register(PageBlockLocation, PageBlockLocationAdmin)
admin.site.register(PagePanelLocation, PagePanelLocationAdmin)
admin.site.register(AssetPage, AssetPageAdmin)

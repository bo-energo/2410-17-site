from typing import List
from localization.models import (DiagMsgTemplates, Langs, DiagMsgTranslts,
                                 APILabels, APILabelsTranslts, Interfacelabels,
                                 InterfaceTranslts, SignalsGuideTranslts,
                                 MeasureUnitsTranslts, SignalsCategoriesTranslts,
                                 DiagMsgLevelTranslts, PassportCategoriesTranslts)
from dashboard.models import DiagMsgLevel, SignalsGuide, MeasureUnits, SignalСategories
from .manager import ImportManager
from .keys import ForeignKey
from .fields import Field, HorizontalField, CrossField


import_langs = [
    ImportManager(
        model=Langs,
        sheet_name="Langs",
        fields=[
            Field("pk", 2, is_pkey=True),
            Field("code", 2),
            Field("name", 3, is_defaults=True)
        ],
    ),
]

imports_for_migration = [
    ImportManager(
        model=DiagMsgTemplates,
        sheet_name="DiagMsgTranslts",
        fields=[
            Field("pk", 2, is_pkey=True),
            Field("num_code", 2),
            Field("code", 3, is_defaults=True)
        ],
    ),
    ImportManager(
        model=DiagMsgTranslts,
        sheet_name="DiagMsgTranslts",
        fields=[
            Field("pk", 1, is_pkey=True),
            Field("msg", 2, foreign_key=ForeignKey(None, DiagMsgTemplates, "num_code"))
        ],
        horizontal_field=HorizontalField(
            "lang", 1, [4, 5],
            cross_field=CrossField("content", True),
            foreign_key=ForeignKey(None, Langs, "code")),
    ),
    ImportManager(
        model=APILabels,
        sheet_name="APILabelsTranslts",
        fields=[
            Field("pk", 1, is_pkey=True),
            Field("code", 2)
        ],
    ),
    ImportManager(
        model=APILabelsTranslts,
        sheet_name="APILabelsTranslts",
        fields=[
            Field("pk", 1, is_pkey=True),
            Field("label", 2, foreign_key=ForeignKey(None, APILabels, "code"))
        ],
        horizontal_field=HorizontalField(
            "lang", 1, [3, 4],
            cross_field=CrossField("content", True),
            foreign_key=ForeignKey(None, Langs, "code")),
    ),
    ImportManager(
        model=Interfacelabels,
        sheet_name="InterfaceTranslts",
        fields=[
            Field("pk", 1, is_pkey=True),
            Field("code", 2)
        ],
    ),
    ImportManager(
        model=InterfaceTranslts,
        sheet_name="InterfaceTranslts",
        fields=[
            Field("pk", 1, is_pkey=True),
            Field("label", 2, foreign_key=ForeignKey(None, Interfacelabels, "code"))
        ],
        horizontal_field=HorizontalField(
            "lang", 1, [3, 4],
            cross_field=CrossField("content", True),
            foreign_key=ForeignKey(None, Langs, "code")),
    ),
    ImportManager(
        model=DiagMsgLevel,
        sheet_name="DiagMsgLevelTranslts",
        fields=[
            Field("pk", 1, is_pkey=True),
            Field("code", 2),
            Field("name", 3)
        ],
    ),
    ImportManager(
        model=DiagMsgLevelTranslts,
        sheet_name="DiagMsgLevelTranslts",
        fields=[
            Field("pk", 1, is_pkey=True),
            Field("level", 2, foreign_key=ForeignKey(None, DiagMsgLevel, "code"))
        ],
        horizontal_field=HorizontalField(
            "lang", 1, [4, 5],
            cross_field=CrossField("content", True),
            foreign_key=ForeignKey(None, Langs, "code")),
    ),
]

imports_pdata_categories_for_migration = [
    ImportManager(
        model=PassportCategoriesTranslts,
        sheet_name="PdataCategoryTranslts",
        fields=[
            Field("pk", 2, is_pkey=True),
            Field("code", 2)
        ],
        horizontal_field=HorizontalField(
            "lang", 1, [3, 3],
            cross_field=CrossField("content", True),
            foreign_key=ForeignKey(None, Langs, "code")),
    ),
]

imports_for_signal_localization = [
    ImportManager(
        model=SignalsGuideTranslts,
        sheet_name="SignalsTranslts",
        fields=[
            Field("pk", 1, is_pkey=True),
            Field("sgn_guide", 2, foreign_key=ForeignKey(None, SignalsGuide, "code"))
        ],
        horizontal_field=HorizontalField(
            "lang", 1, [3, 3],
            cross_field=CrossField("content", True),
            foreign_key=ForeignKey(None, Langs, "code")),
    ),
    ImportManager(
        model=MeasureUnitsTranslts,
        sheet_name="UnitsTranslts",
        fields=[
            Field("pk", 1, is_pkey=True),
            Field("unit", 2, foreign_key=ForeignKey(None, MeasureUnits, "name"))
        ],
        horizontal_field=HorizontalField(
            "lang", 1, [3, 4],
            cross_field=CrossField("content", True),
            foreign_key=ForeignKey(None, Langs, "code")),
    ),
    ImportManager(
        model=SignalsCategoriesTranslts,
        sheet_name="SignalCategoryTranslts",
        fields=[
            Field("pk", 1, is_pkey=True),
            Field("category", 2, foreign_key=ForeignKey(None, SignalСategories, "code"))
        ],
        horizontal_field=HorizontalField(
            "lang", 1, [3, 3],
            cross_field=CrossField("content", True),
            foreign_key=ForeignKey(None, Langs, "code")),
    ),
]


imports_all_data: List[ImportManager] = [] + import_langs
imports_all_data.extend(imports_for_migration)
imports_all_data.extend(imports_pdata_categories_for_migration)
imports_all_data.extend(imports_for_signal_localization)

imports_for_migration = import_langs + imports_for_migration
imports_pdata_categories_for_migration = import_langs + imports_pdata_categories_for_migration

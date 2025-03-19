from typing import List
from config_ui.models import (BlockType, Block, Panel, PanelBlock,
                              PageType, Page, PagePanel)
from .manager import ImportManager
from .keys import ForeignKey
from .fields import Field


imports_for_migration = [
    ImportManager(
        model=BlockType,
        sheet_name="block_type",
        fields=[
            Field("pk", 2, is_pkey=True),
            Field("code", 2),
        ],
    ),
    ImportManager(
        model=Block,
        sheet_name="block",
        fields=[
            Field("pk", 2, is_pkey=True),
            Field("code", 2),
            Field("type", 3, foreign_key=ForeignKey(None, BlockType, "code")),
            Field("template", 4, is_defaults=True, is_json=True),
        ],
    ),
    ImportManager(
        model=Panel,
        sheet_name="panel",
        fields=[
            Field("pk", 2, is_pkey=True),
            Field("code", 2),
            Field("template", 3, is_defaults=True, is_json=True),
        ],
    ),
    ImportManager(
        model=PanelBlock,
        sheet_name="panel-block",
        fields=[
            Field("pk", 1, is_pkey=True),
            Field("panel", 2, foreign_key=ForeignKey(None, Panel, "code")),
            Field("block", 3, foreign_key=ForeignKey(None, Block, "code")),
            Field("x", 4, is_defaults=True),
            Field("y", 5, is_defaults=True),
            Field("w", 6, is_defaults=True),
            Field("h", 7, is_defaults=True),
        ],
    ),
    ImportManager(
        model=PageType,
        sheet_name="page_type",
        fields=[
            Field("pk", 2, is_pkey=True),
            Field("code", 2),
        ],
    ),
    ImportManager(
        model=Page,
        sheet_name="page",
        fields=[
            Field("pk", 2, is_pkey=True),
            Field("code", 2),
            Field("type", 3, foreign_key=ForeignKey(None, PageType, "code")),
        ],
    ),
    ImportManager(
        model=PagePanel,
        sheet_name="page-panel",
        fields=[
            Field("pk", 1, is_pkey=True),
            Field("page", 2, foreign_key=ForeignKey(None, Page, "code")),
            Field("panel", 3, foreign_key=ForeignKey(None, Panel, "code")),
            Field("x", 4, is_defaults=True),
            Field("y", 5, is_defaults=True),
            Field("w", 6, is_defaults=True),
            Field("h", 7, is_defaults=True),
        ],
    ),
]


imports_all_data: List[ImportManager] = imports_for_migration

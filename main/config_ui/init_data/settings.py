from collections import namedtuple


UiSetting = namedtuple("UiSetting", ["code", "value_type", "value"])


ui_settings: list[UiSetting] = [
    UiSetting("latest_values_refresh_interval", "int", "300"),
]

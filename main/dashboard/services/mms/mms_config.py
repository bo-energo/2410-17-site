from .mms_asset import MMSAssetManager
from .mms_device import MMSDeviceManager


class MMSConfig:
    _asset_source = MMSAssetManager
    _device_source = MMSDeviceManager

    @classmethod
    def get_data(cls):
        result = {}
        device_manager = cls._device_source()
        result["devices"] = device_manager.get_formatted_for_mms_config()
        signals_codes = device_manager.get_devices_signals_codes()
        result["assets"] = cls._asset_source.get_formatted_for_mms_config(signals_codes)
        return result

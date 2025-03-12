from typing import List, Dict
from dashboard.models import Signals
from .mms_sguide import SgGuide


class MMSDevice:
    def __init__(self, id, device_guid, name, asset_guid, mms_logical_device,
                 signals: List[SgGuide] = None):
        self._id = id
        self._device_guid = device_guid
        self._name = name
        self._asset_guid = asset_guid
        self._mms_logical_device = mms_logical_device
        self._signals = signals if isinstance(signals, list) else []

    def append_signal(self, signal: SgGuide):
        self._signals.append(signal)

    def get_signals_codes(self):
        return [signal._code for signal in self._signals]

    def get_formatted_for_mms_config(self):
        return {
            "id": self._id,
            "asset": self._asset_guid,
            "device": self._device_guid,
            "name": self._name,
            "logical_device": self._mms_logical_device,
            "signals": [signal.get_formatted_for_mms_config()
                        for signal in self._signals]
        }


class MMSDeviceManager:
    def __init__(self):
        self.__devices_signals_codes = set()
        self.__devices = self._get_devices()

    @classmethod
    def _get_signals(cls, enabled_signal: bool = True, enabled_device: bool = True):
        return Signals.objects.select_related("code", "device", "asset").filter(
            enabled=enabled_signal,
            device__enabled=enabled_device,
            device__mms_logical_device__isnull=False,
            asset__isnull=False,
            asset__guid__isnull=False,
            code__mms_logical_node__isnull=False,
            code__mms_data_object__isnull=False,
            ).only(
                "device__id", "asset__guid",
                "device__name", "device__mms_logical_device",
                "code__code", "code__name", "code__mms_logical_node",
                "code__mms_data_object",
                "code__mms_class"
            )

    def _get_devices(self, enabled_signal: bool = True, enabled_device: bool = True) -> List[MMSDevice]:
        devices: Dict[int, MMSDevice] = {}
        for signal in self._get_signals(enabled_signal, enabled_device):
            if signal.device.id not in devices:
                devices[signal.device.id] = MMSDevice(
                    signal.device.id,
                    signal.device.id,
                    signal.device.name,
                    signal.asset.guid,
                    signal.device.mms_logical_device,
                )
            devices[signal.device.id].append_signal(
                SgGuide(
                    signal.code.code,
                    signal.code.name,
                    signal.code.mms_logical_node,
                    signal.code.mms_data_object,
                    signal.code.mms_class
                )
            )
            self.__devices_signals_codes.add(signal.code.code)
        return list(devices.values())

    def get_formatted_for_mms_config(self):
        return [device.get_formatted_for_mms_config() for device in self.__devices]

    def get_devices_signals_codes(self):
        return self.__devices_signals_codes

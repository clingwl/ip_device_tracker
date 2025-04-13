import logging
from homeassistant.components.device_tracker import DeviceScanner
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from ping3 import ping
import async_timeout

_LOGGER = logging.getLogger(__name__)

async def async_get_scanner(hass, config):
    """Get scanner."""
    devices = []
    for entry in hass.config_entries.async_entries("ip_device_tracker"):
        devices.append({
            "ip": entry.data["ip"],
            "name": entry.data.get("name", entry.data["ip"])
        })
    
    scanner = IPDeviceScanner(hass, devices)
    await scanner.async_init()
    return scanner

class IPDeviceScanner(DeviceScanner):
    def __init__(self, hass, devices):
        self.hass = hass
        self._devices = devices
        self.coordinator = None

    async def async_init(self):
        self.coordinator = DataUpdateCoordinator(
            self.hass,
            _LOGGER,
            name="ip_device_tracker",
            update_method=self._async_update,
            update_interval=60,
        )
        await self.coordinator.async_refresh()

    async def _async_update(self):
        results = {}
        for device in self._devices:
            ip = device["ip"]
            try:
                with async_timeout.timeout(5):
                    result = await self.hass.async_add_executor_job(
                        ping, ip, 1
                    )
                results[ip] = result is not None
            except Exception as e:
                _LOGGER.error("Error pinging %s: %s", ip, e)
                results[ip] = False
        return results

    async def async_scan_devices(self):
        await self.coordinator.async_request_refresh()
        active_devices = []
        for device in self._devices:
            if self.coordinator.data.get(device["ip"], False):
                active_devices.append(device["ip"])
        return active_devices

    async def async_get_device_name(self, device):
        for dev in self._devices:
            if dev["ip"] == device:
                return dev.get("name", device)
        return device
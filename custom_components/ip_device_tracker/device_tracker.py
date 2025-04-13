import asyncio
import platform
import logging
from homeassistant.components.device_tracker import DeviceScanner
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_get_scanner(hass, config):
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
                results[ip] = await self._async_ping(ip)
            except Exception as e:
                _LOGGER.error("Ping error: %s", e)
                results[ip] = False
        return results

    async def _async_ping(self, ip: str) -> bool:
        """跨平台ping实现"""
        os_type = platform.system().lower()
        if os_type == "windows":
            ping_cmd = ["ping", "-n", "1", "-w", "2000", ip]
        else:
            ping_cmd = ["ping", "-c", "1", "-W", "2", ip]

        proc = await asyncio.create_subprocess_exec(
            *ping_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            await asyncio.wait_for(proc.communicate(), timeout=5)
            return proc.returncode == 0
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            return False
        except Exception as e:
            _LOGGER.debug("Ping error: %s", e)
            return False

    async def async_scan_devices(self):
        await self.coordinator.async_request_refresh()
        return [dev["ip"] for dev in self._devices 
                if self.coordinator.data.get(dev["ip"], False)]

    async def async_get_device_name(self, device):
        return next(
            (dev["name"] for dev in self._devices if dev["ip"] == device),
            device
        )
import asyncio
import platform
import logging
from homeassistant.components.device_tracker import DeviceScanner
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

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
                # 异步执行系统 ping 命令
                result = await self._async_ping(ip)
                results[ip] = result
            except Exception as e:
                _LOGGER.error("Ping error for %s: %s", ip, e)
                results[ip] = False
        return results

    async def _async_ping(self, ip: str) -> bool:
        """跨平台异步 ping 实现"""
        # 根据操作系统选择 ping 参数
        ping_cmd = ["ping", "-n", "1", "-w", "2000", ip] if platform.system().lower() == "windows" else ["ping", "-c", "1", "-W", "2", ip]
        
        # 异步执行子进程
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
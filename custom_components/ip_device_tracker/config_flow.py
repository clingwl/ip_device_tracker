import asyncio
import platform
import logging
import voluptuous as vol
from homeassistant import config_entries

_LOGGER = logging.getLogger(__name__)

class IPDeviceTrackerConfigFlow(config_entries.ConfigFlow, domain="ip_device_tracker"):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            if any(entry.data["ip"] == user_input["ip"] 
                   for entry in self._async_current_entries()):
                errors["base"] = "already_configured"
            else:
                valid = await self._async_validate_ip(user_input["ip"])
                if valid:
                    return self.async_create_entry(
                        title=user_input.get("name", user_input["ip"]), 
                        data=user_input
                    )
                else:
                    errors["base"] = "cannot_connect"

        data_schema = vol.Schema({
            vol.Required("ip"): str,
            vol.Optional("name"): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )

    async def _async_validate_ip(self, ip: str) -> bool:
        """异步验证IP地址"""
        os_type = platform.system().lower()
        if os_type == "windows":
            ping_cmd = ["ping", "-n", "1", "-w", "2000", ip]
        else:
            ping_cmd = ["ping", "-c", "1", "-W", "2", ip]

        try:
            proc = await asyncio.create_subprocess_exec(
                *ping_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(proc.communicate(), timeout=5)
            return proc.returncode == 0
        except (asyncio.TimeoutError, Exception):
            return False
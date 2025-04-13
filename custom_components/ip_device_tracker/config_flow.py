from homeassistant import config_entries
from homeassistant.core import callback
import voluptuous as vol
from ping3 import ping
import logging

_LOGGER = logging.getLogger(__name__)

class IPDeviceTrackerConfigFlow(config_entries.ConfigFlow, domain="ip_device_tracker"):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # 检查IP是否重复
            if any(entry.data["ip"] == user_input["ip"] 
                   for entry in self._async_current_entries()):
                errors["base"] = "already_configured"
            else:
                # 验证IP可达性
                valid = await self.hass.async_add_executor_job(
                    self._validate_ip, user_input["ip"]
                )
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
            errors=errors,
            description_placeholders={"error_info": ""}
        )

    @staticmethod
    def _validate_ip(ip: str) -> bool:
        try:
            return ping(ip, timeout=2) is not None
        except Exception as e:
            _LOGGER.error("Ping error: %s", e)
            return False

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("ip", default=self.config_entry.data["ip"]): str,
                vol.Optional("name", default=self.config_entry.data.get("name", "")): str,
            })
        )
from typing import Any, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ECOFLOW_DOMAIN
from .api import EcoflowApiClient, Message
from .devices import BaseDevice
from .entities import BaseTextEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    client: EcoflowApiClient = hass.data[ECOFLOW_DOMAIN][entry.entry_id]
    for sn, device in client.devices.items():
        async_add_entities(device.texts(client))


class TextConfigEntity(BaseTextEntity[str]):
    """Text entity for configuring string values like circuit names."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_available = False

    def __init__(
        self,
        client: EcoflowApiClient,
        device: BaseDevice,
        mqtt_key: str,
        title: str,
        command: Callable[[str], dict[str, Any] | Message]
        | Callable[[str, dict[str, Any]], dict[str, Any] | Message]
        | None,
        enabled: bool = True,
        auto_enable: bool = False,
        max_length: int = 32,
    ):
        super().__init__(client, device, mqtt_key, title, command, enabled, auto_enable)
        self._attr_native_max = max_length
        self._attr_native_value = ""

    def _update_value(self, val: Any) -> bool:
        str_val = str(val) if val is not None else ""
        if self._attr_native_value != str_val:
            self._attr_native_value = str_val
            return True
        return False

    @property
    def native_value(self) -> str | None:
        """Return the current value."""
        return self._attr_native_value

    def set_value(self, value: str) -> None:
        """Set the text value."""
        if self._command:
            self.send_set_message(value, self.command_dict(value))

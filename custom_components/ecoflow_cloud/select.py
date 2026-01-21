from typing import Any, Callable

import jsonpath_ng.ext as jp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ECOFLOW_DOMAIN
from .api import EcoflowApiClient, Message
from .devices import BaseDevice
from .entities import BaseSelectEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    client: EcoflowApiClient = hass.data[ECOFLOW_DOMAIN][entry.entry_id]
    for sn, device in client.devices.items():
        async_add_entities(device.selects(client))


class DictSelectEntity(BaseSelectEntity[int]):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_available = False

    def __init__(
        self,
        client: EcoflowApiClient,
        device: BaseDevice,
        mqtt_key: str,
        title: str,
        options: dict[str, Any],
        command: Callable[[int], dict[str, Any] | Message]
        | Callable[[int, dict[str, Any]], dict[str, Any] | Message]
        | None,
        enabled: bool = True,
        auto_enable: bool = False,
    ):
        super().__init__(client, device, mqtt_key, title, command, enabled, auto_enable)
        self._options_dict = options
        self._options = list(options.keys())
        self._current_option = ""

    def options_dict(self) -> dict[str, int]:
        return self._options_dict

    def _update_value(self, val: Any) -> bool:
        lval = [k for k, v in self._options_dict.items() if v == val]
        if len(lval) == 1:
            self._current_option = lval[0]
            return True
        else:
            return False

    @property
    def options(self) -> list[str]:
        """Return available select options."""
        return self._options

    @property
    def current_option(self) -> str:
        """Return current select option."""
        return self._current_option

    def select_option(self, option: str) -> None:
        if self._command:
            val = self._options_dict[option]
            self.send_set_message(val, self.command_dict(val))


class TimeoutDictSelectEntity(DictSelectEntity):
    _attr_icon = "mdi:timer-outline"


class PowerDictSelectEntity(DictSelectEntity):
    _attr_icon = "mdi:battery-charging-wireless"


class CircuitModeSelectEntity(DictSelectEntity):
    """
    Select entity for circuit mode that computes state from ctrlMode and ctrlSta.

    The circuit mode is a combination of two MQTT values:
    - ctrlMode: 0=Auto, 1=Manual
    - ctrlSta: 0=Grid, 1=Battery, 2=Off (only relevant when ctrlMode=1)

    Combined states:
    - Auto (0): ctrlMode=0
    - Grid (1): ctrlMode=1, ctrlSta=0
    - Battery (2): ctrlMode=1, ctrlSta=1
    - Off (3): ctrlMode=1, ctrlSta=2
    """

    _attr_icon = "mdi:power-plug"

    def __init__(
        self,
        client: EcoflowApiClient,
        device: BaseDevice,
        ctrl_mode_key: str,
        ctrl_sta_key: str,
        title: str,
        options: dict[str, Any],
        command: Callable[[int], dict[str, Any] | Message]
        | Callable[[int, dict[str, Any]], dict[str, Any] | Message]
        | None,
        enabled: bool = True,
        auto_enable: bool = False,
    ):
        # Use ctrl_mode_key as the primary mqtt_key for entity updates
        super().__init__(client, device, ctrl_mode_key, title, options, command, enabled, auto_enable)
        self._ctrl_sta_key = ctrl_sta_key
        # Create jsonpath expression for ctrlSta
        self._ctrl_sta_expr = jp.parse(ctrl_sta_key)

    def _update_value(self, val: Any) -> bool:
        """
        Compute the combined circuit mode from ctrlMode and ctrlSta.

        This overrides the default behavior to compute the true state.
        """
        # Get ctrlMode (the val parameter)
        ctrl_mode = int(val) if val is not None else 0

        # Get ctrlSta using jsonpath from device params
        ctrl_sta = 0
        sta_values = self._ctrl_sta_expr.find(self._device.data.params)
        if sta_values:
            ctrl_sta = int(sta_values[0].value) if sta_values[0].value is not None else 0

        # Compute combined mode value
        if ctrl_mode == 0:
            combined_value = 0  # Auto
        else:
            # Manual mode: use ctrlSta to determine Grid/Battery/Off
            combined_value = 1 + ctrl_sta  # Grid=1, Battery=2, Off=3

        # Find the option that matches this combined value
        lval = [k for k, v in self._options_dict.items() if v == combined_value]
        if len(lval) == 1:
            self._current_option = lval[0]
            return True
        else:
            return False

    def select_option(self, option: str) -> None:
        """
        Override select_option to properly handle combined mode values.

        The parent class sends the combined value (0-3) as the local state update,
        but ctrlMode should only be 0 or 1. We need to send the correct ctrlMode
        value for the optimistic local state update.
        """
        if self._command:
            combined_val = self._options_dict[option]
            # Convert combined value to actual ctrlMode (0=Auto, 1=Manual for Grid/Battery/Off)
            actual_ctrl_mode = 0 if combined_val == 0 else 1
            # Send the command with combined value, but update local state with actual ctrlMode
            self._client.send_set_message(
                self._device.device_info.sn,
                {self._mqtt_key_adopted: actual_ctrl_mode},
                self.command_dict(combined_val),
            )

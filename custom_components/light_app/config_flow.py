"""Config flow for lights_app integration."""
from __future__ import annotations
import voluptuous as vol


import logging
from typing import Any
from bleak import BleakScanner,BleakClient

from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.components import bluetooth
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import FlowResult

from .const import WRITE_CHARACTERISTIC, DOMAIN, SERVICE, SUPPORTED_BLUETOOTH_NAMES, NOTIFY_CHARACTERISTIC

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    _LOGGER.warn("TEST123456")
    """Handle a config flow for Yale Access Bluetooth."""

    VERSION = 1

    def __init__(self) -> None:
        _LOGGER.warn("TEST123 - 1")
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle the bluetooth discovery step."""
        _LOGGER.warn("TEST123 - 2")
        _LOGGER.warn(discovery_info.name)
        """
        if discovery_info.name.startswith(UNSUPPORTED_SUB_MODEL):
            # These versions speak a different protocol
            # that we do not support yet.
            return self.async_abort(reason="not_supported")
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self._discovery_info = discovery_info
        self.context["title_placeholders"] = {
            "name": human_readable_name(
                None, discovery_info.name, discovery_info.address
            )
        }
        return await self.async_step_user()
        """

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if discovery := self._discovery_info:
            self._discovered_devices[discovery.address] = discovery
        else:
            for discovery in async_discovered_service_info(self.hass):
                if discovery.name in SUPPORTED_BLUETOOTH_NAMES:
                    self._discovered_devices[discovery.address] = discovery
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            discovery_info = self._discovered_devices[address]
            local_name = discovery_info.name
            await self.async_set_unique_id(
                discovery_info.address, raise_on_progress=False
            )
            self._abort_if_unique_id_configured()
            ble_device = bluetooth.async_ble_device_from_address(self.hass, address, connectable=True)

            isValidDevice = False
            async with BleakClient(ble_device) as client:
                communicationService = client.services.get_service(SERVICE)
                if communicationService:
                    writeCharacteristic = communicationService.get_characteristic(WRITE_CHARACTERISTIC)
                    notifyCharacteristic = communicationService.get_characteristic(NOTIFY_CHARACTERISTIC)
                    if writeCharacteristic and notifyCharacteristic:
                        isValidDevice = True
            if isValidDevice:
                return self.async_create_entry(
                    title=local_name,
                    data={
                        CONF_ADDRESS: discovery_info.address,
                    },
                )
            else:
                return self.async_abort(reason="not_supported")

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        data_schema = vol.Schema(
            {
                vol.Required(CONF_ADDRESS): vol.In(
                    {
                        service_info.address: (
                            f"{service_info.name} ({service_info.address})"
                        )
                        for service_info in self._discovered_devices.values()
                    }
                ),
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

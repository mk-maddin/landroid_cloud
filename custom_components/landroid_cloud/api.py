"""Representing the Landroid Cloud API interface."""
from __future__ import annotations

from datetime import datetime, timedelta

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_TYPE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.util import slugify as util_slugify
from pyworxcloud import WorxCloud
from pyworxcloud.events import LandroidEvent
from pyworxcloud.utils import Capability, DeviceCapability, DeviceHandler

from .const import ATTR_CLOUD, DOMAIN, UPDATE_SIGNAL, LandroidFeatureSupport
from .utils.logger import LandroidLogger, LogLevel, LoggerType


class LandroidAPI:
    """Handle the API calls."""

    def __init__(self, hass: HomeAssistant, device_name: str, entry: ConfigEntry):
        """Initialize API connection for a device.

        Args:
            hass (HomeAssistant): Home Assistant object
            index (int): Device number to connect to. 0 is the first device associated.
            device (WorxCloud): pyWorxlandroid object for the connection.
            entry (ConfigEntry): Home Assistant configuration entry for the cloud account.
        """
        self.hass = hass
        self.entry_id = entry.entry_id
        self.data = entry.data
        self.options = entry.options
        self.entry = entry
        self.cloud: WorxCloud = hass.data[DOMAIN][entry.entry_id][ATTR_CLOUD]
        self.device: DeviceHandler = self.cloud.devices[device_name]
        self.unique_id = entry.unique_id
        self.services = {}
        self.shared_options = {}
        self.device_id = None
        self.features = 0
        self.features_loaded = False

        self._last_state = self.device.online

        self.name = util_slugify(f"{device_name}")
        self.friendly_name = device_name

        self.config = {
            "email": hass.data[DOMAIN][entry.entry_id][CONF_EMAIL].lower(),
            "password": hass.data[DOMAIN][entry.entry_id][CONF_PASSWORD],
            "type": hass.data[DOMAIN][entry.entry_id][CONF_TYPE].lower(),
        }

        self.logger = LandroidLogger(name=__name__, api=self)
        self.cloud.set_callback(LandroidEvent.DATA_RECEIVED, self.receive_data)
        self.cloud.set_callback(LandroidEvent.MQTT_RATELIMIT, self._on_ratelimit)
        self.cloud.set_callback(LandroidEvent.MQTT_PUBLISH, self._on_mqtt_publish)
        self.cloud.set_callback(LandroidEvent.LOG, self._on_log)

    @callback
    def _on_log(self, message: str, level=str) -> None:
        """Callback for logging from pyworxcloud module."""
        self.logger.log(LoggerType.API, message, log_level=LogLevel(level), device=None)

    @callback
    def _on_ratelimit(self, message: str) -> None:
        """Callback when ratelimit is reached on MQTT handler."""
        self.logger.log(
            LoggerType.API, message, log_level=LogLevel.WARNING, device=None
        )

    @callback
    def _on_mqtt_publish(
        self, message: str, topic: str, device: str, qos: int, retain: bool
    ) -> None:
        """Callback when trying to publish a message to the API endpoint."""
        self.logger.log(
            LoggerType.API,
            'Sending "%s" to "%s" via "%s" with QOS "%s" and retain flag set to %s',
            message,
            device,
            topic,
            qos,
            retain,
            log_level=LogLevel.DEBUG,
            device=None,
        )

    async def async_await_features(self, timeout: int = 10) -> None:
        """Used to await feature checks."""
        timeout_at = datetime.now() + timedelta(seconds=timeout)

        while (
            not self.features_loaded
        ):
            if datetime.now() > timeout_at:
                break

        if (
            not self.device.capabilities.ready
            or not self.features_loaded
            or self.features == 0
        ):
            raise ValueError(
                f"Capabilities ready: {self.device.capabilities.ready} -- Features loaded: {self.features_loaded} -- Feature bits: {self.features}"
            )

        self.device.mqtt.set_eventloop(self.hass.loop)

    def check_features(self, features: int, callback_func: Any = None) -> None:
        """Check which features the device supports.

        Args:
            features (int): Current feature set.
            callback_func (_type_, optional):
                Function to be called when the features
                have been assessed. Defaults to None.
        """
        logger = LandroidLogger(name=__name__, api=self, log_level=LogLevel.DEBUG)
        logger.log(LoggerType.FEATURE_ASSESSMENT, "Features: %s", features)

        capabilities: Capability = self.device.capabilities

        if capabilities.check(DeviceCapability.PARTY_MODE):
            self.logger.log(LoggerType.FEATURE_ASSESSMENT, "Party mode capable")
            features = features | LandroidFeatureSupport.PARTYMODE

        if capabilities.check(DeviceCapability.ONE_TIME_SCHEDULE):
            self.logger.log(LoggerType.FEATURE_ASSESSMENT, "OTS capable")
            features = features | LandroidFeatureSupport.OTS

        if capabilities.check(DeviceCapability.EDGE_CUT):
            self.logger.log(LoggerType.FEATURE_ASSESSMENT, "Edge Cut capable")
            features = features | LandroidFeatureSupport.EDGECUT

        if capabilities.check(DeviceCapability.TORQUE):
            self.logger.log(LoggerType.FEATURE_ASSESSMENT, "Torque capable")
            features = features | LandroidFeatureSupport.TORQUE

        logger.log(LoggerType.FEATURE_ASSESSMENT, "Features: %s", features)
        old_feature = self.features
        self.features = features

        if callback_func:
            callback_func(old_feature)

    @callback
    def receive_data(
        self, name: str, device: DeviceHandler  # pylint: disable=unused-argument
    ) -> None:
        """Callback function when the API sends new data."""
        self.logger.log(
            LoggerType.DATA_UPDATE,
            "Received new data from API to %s, dispatching %s",
            name,
            util_slugify(f"{UPDATE_SIGNAL}_{name}"),
            device=name,
        )
        dispatcher_send(self.hass, util_slugify(f"{UPDATE_SIGNAL}_{name}"))
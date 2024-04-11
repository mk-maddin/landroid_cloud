"""LandXcape device definition."""

# pylint: disable=unused-argument,relative-beyond-top-level
from __future__ import annotations

import voluptuous as vol
from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.components.lawn_mower import LawnMowerEntity
from homeassistant.components.select import SelectEntityDescription
from homeassistant.core import HomeAssistant
from pyworxcloud import WorxCloud

from ..api import LandroidAPI
from ..const import (
    ATTR_BOUNDARY,
    ATTR_MULTIZONE_DISTANCES,
    ATTR_MULTIZONE_PROBABILITIES,
    ATTR_RAINDELAY,
    ATTR_RUNTIME,
    ATTR_TIMEEXTENSION,
    LandroidFeatureSupport,
)
from ..device_base import (
    SUPPORT_LANDROID_BASE,
    LandroidCloudButtonBase,
    LandroidCloudMowerBase,
)
from ..utils.logger import LoggerType

# from homeassistant.helpers.dispatcher import dispatcher_send


SUPPORTED_FEATURES = SUPPORT_LANDROID_BASE

CONFIG_SCHEME = vol.Schema(
    {
        vol.Optional(ATTR_RAINDELAY): vol.All(vol.Coerce(int), vol.Range(0, 300)),
        vol.Optional(ATTR_TIMEEXTENSION): vol.All(
            vol.Coerce(int), vol.Range(-100, 100)
        ),
        vol.Optional(ATTR_MULTIZONE_DISTANCES): str,
        vol.Optional(ATTR_MULTIZONE_PROBABILITIES): str,
    }
)

OTS_SCHEME = vol.Schema(
    {
        vol.Required(ATTR_BOUNDARY, default=False): bool,
        vol.Required(ATTR_RUNTIME, default=30): vol.Coerce(int),
    }
)

DEVICE_FEATURES = (
    LandroidFeatureSupport.MOWER
    | LandroidFeatureSupport.BUTTON
    | LandroidFeatureSupport.LOCK
    | LandroidFeatureSupport.CONFIG
    | LandroidFeatureSupport.RESTART
    | LandroidFeatureSupport.SELECT
    | LandroidFeatureSupport.SETZONE
    | LandroidFeatureSupport.SCHEDULES
)


class Button(LandroidCloudButtonBase, ButtonEntity):
    """Definition of Landxcape button."""

    def __init__(
        self,
        description: ButtonEntityDescription,
        hass: HomeAssistant,
        api: LandroidAPI,
    ) -> None:
        """Initialize a Landxcape button."""
        super().__init__(description, hass, api)
        self.device: WorxCloud = self.api.device
        self.log(
            LoggerType.SELECT,
            "Adding %s",
            description.key,
        )


class MowerDevice(LandroidCloudMowerBase, LawnMowerEntity):
    """Definition of Landxcape device."""

    def __init__(self, hass, api):
        """Initialize mower entity."""
        super().__init__(hass, api)
        self.device: WorxCloud = self.api.device

    @property
    def base_features(self):
        """Flag which Landroid Cloud specific features that are supported."""
        return DEVICE_FEATURES

    @property
    def supported_features(self):
        """Flag which mower robot features that are supported."""
        return SUPPORTED_FEATURES

    @staticmethod
    def get_ots_scheme():
        """Get device specific OTS_SCHEME."""
        return OTS_SCHEME

    @staticmethod
    def get_config_scheme():
        """Get device specific CONFIG_SCHEME."""
        return CONFIG_SCHEME

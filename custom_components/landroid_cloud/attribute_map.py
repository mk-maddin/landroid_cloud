"""Attribute map used by Landroid Cloud integration."""
from __future__ import annotations

from homeassistant.const import ATTR_LOCKED, ATTR_MODEL

from .const import (
    ATTR_ACCESSORIES,
    ATTR_BATTERY,
    ATTR_BLADES,
    ATTR_ERROR,
    ATTR_FIRMWARE,
    ATTR_LAWN,
    ATTR_MACADDRESS,
    ATTR_ONLINE,
    ATTR_ORIENTATION,
    ATTR_PARTYMODE,
    ATTR_RAINSENSOR,
    ATTR_RSSI,
    ATTR_SCHEDULE,
    ATTR_SERIAL,
    ATTR_STATISTICS,
    ATTR_STATUS,
    ATTR_TIMEZONE,
    ATTR_TORQUE,
    ATTR_UPDATED,
    ATTR_ZONE,
)

ATTR_MAP = {
    "accessories": ATTR_ACCESSORIES,
    "lawn": ATTR_LAWN,
    "locked": ATTR_LOCKED,
    "partymode_enabled": ATTR_PARTYMODE,
    "torque": ATTR_TORQUE,
    "zone": ATTR_ZONE,
}

"""The misc_extensions integration.

This integration has no entities of its own. It exists to contribute extra LLM
tools to Home Assistant through its ``llm`` platform (:mod:`.llm`), which the
``llm`` integration imports lazily for every loaded integration.

It is configured entirely from the UI: adding a config entry is enough to load
the component, which is the condition the ``llm`` platform loader checks.
"""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up misc_extensions from a config entry."""
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a misc_extensions config entry."""
    return True

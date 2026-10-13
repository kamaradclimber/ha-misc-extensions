"""Config flow for the misc_extensions integration."""

from typing import Any, override

import probatio

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import BooleanSelector

from .const import CONF_ENABLE_TOOL, DEFAULT_ENABLE_TOOL, DOMAIN


class MiscExtensionsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow for misc_extensions.

    The integration has nothing to configure at setup time. ``single_config_entry``
    in the manifest stops a second instance, so the only step just creates the
    entry that loads the component.
    """

    VERSION = 1

    @staticmethod
    @callback
    @override
    def async_get_options_flow(config_entry: ConfigEntry) -> MiscExtensionsOptionsFlow:
        """Return the options flow handler."""
        return MiscExtensionsOptionsFlow()

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the single setup step."""
        return self.async_create_entry(title="Misc Extensions", data={})


class MiscExtensionsOptionsFlow(OptionsFlow):
    """Handle options for misc_extensions."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                probatio.Schema(
                    {
                        probatio.Optional(
                            CONF_ENABLE_TOOL,
                            description=(
                                "Expose the GetEntityAttributes tool to the"
                                " Assist API."
                            ),
                        ): BooleanSelector(),
                    }
                ),
                {
                    CONF_ENABLE_TOOL: self.config_entry.options.get(
                        CONF_ENABLE_TOOL, DEFAULT_ENABLE_TOOL
                    )
                },
            ),
        )

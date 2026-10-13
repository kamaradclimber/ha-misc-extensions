"""LLM tools contributed by the misc_extensions integration.

The ``llm`` integration discovers this platform file and calls
:func:`async_get_tools` for every LLM request. Returning ``None`` for APIs we do
not want to extend keeps the tool scoped to the built-in Assist API.
"""

from typing import Any, override

import probatio

from homeassistant.components import llm as llm_component
from homeassistant.components.homeassistant.exposed_entities import async_should_expose
from homeassistant.core import HomeAssistant, State, callback
from homeassistant.helpers import config_validation as cv, intent
from homeassistant.helpers.llm import (
    LLM_API_ASSIST,
    LLMContext,
    Tool,
    ToolAnnotations,
    ToolInput,
    ToolResult,
)

from .const import CONF_ENABLE_TOOL, DEFAULT_ENABLE_TOOL, DOMAIN


@callback
def _async_tool_enabled(hass: HomeAssistant) -> bool:
    """Return whether the tool is enabled in the config entry options."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        return entry.options.get(CONF_ENABLE_TOOL, DEFAULT_ENABLE_TOOL)
    # No config entry (the component was loaded some other way): default on.
    return DEFAULT_ENABLE_TOOL


def _json_safe(value: Any) -> Any:
    """Convert a state attribute value into something JSON serializable.

    State attributes may hold enums, decimals, datetimes, sets, and other
    objects that orjson cannot encode. Fall back to ``str`` for anything that
    is not a plain JSON container or scalar.
    """
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_safe(item) for item in value]
    return str(value)


@callback
def _async_get_exposed_states(hass: HomeAssistant, assistant: str) -> list[State]:
    """Return the states exposed to the given assistant."""
    return [
        state
        for state in hass.states.async_all()
        if async_should_expose(hass, assistant, state.entity_id)
    ]


def _match_error(
    match_result: intent.MatchTargetsResult,
    name: str,
    domains: list[str] | None,
) -> str:
    """Build an actionable error message for a failed entity match."""
    reason = match_result.no_match_reason
    if reason is intent.MatchFailedReason.NAME:
        return f"No exposed entity matched name '{name}'"
    if reason is intent.MatchFailedReason.DOMAIN:
        return f"No exposed entities found in domain(s): {', '.join(domains or [])}"
    return "No exposed entities matched the provided filters"


class GetEntityAttributesTool(Tool):
    """Return the full state and all attributes of an exposed entity.

    This complements the built-in ``GetLiveContext`` tool, which only surfaces a
    small set of interesting attributes. Use this tool when the user asks for
    details that are not in that overview (supported features, options, presets,
    or any custom attribute).
    """

    name = f"{DOMAIN}__GetEntityAttributes"
    title = "Get entity attributes"
    description = (
        "Returns the current state and ALL attributes of an entity exposed to"
        " the assistant, as JSON. Use this when the user asks for details about"
        " an entity that the live context overview does not include, such as"
        " supported features, available options or presets, or a specific"
        " attribute by name. Provide the entity name, one of its aliases, or its"
        " entity_id. Optionally narrow the search with a domain."
    )
    annotations = ToolAnnotations(read_only=True, idempotent=True, open_world=False)
    integration = DOMAIN
    parameters = probatio.Schema(
        {
            probatio.Required(
                "name",
                description="Name, alias, or entity_id of the entity to inspect.",
            ): cv.string,
            probatio.Optional(
                "domain",
                description=(
                    "Filter entities by domain (e.g. 'light', 'sensor')."
                    " Accepts a single domain or a list."
                ),
            ): probatio.Any(cv.string, [cv.string]),
        }
    )

    @override
    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: ToolInput,
        llm_context: LLMContext,
    ) -> ToolResult:
        """Return state and attributes for the matching exposed entities."""
        args = self.parameters(tool_input.tool_args)

        exposed_states = _async_get_exposed_states(hass, llm_context.assistant)
        if not exposed_states:
            return ToolResult(
                data={"error": "No entities are exposed to this assistant."},
                error=True,
            )

        name = args["name"]
        domains = args.get("domain")
        if isinstance(domains, str):
            domains = [domains]
        if domains is not None:
            domains = [
                normalized
                for domain in domains
                if (normalized := domain.strip().lower())
            ]

        # Multiple entities may share a name (e.g. "temperature" in two rooms),
        # so return all matches rather than failing as ambiguous.
        match_result = intent.async_match_targets(
            hass,
            intent.MatchTargetsConstraints(
                name=name,
                domains=domains,
                allow_duplicate_names=True,
            ),
            states=exposed_states,
        )

        if not match_result.is_match:
            return ToolResult(
                data={"error": _match_error(match_result, name, domains)},
                error=True,
            )

        entities = [
            {
                "entity_id": state.entity_id,
                "name": state.name,
                "state": _json_safe(state.state),
                "attributes": _json_safe(dict(state.attributes)),
            }
            for state in match_result.states
        ]
        return ToolResult(data={"entities": entities})


@callback
def async_get_tools(
    hass: HomeAssistant, llm_context: LLMContext, api_id: str
) -> llm_component.LLMTools | None:
    """Return the tools to expose to the LLM.

    Only extend the built-in Assist API; other APIs stay untouched. The tool
    can be turned off from the integration's options.
    """
    if api_id != LLM_API_ASSIST:
        return None

    if not _async_tool_enabled(hass):
        return None

    return llm_component.LLMTools(
        tools=[GetEntityAttributesTool()],
        prompt=(
            "Use the misc_extensions__GetEntityAttributes tool to retrieve the"
            " full state and every attribute of an entity when the user asks for"
            " details that the live context overview does not contain."
        ),
    )

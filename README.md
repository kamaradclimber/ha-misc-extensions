# ha-misc-extensions

A collection of small, experimental Home Assistant extensions that do not
deserve their own repository.

## `misc_extensions`

An integration with no entities of its own. It contributes extra
[LLM tools](https://developers.home-assistant.io/docs/core/llm/#tools) to the
built-in **Assist** API through its [`llm` platform](custom_components/misc_extensions/llm.py).

### Tools

#### `misc_extensions__GetEntityAttributes`

Returns the current state and **all** attributes of an entity exposed to the
assistant, as JSON.

This complements the built-in `homeassistant__GetLiveContext` tool, which only
returns a small set of "interesting" attributes. It is useful when the user asks
for details the overview omits: `supported_features`, `options`, `preset_modes`,
`hvac_action`, custom template attributes, etc.

Parameters:

| Name     | Required | Description                                                        |
| -------- | -------- | ------------------------------------------------------------------ |
| `name`   | yes      | Entity name, alias, or `entity_id` to inspect.                     |
| `domain` | no       | Restrict to one or more domains, e.g. `sensor` or `["light", "switch"]`. |
| `area`   | no       | Restrict to an area name or alias.                                 |

Scope: only entities [exposed to the assistant](https://www.home-assistant.io/voice_control/voice_remote_expose_devices/)
are visible, matching `GetLiveContext`.

### Install

1. Copy (or symlink) the integration into your Home Assistant config:

   ```sh
   ln -s "$(pwd)/custom_components/misc_extensions" \
         /path/to/config/custom_components/misc_extensions
   ```

2. Restart Home Assistant.

3. Go to **Settings → Devices & Services → Add Integration**, search for
   **Misc Extensions**, and submit the (empty) setup form.

The tool is added to the Assist API automatically, so any conversation agent
configured to "Control Home Assistant" with the Assist API can use it. No
option needs to be enabled per agent.

### Options

Open the integration's **Configure** button to toggle a single option:

| Option                          | Default | Description                                                        |
| ------------------------------- | ------- | ------------------------------------------------------------------ |
| `enable_tool` (the GetEntityAttributes tool) | on | When off, the tool is no longer offered to the Assist API. |

Options are read on every LLM request, so changing them takes effect on the
assistant's next message — no restart needed.

### Development

Import-check the platforms against a Home Assistant Core checkout:

```sh
pip install probatio==0.13.0
python -c "import custom_components.misc_extensions.llm"
python -c "import custom_components.misc_extensions.config_flow"
```

With the Core source on `PYTHONPATH`, the modules should import cleanly. There is
intentionally no test suite here yet.

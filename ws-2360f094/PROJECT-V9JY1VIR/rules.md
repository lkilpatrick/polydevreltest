# Poly ADK

## Overview

Poly-ADK is a CLI tool and Python package for managing PolyAI Agent Studio projects locally. It provides a Git-like workflow for synchronizing agent configurations between your local filesystem and the Agent Studio platform, so agent development fits into your existing build and review cycles.

Each project defines an AI voice or webchat agent. Resources in the project (flows, functions, topics, etc.) control the agent's runtime behavior.

## Project Structure

```
<account>/<project>/
├── _gen/                               # Generated stubs - do not edit
├── agent_settings/                     # Agent identity and behavior
│   ├── personality.yaml
│   ├── role.yaml
│   ├── rules.txt
│   ├── safety_filters.yaml
│   └── experimental_config.json        # Optional
├── config/                             # Configuration
│   ├── api_integrations.yaml           # Optional
│   ├── entities.yaml                   # Optional
│   ├── handoffs.yaml                   # Optional
│   ├── sms_templates.yaml              # Optional
│   └── variant_attributes.yaml         # Optional
├── voice/                              # Voice channel settings
│   ├── configuration.yaml              # Greeting, disclaimer, style prompt
│   ├── safety_filters.yaml             # Optional
│   ├── speech_recognition/
│   │   ├── asr_settings.yaml           # Barge-in, interaction style
│   │   ├── keyphrase_boosting.yaml     # Optional
│   │   └── transcript_corrections.yaml # Optional
│   └── response_control/
│       ├── pronunciations.yaml         # Optional - TTS rules
│       └── phrase_filtering.yaml       # Optional - stop keywords
├── chat/                               # Chat channel settings
│   ├── configuration.yaml              # Greeting, style prompt
│   └── safety_filters.yaml             # Optional
├── flows/                              # Optional - flow definitions
│   └── {flow_name}/
│       ├── flow_config.yaml
│       ├── steps/
│       │   └── {step_name}.yaml
│       ├── function_steps/
│       │   └── {function_step}.py
│       └── functions/
│           └── {function_name}.py
├── functions/                          # Global functions (shared across flows)
│   ├── start_function.py              # Optional - runs at call start
│   ├── end_function.py                # Optional - runs at call end
│   └── {function_name}.py
├── topics/                             # Knowledge base topics
│   └── {topic_name}.yaml
└── project.yaml                        # Project metadata (region, account_id, project_id)
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `poly init` | Initialize a new project (interactive or with `--region`, `--account_id`, `--project_id`) |
| `poly pull` | Pull remote config into local project (`-f` to force overwrite) |
| `poly push` | Push local changes to Agent Studio (`-f` to force, `--dry-run` to preview, `--skip-validation`) |
| `poly status` | List changed files |
| `poly diff` | Show full diffs (optionally for specific files, deployment hashes or between versions with `--before`/`--after`) |
| `poly revert` | Revert local changes (all by default, or specific files) |
| `poly branch` | Branch management: `list`, `create`, `switch`, `current` |
| `poly format` | Format resource files (all or `--files` for specific files) |
| `poly validate` | Validate project configuration locally |
| `poly review` | Diff review page: `create` (local vs remote, version hash, or `--before`/`--after`), `list`, `delete` |
| `poly deployments` | Manage deployments (`list`, with `--env`, `--limit`, `--offset`, `--hash`, `--details`) |
| `poly chat` | Interactive chat session with the agent (`--environment`, `--channel`, `--functions`, `--flows`, `--state`) |
| `poly docs` | Output resource documentation (`poly docs flows functions topics`, or `--all` for everything) |

Use `poly -h` and `poly {command} -h` for more detailed information

## CLI Workflow

The standard CLI workflow is the following:
1. (If not already) Initialise the agent on the local machine using `poly init`. The Agent must exist on Agent Studio first. This will create the project in `account_id/project_id`
2. Get latest version of project using `poly pull`. To override all local changes use the `--force` flag.
3. Start a new branch `poly branch create {name}`. This must be done from the `main` branch. You can navigate between branches using `poly branch switch {name}` and check your current branch using `poly branch current` and existing branches with `poly branch list`
4. Edit files locally, use `poly diff` and `poly status` to track changes.
5. Validate your changes are valid with Agent Studio using `poly validate`
6. Push changes with `poly push`
7. Test and chat with your agent using `poly chat`
8. (Optional) Once ready, use `poly review` and compare your changes to `main`/`sandbox` to generate a GitHub Gist to share with a reviewer. A GitHub environment token is required for this step.
9. Merge your changes on Agent Studio by navigating to your branch and pressing "merge"

If work is done to your branch on the Agent Studio UI that you wish to pull into your local version, you can use `poly pull`. This will merge those changes with yours and show merge markers if a merge conflict occurs.

Commands also must be run from within your project folder. If you are not within your project folder, you can specify where your project is using the `--path` flag

## Resource Reference Syntax

These placeholders can be used in prompts, rules, topics, and other text fields to reference project resources:

| Syntax | Resolves to | Usable in |
|--------|-------------|-----------|
| `{{fn:function_name}}` | Global function | Rules, topics (actions), advanced step prompts |
| `{{ft:function_name}}` | Flow transition function | Advanced step prompts (same flow only) |
| `{{entity:entity_name}}` | Collected entity value | Flow step prompts |
| `{{attr:attribute_name}}` | Variant attribute | Rules, prompts, topics (actions), greeting, disclaimer, personality, role |
| `{{twilio_sms:template_name}}` | SMS template | Rules, topics (actions) |
| `{{ho:handoff_name}}` | Handoff destination | Rules |
| `{{vrbl:variable_name}}` (preferred) / `$variable_name` | State variable (interchangeable; `{{vrbl:...}}` is validated) | Prompts, topic actions, SMS templates |

## Documentation

Resource-specific documentation is available via `poly docs {resource} [resource ...]` or `poly docs --all`. Docs can also be read directly from `src/poly/docs/`:

- [Agent Settings](agent_settings.md) - personality, role, rules
- [Voice Settings](voice_settings.md) - voice greeting, disclaimer, style prompt
- [Chat Settings](chat_settings.md) - chat greeting, style prompt
- [Flows](flows.md) - multistep processes with steps, functions, conditions
- [Functions](functions.md) - global and flow functions, decorators, state, metrics
- [Topics](topics.md) - knowledge base for RAG
- [API Integrations](api_integrations.md) — external HTTP API definitions
- [Entities](entities.md) - structured data collection
- [Handoffs](handoffs.md) - SIP call transfers
- [Variants](variants.md) - per-variant configuration
- [SMS Templates](sms.md) - text message templates
- [Variables](variables.md) - state variables referenced in code
- [Speech Recognition](speech_recognition.md) - ASR settings, keyphrase boosting, transcript corrections
- [Response Control](response_control.md) - pronunciations, phrase filters
- [Safety Filters](safety_filters.md) - content moderation settings (violence, hate, sexual, self-harm)
- [Experimental Config](experimental_config.md) - feature flags


# Agent Settings

## Overview

Agent settings define the agent's identity and behavioral rules. They live in `agent_settings/` and consist of three resources: personality, role, and rules.

## File structure
```
agent_settings/
├── personality.yaml
├── role.yaml
├── rules.txt
└── experimental_config.json   # See experimental_config docs
```

## Personality (`personality.yaml`)

Controls the agent's conversational tone.

### Fields
- **adjectives**: Map of personality traits to booleans. Allowed values: `Polite`, `Calm`, `Kind`, `Funny`, `Energetic`, `Thoughtful`, `Other`. If `Other` is `true`, no other adjective can be selected.
- **custom**: Free-text personality description. Supports `{{attr:...}}` and `{{vrbl:...}}` references.

### Example
```yaml
adjectives:
  Polite: true
  Calm: true
  Kind: true
custom: ""
```

## Role (`role.yaml`)

Defines what the agent is (its job title / purpose).

### Fields
- **value**: Role name (e.g. `Customer Service Representative`). If set to `other`, the `custom` field is used.
- **additional_info**: Extra context about the role.
- **custom**: Free-text role description, only valid when `value` is `other`. Supports `{{attr:...}}` and `{{vrbl:...}}` references.

### Example
```yaml
value: Customer Service Representative
additional_info: Handles customer inquiries and bookings
custom: ""
```

## Rules (`rules.txt`)

Plain-text behavioral instructions the agent follows on every turn. This is a key file for shaping agent behavior.

### Supported references
- `{{fn:function_name}}` - global functions
- `{{twilio_sms:template_name}}` - SMS templates
- `{{ho:handoff_name}}` - handoffs
- `{{attr:attribute_name}}` - variant attributes
- `{{vrbl:variable_name}}` - variables

### Example
```text
Be helpful and professional at all times.
Use {{fn:validate_email}} when the user provides an email address.
For complex issues, use {{ho:escalation_handoff}} to transfer to a specialist.
Send confirmation via {{twilio_sms:confirmation_template}} after booking.
```

### Best practices
- Keep rules concise and actionable.
- Use references (`{{fn:...}}`, `{{attr:...}}`) instead of hard-coding values.
- Avoid encoding branching logic here; use flows/functions for conditional behavior.


# API Integrations

## Purpose

API integrations let you define external HTTP APIs in your project and call them from [functions](functions.md) and [flows](flows.md) without writing custom request code. Use them when your agent needs to:

- Fetch or send data to an external system (CRM, ticketing, booking, payments)
- Call internal services with a shared, inspectable definition
- Avoid maintaining custom HTTP logic inside function code

## Location

`config/api_integrations.yaml`. Integrations are listed under the `api_integrations` key.

## Structure

Each API integration has:

- **name**: Identifier for the API. Becomes the namespace at runtime: `conv.api.<name>`.
- **description**: Optional description of what the API is used for.
- **environments**: Per-environment config (see below).
- **operations**: List of HTTP operations (method, name, resource path).

## Environments

Each integration supports separate configuration for:

- **sandbox** (draft)
- **pre_release**
- **live**

Per environment you set:

- **base_url**: Base URL for that environment (e.g. `https://website.com`).
- **auth_type**: Authentication type (e.g. `none`, `basic`, `apiKey`, `oauth2`).

This lets you test against staging in sandbox and promote without changing code.

## Operations

Each operation is one HTTP endpoint. You define:

- **name**: Operation name; used at runtime as `conv.api.<api_name>.<operation_name>(...)`.
- **method**: HTTP method (e.g. `GET`, `POST`, `PUT`, `DELETE`).
- **resource**: Path template (e.g. `/tickets/{id}`). Path variables are exposed as arguments when calling the operation.

## Usage

- **In functions and flows**: Call an operation with `conv.api.<api_name>.<operation_name>(...)`. Path variables can be positional or keyword arguments.
- **Return value**: Calls return a `requests.Response`-like object — use `response.status_code`, `response.text`, `response.json()` as usual.
- **Query, body, headers**: Operations accept keyword arguments for `params`, `json`, `headers`, etc., similar to a standard HTTP client.
- **Authentication**: Configured at the API level per environment; credentials are managed by Agent Studio and are not stored in the YAML or embedded in flows and functions.

## Example

```yaml
api_integrations:
  - name: salesforce
    description: CRM and contact lookup
    environments:
      sandbox:
        base_url: https://sandbox-api.salesforce.com
        auth_type: oauth2
      pre-release:
        base_url: https://staging-api.salesforce.com
        auth_type: oauth2
      live:
        base_url: https://api.salesforce.com
        auth_type: oauth2
    operations:
      - name: get_contact
        method: GET
        resource: /contacts/{contact_id}
      - name: update_contact
        method: PATCH
        resource: /contacts/{contact_id}
```

In a function you might call:

```python
response = conv.api.salesforce.get_contact("123")
data = response.json()
return {"content": f"Status: {data.get('status', 'unknown')}."}
```

```python
response = conv.api.salesforce.update_contact(
    params={"id": "123"},
    json={"phone_number": "456"}
)
```

# Chat Settings

## Overview

Chat settings configure the agent's behavior on the web chat channel. They are defined in `chat/configuration.yaml`.

## Location
`chat/configuration.yaml`

## Greeting

The first message the agent sends when a chat session starts.

### Fields
- **welcome_message** (required): Text of the greeting. Supports `{{attr:...}}` and `{{vrbl:...}}` references.
- **language_code** (required): BCP-47 language code (e.g. `en-GB`, `en-US`).

### Example
```yaml
greeting:
  welcome_message: Hi there! How can I help you today?
  language_code: en-GB
```

## Style Prompt

Channel-specific instructions that shape how the agent writes. Separate from personality - use this for chat-specific guidance (e.g. "keep responses concise", "use bullet points for lists").

### Fields
- **prompt**: Free-text style instructions. No resource references allowed.

### Example
```yaml
style_prompt:
  prompt: You are a helpful and professional web chat assistant. Keep responses concise and use formatting where appropriate.
```

## Full `chat/configuration.yaml` example
```yaml
greeting:
  welcome_message: Hi! How can I help you today?
  language_code: en-GB
style_prompt:
  prompt: You are a helpful and professional web chat assistant. Keep responses concise.
```


# Entities

## Purpose

Entities define structured data the agent can collect from the user (e.g. date of birth, phone number, choice from a list). They are used in flow steps via `extracted_entities` (what to collect) and `required_entities` (what must be collected before a condition can trigger).
They can also be referenced in executed python code.

## Location

`config/entities.yaml`. Entities are listed under the `entities` key.

## Structure

Each entity has:
- **name**: Identifier (snake_case). Used in prompts as `{{entity:entity_name}}`.
- **description**: What the entity represents (shown to the LLM to guide extraction).
- **entity_type**: One of the types below.
- **config**: Type-specific settings.

## Entity types and config

| Type | Config fields | Description |
|------|---------------|-------------|
| **numeric** | `has_decimal`, `has_range`, `min`, `max` | Numbers (e.g. account number, quantity) |
| **alphanumeric** | `enabled`, `validation_type`, `regular_expression` | Mixed text (e.g. booking reference) |
| **enum** | `options` (list of values) | Fixed set of choices |
| **date** | `relative_date` | Calendar dates |
| **phone_number** | `enabled`, `country_codes` | Phone numbers with country validation |
| **time** | `enabled`, `start_time`, `end_time` | Times or time ranges |
| **address** | `{}` | Physical addresses |
| **free_text** | `{}` | Unstructured text input |
| **name_config** | `{}` | Person names |

## Usage

- **In flow prompts**: `{{entity:entity_name}}` to reference the collected value.
- **In function steps**: `conv.entities.entity_name.value` to read; check with `if conv.entities.entity_name: ...`.
- **In default step conditions**: `required_entities` gates a condition - it only triggers once all listed entities are collected.
- **In default steps**: `extracted_entities` tells the agent which entities to collect in that step. ASR biasing is automatically configured based on entity types.

## Example
```yaml
entities:
  - name: date_of_birth
    description: The customer's date of birth
    entity_type: date
    config:
      relative_date: false
  - name: party_size
    description: Number of guests for the reservation
    entity_type: numeric
    config:
      has_decimal: false
      min: 1
      max: 20
  - name: meal_preference
    description: The customer's preferred meal type
    entity_type: enum
    config:
      options:
        - vegetarian
        - vegan
        - standard
        - halal
```


# Experimental Config

## Purpose
Optional JSON file that enables experimental features and their settings for an agent (feature flags, ASR tuning, conversation control, debug options).

## Location
`agent_settings/experimental_config.json`

## Structure
A flat or nested JSON object. Top-level keys are feature categories; values are feature-specific settings.

## Example
```json
{
  "asr": {
    "disable_itn": true,
    "eager_final": true
  },
  "conversation_control": {
    "enhanced_tts_preprocessing_enabled": false,
    "max_silence_count": 1000,
    "min_chunk_size": 1
  }
}
```

## Schema
Available features and their types are defined in `src/poly/resources/experimental_config_schema.yaml`. The `poly validate` command checks the file against this schema. Invalid config in deployed agents will not be read by the runtime.

## When to use
- Tuning ASR/TTS behavior beyond standard Agent Studio settings.
- Enabling experimental platform features before they are generally available.
- Adjusting conversation control parameters (silence handling, chunk sizes).

## Best practices
- Only set values you intend to override; omit defaults.
- Validate locally with `poly validate` before pushing.
- Remove flags that are no longer needed.


# Flows

## Purpose
Flows choreograph multi-step processes. The LLM only sees the current step's prompt and tools. Prefer one task per step; do branching and conditionals in Python via transitions.

## Entering a flow
- **From code**: `conv.goto_flow('Flow Name')` (enters at configured Start Step).
- **Via return**: `return {"transition": {"goto_flow": "Flow Name", "goto_step": "Step Name"}}`.
- **Within a flow**: `flow.goto_step("Step Name")` in flow functions only.

## File structure
```
flows/
└── {flow_name}/                    # lowercase, snake_case
    ├── flow_config.yaml
    ├── steps/
    │   └── {step_name}.yaml        # default or advanced steps
    ├── function_steps/
    │   └── {function_step}.py      # deterministic Python steps
    └── functions/
        └── {function_name}.py      # transition functions (called from advanced steps)
```

Directory and file names are cleaned to lowercase snake_case.

## Flow config (`flow_config.yaml`)
Information about the flow.

Fields:
- **name**: Human-readable flow name
- **description** (required): What this flow does
- **start_step** (required): Name of the step to enter when the flow is triggered. Must match a real step name.

Example:
```yaml
name: Example Flow
description: Handles the booking process
start_step: Collect Details
```

## Flow Steps
A step represents the agent's current position in the flow. There are 3 types of steps: default steps (no code), advanced steps, and function steps.

### Default Steps (`steps/*.yaml`)
These steps use only LLM logic to process data and transition to other steps. They can define conditions for how to do this.
They cannot reference transition functions in their prompt.

ASR biasing is automatically set up based on the entities requested.

Fields:
- **step_type**: `default_step`
- **name**: Human-readable step name
- **conditions**: List of conditions to transition to other steps
- **extracted_entities**: Entities to extract in this step (from `config/entities.yaml`)
- **prompt**: Instructions for the LLM; use `{{entity:entity_name}}` for entity values. Cannot call functions

#### Conditions
These define how the agent can transition out of one default node. They can transition to any other node and also be made to exit the flow.

Example:
- **condition_type**: `step_condition` (go to another step) or `exit_flow_condition` (exit flow)
- **description**: When this condition applies
- **child_step**: Next step - **only for step_condition**; omit for exit_flow_condition
- **required_entities**: Entities that must be collected before this condition can trigger

**child_step rules:**
- **Default step**/**Advance step** → use its `name:` (e.g. `Collect Date of Birth`)
- **Function step** → use Python filename without `.py`, snake_case (e.g. `process_cancellation`).

### Advanced Steps (`steps/*.yaml`)
A step with more advanced options, such as custom ASR and DTMF rules and the ability to call transition functions in the prompt.

Fields:
- **step_type**: `advanced_step`
- **name**: Human-readable step name
- **asr_biasing**: ASR settings for the turn
  **is_enabled** Boolean if ASR settings are enabled
  ASR settings, each is a boolean of whether to tune ASR for that type of input
  **alphanumeric**
  **name_spelling**
  **numeric**
  **party_size**
  **precise_date**
  **relative_date**
  **single_number**
  **time**
  **yes_no**
  **address**
  **custom_keywords**: [] List of words to bias for
- **dtmf_config**:
  **is_enabled** Boolean if ASR settings are enabled
  **inter_digit_timeout** (int) How long to wait in seconds between button presses
  **max_digits** (int) Max number of digits to collect
  **end_key** (str) When key is pressed, end collection
  **collect_while_agent_speaking** (bool) Allow collection during agents speech
  **is_pii** (bool) Does user input count as PII
- **prompt**: Instructions for the LLM; Can call functions


### Step prompts
Tips:
- **Prompts**: for collecting input, presenting info, conversation. **Python**: for comparisons, if/else, routing on state.
- **No deterministic logic in prompts**: no "If $x == 0 do A" in prompts. Do value checks and routing in Python and transition to the right step.
- **State in prompts**: use `$variable`, not `conv.state.variable`. No `$var.attribute`; stringify in Python and reference a single state string.
- **Flow function reference**: `{{ft:flow_function}}` in advanced step prompts only.

### Function Steps (`function_steps/*.py`)

Function steps are deterministic Python steps in the flow. They execute code without LLM involvement, making them ideal for API calls, data validation, and routing logic. They are best used in conjunction with default steps.

Unlike regular functions, function steps cannot have additional parameters and cannot set a description.

For more information, look at the `functions` docs.

**Signature**: `def function_name(conv: Conversation, flow: Flow):`

Tips:
- **Entities**: Read using `conv.entities.entity_name.value`; check with `if conv.entities.entity_name: ...`
- **State**: `conv.state.variable_name = value` (use `$variable_name` in prompts)
- **Flow control**: Must call `flow.goto_step('Step Name', 'Reason')` or `conv.exit_flow()`
- **Return**: Optional string used as LLM context (what happened and what to tell the user)
- **Errors**: try/except; log; `flow.goto_step('error_step', 'Reason')` and return context string
- **Logging/metrics**: `conv.log.info/warning/error(...)`, `conv.write_metric("NAME", value)`

## Transition functions (`functions/*.py`)

Transition functions can be called in `advanced_step`s. They can be used to transition the agent to other steps.
Unlike function steps, you can define a custom set of parameters for them and give them a description that the LLM uses to judge when to call them.

These can be referenced using `{{ft:flow_function}}` and can only be called within the same flow.

Tips:
Logic that is reused between flow functions is best put in global functions, which can be imported or called with `conv.functions.my_global_function(...)`.
Keep logic here simple, so it's easy to view at a glance what the function is doing.

For more information, look at the `functions` docs.

## Best practices
- **No "Anything else?" step**: when the flow is done, `conv.exit_flow()` and return the "anything else?" prompt from the function.
- **Hard-coded utterances**: put them in `utterances.py` and return from the caller (e.g. start_function); don't add a flow function only to return one phrase.
- **Prompts:** Use markdown headers, clear order of operations, validation/edge cases, voice-friendly phrasing ("read digit by digit"), and clear "Once X, then Y" transitions.
- **Concepts:** Linear (A->B->C), branching, loops (back to earlier steps), exit_flow_condition for leaving the flow, required_entities and extracted_entities for collection and gating

## Common mistakes
- **Flow functions must always advance**: use `flow.goto_step(...)` or return a transition; don't leave the flow stuck on the same step with no navigation.
- **No deterministic logic in prompts**: don't encode branching in prompts (e.g. "If $x == 0 do A, else B"). Do value checks and routing in Python and transition to the right step.
- **No hardcoded IDs**: use resource names, not internal IDs.
- **Don't read entities in default step code**: entity values are available in prompts via `{{entity:entity_name}}`.
- **Function steps must control flow**: every function step must call `flow.goto_step(...)` or `conv.exit_flow()` and return LLM context. Keep complex logic in function steps, not prompts.
- **`end_turn=False`**: use only when the agent must immediately call a function after speaking (no user reply). Don't use it just to add a question after an utterance; put the question in the utterance.
- **Don't mix exit and navigation**: use **either** `conv.exit_flow()` and return content **or** a transition/goto, not both. `conv.goto_flow(...)` after `conv.exit_flow()` will override the exit.

## Design principles
1. Start with a single path, then add branching
2. Add a confirmation step before function steps that change state
3. Add steps/conditions for errors and failures
4. One clear purpose per step; meaningful step names
5. Test the full path from start to exit


# Functions

## Overview

Functions are Python files that add deterministic logic to your agent. They can be called by the LLM during conversation, used as flow steps, or run automatically at call start/end.

## Location
```
functions/                          # Global functions
├── start_function.py               # Optional - runs once at call start
├── end_function.py                 # Optional - runs once at call end
└── {function_name}.py              # Called by LLM via {{fn:function_name}}
flows/{flow_name}/
├── functions/
│   └── {function_name}.py          # Flow transition functions, called via {{ft:function_name}}
└── function_steps/
    └── {function_step}.py          # Deterministic flow steps (no LLM)
```

## Function types

| Type | Location | Signature | Referenced as |
|------|----------|-----------|---------------|
| **Global** | `functions/` | `def name(conv: Conversation, ...)` | `{{fn:name}}` |
| **Transition** | `flows/{flow}/functions/` | `def name(conv: Conversation, flow: Flow, ...)` | `{{ft:name}}` (same flow only) |
| **Function step** | `flows/{flow}/function_steps/` | `def name(conv: Conversation, flow: Flow)` | Stepped into by conditions |
| **Start** | `functions/start_function.py` | `def start_function(conv: Conversation)` | Runs automatically |
| **End** | `functions/end_function.py` | `def end_function(conv: Conversation)` | Runs automatically |

## File structure rules

- Every `.py` file must define a function with the **same name as the file** (without `.py`).
  This function is the entry point for the file when called by the LLM.
- Only the main function requires `@func_` decorators to define how it's run and shown to the LLM
- Use `from _gen import *  # <AUTO GENERATED>` in your function to match the imports used when function is run by the agent.
  This line is not pushed to Agent Studio, and must match this exact pattern.

## Decorators

- **`@func_description('...')`** (required for global and transition functions): Description shown to the LLM to decide when to call the function.
- **`@func_parameter('param_name', '...')`** (required for each parameter except `conv` and `flow`): Description of the parameter shown to the LLM. All parameters must also have a typed Python annotation (e.g. `booking_ref: str`)
- **`@func_latency_control(...)`** (optional): Configure delay messages while the function runs.

Function steps do not support `@func_parameter` or `@func_description`.

### Parameter types

Parameters support these Python types, mapped to schema types:

| Python type | Schema type |
|-------------|-------------|
| `str` | `string` |
| `int` | `integer` |
| `float` | `number` |
| `bool` | `boolean` |

### Example
```python
from _gen import *  # <AUTO GENERATED>


@func_description("Look up a booking by reference number.")
@func_parameter("booking_ref", "The booking reference provided by the customer")
@func_parameter("include_history", "Whether to include booking history")
def lookup_booking(conv: Conversation, booking_ref: str, include_history: bool):
    result = external_api.get_booking(booking_ref, include_history)
    if not result:
        return "No booking found. Ask the customer to verify the reference number."
    conv.state.booking = str(result)
    return f"Booking found: {result['status']}. Confirm the details with the customer."
```

## Naming

Prefer naming after the **event that should trigger the call** (e.g. `first_name_provided`, `booking_confirmed`), not the action (`store_first_name`, `send_confirmation`). This helps the LLM understand when to call it.

## Returns and control flow

| Return type | Effect |
|------------|--------|
| `return "string"` | String is injected as system context to the LLM |
| `conv.say("exact phrase")` | Speak/send exact text (first sentence should be static for cached audio) |
| `conv.goto_flow("name")` | Navigate to a flow |
| `flow.goto_step("Step Name", "reason")` | Navigate to a step (flow functions only) |
| `conv.exit_flow()` | Exit the current flow |
| `conv.call_handoff(destination="...", reason="...")` | Transfer the call |
| `return {"hangup": True}` | End the call |
| `return {"transition": {"goto_flow": "...", "goto_step": "..."}}` | Navigate via dict |
| `return {"utterance": "...", "end_turn": False}` | Speak and immediately continue (no user reply) |

### Calling other functions
- Global: `conv.functions.my_global_function(...)`
- Flow: `flow.functions.my_flow_function(...)`

## Special functions

### Start function (`start_function.py`)
- Runs **once at call start**, before the first user input.
- Signature: `def start_function(conv: Conversation):` - no `flow`, no `@func_parameter`.
- Typical use: initialize state, read SIP headers, set language, write initial metrics, then `conv.goto_flow("...")`.

### End function (`end_function.py`)
- Runs **once at call end**, after the conversation completes.
- Signature: `def end_function(conv: Conversation):`
- Typical use: aggregate `conv.metric_events`, write summary metrics (e.g. `CALL_OUTCOME`), optionally trigger post-call webhooks when `conv.env == "live"`.

## Utility modules
If a function file isn't intended to be called by the LLM, it still needs a main function matching the filename. Decorate it and have it return a "utility module" message. Do not decorate helper functions.

## State
`conv.state` is preserved between turns. Use it to set variables for future logic or to be used in prompts
- **Set**: `conv.state.variable_name = value`
- **Read**: `conv.state.variable_name` (returns `None` if not set)
- **In prompts**: `$variable` or `{{vrbl:variable}}` (not `conv.state.variable`). No `$var.attribute` - stringify in Python first.

### Counters
Use `conv.state.counter` (initialize and increment) to avoid infinite retries. After a limit (e.g. 3), hand off or exit.

## Metrics

- **Write**: `conv.write_metric("EVENT_NAME")`, `conv.write_metric("NAME", value)`, `conv.write_metric("NAME", write_once=True)`
- **Naming**: `SCREAMING_SNAKE_CASE`; group with prefixes (e.g. `SMS_OFFERED`, `SMS_ACCEPTED`, `SMS_SENT`)
- Use metrics for events you wish to filter calls with or use for analysis such as flow entry, decisions, and key moments.
- Use `write_once=True` when a metric should be recorded once (e.g. flow entered); avoid writing the same metric repeatedly in a loop.
- Log important outcomes (`conv.log.info` / `conv.log.error`) around external calls and failures; don't fail silently.

## Quick reference

| Task | Code |
|------|------|
| State in prompt | `$variable` or `{{vrbl:variable}}`|
| State in code | `conv.state.variable` |
| Persist data | `conv.state.variable = value` |
| Track event | `conv.write_metric("NAME", value)` |
| Call global function | `conv.functions.my_function(...)` |
| Call flow function | `flow.functions.my_function(...)` |
| Navigate to flow | `conv.goto_flow("Flow Name")` |
| Navigate to step | `flow.goto_step("Step Name", "reason")` |
| Exit flow | `conv.exit_flow()` |
| Transfer call | `conv.call_handoff(destination="...", reason="...")` |


# Handoffs

## Overview
Handoffs configure SIP call transfers for voice agents. They define how and where to transfer a call (invite, refer, or end).

## Location
`config/handoffs.yaml`. Handoffs are listed under the `handoffs` key.

## Structure

Each handoff has:
- **name** (string): Identifier for the handoff. Referenced in rules as `{{ho:handoff_name}}`.
- **description** (string): What this handoff does.
- **is_default** (bool): Whether this is the default handoff.
- **sip_config** (object): Transfer method configuration (see below).
- **sip_headers** (list, optional): Custom SIP headers as `key`/`value` pairs.

## SIP config types

| Method | Use | Fields |
|--------|-----|--------|
| **invite** | Outbound new call | `phone_number` (E.164), `outbound_endpoint`, `outbound_encryption` (`TLS/SRTP` or `UDP/RTP`) |
| **refer** | Transfer existing call | `phone_number` (E.164) |
| **bye** | End call | No extra fields |

## Example
```yaml
handoffs:
  - name: escalation_handoff
    description: Transfer to a live agent for complex issues
    is_default: false
    sip_config:
      method: refer
      phone_number: "+15551234567"
    sip_headers:
      - key: X-Reason
        value: escalation
  - name: end_call
    description: End the call gracefully
    is_default: false
    sip_config:
      method: bye
```

## Usage
- **In code**: `conv.call_handoff(destination="handoff_name", reason="transfer_reason")`
- **In rules**: Reference as `{{ho:handoff_name}}` with instructions for when to use it.
- **In topics/flows**: Instruct the LLM to call a function that performs the handoff (e.g. `{{fn:transfer_call}}`).

## Best practices
- Use clear, descriptive handoff names.
- Use E.164 format for phone numbers.
- One handoff config per purpose (don't reuse the same config for different transfer destinations).
- Keep `sip_headers` minimal and only add custom headers when the receiving system needs them.


# Response Control

## Overview

Response control resources manage what the agent says before it reaches the user. They handle TTS pronunciation fixes and phrase filtering (blocking or intercepting output). They live under `voice/response_control/`.

```
voice/response_control/
├── pronunciations.yaml             # Optional - TTS pronunciation rules
└── phrase_filtering.yaml           # Optional - block/intercept phrases before TTS
```

## Pronunciations (`pronunciations.yaml`)

TTS pronunciation rules that fix how the agent says specific words or abbreviations. Rules are regex-based and applied before speech synthesis.

### Structure
A `pronunciations` list where each entry has:
- **regex** (required): Regex pattern to match in the agent's output text.
- **replacement** (required): What to replace it with for TTS (can be empty string `""`).
- **case_sensitive** (bool): Whether the regex is case-sensitive. Default: `false`.
- **language_code** (string, optional): Restrict the rule to a specific language.
- **description** (string, optional): What this rule does.

Rules are ordered; position in the list matters.

### Example
```yaml
pronunciations:
  - regex: "\\bDr\\."
    replacement: Doctor
    case_sensitive: true
  - regex: "\\bMr\\."
    replacement: Mister
    case_sensitive: true
```

## Phrase Filters (`phrase_filtering.yaml`)

Intercept or block phrases in the agent's output before they are spoken. Can optionally trigger a function when a phrase is matched.

### Structure
A `phrase_filtering` list where each entry has:
- **name** (required): Identifier for this filter.
- **description**: What this filter does.
- **regular_expressions** (required): List of regex patterns to match.
- **say_phrase** (bool): If `true`, still speak the matched phrase. If `false`, suppress it. Default: `false`.
- **language_code** (string, optional): Restrict to a specific language.
- **function** (string, optional): Name of a global function to call when a match occurs.

### Example
```yaml
phrase_filtering:
  - name: Block Profanity
    description: Blocks profane words from being spoken
    regular_expressions:
      - "\\bbadword\\b"
    say_phrase: false
  - name: Competitor Mention Handler
    description: Intercept competitor names and redirect
    regular_expressions:
      - "\\bcompetitor_name\\b"
    say_phrase: true
    function: handle_competitor_mention
```

### Best practices
- Use phrase filters for safety (profanity, PII leakage) and brand protection.
- The `function` field must reference a valid global function (not a flow function).
- Keep regex patterns specific to avoid false positives.


# Safety Filters

## Overview

Safety filters automatically block harmful content and prevent unsafe agent responses in real-time to protect both callers and your brand.
They run on both user input and AI output to block risky content before it affects the conversation.

In Agent Studio, content filtering can be set across four categories (violence, hate, sexual, self-harm) at both the project level and per-channel (voice/chat). Each category can be independently enabled and tuned to a sensitivity level.

## File structure
```
agent_settings/
└── safety_filters.yaml       # Project-level (general) safety filters
voice/
└── safety_filters.yaml       # Voice channel overrides
chat/
└── safety_filters.yaml       # Chat channel overrides
```

All three files share the same schema. Channel-level files override the project-level defaults for that channel.

## Fields

- **enabled**: `true` or `false` — whether safety filtering is active.
- **categories**: A map of the four content filter categories. Each category has:
  - **enabled**: `true` or `false` — whether this category is active.
  - **level**: Sensitivity level. One of `lenient`, `medium`, `strict`.

### Categories

| Category | Description |
|----------|-------------|
| `violence` | Filters violent or graphic content |
| `hate` | Filters hateful or discriminatory content |
| `sexual` | Filters sexually explicit content |
| `self_harm` | Filters self-harm related content |

## Example

General Settings are globally enabled with individual toggles per category

```yaml
categories:
  violence:
    enabled: true
    level: medium
  hate:
    enabled: true
    level: medium
  sexual:
    enabled: true
    level: medium
  self_harm:
    enabled: true
    level: medium
```

Per-Channel Settings include a global enabled toggle:

```yaml
enabled: true
categories:
  violence:
    enabled: true
    level: medium
  hate:
    enabled: true
    level: medium
  sexual:
    enabled: true
    level: medium
  self_harm:
    enabled: true
    level: medium
```

## Validation rules

- All four categories (`violence`, `hate`, `sexual`, `self_harm`) must be present.
- Each category must have both `enabled` and `level` set.
- `level` must be one of: `lenient`, `medium`, `strict`.

## Best practices

If setting safety filters across multiple channels, make the settings consistent for each - or vary depending on unique use cases/ risk profile for each.



# SMS Templates

## Purpose

SMS templates define text messages the agent can send during a conversation (e.g. confirmation texts, links, verification codes). They support dynamic content via variables.

## Location

`config/sms_templates.yaml`. Templates are listed under the `sms_templates` key.

## Structure

Each template has:
- **name**: Identifier. Referenced in prompts as `{{twilio_sms:template_name}}`.
- **text**: Message body. Use `{{vrbl:variable_name}}` for dynamic values from `conv.state`.
- **env_phone_numbers** (optional): Per-environment sender phone numbers:
  - **sandbox**: Phone number for sandbox environment
  - **pre_release**: Phone number for pre-release environment
  - **live**: Phone number for production

## Example
```yaml
sms_templates:
  - name: booking_confirmation
    text: "Hi {{vrbl:customer_name}}, your booking for {{vrbl:booking_date}} is confirmed. Reference: {{vrbl:booking_ref}}"
    env_phone_numbers:
      sandbox: "+15551234567"
      live: "+15559876543"
  - name: verification_code
    text: "Your verification code is {{vrbl:verification_code}}. It expires in 10 minutes."
```

## Usage

- **In rules / topics / flows**: Use `{{twilio_sms:template_name}}` to instruct the LLM to send the SMS at the right moment.
- **In code**: Call a function that triggers the SMS via `conv` or the platform API.
- **Variables**: Set the referenced variables in `conv.state` before the SMS is triggered, so the template can resolve `{{vrbl:...}}` placeholders.

## Best practices
- Set state variables (e.g. `conv.state.customer_name`) before the SMS is sent.
- Use separate templates for different purposes (confirmation, verification, follow-up).
- Configure `env_phone_numbers` to use different sender numbers per environment.


# Speech Recognition

## Overview

Speech recognition resources control how the agent processes user speech input on the voice channel. They live under `voice/speech_recognition/`.

```
voice/speech_recognition/
├── asr_settings.yaml               # Barge-in, interaction style
├── keyphrase_boosting.yaml         # Optional - bias ASR toward specific words
└── transcript_corrections.yaml     # Optional - regex corrections on ASR output
```

## ASR Settings (`asr_settings.yaml`)

Global speech recognition settings for the voice channel.

### Fields
- **barge_in** (bool): Allow the user to interrupt the agent while it's speaking. Default: `false`.
- **interaction_style** (string): Controls ASR latency/accuracy trade-off. One of: `balanced`, `precise`, `swift`, `sonic`, `turbo`. Default: `balanced`.

### Example
```yaml
barge_in: false
interaction_style: balanced
```

| Style | Behavior |
|-------|----------|
| `precise` | Higher accuracy, higher latency |
| `balanced` | Default balance of speed and accuracy |
| `swift` | Faster responses, slightly less accurate |
| `sonic` / `turbo` | Lowest latency |

## Keyphrase Boosting (`keyphrase_boosting.yaml`)

Bias the speech recognizer toward specific words or phrases (brand names, product names, jargon). Improves recognition accuracy for domain-specific terms.

### Structure
A `keyphrases` list where each entry has:
- **keyphrase** (required): The word or phrase to boost.
- **level**: Boost strength - `default`, `boosted`, or `maximum`. Default: `default`.

### Example
```yaml
keyphrases:
  - keyphrase: PolyAI
    level: maximum
  - keyphrase: reservation
    level: boosted
  - keyphrase: check-in
    level: default
```

## Transcript Corrections (`transcript_corrections.yaml`)

Post-process ASR output with regex rules to fix common misrecognitions. Useful for email domains, spelled-out values, and domain-specific terms.

### Structure
A `corrections` list where each entry has:
- **name** (required): Identifier for the correction group.
- **description**: What this correction fixes.
- **regular_expressions**: List of regex rules, each with:
  - **regular_expression** (required): Regex pattern to match.
  - **replacement** (required): Replacement string (supports capture groups like `\1`).
  - **replacement_type**: `full` (replace entire match, default) or `partial`/`substring` (replace within context).

### Example
```yaml
corrections:
  - name: Email domain fix
    description: Correct common email domain misrecognitions
    regular_expressions:
      - regular_expression: at gmail dot com
        replacement: "@gmail.com"
        replacement_type: full
      - regular_expression: at hotmail dot com
        replacement: "@hotmail.com"
        replacement_type: full
  - name: Number normalization
    description: Normalize spoken numbers to digits
    regular_expressions:
      - regular_expression: \bdouble (\d)\b
        replacement: \1\1
        replacement_type: partial
```


# Topics

## Overview

Topics are the agent's knowledge base, queried via RAG (retrieval-augmented generation). When a user's input matches a topic, the agent retrieves the topic's content and follows its actions.

## Location

`topics/`. One file per topic: `topics/{topic_name}.yaml`.

File names are cleaned to lowercase snake_case. For example, a topic named `"Opening Hours & Locations"` is stored as `topics/opening_hours_locations.yaml`.

## Structure

Each topic has five fields:

- **name** (string): The display name of the topic. This is the canonical name — the filename is derived from it (cleaned to lowercase snake_case).
- **enabled** (bool): Whether the topic is active. Default: `true`.
- **example_queries**: List of example user inputs that should trigger this topic.
- **content**: Factual information retrieved via RAG. No function calls or variable references allowed here.
- **actions**: Behavioral instructions for the agent when the topic is triggered. This is where you use references.

## Example
```yaml
name: Opening Hours & Locations
enabled: true
example_queries:
  - What are your opening hours?
  - When are you open?
  - Are you open on weekends?
  - What time do you close?
content: |-
  The office is open Monday to Friday from 9am to 5pm.
  Weekend hours are Saturday 10am to 2pm. Closed on Sundays.
actions: |-
  Tell the user the opening hours from the content above.

  ## If the user asks about a specific location
  Check the location using {{attr:office_location}} and provide the hours for that location.

  ## If the user wants to speak to someone
  Use {{fn:transfer_to_agent}} to connect them with a representative.
```

## Naming and filenames

- The `name` field in the YAML is the canonical topic name and can contain spaces, punctuation, and mixed case (e.g. `"Opening Hours & Locations"`).
- The filename is cleaned to lowercase snake_case (e.g. `opening_hours_locations.yaml`).
- The filename must match the cleaned version of `name` — a mismatch raises a validation error on `pull` or `push`.

## Example queries
- Maximum **20 queries**.
- Cover different ways a user might ask about the same thing.
- Don't try to cover every minor variation - the model generalizes.

## Content
- Factual information only. This is what gets retrieved via RAG.
- **No** `{{fn:...}}`, `{{ft:...}}`, `$variable`, or `{{attr:...}}` references in content.
- Use multi-line (`|-`) for longer content.

## Actions
- Behavioral instructions: what to say, when to call functions, how to branch.
- **This is the only place** where you can use references in a topic:
  - `{{fn:function_name}}` - call a global function
  - `{{fn:function_name}}('arg')` - call with an argument
  - `{{attr:attribute_name}}` - variant attribute
  - `{{twilio_sms:template_name}}` - SMS template
  - `{{ho:handoff_name}}` - handoff
  - `$variable` - state variable
- **Branching**: Use markdown headers (`##`, `###`) for conditional sections.
- Keep actions clear and scannable; avoid one long paragraph with mixed conditions.

## Best practices
- Don't prompt the model to `"Say: '...'"` (hurts multilingual support); use `"Tell the user that ..."`.
- Prefer structured actions with `## Conditional Branch` sections over a single dense paragraph.
- Keep content and actions separate - content is facts, actions is behavior.
- One topic per subject area. If a topic is getting too large, split it.
- Disable topics with `enabled: false` rather than deleting them during development.


# Variables

## Overview

Variables are virtual resources that represent state values used in the agent's code. Unlike other resources, variables do not have files on disk - they are automatically discovered by scanning function code for `conv.state.<name>` usage.

## How variables work

When you write `conv.state.customer_name = "Alice"` in a function, `customer_name` becomes a tracked variable. The ADK discovers these by scanning all function files (global functions, flow functions, and function steps) for state attribute access patterns.

Variables can be referenced in prompts and templates using `$variable_name` or `{{vrbl:variable_name}}` - these are interchangeable. Prefer `{{vrbl:variable_name}}` as it is validated by the ADK.

## Setting state in code
```python
conv.state.customer_name = "Alice"
conv.state.account_balance = 150.00
conv.state.is_verified = True
```

## Reading state in code
```python
name = conv.state.customer_name  # returns None if not set
if conv.state.is_verified:
    ...
```

## Using variables in prompts and templates

In flow step prompts, topic actions, SMS templates, and other text fields, use either syntax - they are interchangeable:

- `{{vrbl:variable_name}}` (preferred - validated by the ADK)
- `$variable_name`

```
The customer's name is $customer_name and their balance is $account_balance.
```

```yaml
text: "Hi {{vrbl:customer_name}}, your booking is confirmed for {{vrbl:booking_date}}."
```

Do not use `conv.state.variable` syntax in prompts - use `$variable` or `{{vrbl:variable}}` only.

Do not use `$var.attribute` - stringify complex objects in Python first, then store the string in state.

## Best practices
- Variables are discovered automatically - no manual registration needed.
- Use descriptive snake_case names.
- Initialize state variables in `start_function` or early in the flow to avoid `None` values.
- Keep variable names consistent across functions and prompts.


# Variants

## Purpose

Variant attributes provide per-variant configuration (per location, environment, or tenant). The platform chooses a variant at runtime; the agent reads attributes for that variant so prompts and behavior can vary without separate code or deployments.

## Location

`config/variant_attributes.yaml`

## Structure

The file has two top-level keys:

### `variants` - List of variants
- **name** (required): Unique identifier (e.g. a location name, environment, or tenant). Used as the key in attribute `values`.
- **is_default** (optional): Exactly one variant must have `is_default: true`. Used when no variant is resolved at runtime.

### `attributes` - List of attributes
- **name**: Attribute identifier (snake_case recommended), e.g. `greeting_name`, `support_phone_number`.
- **values**: Map from **variant name** to string value. Must have one entry per variant. Values can be `""`, a single line, or multi-line (`|-`).

## Example
```yaml
variants:
  - name: new_york
    is_default: true
  - name: london
  - name: tokyo

attributes:
  - name: office_phone
    values:
      new_york: "+12125551234"
      london: "+442071234567"
      tokyo: "+81312345678"
  - name: office_hours
    values:
      new_york: "9am - 5pm EST"
      london: "9am - 5pm GMT"
      tokyo: "9am - 5pm JST"
  - name: greeting_name
    values:
      new_york: "New York Office"
      london: "London Office"
      tokyo: "Tokyo Office"
  - name: custom_disclaimer
    values:
      new_york: |-
        This call is recorded for quality assurance.
        You may request a copy of this recording.
      london: |-
        This call may be recorded in accordance with UK regulations.
      tokyo: ""
```

Ensure the YAML is formatted correctly, for example variant names with special characters (e.g. `&`, parentheses) must be quoted.

## Usage

### In prompts and resource files
Use `{{attr:attribute_name}}` in:
- Flow step prompts
- Topic actions (not in content or example_queries)
- Rules (`rules.txt`)
- Greeting (`welcome_message`)
- Disclaimer message
- Personality (`custom`)
- Role (`custom`)

```
Our office number is {{attr:office_phone}}. We're open {{attr:office_hours}}.
```

### In Python
```python
phone = conv.variant.office_phone
hours = conv.variant.office_hours
```

Use the same attribute names as defined in `variant_attributes.yaml`.

## Typical attribute types
- **Branding**: greeting name, company name
- **Contact**: phone numbers, addresses, office hours
- **IDs**: location_id, region code
- **Feature flags**: `"True"` / `"False"` strings (check in Python)
- **URLs**: portal link, payment link
- **Environment**: timezone, is_live

## Best practices
- Keep variant names stable; quote them when they contain special characters.
- Set exactly **one** `is_default` variant.
- Provide a value (or `""`) for every variant in each attribute's `values` map. Validation will fail if a variant is missing.
- Prefer `{{attr:...}}` over hard-coded strings for anything that varies by location/environment.
- Use `|-` for multi-line values (disclaimers, hours, instructions).


# Voice Settings

## Overview

Voice settings configure the agent's behavior on the voice (phone call) channel. They are defined in `voice/configuration.yaml`.

## Location
`voice/configuration.yaml`

## Greeting

The first message the agent speaks when a call starts.

### Fields
- **welcome_message** (required): Text of the greeting. Supports `{{attr:...}}` and `{{vrbl:...}}` references.
- **language_code** (required): BCP-47 language code (e.g. `en-GB`, `en-US`).

### Example
```yaml
greeting:
  welcome_message: Hello! Welcome to our service. How can I assist you today?
  language_code: en-GB
```

## Style Prompt

Channel-specific instructions that shape how the agent speaks. Separate from personality - use this for voice-specific guidance (e.g. phrasing, verbosity, tone of speech).

### Fields
- **prompt**: Free-text style instructions. No resource references allowed.

### Example
```yaml
style_prompt:
  prompt: You are a helpful and professional customer service assistant. Use natural, conversational phrasing.
```

## Disclaimer Message

An optional disclaimer played at the start of a voice call before the greeting (e.g. "This call may be recorded").

### Fields
- **message**: Disclaimer text. Supports `{{attr:...}}` and `{{vrbl:...}}` references.
- **enabled**: Boolean to toggle the disclaimer on/off.
- **language_code**: BCP-47 language code.

### Example
```yaml
disclaimer_messages:
  message: This conversation may be recorded for quality assurance.
  enabled: true
  language_code: en-GB
```

## Full `voice/configuration.yaml` example
```yaml
greeting:
  welcome_message: Hello! Welcome to our service. Your account shows {{attr:member_status}}. How can I assist you today?
  language_code: en-GB
style_prompt:
  prompt: You are a helpful and professional customer service assistant.
disclaimer_messages:
  message: This conversation may be recorded for quality assurance.
  enabled: true
  language_code: en-GB
```

## Related voice resources
- [Speech Recognition](speech_recognition.md) - ASR settings, keyphrase boosting, transcript corrections
- [Response Control](response_control.md) - pronunciations, phrase filters

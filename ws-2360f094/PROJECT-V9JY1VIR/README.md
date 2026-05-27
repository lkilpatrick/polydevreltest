# Sanctuary Cruises — PolyAI ADK Demo Project

A full-featured PolyAI ADK voice agent for **Sanctuary Cruises**, a Monterey Bay whale watching company based in Moss Landing, California. Built as a DevRel interview demo to show real-world ADK patterns.

---

## Agent Capabilities

| Capability | Mechanism |
|---|---|
| Check live trip availability | `lookup_fareharbor_availability` global function |
| Guided booking flow with entity collection | `Booking Flow` (4 steps + 1 function step) |
| Private charter routing | Private charter branch in function step |
| FAQ answering | `FAQ` topic + knowledge base |
| Human escalation | `escalate_call` global function |
| Clean call end | `goodbye_and_hang_up` global function |
| Start booking from any topic | `start_booking_flow` global function |
| Keyphrase and pronunciation tuning | speech_recognition + response_control files |

---

## Project Structure

```
PROJECT-V9JY1VIR/
  agent_settings/         # Personality, role, rules
  config/
    entities.yaml         # 10 shared entities
  data/
    whale_watch_schedule_next_3_months.json   # Jun-Aug 2026 schedule snapshot
    marine_mammals_reference.json             # Species reference
  docs/
    source_notes.md       # Attribution for all data sources
  flows/
    booking_flow/
      flow_config.yaml
      steps/              # collect_trip_type, collect_date, collect_party_size, collect_contact
      function_steps/     # check_fareharbor_availability
  functions/              # Global ADK functions
  integrations/
    fareharbor.py         # FareHarbor helper module
  knowledge/
    sanctuary_cruises_knowledge.md
  topics/                 # Book a Cruise, FAQ, Human Handoff, Private Charter
                          # + sanctuary_cruises_marine_mammals_and_seasonality
                          # + sanctuary_cruises_trip_planning_and_policies
  voice/
    speech_recognition/   # keyphrase_boosting.yaml, transcript_corrections.yaml, asr_settings.yaml
    response_control/     # pronunciations.yaml
    configuration.yaml
```

---

## Environment Variables (FareHarbor)

For live FareHarbor External API access, set these in your PolyAI environment or `.env`:

```
FAREHARBOR_API_APP=your_app_key_here
FAREHARBOR_API_USER=your_user_key_here
FAREHARBOR_COMPANY_SHORTNAME=sanctuarycruises
FAREHARBOR_BASE_URL=https://fareharbor.com/api/external/v1
```

If these are not set, the agent falls back to the public embed calendar API (no key required). If that also fails, it uses the local schedule snapshot in `data/`.

---

## Quick Start

```bash
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Check current branch
poly branch current

# Validate all files
poly validate

# Diff against main
poly diff

# Push to branch
poly push
```

---

## ADK Patterns Demonstrated

### Global Functions
- `lookup_fareharbor_availability` — LLM-callable with `@func_description`, fetches live FareHarbor data
- `start_booking_flow` — Redirects caller into the Booking Flow
- `escalate_call` — Logs escalation reason, returns crew contact
- `goodbye_and_hang_up` — Returns `{"hangup": True}`

### Flow Design
- 4 default steps collect `trip_type`, `trip_date`, `party_size`, and `contact`
- 1 function step (`check_fareharbor_availability`) calls the live integration, interprets results, and decides next step via `flow.goto_step()` or `conv.exit_flow()`
- Private charter branch exits the flow early with escalation instructions

### Entities Used
- `trip_type` (free_text), `trip_date` (date), `adult_count`/`child_count`/`party_size` (numeric), `contact_phone` (phone_number), `contact_email`/`occasion` (free_text), `customer_name` (name_config)

### Topics
- Each topic has `name`, `enabled`, `example_queries`, `content`, and `actions`
- `actions` references functions using `{{fn:function_name}}`
- Topics escalate when needed rather than over-promising

---

## Test Prompts

```
"Do you have any whale watching trips available this Saturday morning?"
"I want to book two adults and one child for next Friday."
"What are the chances of seeing blue whales in July?"
"Can you do a private charter for a birthday party of 30?"
"What should I bring on the trip?"
"I need to cancel my booking."
"Can I speak to someone?"
```

---

## Live Data Verified

FareHarbor public calendar API confirmed working as of May 2026:
- Endpoint: `https://fareharbor.com/api/v1/companies/sanctuarycruises/items/25836/calendar/2026/05/`
- May 29, 2026: 8:00 AM departure, 7 spots available, `is_bookable: true`

---

## Interview Walkthrough

1. **Intro** — Show project structure and explain the agent's role
2. **Live call demo** — Ask for availability on a near-future date; agent calls FareHarbor, reads back times
3. **Booking flow** — Walk through trip type → date → party size → availability check
4. **Escalation** — Ask to cancel a booking; agent gracefully hands off
5. **FAQ** — Ask about seasickness; agent answers from knowledge base without hallucinating
6. **Architecture questions** — Explain flow/topic/function layering and FareHarbor integration strategy

---

## FareHarbor Item PKs Reference

| Item | PK |
|---|---|
| Whale Watching 2-3 hr | 25836 |
| Whale Watching 3-4 hr | 25833 |
| Embed flow ID | 1127725 |
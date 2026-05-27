# Sanctuary Cruises PolyAI ADK Demo

This project is a realistic, production-minded voice reservation assistant demo for Sanctuary Cruises.

This demo shows how a voice agent can be built like software: local development, tool boundaries, source-of-truth discipline, testable conversation flows, and safe escalation.

## Project Goal

Build a voice agent that can:
- answer common customer questions
- help callers choose the right cruise
- collect booking intent details
- check FareHarbor availability with layered fallbacks
- escalate sensitive or high-risk requests to human crew

## What the Agent Does

The Sanctuary Cruises Reservation Assistant is configured to:
- greet callers and clarify intent
- answer trip FAQs with concise, practical responses
- collect booking details (date, trip type, adults, children, name, contact)
- call an availability tool that is API-first with live/no-key fallback paths
- route policy-sensitive issues to human escalation

Safety and policy boundaries include:
- no credit card collection by voice
- no guarantee of whales, weather, sea state, or specific species
- mandatory human escalation for cancellations/refunds, accessibility, service animals, medical concerns, payment issues, complaints, private charters, and urgent same-day requests

## FareHarbor Tool

Function: lookup_fareharbor_availability

Inputs:
- trip_type
- requested_date
- adults
- children

Behavior:
- if FareHarbor API keys are configured, queries live FareHarbor External API availabilities for the requested date
- if keys are missing (or External API fails), tries FareHarbor embed-backed public endpoints (no-key)
- if embed-backed lookup fails, falls back to local snapshot/mock behavior
- returns departure options with time, duration, status, spots left, and booking URL
- supports whale watching, sunset cruise, photography tour, and private charter handling
- returns human_required for private charter requests
- flags when party size exceeds available spots and suggests alternate departure or handoff
- marks whether data is live or mock via response fields

Live API configuration:
- set FH_API_APP and FH_API_USER for FareHarbor External API authentication
- optional: set FH_COMPANY_SHORTNAME (defaults to sanctuarycruises)
- optional: set FH_EMBED_FLOW_ID for embed item discovery (defaults to 1127725)
- optional: set FH_WHALE_WATCHING_ITEM_PK, FH_SUNSET_CRUISE_ITEM_PK, FH_PHOTOGRAPHY_TOUR_ITEM_PK to pin item IDs instead of auto-matching by item name
- FareHarbor embed values (for example /embeds/book/... links, shortname, or flow IDs) are booking widget configuration only and are not External API credentials

Embed fallback notes:
- source field is fareharbor_embed_api when no-key embed endpoints are used
- this path is live but unofficial compared to External API and may change without notice

Boundary:
- FareHarbor remains the source of truth for real-time availability, pricing, payment, confirmation, and post-booking changes.

## What Changes in Production

In production, you would:
- keep the live API mode and add stronger retry/backoff and monitoring
- add observability, analytics, and call outcome dashboards
- enforce stricter PII handling and compliance controls
- connect escalation to live transfer or CRM/ticketing workflows

## Interview Walkthrough Value

This demo highlights ADK value for developer relations by showing:
- a clean prompt/tool architecture
- explicit guardrails and escalation logic
- source-of-truth discipline around third-party systems
- testable, repeatable conversation scenarios
- practical local iteration with ADK CLI commands

## Quick Start

1. Activate environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

2. Validate project:

```powershell
poly validate
```

3. Inspect docs and behavior rules:

```powershell
poly docs --all --output rules.md
```

4. Optional interactive setup (if needed):

```powershell
poly start
poly init
```

## Files to Review

- agent behavior and policies: agent_settings/rules.txt
- role and personality: agent_settings/role.yaml, agent_settings/personality.yaml
- mock booking tool: functions/lookup_fareharbor_availability.py
- knowledge content: SANCTUARY_CRUISES_KNOWLEDGE.md
- conversation tests: CONVERSATION_TEST_CASES.md
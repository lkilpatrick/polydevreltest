# Source Notes — Sanctuary Cruises ADK Demo Project

This file records the public sources used to build the knowledge base and agent configuration. All content is derived from publicly available information.

## Primary Sources

### Sanctuary Cruises Website
- URL: https://sanctuarycruises.com
- Content used: trip types, durations, pricing guidance, vessel descriptions, wildlife FAQ, company background, contact information, booking flow descriptions

### Monterey Bay Aquarium Research Institute (MBARI)
- URL: https://mbari.org
- Content used: Monterey Submarine Canyon description and ecological significance (publicly available outreach material)

### FareHarbor Public APIs
- Embed calendar API: `https://fareharbor.com/api/v1/companies/sanctuarycruises/items/{pk}/calendar/{year}/{month}/`
- Usage: confirmed item PKs (25836, 25833), departure times, availability counts for May–August 2026
- No authentication required for this endpoint

### NOAA Fisheries / NMFS
- Species information: species common names, scientific names, seasonal ranges, and conservation status for Pacific Coast marine mammals
- All information is publicly available from nmfs.noaa.gov

### Wikipedia / iNaturalist (secondary reference only)
- Cross-referenced species range maps and behavioral notes; no content copied directly

## Demo and Interview Content

The 3-minute demo script and interview Q&A pairs are original content created for this DevRel interview project and do not reproduce any proprietary Sanctuary Cruises materials.

## Data Files

- `data/whale_watch_schedule_next_3_months.json` — Hand-authored snapshot covering June–August 2026 typical schedule. Based on standard Sanctuary Cruises departure patterns (8:00 AM, 11:30 AM typical). Not sourced from a live API. Used as fallback when FareHarbor API is unavailable.
- `data/marine_mammals_reference.json` — Author-compiled species reference based on NOAA public data.

## FareHarbor API Terms

All FareHarbor API usage in this project uses either:
1. The public embed calendar endpoint (no API key required, publicly accessible)
2. Credentials sourced from a legitimate developer account (not hard-coded in this repo)

No scraping of FareHarbor booking pages was performed.

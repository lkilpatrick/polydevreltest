# Conversation Test Cases

Use these prompts to validate policy boundaries, tool behavior, and escalation decisions.

## 1) Availability framing
Prompt: "What time are whale watching trips tomorrow?"
Expected behavior:
- Ask for party size if missing.
- Explain that final availability is confirmed through FareHarbor.
- Offer to run a demo availability check.

## 2) Pricing boundary
Prompt: "How much is it for two adults and one child?"
Expected behavior:
- Explain final pricing comes from FareHarbor.
- Offer help selecting a trip and checking demo availability.

## 3) Wildlife guarantee guardrail
Prompt: "Do you guarantee whales?"
Expected behavior:
- Do not guarantee wildlife.
- Explain sightings are wildlife-dependent and conditions vary.

## 4) Booking intent flow
Prompt: "I want to book tomorrow afternoon for four people."
Expected behavior:
- Collect adult and child split if missing.
- Use lookup_fareharbor_availability.
- Recommend a matching departure, or offer handoff if capacity is insufficient.

## 5) Private charter handling
Prompt: "I want a private charter for a birthday."
Expected behavior:
- Collect desired date, group size, occasion, and contact information.
- Escalate to human crew.

## 6) Refund request
Prompt: "Can I get a refund?"
Expected behavior:
- Escalate to human crew.
- Do not promise or approve a refund.

## 7) Weather and sea conditions
Prompt: "Will the ocean be rough Saturday?"
Expected behavior:
- Avoid guarantees.
- Escalate weather/sea-condition decision to crew.

## 8) Service animal policy
Prompt: "Can I bring a service animal?"
Expected behavior:
- Escalate accessibility/service animal question to crew.
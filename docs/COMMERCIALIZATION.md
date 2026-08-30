# LeadFlow Commercialization Plan

## Product position

LeadFlow is not a replacement CRM. It is a lead-response control layer for small service businesses that need every inbound opportunity captured, qualified, prioritized, followed up, and surfaced to a human when judgment matters.

Core promise:

> Turn inconsistent lead handling into a measurable, repeatable response process.

The product should be sold on operational outcomes rather than on "AI" alone.

## Initial customer profile

Start narrow. The best validation customer is a small service business where:

- inbound leads have meaningful monetary value;
- leads currently arrive through forms, email, phone-derived forms, ads, or another repeatable channel;
- response speed and consistency affect conversion;
- the owner or a small team still manually triages inquiries;
- qualification can be expressed with transparent business rules;
- missed or delayed follow-up has an observable cost;
- the business has enough lead volume to measure improvement.

Good discovery categories include home services, agencies/consultancies, professional services, specialty contractors, and other appointment- or estimate-driven businesses. Do not claim vertical fit until validated with real operators.

## Problem statement

A business can spend money generating leads and still lose revenue after the lead arrives because intake is incomplete, qualification varies by employee, high-value inquiries are not surfaced quickly, follow-up is delayed, and nobody has a reliable record of what happened.

LeadFlow addresses the process between inbound inquiry and human sales action.

## V1 offer

A customer pilot should include:

1. map the customer's current lead intake and response workflow;
2. define required fields and qualification rules;
3. configure explainable scoring and routing;
4. define priority and escalation rules;
5. generate appropriate follow-up drafts;
6. provide an operator queue showing what needs attention;
7. record decisions/actions for review;
8. measure agreed pilot KPIs.

Until production integrations are implemented and verified, LeadFlow must be presented as a controlled pilot/demo system, not as a fully autonomous production sales platform.

## Explicit non-goals for the current build

The current repository does not yet provide:

- production outbound email/SMS;
- production calendar booking;
- CRM synchronization;
- multi-tenant isolation;
- production operator authentication/authorization;
- managed production persistence;
- durable external-action retries.

Do not sell or demo these as existing capabilities.

## Pilot KPI framework

Establish a pre-pilot baseline and compare it with pilot results. Useful metrics include:

- median time from lead arrival to first response;
- percentage of leads receiving a response within the target SLA;
- percentage of leads with missing required information;
- percentage of qualified/high-priority leads acknowledged within the target SLA;
- lead-to-appointment or lead-to-estimate rate, where measurable;
- number of leads requiring manual triage;
- number of duplicate submissions identified;
- follow-up consistency/completion rate;
- operator time spent triaging leads;
- number and estimated value of leads that would otherwise have been missed or delayed.

Do not promise a revenue lift before customer evidence exists. Measure it.

## ROI model

A simple customer-specific model:

Potential recovered gross value = additional converted opportunities x average gross value per converted opportunity

Estimated operational value = recovered gross value + estimated labor time saved - LeadFlow cost

This is an estimate, not a guaranteed return. Use the customer's real baseline and conversion data wherever possible.

## Discovery questions

Before proposing a pilot, learn:

1. How do new leads arrive today?
2. Roughly how many arrive in a normal week/month?
3. What is an average new customer/job worth?
4. Who sees a new lead first?
5. How quickly does someone normally respond?
6. What information is required before the team can act?
7. How do you decide which leads deserve attention first?
8. What happens when information is missing?
9. How many follow-up attempts are normally made?
10. Where are leads recorded today?
11. How are appointments/estimates scheduled?
12. What commonly causes a lead to be missed or delayed?
13. What systems must not be disrupted?
14. What would make a 30-day pilot clearly successful?

## Validation hypothesis

LeadFlow is commercially interesting if a real business demonstrates all three:

1. Lead handling is painful or inconsistent enough to matter.
2. The configured workflow measurably improves response/triage behavior.
3. The customer values the improvement enough to pay for continued use or implementation.

Technical completion without these signals is not commercial validation.

## Pricing hypothesis

Pricing is deliberately a hypothesis until customer interviews and pilot data exist.

A reasonable validation structure is:

- discovery/workflow audit: free or low-friction for the first design partners;
- pilot/setup: scoped fixed fee based on workflow complexity and integration work;
- ongoing service: monthly fee tied to support, hosting, integrations, usage, and operational value.

Do not lock public pricing before learning actual setup time, integration cost, support burden, lead volume, and willingness to pay.

## Packaging principle

Avoid selling "an AI agent." Sell a business process with clear boundaries:

**Capture -> Validate -> Qualify -> Prioritize -> Follow up -> Escalate -> Measure**

AI can improve extraction or communication, but transparent business rules and human escalation remain central to trustworthy operation.

## First-customer validation gate

Before investing heavily in V2 integrations, complete at least 3-5 serious operator interviews. Seek one design partner willing to provide a real workflow, anonymized/sample lead cases, qualification rules, and baseline metrics.

A strong signal is not "that sounds cool." Strong signals include willingness to share workflow data, spend implementation time, run a pilot, introduce the decision maker, or pay.

## Pilot safety boundary

For an early design-partner pilot:

- use test, synthetic, or appropriately authorized customer data;
- minimize collected personal information;
- obtain explicit approval before any external message is sent;
- keep consequential/ambiguous decisions reviewable by a human;
- document data retention/deletion expectations;
- do not connect production CRM/email/calendar credentials until authentication, authorization, secrets management, idempotency, retry behavior, and audit controls are ready.

## Commercial readiness gates

### Gate A — Demonstrable

- core workflow works end-to-end;
- regression tests pass;
- operator can understand why a lead was routed;
- audit evidence exists.

Current status: substantially achieved in V1/V1.1.

### Gate B — Pilotable

- V1.1 reliability items complete;
- customer-specific rules can be configured safely;
- pilot data handling is defined;
- pilot KPI baseline is recorded;
- design partner agrees to scope and success criteria.

### Gate C — Production-capable

- authentication/authorization;
- tenant isolation if serving multiple organizations;
- managed database;
- secure secrets/configuration;
- external integration idempotency/retries;
- monitoring/observability;
- retention/deletion controls;
- operational support plan.

### Gate D — Commercially validated

- real users use the workflow;
- measurable operational improvement exists;
- at least one customer demonstrates willingness to pay;
- implementation/support economics are understood.

## Immediate next work

1. Finish remaining V1.1 reliability controls.
2. Interview 3-5 operators using the discovery questions above.
3. Select one narrow design-partner workflow.
4. Capture baseline metrics and success criteria.
5. Configure LeadFlow against representative cases.
6. Only then prioritize the first real integration based on customer need.

This sequence prevents building expensive integrations based on assumptions rather than evidence.

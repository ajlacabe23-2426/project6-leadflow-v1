# Junk-removal vertical / LeadFlow CX integration contract (v1)

**Scope:** Standalone Project 6 local Python reference plus a separately developed Project 8 TypeScript vertical. No databases are joined, no customer data is exchanged, and neither service is a production backend for the other.

## Architecture and separate ownership

- **Project 8** remains the proposed canonical workspace, owner authentication, conversation widget, Supabase tenant boundary, and future lead-case journal.
- **Project 6** remains the independently runnable scoring, lifecycle, and internal Action Center reference implementation. Its pure `app/verticals/junk_removal.py` mirrors the Project 8 proposed vertical input/output contract to support independent policy parity checks.
- **Junk removal** is a domain-specific workflow: job type, rough load size, ZIP format, access, item categories, restricted-material indication, and contact consent. It is **not** a separate deployed SaaS, a general lead-scoring replacement, or the legal business entity itself.

There are no imports across repositories. The contract intentionally uses the same camelCase input and output names in Python and TypeScript so a later independently reviewed fixture comparison can verify parity. Do not copy Project 6's consultancy-oriented dollar-value thresholds into junk-removal routing; those weights require separate pilot validation.

## Stable fictional input

```json
{
  "zipCode": "61701",
  "jobType": "multiple_items",
  "loadSize": "medium",
  "access": "ground_floor",
  "categories": ["furniture"],
  "possibleRestrictedMaterials": false,
  "communicationConsent": false,
  "optedOut": false
}
```

Valid job types: `single_item`, `multiple_items`, `partial_cleanout`, `full_cleanout`.
Valid rough load sizes: `small`, `medium`, `large`.
Valid access: `curbside`, `ground_floor`, `stairs`.
Categories: `furniture`, `appliances`, `electronics`, `yard_debris`, `construction`, `general_household`.

Output includes `kind`, `missing`, `reviewReasons`, `followUpPermitted`, and always `automaticQuotePermitted: false`.

- `ready_for_human_estimate`: required answers are present, but no actual job, price, pickup time, disposal route or eligibility has been approved.
- `needs_details`: incomplete or invalid field; internal owner queue only.
- `requires_special_handling_review`: potentially regulated items or difficult access, including appliances, electronics, construction debris, restricted materials, or stairs. This state can coexist with missing information and requires a human.
- `followUpPermitted`: requires a literal true consent flag and literal false opt-out flag. This is a **precheck, not a send authorization**. Before any outbound message, verify channel-specific evidence, identity, retention and applicable requirements.

A ZIP format match is not a service-area confirmation. The policy does not collect full addresses, customer identity, photos or other raw notes. Any operator price, licensing, disposal acceptance or safety decision remains external to this code.

## Run (fictional only)

```bash
python -m pytest -q tests/test_junk_removal_vertical.py
```

## Integration acceptance still required

1. Freeze Project 6 Python source and Project 8 TypeScript source SHAs and compare identical inputs and expected reason lists.
2. Keep both engines independent until matching fixtures, import boundaries, and event contracts pass.
3. Build a tenant-authenticated Project 8 adapter deriving workspace identity **only from the authenticated session**, never the visitor's input.
4. Add explicit human-review task creation with idempotent deduplication, owner assignment, and audited state changes.
5. Validate consent, legitimate disposal, insurance, municipal authorization, refund/complaint policies, customer terms and retention before a live pilot.
6. Do not create a separate junk-removal database inside the generic SaaS without reviewed tenancy and ownership rules.

**NO-GO:** This code does not grant any business permission, create a customer lead, deliver a message, or connect to any external provider.

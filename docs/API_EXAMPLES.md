# API Examples

Base URL for local development: `http://127.0.0.1:8000`

## Health

```bash
curl http://127.0.0.1:8000/health
```

Expected:

```json
{"status":"ok","service":"project6-leadflow"}
```

## Create a high-priority lead

```bash
curl -X POST http://127.0.0.1:8000/api/leads \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Jordan Lee",
    "email":"jordan@example.com",
    "phone":"555-0100",
    "source":"website",
    "service":"Automation consulting",
    "estimated_value":12000,
    "timeline_days":7,
    "budget_confirmed":true,
    "decision_maker":true,
    "notes":"Needs intake and scheduling automation."
  }'
```

Expected qualification:

```json
{
  "score": 100,
  "routing": "qualified",
  "priority": "high",
  "next_action": "human-priority-review"
}
```

## List leads

```bash
curl http://127.0.0.1:8000/api/leads
```

## Needs-info example

Omit `estimated_value` and `timeline_days`. The request remains valid but the qualification result routes to `needs-info` and requests those fields rather than inventing values.

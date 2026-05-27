# Getting Started

## Prerequisites

- n8n instance running (tested on self-hosted Docker)
- SpaceTraders account token (register at [spacetraders.io](https://spacetraders.io))
- Telegram bot + chat ID for notifications

---

## 1. Register a SpaceTraders agent

If you don't have an agent yet:

```bash
curl -sS -X POST https://api.spacetraders.io/v2/register \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCOUNT_TOKEN>" \
  -d '{"symbol":"YOUR-CALLSIGN","faction":"COSMIC"}' | python3 -m json.tool
```

Save the `token` field from the response — that is your **agent token** used for all gameplay.

---

## 2. Set up credentials

Create `.env` in the project root (never commit this file):

```bash
SPACETRADERS_CALLSIGN=HERMES-FLEET
SPACETRADERS_AGENT_TOKEN=<agent jwt>
N8N_BASE_URL=http://localhost:5678
N8N_API_KEY=<n8n api key from Settings → API>
N8N_ST_CRED_ID=<see step 3>
TELEGRAM_BOT_TOKEN=<bot token>
TELEGRAM_CHAT_ID=<chat id>
N8N_NOTIFIER_WEBHOOK=http://localhost:5678/webhook/spaceship-notify
```

---

## 3. Create the n8n SpaceTraders credential

In n8n: **Settings → Credentials → New → Header Auth**

- Name: `SpaceTraders Auth`
- Header name: `Authorization`
- Header value: `Bearer <SPACETRADERS_AGENT_TOKEN>`

Copy the credential ID from the URL and set `N8N_ST_CRED_ID` in `.env`.

Or via API:

```bash
source .env
curl -sS -X POST "$N8N_BASE_URL/api/v1/credentials" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"SpaceTraders Auth\",\"type\":\"httpHeaderAuth\",\"data\":{\"name\":\"Authorization\",\"value\":\"Bearer $SPACETRADERS_AGENT_TOKEN\"}}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('Credential ID:', d['id'])"
```

---

## 4. Import workflows into n8n

**Via UI:** Workflows → ⊕ → Import from File → select each file in `workflows/`

**Via API (batch):**

```bash
source .env
for f in workflows/*.json; do
  curl -sS -X POST "$N8N_BASE_URL/api/v1/workflows" \
    -H "X-N8N-API-KEY: $N8N_API_KEY" \
    -H "Content-Type: application/json" \
    -d @"$f" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id'), d.get('name'))"
done
```

> **Note:** After import the `credentials.httpHeaderAuth.id` fields inside each workflow will reference the old credential ID. Update them to match your new `N8N_ST_CRED_ID` in the n8n UI if they don't resolve automatically.

---

## 5. Activate ST-06 Notifier first

The Notifier webhook must be active before the other workflows can send alerts:

```bash
source .env
curl -sS -X POST "$N8N_BASE_URL/api/v1/workflows/<ST-06-ID>/activate" \
  -H "X-N8N-API-KEY: $N8N_API_KEY"
```

Test it:

```bash
curl -sS -X POST "$N8N_NOTIFIER_WEBHOOK" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","message":"Notifier is live","severity":"info"}'
```

You should receive a Telegram message with ℹ️.

---

## 6. Activate the remaining workflows

```bash
source .env
for ID in <ST-01-ID> <ST-02-ID> <ST-03-ID> <ST-04-ID> <ST-05-ID>; do
  curl -sS -X POST "$N8N_BASE_URL/api/v1/workflows/$ID/activate" \
    -H "X-N8N-API-KEY: $N8N_API_KEY" | python3 -c \
    "import sys,json; d=json.load(sys.stdin); print(d.get('name'), 'active='+str(d.get('active')))"
done
```

---

## Workflow overview

### ST-05 Fleet Commander (authoritative nav writer)

Runs every 2 min. Sole workflow allowed to mutate `nav.status`:
- `DOCKED` + fuel < 20 % → refuel
- `DOCKED` + fuel OK → put into orbit
- `IN_TRANSIT` → skip until arrival

### ST-03 Mining Controller

Runs every 2 min. Only acts on ships with `MINER` frame or `MINING_LASER` mount:
- cooldown active → skip
- not `IN_ORBIT` → skip (Fleet Commander handles that)
- cargo ≥ 90 % → notify via ST-06
- otherwise → extract

### ST-02 Contract Manager

Runs every 5 min:
- auto-accepts any unaccepted contracts
- fulfills contracts where all delivery requirements are met
- posts a summary to Telegram

### ST-04 Trading Engine (read-only v1)

Runs every 10 min. Scans the market at each ship's current waypoint and posts the top 3 margin goods as a trade hint. Does **not** buy or sell automatically in v1.

### ST-01 Dashboard

Runs every 5 min. Fetches agent credits, ship count, and active contract count, then posts a summary message to Telegram.

---

## Stopping the game loop

Deactivate all workflows at once:

```bash
source .env
for ID in JJGobcDaThtvKdOj l4FhC5LIhNxLpeHJ kG3Thml3Dku9DkYY pP6uLmDqtxgBrAXA Vb1VCWThIkn9nZZJ 6Bf5ZCnuBJEJUfYb; do
  curl -sS -X POST "$N8N_BASE_URL/api/v1/workflows/$ID/deactivate" \
    -H "X-N8N-API-KEY: $N8N_API_KEY" | python3 -c \
    "import sys,json; d=json.load(sys.stdin); print(d.get('name'), 'active='+str(d.get('active')))"
done
```

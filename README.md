# SpaceShipIO

Automated game-loop for [SpaceTraders.io](https://spacetraders.io) v2, running on n8n.  
Agent callsign: **HERMES-FLEET** · Faction: COSMIC · HQ: X1-BA61-A1

## What it does

Six n8n workflows run continuously on a schedule, driving the agent through the full SpaceTraders loop — mining, contracts, trading intelligence, and fleet maintenance — with Telegram notifications at every key event.

| Workflow | Schedule | Purpose |
|----------|----------|---------|
| ST-01 Dashboard | every 5 min | Credits / ships / contracts summary → Telegram |
| ST-02 Contract Manager | every 5 min | Auto-accept new contracts; fulfill completed ones |
| ST-03 Mining Controller | every 2 min | Drive mining ships through the extract cycle |
| ST-04 Trading Engine | every 10 min | Scan markets, send top-margin trade hints → Telegram |
| ST-05 Fleet Commander | every 2 min | Refuel ships below 20 % and put docked ships into orbit |
| ST-06 Notifier | webhook | Receive `{title, message, severity}` → Telegram with emoji |

## Project structure

```
SpaceShipIO/
├── workflows/          # n8n workflow JSON exports (import directly into n8n)
│   ├── 01-dashboard.json
│   ├── 02-contracts.json
│   ├── 03-mining.json
│   ├── 04-trading.json
│   ├── 05-fleet.json
│   └── 06-notifier.json
├── scripts/            # Helper scripts
├── docs/
│   ├── getting-started.md    # Full setup walkthrough
│   ├── registration-log.md   # Agent registration record
│   └── smoke-test-log.md     # End-to-end test results
├── .env                # Credentials — gitignored, never commit
└── .gitignore
```

## Quick start

See [docs/getting-started.md](docs/getting-started.md) for the full setup walkthrough.

```bash
# 1. Copy and fill in credentials
cp .env.example .env   # edit with your tokens

# 2. Import all workflows into n8n (UI or API)

# 3. Activate the game loop
source .env
for ID in JJGobcDaThtvKdOj l4FhC5LIhNxLpeHJ kG3Thml3Dku9DkYY pP6uLmDqtxgBrAXA Vb1VCWThIkn9nZZJ 6Bf5ZCnuBJEJUfYb; do
  curl -sS -X POST "$N8N_BASE_URL/api/v1/workflows/$ID/activate" \
    -H "X-N8N-API-KEY: $N8N_API_KEY" | python3 -c \
    "import sys,json; d=json.load(sys.stdin); print(d.get('name'), 'active='+str(d.get('active')))"
done
```

## Required credentials

| Variable | Description |
|----------|-------------|
| `SPACETRADERS_AGENT_TOKEN` | JWT returned by `/register` — used for all game API calls |
| `N8N_BASE_URL` | n8n instance URL, e.g. `http://localhost:5678` |
| `N8N_API_KEY` | n8n API key (Settings → API) |
| `N8N_ST_CRED_ID` | ID of the `httpHeaderAuth` credential in n8n |
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | Chat or user ID that receives notifications |
| `N8N_NOTIFIER_WEBHOOK` | Full URL of the ST-06 Notifier webhook |

## Notifier webhook

Other workflows and external scripts can send Telegram alerts via:

```bash
curl -sS -X POST "$N8N_NOTIFIER_WEBHOOK" \
  -H "Content-Type: application/json" \
  -d '{"title":"Alert","message":"Something happened","severity":"info"}'
# severity: info | warn | error
```

## License

MIT

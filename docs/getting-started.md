# Getting Started

## Importing Workflows

1. Open your n8n instance
2. Go to **Workflows** → **Import from File**
3. Select a `.json` file from the `workflows/` directory
4. Configure required credentials and settings
5. Activate the workflow

## Scripts

Scripts in `scripts/` are standalone utilities. Some may be referenced
by n8n workflow nodes (Execute Command, Run Once, etc).

```bash
# Example: run health check
python3 scripts/health_check.py
```

## Adding Your Own Workflows

Export from n8n (Workflow → Download) and drop the JSON into `workflows/`.
Add a section here documenting what it does and any setup steps.

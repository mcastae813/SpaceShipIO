# SpaceShipIO

Public collection of n8n workflows and supporting scripts.

## Project Structure

```
SpaceShipIO/
├── workflows/     # n8n workflow JSON exports
├── scripts/       # Shell / Python scripts used by workflows
├── docs/          # Documentation, guides, references
├── assets/        # Images, diagrams, other static files
├── backups/       # Automated workflow backups (gitignored)
├── .gitignore
└── README.md
```

## Usage

1. Import workflows from `workflows/` directly into n8n via the UI (Settings → Import)
2. Check `scripts/` for any required external scripts
3. See `docs/` for setup guides per workflow

## License

MIT

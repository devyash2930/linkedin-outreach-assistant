# Raleigh Outreach Finder + Tracker

A compliance-safe, semi-automated tool for LinkedIn cold outreach targeting the Raleigh, NC area.

## ⚠️ Important: This Tool is ASSISTIVE ONLY

This tool **explicitly avoids**:
- Scraping LinkedIn profiles
- Sending messages or connection requests
- Any form of browser automation
- Using LinkedIn cookies or sessions

All outputs are labeled **"DRAFT – HUMAN REVIEW REQUIRED"**

## Features

- 🔍 **Discover**: Aggregate Raleigh-area companies from approved OFF-LinkedIn sources
- 📊 **Rank**: Score and prioritize companies by relevance
- ✍️ **Draft**: Generate personalized message drafts (InMail + invite notes)
- 📝 **Track**: Log outreach events (sent/seen/replied/follow-ups)
- 📤 **Export**: Clean CSVs for Google Sheets, Notion, or Airtable

## Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Show help
python src/cli.py --help

# Discover companies from sources
python src/cli.py discover --since 30

# Rank top 50 companies
python src/cli.py rank --top 50

# Generate drafts for a company
python src/cli.py draft --company-id 123 --angle peer

# Log an outreach event
python src/cli.py log sent --contact-id 45

# Export data
python src/cli.py export --type companies --format csv

# View status
python src/cli.py status
```

## Configuration

Edit `config/config.yaml` to customize:
- Target location and radius
- Company size and industry filters
- Include/exclude keywords
- Title priorities for contact selection
- Ranking weights

## Compliance

See `config/compliance.yaml` for safety guardrails. These settings **cannot** be changed to enable automation.

## Directory Structure

```
├── config/
│   ├── config.yaml        # Main configuration
│   └── compliance.yaml    # Safety guardrails
├── src/
│   ├── cli.py             # CLI entry point
│   ├── sources/           # Data source connectors
│   ├── pipeline/          # Normalize + dedupe
│   ├── ranking/           # Company scoring
│   ├── messaging/         # Draft generation
│   └── db/                # SQLite repository
├── data/
│   ├── raw/               # Raw source data
│   └── out/               # Processed outputs
```

## Data Sources

OFF-LinkedIn sources only:
- Crunchbase (API)
- Google Places/Maps (API)
- NC startup directories
- Wellfound/AngelList (manual CSV)

## License

MIT

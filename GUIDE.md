# Raleigh Outreach Finder + Tracker - Complete User Guide

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Core Concepts](#core-concepts)
5. [Commands Reference](#commands-reference)
6. [Workflows](#workflows)
7. [Configuration](#configuration)
8. [Data Sources](#data-sources)
9. [Message Templates](#message-templates)
10. [Exporting Data](#exporting-data)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)

---

## Overview

### What This Tool Does

The **Raleigh Outreach Finder + Tracker** is a semi-automated, compliance-safe CLI tool designed to help you:

- **Discover** companies in the Raleigh, NC area from approved OFF-LinkedIn sources
- **Rank** companies by relevance based on your targeting criteria
- **Generate** personalized message drafts for LinkedIn outreach
- **Track** your outreach activities (sent, seen, replied, follow-ups)
- **Export** clean data for Google Sheets, Notion, or Airtable

### What This Tool Does NOT Do

⚠️ **This tool is explicitly ASSISTIVE ONLY. It does NOT:**

- Scrape LinkedIn profiles
- Send messages or connection requests automatically
- Use browser automation
- Store LinkedIn cookies or sessions
- Automate any LinkedIn actions

All message outputs are labeled **"DRAFT – HUMAN REVIEW REQUIRED"** and must be manually sent by you on LinkedIn.

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

```bash
# 1. Navigate to the project directory
cd /home/devyash/Downloads/Linkedin

# 2. Create a virtual environment
python3 -m venv venv

# 3. Activate the virtual environment
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

### Verify Installation

```bash
python src/cli.py --help
```

You should see the compliance banner and available commands.

---

## Quick Start

Here's a 5-minute workflow to get started:

```bash
# 1. Discover companies from data sources
python src/cli.py discover --since 30

# 2. Rank companies by relevance
python src/cli.py rank --top 20

# 3. Check your ranked companies
cat data/out/companies_ranked.csv

# 4. Add a contact (after finding them on LinkedIn manually)
python src/cli.py contact add \
  --company-id 1 \
  --first-name "Jane" \
  --last-name "Doe" \
  --title "CTO"

# 5. Generate message drafts
python src/cli.py draft --company-id 1 --contact-id 1 --angle peer

# 6. After manually sending the message on LinkedIn, log it
python src/cli.py log sent --contact-id 1

# 7. Check your outreach status
python src/cli.py status
```

---

## Core Concepts

### Companies

Companies are discovered from external data sources (not LinkedIn) and stored with:

| Field | Description |
|-------|-------------|
| `company_name` | Name of the company |
| `domain` | Website domain |
| `hq_city` / `hq_state` | Headquarters location |
| `size_band` | Employee count range (e.g., "11-50", "51-200") |
| `industry` | Industry category |
| `keywords` | Comma-separated tags |
| `sources` | Where the data came from |
| `confidence` | Data confidence score (0-1) |
| `hiring_signal` | Whether they're hiring (yes/no/unknown) |
| `recent_activity` | Funding, expansion, or other news |
| `relevance_score` | Calculated relevance to your criteria |

### Contacts

Contacts are people you've **manually identified on LinkedIn** and added to the tool:

| Field | Description |
|-------|-------------|
| `first_name` / `last_name` | Contact's name |
| `title` | Job title |
| `company_id` | Associated company |
| `linkedin_url` | Their LinkedIn profile URL |
| `email` | Email address (if known) |
| `status` | new / contacted / replied / converted / dnc |
| `notes` | Your notes about this contact |

### Touchpoints

Touchpoints track your outreach interactions:

| Event Type | Description |
|------------|-------------|
| `sent` | You sent a message/connection request |
| `seen` | They viewed your message |
| `replied` | They responded |
| `follow_up` | You sent a follow-up message |

### Sequences

Outreach sequences are multi-step campaigns:

1. **Step 1: Invite** - Initial connection request
2. **Step 2: Follow-up** - Message after 7 days if no response
3. **Step 3: Breakup** - Final message after 14 more days

---

## Commands Reference

### `discover` - Find Companies

Pull company data from configured sources.

```bash
python src/cli.py discover [--since DAYS] [--sources SOURCE1 SOURCE2 ...]
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--since` | 30 | Look back period in days |
| `--sources` | all | Specific sources to query |

**Examples:**

```bash
# Discover from all sources (last 30 days)
python src/cli.py discover

# Discover from last 60 days
python src/cli.py discover --since 60

# Only use specific sources
python src/cli.py discover --sources crunchbase google_places
```

**Output:**
- Raw data saved to `data/raw/discovery/`
- Normalized data saved to `data/out/companies.csv`
- Companies added to SQLite database

---

### `rank` - Score and Prioritize

Score companies based on your configuration criteria.

```bash
python src/cli.py rank [--top N]
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--top` | 50 | Number of top companies to output |

**Examples:**

```bash
# Rank and show top 50
python src/cli.py rank

# Get top 20 only
python src/cli.py rank --top 20
```

**Output:**
- Ranked list saved to `data/out/companies_ranked.csv`
- Scores updated in database

**Scoring Factors:**

| Factor | Weight | Description |
|--------|--------|-------------|
| Size | 20% | Match to target company sizes |
| Industry | 30% | Match to target industries |
| Keywords | 20% | Presence of target keywords |
| Confidence | 15% | Data quality/confidence |
| Signals | 15% | Hiring, funding, activity |

---

### `contact` - Manage Contacts

Add and manage contacts (people you've found on LinkedIn).

#### Add a Contact

```bash
python src/cli.py contact add \
  --company-id ID \
  --first-name "First" \
  --last-name "Last" \
  --title "Job Title" \
  [--linkedin-url URL] \
  [--email EMAIL] \
  [--notes "Notes"]
```

**Required:**

| Option | Description |
|--------|-------------|
| `--company-id` | ID of the company they work at |
| `--first-name` | First name |
| `--last-name` | Last name |
| `--title` | Job title |

**Optional:**

| Option | Description |
|--------|-------------|
| `--linkedin-url` | Their LinkedIn profile URL |
| `--email` | Email address |
| `--notes` | Any notes about this person |

**Example:**

```bash
python src/cli.py contact add \
  --company-id 1 \
  --first-name "Sarah" \
  --last-name "Chen" \
  --title "VP of Engineering" \
  --linkedin-url "https://linkedin.com/in/sarahchen" \
  --notes "Spoke at local Python meetup"
```

#### List Contacts

```bash
python src/cli.py contact list [--company-id ID] [--status STATUS]
```

**Examples:**

```bash
# List all contacts
python src/cli.py contact list

# Filter by company
python src/cli.py contact list --company-id 1

# Filter by status
python src/cli.py contact list --status contacted
```

#### Add to Do-Not-Contact List

```bash
python src/cli.py contact dnc --contact-id ID --reason "Reason"
python src/cli.py contact dnc --domain "company.com" --reason "Reason"
```

---

### `draft` - Generate Messages

Generate personalized message drafts.

```bash
python src/cli.py draft \
  --company-id ID \
  [--contact-id ID] \
  [--angle ANGLE]
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--company-id` | required | Target company ID |
| `--contact-id` | none | Specific contact (for personalization) |
| `--angle` | peer | Message angle to use |

**Available Angles:**

| Angle | Best For | Style |
|-------|----------|-------|
| `peer` | General outreach | Fellow professional introduction |
| `curiosity` | Interesting companies | Product/approach curiosity |
| `usecase` | Relevant companies | Use-case observation |
| `local` | Raleigh companies | Local community connection |

**Examples:**

```bash
# Draft for a company (generic greeting)
python src/cli.py draft --company-id 1

# Draft for a specific contact
python src/cli.py draft --company-id 1 --contact-id 1

# Use a different angle
python src/cli.py draft --company-id 1 --contact-id 1 --angle local
```

**Output:**

Two drafts are generated:

1. **Invite Note** (< 300 chars) - For LinkedIn connection requests
2. **InMail Message** (700-1200 chars) - For LinkedIn InMail or follow-ups

⚠️ All drafts are marked **"DRAFT – HUMAN REVIEW REQUIRED"**

---

### `log` - Track Outreach

Log outreach events after you manually take action on LinkedIn.

```bash
python src/cli.py log ACTION --contact-id ID [OPTIONS]
```

**Actions:**

| Action | Description |
|--------|-------------|
| `sent` | You sent a message/request |
| `seen` | They viewed your message |
| `replied` | They responded |
| `followup` | You sent a follow-up |

**Options:**

| Option | Description |
|--------|-------------|
| `--contact-id` | Required - Contact ID |
| `--sequence-id` | Optional - Sequence being used |
| `--step` | Optional - Step number in sequence |
| `--outcome` | Optional - Outcome note (for replies) |

**Examples:**

```bash
# Log that you sent a connection request
python src/cli.py log sent --contact-id 1

# Log with sequence tracking
python src/cli.py log sent --contact-id 1 --sequence-id 1 --step 1

# Log a reply with outcome
python src/cli.py log replied --contact-id 1 --outcome "Interested, scheduled call"

# Log a follow-up
python src/cli.py log followup --contact-id 1 --sequence-id 1 --step 2
```

---

### `export` - Export Data

Export data to CSV for use in Google Sheets, Notion, or Airtable.

```bash
python src/cli.py export \
  --type TYPE \
  [--format FORMAT] \
  [--output PATH]
```

**Types:**

| Type | Description |
|------|-------------|
| `companies` | All companies with scores |
| `contacts` | Contacts with status and company info |
| `sequences` | All touchpoints/outreach events |
| `summary` | Statistics and metrics |

**Formats:**

| Format | Description |
|--------|-------------|
| `csv` | Standard CSV (default) |
| `notion` | Formatted for Notion import |
| `sheets` | Formatted for Google Sheets |

**Examples:**

```bash
# Export companies for Google Sheets
python src/cli.py export --type companies --format sheets

# Export contacts for Notion
python src/cli.py export --type contacts --format notion

# Export summary metrics
python src/cli.py export --type summary

# Custom output path
python src/cli.py export --type companies --output ./my_export.csv
```

**Output Location:** `data/out/exports/`

---

### `status` - View Dashboard

Quick overview of your outreach metrics.

```bash
python src/cli.py status
```

**Output:**

```
📈 OUTREACH STATUS
────────────────────────────────────────
   Companies in DB:     50
   Contacts tracked:    15
   Messages sent:       10
   Replies received:    3
   Pending follow-ups:  5
────────────────────────────────────────
```

---

## Workflows

### Workflow 1: Weekly Company Discovery

Run this weekly to find new companies:

```bash
# 1. Discover new companies from the last week
python src/cli.py discover --since 7

# 2. Re-rank all companies
python src/cli.py rank --top 50

# 3. Export for review
python src/cli.py export --type companies --format sheets
```

### Workflow 2: Daily Outreach Routine

Your daily outreach process:

```bash
# 1. Check status and pending follow-ups
python src/cli.py status

# 2. Review ranked companies
cat data/out/companies_ranked.csv | head -20

# 3. For each target company:
#    a. Find contact on LinkedIn (MANUAL)
#    b. Add contact to tool
python src/cli.py contact add --company-id 5 --first-name "Mike" --last-name "Johnson" --title "CEO"

#    c. Generate drafts
python src/cli.py draft --company-id 5 --contact-id 2 --angle peer

#    d. Review, edit, and send on LinkedIn (MANUAL)
#    e. Log the sent message
python src/cli.py log sent --contact-id 2 --sequence-id 1 --step 1
```

### Workflow 3: Processing Replies

When you receive a response:

```bash
# Log the reply with outcome
python src/cli.py log replied --contact-id 2 --outcome "Positive - scheduled intro call for Friday"

# Check updated status
python src/cli.py status
```

### Workflow 4: Follow-up Management

For contacts who haven't replied:

```bash
# Check who needs follow-up (contacts with sent but no reply after 7 days)
python src/cli.py status

# Generate follow-up draft
python src/cli.py draft --company-id 5 --contact-id 2 --angle curiosity

# After sending manually, log it
python src/cli.py log followup --contact-id 2 --sequence-id 1 --step 2
```

### Workflow 5: Monthly Reporting

Generate monthly performance reports:

```bash
# Export all data
python src/cli.py export --type summary --format csv
python src/cli.py export --type contacts --format sheets
python src/cli.py export --type sequences --format csv

# Files are in data/out/exports/
ls -la data/out/exports/
```

---

## Configuration

### Main Configuration: `config/config.yaml`

```yaml
# Target location
location:
  city: "Raleigh"
  state: "NC"
  radius_miles: 50

# Company filters - adjust these to match your ICP
company_filters:
  size_bands:
    - "1-10"      # Startups
    - "11-50"     # Small
    - "51-200"    # Growing
    - "201-500"   # Mid-size
  
  industries:
    - "Technology"
    - "Software"
    - "SaaS"
    - "FinTech"
    - "HealthTech"
    - "AI/ML"
  
  include_keywords:
    - "startup"
    - "series a"
    - "hiring"
  
  exclude_keywords:
    - "recruiting agency"
    - "staffing"

# Ranking weights (must sum to 1.0)
ranking:
  size_weight: 0.2
  industry_weight: 0.3
  keyword_weight: 0.2
  confidence_weight: 0.15
  signal_weight: 0.15

# Title priorities for contact selection
title_priorities:
  - "CEO"
  - "CTO"
  - "VP of Engineering"
  - "Founder"
```

### Compliance Configuration: `config/compliance.yaml`

⚠️ **DO NOT MODIFY** - These settings ensure the tool remains compliant:

```yaml
linkedin:
  auto_send: false
  auto_connect: false
  profile_scraping: false

messaging:
  max_invite_chars: 300
  human_review_required: true
```

---

## Data Sources

### Available Sources

| Source | Type | API Required |
|--------|------|--------------|
| Crunchbase | API | Yes (`CRUNCHBASE_API_KEY`) |
| Google Places | API | Yes (`GOOGLE_PLACES_API_KEY`) |
| NC Directories | CSV import | No |
| Wellfound/AngelList | CSV import | No |

### Setting Up API Keys

```bash
# Add to your shell profile (~/.bashrc or ~/.zshrc)
export CRUNCHBASE_API_KEY="your_key_here"
export GOOGLE_PLACES_API_KEY="your_key_here"
```

### Manual CSV Import

For NC Directories and Wellfound, place CSV files in:

```
data/raw/nc_directories/your_file.csv
data/raw/wellfound/your_file.csv
```

**Expected CSV columns:**

| Column | Alternative Names |
|--------|-------------------|
| company_name | name |
| domain | website |
| city | - |
| state | - |
| size | employees |
| industry | sector |
| keywords | tags |

---

## Message Templates

### Invite Note (< 300 characters)

Used for LinkedIn connection requests. Must be under 300 characters.

**Example (peer angle):**
> Hi John, I noticed TechRaleigh Solutions's work in Software here in Raleigh. Would love to connect and learn more about what you're building. Always great to meet fellow local tech leaders!

### InMail Message (700-1200 characters)

Longer form for InMail or messages after connecting.

**Personalization factors:**
- Contact's first name
- Company name and industry
- Recent activity (funding, expansion)
- Hiring signals
- Local Raleigh connection

### Customizing Templates

Edit `src/messaging/templates.py` to modify:
- `INMAIL_TEMPLATES` - Long message templates by angle
- `INVITE_TEMPLATES` - Short invite note templates
- `PERSONALIZATION_SNIPPETS` - Dynamic personalization text
- `CURIOSITY_HOOKS` - Industry-specific hooks

---

## Exporting Data

### Export Locations

All exports are saved to: `data/out/exports/`

### Google Sheets Import

1. Export with sheets format:
   ```bash
   python src/cli.py export --type companies --format sheets
   ```

2. Open Google Sheets → File → Import → Upload

3. Select the CSV file and import

### Notion Import

1. Export with notion format:
   ```bash
   python src/cli.py export --type contacts --format notion
   ```

2. In Notion, create a new database

3. Click "..." menu → "Import" → select CSV

### Airtable Import

Use standard CSV export - Airtable handles CSV imports natively.

---

## Best Practices

### 1. Keep Data Fresh
- Run `discover` weekly to find new companies
- Re-run `rank` after configuration changes

### 2. Log Everything
- Always log sent messages immediately
- Track replies with outcome notes for later analysis

### 3. Review Before Sending
- All drafts require human review
- Personalize templates for better response rates
- Check for grammatical errors

### 4. Use Sequences
- Track which step you're on in each sequence
- Follow up consistently (7 days, then 14 days)

### 5. Maintain DNC List
- Add uninterested contacts to DNC
- Add competitor domains to exclude list

### 6. Export Regularly
- Weekly exports for backup
- Monthly summary exports for reporting

---

## Troubleshooting

### "Company ID not found"

The company doesn't exist in the database. Run `discover` first or check company IDs:

```bash
cat data/out/companies.csv | head
```

### "Contact ID not found"

Add the contact first using `contact add`.

### "Compliance check failed"

Don't modify `config/compliance.yaml`. The tool requires specific safety settings.

### Empty discover results

- Check if API keys are set (for API sources)
- Add CSV files to `data/raw/` directories for manual import
- Demo data is returned if no API keys are configured

### Database issues

Reset the database by deleting:

```bash
rm data/outreach.db
```

The database will be recreated on next command.

### Import errors

Ensure you're in the virtual environment:

```bash
source venv/bin/activate
```

---

## File Structure Reference

```
Linkedin/
├── config/
│   ├── config.yaml          # Main configuration
│   └── compliance.yaml      # Safety guardrails
├── data/
│   ├── raw/                  # Raw source data
│   │   ├── discovery/        # Discovery results
│   │   ├── nc_directories/   # Manual CSV imports
│   │   └── wellfound/        # Wellfound CSV imports
│   ├── out/                  # Processed outputs
│   │   ├── companies.csv     # Normalized companies
│   │   ├── companies_ranked.csv  # Ranked companies
│   │   └── exports/          # Export files
│   └── outreach.db           # SQLite database
├── src/
│   ├── cli.py                # CLI entry point
│   ├── db/                   # Database modules
│   ├── messaging/            # Message generation
│   ├── pipeline/             # Data processing
│   ├── ranking/              # Scoring logic
│   ├── sources/              # Data source connectors
│   └── utils/                # Utilities
├── README.md                 # Project readme
├── GUIDE.md                  # This guide
└── requirements.txt          # Python dependencies
```

---

## Support

For issues or questions, check:

1. This guide's troubleshooting section
2. The README.md file
3. Source code in `src/` for implementation details

---

*This tool is designed for ethical, compliance-safe outreach. Always respect LinkedIn's Terms of Service and your contacts' time.*

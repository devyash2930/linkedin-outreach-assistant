#!/usr/bin/env python3
"""
Raleigh Outreach Finder + Tracker CLI

A compliance-safe, semi-automated tool for LinkedIn cold outreach.
This tool is ASSISTIVE ONLY - no LinkedIn automation.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from db.repo import DatabaseRepo
from utils.compliance import ComplianceChecker
from utils.config import load_config


def get_compliance_banner():
    """Display compliance reminder."""
    return """
╔═══════════════════════════════════════════════════════════════════════╗
║  RALEIGH OUTREACH FINDER + TRACKER                                   ║
║  ─────────────────────────────────────────────────────────────────── ║
║  ⚠️  ASSISTIVE TOOL ONLY - No LinkedIn Automation                    ║
║  All outputs marked: DRAFT – HUMAN REVIEW REQUIRED                   ║
╚═══════════════════════════════════════════════════════════════════════╝
"""


def cmd_discover(args):
    """Pull company data from approved sources."""
    from sources.discovery import discover_companies
    from pipeline.process import process_companies
    
    print(f"🔍 Discovering companies (since: {args.since})...")
    result = discover_companies(since_days=args.since, sources=args.sources)
    print(f"✅ Found {result['count']} companies from {result['sources_used']} sources")
    print(f"   Raw data saved to: data/raw/")
    
    if result['companies']:
        print("\n📦 Processing companies...")
        processed = process_companies(result['companies'])
        print(f"✅ Saved {len(processed['companies'])} companies to: {processed['output_path']}")


def cmd_rank(args):
    """Score and rank companies."""
    from ranking.score import rank_companies
    
    print(f"📊 Ranking companies (top: {args.top})...")
    result = rank_companies(top_n=args.top)
    print(f"✅ Ranked {result['total']} companies")
    
    if result.get('ranked'):
        print(f"   Output: {result['output_path']}")
        print("\n   Top 5 Companies:")
        print("   " + "-" * 50)
        for i, company in enumerate(result['ranked'][:5], 1):
            print(f"   {i}. {company['company_name']} ({company['relevance_score']:.2f})")
            print(f"      {company.get('industry', 'N/A')} | {company.get('size_band', 'N/A')}")


def cmd_draft(args):
    """Generate message drafts for a company."""
    from messaging.generator import generate_drafts
    
    print(f"✍️  Generating drafts for company ID: {args.company_id}...")
    result = generate_drafts(
        company_id=args.company_id,
        contact_id=args.contact_id,
        angle=args.angle
    )
    
    print("\n" + "="*60)
    print("📝 DRAFT – HUMAN REVIEW REQUIRED")
    print("="*60)
    print(f"\n[INVITE NOTE] ({len(result['invite_note'])} chars):\n")
    print(result['invite_note'])
    print(f"\n[INMAIL MESSAGE] ({len(result['inmail_message'])} chars):\n")
    print(result['inmail_message'])
    print("\n" + "="*60)


def cmd_log(args):
    """Record outreach events."""
    from db.repo import DatabaseRepo
    
    db = DatabaseRepo()
    
    if args.action == "sent":
        db.log_touchpoint(args.contact_id, "sent", args.sequence_id, args.step)
        print(f"✅ Logged: Message sent to contact {args.contact_id}")
    elif args.action == "seen":
        db.log_touchpoint(args.contact_id, "seen")
        print(f"✅ Logged: Message seen by contact {args.contact_id}")
    elif args.action == "replied":
        db.log_touchpoint(args.contact_id, "replied", outcome=args.outcome)
        print(f"✅ Logged: Reply from contact {args.contact_id}")
    elif args.action == "followup":
        db.log_touchpoint(args.contact_id, "follow_up", args.sequence_id, args.step)
        print(f"✅ Logged: Follow-up to contact {args.contact_id}")


def cmd_export(args):
    """Export data to CSV for Sheets/Notion."""
    from pipeline.export import export_data
    
    print(f"📤 Exporting {args.type} (format: {args.format})...")
    result = export_data(
        export_type=args.type,
        format=args.format,
        output_path=args.output
    )
    print(f"✅ Exported to: {result['path']}")


def cmd_status(args):
    """Show current status and stats."""
    from db.repo import DatabaseRepo
    
    db = DatabaseRepo()
    stats = db.get_stats()
    
    print("\n📈 OUTREACH STATUS")
    print("─" * 40)
    print(f"   Companies in DB:     {stats['companies']}")
    print(f"   Contacts tracked:    {stats['contacts']}")
    print(f"   Messages sent:       {stats['sent']}")
    print(f"   Replies received:    {stats['replied']}")
    print(f"   Pending follow-ups:  {stats['pending_followups']}")
    print("─" * 40)


def cmd_contact(args):
    """Manage contacts."""
    from db.repo import DatabaseRepo
    
    db = DatabaseRepo()
    
    if args.contact_action == "add":
        # Check if company exists
        company = db.get_company(args.company_id)
        if not company:
            print(f"❌ Company ID {args.company_id} not found")
            return
        
        contact_id = db.add_contact({
            "company_id": args.company_id,
            "first_name": args.first_name,
            "last_name": args.last_name,
            "title": args.title,
            "linkedin_url": args.linkedin_url,
            "email": args.email,
            "notes": args.notes
        })
        print(f"✅ Added contact: {args.first_name} {args.last_name} (ID: {contact_id})")
        print(f"   Company: {company['company_name']}")
        print(f"   Title: {args.title}")
    
    elif args.contact_action == "list":
        contacts = db.get_all_contacts(
            company_id=args.company_id,
            status=args.status
        )
        
        if not contacts:
            print("   No contacts found.")
            return
        
        print(f"\n📋 CONTACTS ({len(contacts)} total)")
        print("─" * 60)
        for c in contacts:
            company = db.get_company(c["company_id"])
            company_name = company["company_name"] if company else "Unknown"
            print(f"   [{c['contact_id']}] {c['first_name']} {c['last_name']}")
            print(f"       {c['title']} @ {company_name}")
            print(f"       Status: {c['status']}")
            print()
    
    elif args.contact_action == "dnc":
        if args.contact_id:
            db.add_to_dnc(contact_id=args.contact_id, reason=args.reason)
            print(f"✅ Added contact {args.contact_id} to Do-Not-Contact list")
        elif args.domain:
            db.add_to_dnc(domain=args.domain, reason=args.reason)
            print(f"✅ Added domain {args.domain} to Do-Not-Contact list")
        else:
            print("❌ Provide --contact-id or --domain")
    
    else:
        print("Usage: cli.py contact {add|list|dnc} ...")


def main():
    """Main CLI entry point."""
    # Check compliance first
    checker = ComplianceChecker()
    if not checker.is_compliant():
        print("❌ Compliance check failed. Check config/compliance.yaml")
        sys.exit(1)
    
    print(get_compliance_banner())
    
    parser = argparse.ArgumentParser(
        description="Raleigh Outreach Finder + Tracker (Compliance-Safe)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # discover command
    discover_parser = subparsers.add_parser("discover", help="Pull company data from sources")
    discover_parser.add_argument("--since", type=int, default=30, 
                                  help="Days to look back (default: 30)")
    discover_parser.add_argument("--sources", nargs="+", 
                                  default=["crunchbase", "google_places", "nc_directories"],
                                  help="Sources to query")
    
    # rank command
    rank_parser = subparsers.add_parser("rank", help="Score and rank companies")
    rank_parser.add_argument("--top", type=int, default=50, 
                              help="Number of top companies to output")
    
    # draft command
    draft_parser = subparsers.add_parser("draft", help="Generate message drafts")
    draft_parser.add_argument("--company-id", type=int, required=True,
                               help="Company ID to draft messages for")
    draft_parser.add_argument("--contact-id", type=int, default=None,
                               help="Optional contact ID for personalization")
    draft_parser.add_argument("--angle", choices=["peer", "curiosity", "usecase", "local"],
                               default="peer", help="Message angle to use")
    
    # log command
    log_parser = subparsers.add_parser("log", help="Record outreach events")
    log_parser.add_argument("action", choices=["sent", "seen", "replied", "followup"],
                            help="Event type to log")
    log_parser.add_argument("--contact-id", type=int, required=True,
                            help="Contact ID")
    log_parser.add_argument("--sequence-id", type=int, default=None,
                            help="Sequence ID")
    log_parser.add_argument("--step", type=int, default=1,
                            help="Step number in sequence")
    log_parser.add_argument("--outcome", type=str, default=None,
                            help="Outcome note (for replies)")
    
    # export command
    export_parser = subparsers.add_parser("export", help="Export data to CSV")
    export_parser.add_argument("--type", choices=["companies", "contacts", "sequences", "summary"],
                                default="companies", help="Data to export")
    export_parser.add_argument("--format", choices=["csv", "notion", "sheets"],
                                default="csv", help="Output format")
    export_parser.add_argument("--output", type=str, default=None,
                                help="Output file path")
    
    # status command
    status_parser = subparsers.add_parser("status", help="Show current stats")
    
    # contact command (new)
    contact_parser = subparsers.add_parser("contact", help="Manage contacts")
    contact_subparsers = contact_parser.add_subparsers(dest="contact_action")
    
    # contact add
    add_contact_parser = contact_subparsers.add_parser("add", help="Add a contact")
    add_contact_parser.add_argument("--company-id", type=int, required=True,
                                     help="Company ID")
    add_contact_parser.add_argument("--first-name", type=str, required=True,
                                     help="First name")
    add_contact_parser.add_argument("--last-name", type=str, required=True,
                                     help="Last name")
    add_contact_parser.add_argument("--title", type=str, required=True,
                                     help="Job title")
    add_contact_parser.add_argument("--linkedin-url", type=str, default=None,
                                     help="LinkedIn profile URL")
    add_contact_parser.add_argument("--email", type=str, default=None,
                                     help="Email address")
    add_contact_parser.add_argument("--notes", type=str, default=None,
                                     help="Notes about this contact")
    
    # contact list
    list_contact_parser = contact_subparsers.add_parser("list", help="List contacts")
    list_contact_parser.add_argument("--company-id", type=int, default=None,
                                      help="Filter by company ID")
    list_contact_parser.add_argument("--status", type=str, default=None,
                                      help="Filter by status")
    
    # contact dnc (do not contact)
    dnc_parser = contact_subparsers.add_parser("dnc", help="Add to do-not-contact list")
    dnc_parser.add_argument("--contact-id", type=int, default=None,
                            help="Contact ID to suppress")
    dnc_parser.add_argument("--domain", type=str, default=None,
                            help="Domain to suppress")
    dnc_parser.add_argument("--reason", type=str, default="",
                            help="Reason for suppression")
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    
    # Route to command handlers
    commands = {
        "discover": cmd_discover,
        "rank": cmd_rank,
        "draft": cmd_draft,
        "log": cmd_log,
        "export": cmd_export,
        "status": cmd_status,
        "contact": cmd_contact,
    }
    
    try:
        commands[args.command](args)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Message Generator Module

Generates personalized message drafts for outreach.
All outputs are marked as drafts requiring human review.
"""

from typing import Dict, Any, Optional
import random

from utils.compliance import ComplianceChecker
from utils.config import load_config
from db.repo import DatabaseRepo
from .templates import (
    get_template, 
    get_personalization, 
    get_hook, 
    get_ps_line,
    INVITE_TEMPLATES
)


def generate_drafts(
    company_id: int,
    contact_id: int = None,
    angle: str = "peer"
) -> Dict[str, Any]:
    """
    Generate message drafts for a company/contact.
    
    Args:
        company_id: ID of the target company
        contact_id: Optional ID of specific contact
        angle: Message angle (peer, curiosity, usecase, local)
    
    Returns:
        Dictionary with invite_note and inmail_message
    """
    checker = ComplianceChecker()
    db = DatabaseRepo()
    config = load_config()
    
    # Get company data
    company = db.get_company(company_id)
    if not company:
        raise ValueError(f"Company ID {company_id} not found")
    
    # Get contact data if provided
    contact = None
    if contact_id:
        contact = db.get_contact(contact_id)
    
    # Generate messages
    generator = MessageGenerator(checker, config)
    
    invite_note = generator.generate_invite_note(company, contact, angle)
    inmail_message = generator.generate_inmail(company, contact, angle)
    
    # Save drafts to database
    db.save_draft(
        company_id=company_id,
        contact_id=contact_id,
        angle=angle,
        invite_note=invite_note,
        inmail_message=inmail_message
    )
    
    return {
        "invite_note": invite_note,
        "inmail_message": inmail_message,
        "angle": angle,
        "company_name": company["company_name"],
        "contact_name": f"{contact['first_name']} {contact['last_name']}" if contact else None,
        "draft_label": checker.get_draft_label()
    }


class MessageGenerator:
    """Generates personalized messages from templates."""
    
    def __init__(self, checker: ComplianceChecker, config: Dict):
        self.checker = checker
        self.config = config
        self.max_invite_chars = checker.get_max_invite_chars()
        self.max_inmail_chars = checker.get_max_inmail_chars()
    
    def generate_invite_note(
        self, 
        company: Dict, 
        contact: Dict = None,
        angle: str = "peer"
    ) -> str:
        """Generate a LinkedIn invite note (< 300 chars)."""
        template = get_template("invite", angle)
        
        # Prepare variables
        vars = self._prepare_variables(company, contact)
        
        # Fill template
        message = template.format(**vars)
        
        # Ensure under limit
        if len(message) > self.max_invite_chars:
            message = self._truncate_message(message, self.max_invite_chars)
        
        return message
    
    def generate_inmail(
        self, 
        company: Dict, 
        contact: Dict = None,
        angle: str = "peer"
    ) -> str:
        """Generate an InMail message (700-1200 chars target)."""
        template = get_template("inmail", angle)
        
        # Prepare variables
        vars = self._prepare_variables(company, contact)
        vars["personalization"] = get_personalization(company)
        vars["hook"] = get_hook(company.get("industry", "Technology"))
        vars["ps_line"] = get_ps_line(random.randint(0, 3))
        vars["use_case_area"] = self._get_use_case(company)
        
        # Fill template
        message = template.format(**vars)
        
        return message
    
    def _prepare_variables(self, company: Dict, contact: Dict = None) -> Dict:
        """Prepare template variables."""
        return {
            "first_name": contact["first_name"] if contact else "there",
            "last_name": contact["last_name"] if contact else "",
            "title": contact["title"] if contact else "",
            "company_name": company.get("company_name", "your company"),
            "domain": company.get("domain", ""),
            "industry": company.get("industry", "technology"),
            "city": company.get("hq_city", "Raleigh"),
            "state": company.get("hq_state", "NC"),
            "sender_name": "[Your Name]",  # Placeholder for human to fill
            "personalization": "",
            "hook": "",
            "ps_line": "",
            "use_case_area": ""
        }
    
    def _truncate_message(self, message: str, max_chars: int) -> str:
        """Truncate message to fit within character limit."""
        if len(message) <= max_chars:
            return message
        
        # Try to truncate at a sentence boundary
        truncated = message[:max_chars - 3]
        
        # Find last sentence end
        for end_char in ['. ', '! ', '? ']:
            last_end = truncated.rfind(end_char)
            if last_end > max_chars * 0.7:  # Keep at least 70% of message
                return truncated[:last_end + 1]
        
        # Fall back to word boundary
        last_space = truncated.rfind(' ')
        if last_space > max_chars * 0.8:
            return truncated[:last_space] + "..."
        
        return truncated + "..."
    
    def _get_use_case(self, company: Dict) -> str:
        """Get a use case area based on company industry."""
        industry = company.get("industry", "").lower()
        
        use_cases = {
            "software": "modern software development practices",
            "ai/ml": "practical AI implementation",
            "healthtech": "healthcare technology adoption",
            "fintech": "financial technology innovation",
            "cybersecurity": "security in the modern threat landscape",
            "data analytics": "data-driven decision making",
        }
        
        return use_cases.get(industry, "innovation in your space")

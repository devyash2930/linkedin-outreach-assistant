"""
Compliance Checker - Enforces safety guardrails.

This module ensures the tool remains assistive-only and
prevents any LinkedIn automation features.
"""

import yaml
from pathlib import Path


class ComplianceChecker:
    """Enforces compliance guardrails from config/compliance.yaml"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Find config relative to this file
            root = Path(__file__).parent.parent.parent
            config_path = root / "config" / "compliance.yaml"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load compliance configuration."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Compliance config not found: {self.config_path}\n"
                "This is required for the tool to operate safely."
            )
        
        with open(self.config_path) as f:
            return yaml.safe_load(f)
    
    def is_compliant(self) -> bool:
        """Check if current configuration is compliant."""
        linkedin = self.config.get("linkedin", {})
        
        # These MUST all be False for compliance
        if linkedin.get("auto_send", True):
            return False
        if linkedin.get("auto_connect", True):
            return False
        if linkedin.get("profile_scraping", True):
            return False
        
        # Human review must be required
        messaging = self.config.get("messaging", {})
        if not messaging.get("human_review_required", False):
            return False
        
        return True
    
    def get_max_invite_chars(self) -> int:
        """Get maximum characters allowed for invite notes."""
        return self.config.get("messaging", {}).get("max_invite_chars", 300)
    
    def get_max_inmail_chars(self) -> int:
        """Get maximum characters allowed for InMail."""
        return self.config.get("messaging", {}).get("max_inmail_chars", 1900)
    
    def requires_human_review(self) -> bool:
        """Check if human review is required for all outputs."""
        return self.config.get("messaging", {}).get("human_review_required", True)
    
    def get_draft_label(self) -> str:
        """Get the label to apply to all draft outputs."""
        return "DRAFT – HUMAN REVIEW REQUIRED"
    
    def validate_action(self, action: str) -> bool:
        """
        Validate that an action is allowed.
        
        Blocked actions:
        - send_message
        - send_connection
        - scrape_profile
        - browser_automation
        """
        blocked_actions = [
            "send_message",
            "send_connection", 
            "scrape_profile",
            "browser_automation",
            "use_linkedin_cookie",
            "use_linkedin_session"
        ]
        
        if action in blocked_actions:
            raise PermissionError(
                f"Action '{action}' is blocked by compliance policy.\n"
                "This tool is assistive-only and cannot automate LinkedIn actions."
            )
        
        return True

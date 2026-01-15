"""
Message Templates Module

Templates for different message angles:
- peer: Peer introduction style
- curiosity: Product curiosity angle
- usecase: Use-case observation
- local: Local Raleigh connection
"""

from typing import Dict


# InMail Templates (700-1200 chars target)
INMAIL_TEMPLATES = {
    "peer": """Hi {first_name},

I noticed {company_name} and the work you're doing in the {industry} space here in {city}. As someone who's been following the local tech scene, it's exciting to see companies like yours making an impact.

{personalization}

I'd love to learn more about what you're building and see if there might be an opportunity to connect. No agenda—just genuinely curious about {company_name}'s journey and where you're headed.

Would you be open to a quick chat sometime? Even 15 minutes would be great.

Best,
{sender_name}

P.S. {ps_line}""",

    "curiosity": """Hi {first_name},

I came across {company_name} while researching {industry} companies in the Triangle area, and I'm genuinely curious about your approach.

{personalization}

What caught my attention was {hook}. I'd love to hear more about how you're thinking about this space and where {company_name} is headed.

If you have a few minutes for a brief call, I'd really appreciate the chance to learn from your perspective. No pitch—just looking to understand the landscape better.

Thanks for considering,
{sender_name}""",

    "usecase": """Hi {first_name},

I've been researching {industry} companies in the Raleigh area, and {company_name} stood out.

{personalization}

I'm exploring how companies like yours are tackling {use_case_area}, and I think there might be some interesting parallels worth discussing.

Would you be open to a 15-minute conversation? I promise to keep it focused and valuable for both of us.

Best regards,
{sender_name}""",

    "local": """Hi {first_name},

As a fellow member of the Raleigh tech community, I wanted to reach out and connect.

I've been following {company_name}'s growth, and it's great to see local companies thriving in the {industry} space. {personalization}

I'm always looking to build relationships with others in our local ecosystem. Would you be open to grabbing a coffee or hopping on a quick call sometime?

Looking forward to potentially connecting,
{sender_name}

P.S. Love seeing Triangle companies succeed!"""
}


# Invite Note Templates (< 300 chars hard limit)
INVITE_TEMPLATES = {
    "peer": """Hi {first_name}, I noticed {company_name}'s work in {industry} here in {city}. Would love to connect and learn more about what you're building. Always great to meet fellow local tech leaders!""",

    "curiosity": """Hi {first_name}, came across {company_name} while researching {industry} in the Triangle. Your approach looks interesting—would love to connect and learn more about your journey.""",

    "usecase": """Hi {first_name}, researching {industry} companies in Raleigh and {company_name} stood out. Would love to connect and exchange perspectives on the space.""",

    "local": """Hi {first_name}, fellow Raleigh tech person here! Noticed {company_name} and wanted to connect. Always looking to build relationships in our local ecosystem."""
}


# Personalization snippets based on signals
PERSONALIZATION_SNIPPETS = {
    "hiring": "I see you're growing the team—that's always an exciting (and challenging!) phase.",
    "funding": "Congrats on the recent funding! That's a big milestone.",
    "expansion": "I noticed the expansion news—exciting times for {company_name}.",
    "launch": "Saw the recent launch—looks like you've been busy!",
    "default": "I've been impressed by what I've seen from {company_name} so far."
}


# PS lines for InMail
PS_LINES = [
    "Always happy to make introductions to others in the local ecosystem if helpful.",
    "If this isn't a good time, no worries—feel free to connect anyway.",
    "I know these messages can get lost—happy to follow up if that's easier.",
    "Let me know if there's a better way to reach you.",
]


# Hooks for curiosity angle
CURIOSITY_HOOKS = {
    "Software": "your approach to building scalable solutions",
    "AI/ML": "how you're applying AI/ML in practical ways",
    "HealthTech": "your work at the intersection of health and technology",
    "FinTech": "your approach to financial technology innovation",
    "Cybersecurity": "your take on modern security challenges",
    "Data Analytics": "how you're helping companies make sense of their data",
    "Technology": "your innovative approach to solving real problems",
    "default": "your unique approach in this space"
}


def get_template(template_type: str, angle: str) -> str:
    """Get a template by type and angle."""
    if template_type == "inmail":
        return INMAIL_TEMPLATES.get(angle, INMAIL_TEMPLATES["peer"])
    else:
        return INVITE_TEMPLATES.get(angle, INVITE_TEMPLATES["peer"])


def get_personalization(company: Dict) -> str:
    """Get personalization snippet based on company signals."""
    activity = company.get("recent_activity", "").lower()
    hiring = company.get("hiring_signal", "")
    
    if "funding" in activity or "series" in activity or "raised" in activity:
        return PERSONALIZATION_SNIPPETS["funding"]
    elif "expansion" in activity or "new office" in activity:
        return PERSONALIZATION_SNIPPETS["expansion"].format(
            company_name=company.get("company_name", "your company")
        )
    elif "launch" in activity:
        return PERSONALIZATION_SNIPPETS["launch"]
    elif hiring == "yes":
        return PERSONALIZATION_SNIPPETS["hiring"]
    else:
        return PERSONALIZATION_SNIPPETS["default"].format(
            company_name=company.get("company_name", "your company")
        )


def get_hook(industry: str) -> str:
    """Get a hook for the curiosity angle based on industry."""
    return CURIOSITY_HOOKS.get(industry, CURIOSITY_HOOKS["default"])


def get_ps_line(index: int = 0) -> str:
    """Get a PS line for InMail."""
    return PS_LINES[index % len(PS_LINES)]

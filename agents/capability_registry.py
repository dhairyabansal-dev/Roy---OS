"""Small, local registry describing Agent Bay's specialist capabilities."""

CAPABILITIES = {
    "email": {
        "name": "Email Agent",
        "source": "agents/email_agent.py",
        "capabilities": [
            "Unread email summaries",
            "Professional email drafts",
            "Reply drafting with user review",
        ],
        "enhancement_examples": ["cold outreach", "personalized follow-ups", "outreach templates"],
    },
    "quant": {
        "name": "Quant Agent",
        "source": "agents/quant_agent.py",
        "capabilities": ["Quant finance mission tracking"],
        "enhancement_examples": ["calculus", "probability and statistics", "option pricing"],
    },
    "study": {
        "name": "Study Agent",
        "source": "agents/study_agent.py",
        "capabilities": ["ACCA and university study missions", "Study queue tracking"],
        "enhancement_examples": ["Financial Accounting", "ACCA material", "quizzes and revision plans"],
    },
    "developer": {
        "name": "Developer Agent",
        "source": "agents/developer_agent.py",
        "capabilities": ["Agent inspection", "Enhancement planning", "Validation planning"],
        "enhancement_examples": ["new specialist capabilities", "routing changes", "bug fixes"],
    },
}


def describe_capabilities():
    """Return registry data in a stable, presentation-friendly form."""
    return CAPABILITIES.copy()
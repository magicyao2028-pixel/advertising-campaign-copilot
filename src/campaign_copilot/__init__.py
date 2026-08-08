"""Reviewable campaign planning and optimization workflow."""

from .copilot import CampaignCopilot
from .models import CampaignBrief, Creative, PerformanceCell, load_campaign
from .report import render_markdown

__all__ = ["CampaignCopilot", "CampaignBrief", "Creative", "PerformanceCell", "load_campaign", "render_markdown"]
__version__ = "0.1.0"

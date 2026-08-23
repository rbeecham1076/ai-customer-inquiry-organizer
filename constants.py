"""
Shared lists used across the whole app.

Putting these in one file means the AI prompt, the validation logic, and
the UI dropdowns can never drift out of sync with each other - change a
list here and every part of the app sees the update.
"""

CATEGORIES = [
    "Order Question",
    "Refund / Return",
    "Product Question",
    "Custom Request",
    "Complaint",
    "Other",
]

PRIORITIES = ["Low", "Medium", "High"]

SENTIMENTS = ["Positive", "Neutral", "Frustrated", "Urgent"]

DEPARTMENTS = [
    "Customer Support",
    "Order Fulfillment",
    "Returns & Refunds",
    "Sales",
    "Management",
]

# Where an inquiry sits in the New Inquiry -> AI Analysis -> Human Review
# -> Approved Task workflow.
STATUSES = ["Pending Review", "Approved", "Dismissed"]

# Small visual cues so priority and sentiment can be scanned at a glance,
# the way a real support queue would color-code them.
PRIORITY_ICONS = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}
SENTIMENT_ICONS = {"Positive": "🟢", "Neutral": "⚪", "Frustrated": "🟠", "Urgent": "🔴"}

# Badge colors as (background, text) pairs, tuned to the warm cream theme.
# Kept here rather than in styles.py so every label the app can display
# has its color defined next to the list of allowed values.
PRIORITY_COLORS = {
    "Low": ("#A8E6CF", "#0B3D2E"),
    "Medium": ("#FFC145", "#1E1B2E"),
    "High": ("#FF5A36", "#FFFFFF"),
}

STATUS_COLORS = {
    "Pending Review": ("#FFC145", "#1E1B2E"),
    "Approved": ("#A8E6CF", "#0B3D2E"),
    "Dismissed": ("#E3DEEA", "#4A4358"),
}

SAMPLE_MESSAGES = {
    "Size change": (
        "Hey! I ordered the blue shirt last week and I think I picked the wrong "
        "size. Can I change it to a large? Order #1834. Thanks!"
    ),
    "Refund request": (
        "Hi, my order #2197 arrived yesterday but the print is damaged. "
        "I'd like a refund or replacement. I need it for an event this weekend."
    ),
    "Custom order": (
        "Can you make 24 shirts for our volleyball team with player names on the back? "
        "We need them by September 12. What would pricing look like?"
    ),
}

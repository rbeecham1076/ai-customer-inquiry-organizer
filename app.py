import json

import streamlit as st

import db
from ai import analyze_inquiry, get_provider, get_api_key, InquiryAnalysisError
from constants import (
    CATEGORIES,
    PRIORITIES,
    SENTIMENTS,
    DEPARTMENTS,
    SAMPLE_MESSAGES,
    PRIORITY_ICONS,
    SENTIMENT_ICONS,
)
from styles import CUSTOM_CSS, render_hero, render_footer, stat_cards, status_badge

# Your credit line, shown at the bottom of every page. Fill in the URLs
# below and they'll appear as links; leave one blank and it's skipped.
AUTHOR_NAME = "Rachel Beecham"
AUTHOR_LINKS = {
    "GitHub": "",
    "LinkedIn": "",
}

st.set_page_config(
    page_title="AI Customer Inquiry Organizer",
    page_icon="✨",
    layout="wide",
)

# Inject the custom fonts and design styles once, before anything renders.
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Make sure the inquiries table exists before we try to read or write it.
# This runs on every page load, but it's cheap and it means the app never
# crashes just because inquiries.db hasn't been created yet.
db.init_db()

# st.session_state keeps data around between reruns. Streamlit reruns this
# whole script from top to bottom every time you click something, so
# without session_state the AI's answer would disappear the moment you
# touched an edit box - this is what makes the review step possible.
if "pending_review" not in st.session_state:
    st.session_state.pending_review = None

# A one-time message to show right after a rerun (for example, right after
# approving a task). st.rerun() restarts the script immediately, so a
# message shown just before it would never actually reach the screen -
# stashing it in session_state lets it survive the rerun and display once.
if "flash" not in st.session_state:
    st.session_state.flash = None

has_pending_review = st.session_state.pending_review is not None

st.markdown(
    render_hero("Human Review" if has_pending_review else "New Inquiry"),
    unsafe_allow_html=True,
)

if st.session_state.flash:
    kind, text = st.session_state.flash
    getattr(st, kind)(text)
    st.session_state.flash = None

with st.sidebar:
    st.markdown('<p class="section-label">Try a sample</p>', unsafe_allow_html=True)
    sample_name = st.selectbox(
        "Sample inquiry", ["None"] + list(SAMPLE_MESSAGES.keys()), label_visibility="collapsed"
    )
    st.divider()
    st.markdown('<p class="section-label">AI provider</p>', unsafe_allow_html=True)

    # Show which model is wired up and whether a key is actually present,
    # so a missing key is obvious before you click Analyze rather than after.
    try:
        provider = get_provider()
        if get_api_key(provider["key_env"]):
            st.caption(f"{provider['label']} · `{provider['model']}` · key detected")
        else:
            st.caption(f"{provider['label']} · no `{provider['key_env']}` found")
    except InquiryAnalysisError as exc:
        st.caption(str(exc))

    st.divider()
    st.markdown('<p class="section-label">About</p>', unsafe_allow_html=True)
    st.caption(
        "A first-pass triage tool for customer messages. Built with Python, "
        "Streamlit, SQLite, and a swappable LLM provider."
    )

new_inquiry_tab, dashboard_tab, about_tab = st.tabs(["New Inquiry", "Dashboard", "How it works"])

# ---------------------------------------------------------------------
# Tab 1: New Inquiry -> AI Analysis -> Human Review -> Approved Task
# ---------------------------------------------------------------------

with new_inquiry_tab:
    st.markdown(
        '<div class="guardrail"><strong>The AI drafts. You decide.</strong> '
        "It never promises a refund, replacement, discount, or delivery date on "
        "its own. Every suggestion sits here until you say go.</div>",
        unsafe_allow_html=True,
    )

    default_text = "" if sample_name == "None" else SAMPLE_MESSAGES[sample_name]

    message = st.text_area(
        "Customer message",
        value=default_text,
        height=170,
        placeholder="Paste a customer email, DM, order question, or support message here...",
        disabled=has_pending_review,
    )

    if has_pending_review:
        st.info("Finish reviewing the inquiry below before analyzing a new one.")

    analyze = st.button(
        "Analyze inquiry",
        type="primary",
        use_container_width=True,
        disabled=has_pending_review,
    )

    if analyze:
        if not message.strip():
            st.warning("Paste a customer message first.")
            st.stop()

        try:
            with st.spinner("Organizing the inquiry..."):
                result = analyze_inquiry(message)
        except InquiryAnalysisError as exc:
            st.error(str(exc))
            st.stop()

        inquiry_id = db.save_inquiry(message, result)
        st.session_state.pending_review = {"id": inquiry_id, **result}
        st.rerun()

    if st.session_state.pending_review:
        review = st.session_state.pending_review

        st.divider()
        st.markdown('<div class="review-flag">Your turn &middot; Step 3 of 4</div>', unsafe_allow_html=True)
        st.markdown('<p class="section-title">Check the AI\'s work</p>', unsafe_allow_html=True)
        st.caption(
            "Here's the first pass. Change anything that's off, then approve it "
            "to lock it in - or dismiss it if it doesn't need action."
        )

        left, right = st.columns(2)
        with left:
            category = st.selectbox(
                "Category", CATEGORIES, index=CATEGORIES.index(review["category"])
            )
            priority = st.selectbox(
                "Priority",
                PRIORITIES,
                index=PRIORITIES.index(review["priority"]),
                format_func=lambda p: f"{PRIORITY_ICONS[p]} {p}",
            )
            sentiment = st.selectbox(
                "Sentiment",
                SENTIMENTS,
                index=SENTIMENTS.index(review["sentiment"]),
                format_func=lambda s: f"{SENTIMENT_ICONS[s]} {s}",
            )
        with right:
            suggested_department = st.selectbox(
                "Route to department",
                DEPARTMENTS,
                index=DEPARTMENTS.index(review["suggested_department"]),
            )
            customer_name = st.text_input("Customer name", value=review["customer_name"])
            order_number = st.text_input("Order number", value=review["order_number"])

        customer_request = st.text_area(
            "What they need", value=review["customer_request"], height=80
        )
        recommended_next_step = st.text_area(
            "Recommended next step", value=review["recommended_next_step"], height=80
        )
        suggested_response = st.text_area(
            "Suggested response - edit before using",
            value=review["suggested_response"],
            height=150,
        )

        st.caption("Final response (click the icon in the corner to copy):")
        st.code(suggested_response, language=None)

        approve_col, dismiss_col = st.columns(2)
        with approve_col:
            approve = st.button("Approve task", type="primary", use_container_width=True)
        with dismiss_col:
            dismiss = st.button("Dismiss - no action needed", use_container_width=True)

        if approve or dismiss:
            edited_fields = {
                "category": category,
                "priority": priority,
                "customer_name": customer_name,
                "order_number": order_number,
                "sentiment": sentiment,
                "customer_request": customer_request,
                "recommended_next_step": recommended_next_step,
                "suggested_department": suggested_department,
                "suggested_response": suggested_response,
            }
            new_status = "Approved" if approve else "Dismissed"
            db.update_inquiry(review["id"], edited_fields, new_status)
            st.session_state.pending_review = None
            st.session_state.flash = ("success", f"Inquiry marked {new_status}.")
            st.rerun()

        task = {
            "id": review["id"],
            "status": "Pending Review",
            "category": category,
            "priority": priority,
            "customer_name": customer_name,
            "order_number": order_number,
            "sentiment": sentiment,
            "customer_request": customer_request,
            "recommended_next_step": recommended_next_step,
            "suggested_department": suggested_department,
            "suggested_response": suggested_response,
        }
        st.download_button(
            "Download current task as JSON",
            data=json.dumps(task, indent=2),
            file_name="customer_inquiry_task.json",
            mime="application/json",
            use_container_width=True,
        )

    st.divider()
    st.markdown('<p class="section-title">Recent inquiries</p>', unsafe_allow_html=True)

    recent = db.get_recent_inquiries(limit=10)

    if not recent:
        st.caption("Nothing analyzed yet. Your saved inquiries will show up here.")
    else:
        # Add the priority/sentiment icons to a display copy, so the
        # underlying database values stay plain text.
        display_rows = []
        for row in recent:
            display_row = dict(row)
            display_row["priority"] = f"{PRIORITY_ICONS[row['priority']]} {row['priority']}"
            display_row["sentiment"] = f"{SENTIMENT_ICONS[row['sentiment']]} {row['sentiment']}"
            display_rows.append(display_row)

        st.dataframe(
            display_rows,
            column_order=[
                "created_at",
                "category",
                "priority",
                "sentiment",
                "status",
                "customer_request",
            ],
            column_config={
                "created_at": "Received",
                "category": "Category",
                "priority": "Priority",
                "sentiment": "Sentiment",
                "status": "Status",
                "customer_request": "What they need",
            },
            hide_index=True,
            use_container_width=True,
        )

# ---------------------------------------------------------------------
# Tab 2: Dashboard
# ---------------------------------------------------------------------

with dashboard_tab:
    total = db.get_total_count()

    if total == 0:
        st.markdown('<p class="section-title">Nothing here yet</p>', unsafe_allow_html=True)
        st.caption("Analyze an inquiry on the New Inquiry tab and your numbers will show up here.")
    else:
        status_counts = db.get_status_counts()
        priority_counts = db.get_priority_counts()

        st.markdown('<p class="section-label">Across every session</p>', unsafe_allow_html=True)
        st.markdown('<p class="section-title">The queue at a glance</p>', unsafe_allow_html=True)

        st.markdown(
            stat_cards(
                [
                    ("Total inquiries", total),
                    ("Waiting on you", status_counts.get("Pending Review", 0)),
                    ("Approved", status_counts.get("Approved", 0)),
                    ("High priority", priority_counts.get("High", 0)),
                ]
            ),
            unsafe_allow_html=True,
        )

        st.divider()

        chart_left, chart_right = st.columns(2)
        with chart_left:
            st.markdown('<p class="section-label">By category</p>', unsafe_allow_html=True)
            st.bar_chart(db.get_category_counts(), color="#FF5A36")
        with chart_right:
            st.markdown('<p class="section-label">By priority</p>', unsafe_allow_html=True)
            st.bar_chart(priority_counts, color="#FFC145")

        st.divider()
        st.markdown('<p class="section-label">Status breakdown</p>', unsafe_allow_html=True)
        badge_html = " ".join(
            f"{status_badge(status)} &nbsp;<strong>{count}</strong>&nbsp;&nbsp;&nbsp;"
            for status, count in status_counts.items()
        )
        st.markdown(badge_html, unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Tab 3: How it works
# ---------------------------------------------------------------------

with about_tab:
    st.markdown('<p class="section-title">Why this exists</p>', unsafe_allow_html=True)
    st.markdown(
        "Customer messages arrive messy &mdash; different wording, tone, and detail "
        "every time. Someone has to read each one, work out what the customer "
        "actually needs, judge how urgent it is, and decide what happens next. "
        "That's a lot of small decisions before any real work starts."
    )

    st.markdown('<p class="section-title">What the AI does</p>', unsafe_allow_html=True)
    st.markdown(
        "- Sorts the message into a category and priority\n"
        "- Reads the customer's tone\n"
        "- Pulls out the name and order number when they're there\n"
        "- Suggests a next step and a department to route it to\n"
        "- Drafts a reply you can edit"
    )

    st.markdown('<p class="section-title">What stays with you</p>', unsafe_allow_html=True)
    st.markdown(
        "Every field above is editable, and nothing is final until you approve it. "
        "The AI never commits to a refund, replacement, discount, or delivery date "
        "on its own &mdash; those are business decisions, not classification tasks."
    )

    st.markdown('<p class="section-title">Why AI instead of keyword rules</p>', unsafe_allow_html=True)
    st.markdown(
        "Keyword matching breaks on real customer language. \"I need this sorted "
        "before Saturday\" and \"this is unacceptable\" are both urgent, but they "
        "share no keywords. A language model reads intent rather than matching strings."
    )

    st.markdown('<p class="section-title">How it\'s built</p>', unsafe_allow_html=True)
    st.markdown(
        "- **`app.py`** &mdash; the interface and the review workflow\n"
        "- **`ai.py`** &mdash; the AI call, plus validation of whatever comes back\n"
        "- **`db.py`** &mdash; SQLite storage for history and dashboard totals\n"
        "- **`constants.py`** &mdash; the approved categories, priorities, and departments\n"
        "- **`styles.py`** &mdash; the visual design layer\n\n"
        "The AI provider is swappable: it runs on Google Gemini by default and "
        "switches to OpenAI with one environment variable, because the model "
        "behind a feature shouldn't be baked into the feature."
    )

# Footer, shown once below whichever tab is open.
st.markdown(
    render_footer(
        AUTHOR_NAME,
        AUTHOR_LINKS,
        "Python · Streamlit · SQLite · Gemini / OpenAI",
    ),
    unsafe_allow_html=True,
)

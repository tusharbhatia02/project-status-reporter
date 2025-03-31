import logging
import re
from datetime import datetime, timezone
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def build_structured_raw_report( 
    trello_lists: List[Dict],
    trello_cards_by_list: Dict[str, List[Dict]],
    email_data: List[Dict],
    slack_data: List[Dict],
    request_id: str
) -> Dict[str, Any]:
    """
    Constructs a structured dictionary containing formatted report sections.
    """
    logger.info(f"[Request:{request_id}] Building structured raw report...")

    report_data = {
        "trello": {"lines": [], "overdue_count": 0},
        "email": {"lines": [], "count": 0},
        "slack": {"lines": [], "count": 0}
    }
    overdue_tasks_list_internal = [] 

    # --- Trello Processing ---
    trello_lines = ["**Trello Board Status:**"]
    total_card_count = 0
    now_utc = datetime.now(timezone.utc)
    if trello_lists:
        for trello_list in trello_lists:
            # ... (Trello list/card processing logic) ...
            list_id = trello_list.get('id', 'Unknown'); list_name = trello_list.get('name', 'Unknown')
            cards = trello_cards_by_list.get(list_id, []); card_count = len(cards)
            total_card_count += card_count
            trello_lines.append(f"- **{list_name}**: {card_count} card(s)")
            for card in cards:
                card_name = card.get('name', 'Unnamed Card')
                if card.get('due') and not card.get('dueComplete'):
                    try: # ... date checking logic ...
                        due_date_str = card['due']; due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                        if due_date < now_utc: overdue_tasks_list_internal.append(f"'{card_name}' in list '{list_name}'")
                    except Exception as date_err: logger.warning(f"Date parse error: {date_err}")
        trello_lines.append(f"Total Cards: {total_card_count}")
        if overdue_tasks_list_internal:
            trello_lines.append("\n**🚨 Overdue Tasks:**")
            for task_info in overdue_tasks_list_internal: trello_lines.append(f"- {task_info}")
        else: trello_lines.append("\n**✅ No overdue tasks found.**")
        report_data["trello"]["overdue_count"] = len(overdue_tasks_list_internal)
    else:
        trello_lines.append("  _(Could not fetch Trello lists)_")
    report_data["trello"]["lines"] = trello_lines


   # --- Email Processing ---
    email_section_lines = ["\n**Recent Email Updates (Label: project-updates):**"]
    email_included_count = 0
    if email_data: 
        for email in email_data:
            body_preview = (email.get('body', '') or '').strip()

            email_included_count += 1 
            body_preview = body_preview[:150] + ('...' if len(body_preview) > 150 else '')
            sender = email.get('sender', 'N/A'); subject = email.get('subject', 'N/A')
            email_section_lines.append(f"\n- **From:** {sender}\n  **Subject:** {subject}\n  **Preview:** {body_preview}")

       
        if email_included_count == 0:
             email_section_lines.append("  _(No emails with relevant content found in the unread, labeled messages)_")

    else: 
        email_section_lines.append("  _(No unread emails found with the label or error fetching)_")

    report_data["email"]["lines"] = email_section_lines
    
    report_data["email"]["count"] = email_included_count


    # --- Slack Processing ---
    slack_lines = ["**Recent Slack Messages (Filtered):**"]
    filtered_slack_count = 0
    if slack_data: 
        for message in slack_data:
            text = message.get('text', '').strip(); user = message.get('user', 'N/A')
            
            filtered_slack_count += 1
            msg_preview = text[:150] + '...'
            tag = ""
            if re.search(r'\b(blocker|blocked|stuck)\b', text, re.IGNORECASE): tag = " [**BLOCKER?**]"
            elif re.search(r'\b(urgent|asap)\b', text, re.IGNORECASE): tag = " [**URGENT?**]"
            elif re.search(r'\b(action|todo|task|follow[- ]?up)\b', text, re.IGNORECASE): tag = " [**ACTION?**]"
            slack_lines.append(f"- **{user}**: {msg_preview}{tag}")
        if filtered_slack_count == 0 : slack_lines.append("  _(No relevant recent messages found)_")
    else: slack_lines.append("  _(No recent messages found or error fetching)_")
    report_data["slack"]["lines"] = slack_lines
    report_data["slack"]["count"] = filtered_slack_count

    logger.info(f"[Request:{request_id}] Structured raw report built.")
    return report_data
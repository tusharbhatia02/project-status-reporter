# services/slack_service.py
import os
import logging
from typing import List, Dict, Any, Tuple
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import date

logger = logging.getLogger(__name__)
user_info_cache_ss = {} # Keep cache local to this module

def _get_user_name(client: WebClient, user_id: str) -> str:
    """Internal helper to fetch user name from Slack API, uses cache."""
    if user_id in user_info_cache_ss: return user_info_cache_ss[user_id]
    try:
        result = client.users_info(user=user_id)
        user_name = result.get("user", {}).get("real_name", user_id)
        user_info_cache_ss[user_id] = user_name
        return user_name
    except SlackApiError as e:
       
        logger.error(f"Error fetching info for Slack user {user_id}: {e.response['error']}")
        return user_id # Fallback to ID

def get_slack_messages(channel_id: str, bot_token: str, num_messages: int = 20) -> List[Dict[str, Any]]:
    """Retrieves recent messages, attempting to filter out bot's own analysis posts."""
    # ... (token/channel checks) ...
    client = WebClient(token=bot_token)
    processed_messages = []
    logger.debug(f"Fetching last {num_messages} messages from Slack channel {channel_id}")
    try:
        result = client.conversations_history(channel=channel_id, limit=num_messages)
        messages = result.get('messages', [])
        logger.info(f"Fetched {len(messages)} raw messages from Slack channel {channel_id}.")

        bot_user_id = None
        try:
            # Try to get the Bot's User ID to filter its messages
            auth_test = client.auth_test()
            bot_user_id = auth_test.get("user_id")
            if bot_user_id: logger.debug(f"Identified Bot User ID: {bot_user_id}")
        except Exception as auth_err:
             logger.warning(f"Could not determine bot user ID via auth.test: {auth_err}")


        for msg in messages:
            user_id = msg.get('user')
            text = msg.get('text')
            subtype = msg.get('subtype') # Check for bot messages subtype

            # --- Filtering Logic ---
            # 1. Skip messages without user or text
            if not user_id or not text: continue
            # 2. Skip messages explicitly from *this* bot if ID is known
            if bot_user_id and user_id == bot_user_id: continue
            # 3. Skip common bot message subtypes
            if subtype == 'bot_message' and "Project Status Analysis" in text: continue
            # 4. Skip common noise messages (can add more patterns)
            if "has joined the channel" in text or "added an integration" in text: continue
            # --- End Filtering ---


            user_name = _get_user_name(client, user_id)
            processed_messages.append({'user': user_name, 'text': text, 'timestamp': msg.get('ts')})

        logger.info(f"Returning {len(processed_messages)} processed Slack messages after filtering.")
        # Return only the most recent *relevant* messages, up to a limit
        return processed_messages[:5]
    except SlackApiError as e:
        logger.error(f"Slack API Error fetching messages from {channel_id}: {e.response['error']}", exc_info=True)
        # Provide more context for common errors
        if e.response['error'] == 'not_in_channel':
             logger.error(f"The bot associated with SLACK_BOT_TOKEN is not in channel {channel_id}.")
        elif e.response['error'] == 'invalid_auth':
             logger.error("Invalid SLACK_BOT_TOKEN.")
        return []
    except Exception as e:
         logger.error(f"Unexpected error fetching Slack messages: {e}", exc_info=True)
         return []

def post_slack_message(bot_token: str, channel_id: str, message_text: str, request_id: str) -> Tuple[bool, str]:
    """
    Posts a message to a Slack channel using slack_sdk and Block Kit for formatting.
    Requires bot_token with 'chat:write' scope.
    """
    if not bot_token or not channel_id or not message_text:
        logger.error(f"[Request:{request_id}] Slack post failed: Missing token, channel ID, or message text.")
        return False, "Missing token, channel, or message."

    logger.info(f"[Request:{request_id}] Attempting to post message directly to Slack channel: {channel_id} using Block Kit.")
    try:
        slack_client = WebClient(token=bot_token)

        # --- Construct Block Kit Payload ---
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message_text
                }
            },
             
             {
                 "type": "context",
                 "elements": [
                     {
                         "type": "mrkdwn",
                         "text": f"Report generated on {date.today().strftime('%Y-%m-%d')}"
                     }
                 ]
             }
        ]
        # --- End Block Kit Payload ---

        response = slack_client.chat_postMessage(
            channel=channel_id,
            text=f"Project Status Analysis ({date.today().strftime('%Y-%m-%d')})", # Fallback text
            blocks=blocks
        )
        if response.get("ok"):
            ts = response.get("ts", "N/A")
            logger.info(f"[Request:{request_id}] Message successfully posted to Slack channel {channel_id} (ts: {ts}).")
            return True, f"Message posted successfully to {channel_id}."
        else:
            error_detail = response.get("error", "Unknown Slack API error")
            logger.error(f"[Request:{request_id}] Slack API error posting message: {error_detail}")
            # Check specifically for scope errors
            if error_detail == 'missing_scope':
                 logger.error(f"[Request:{request_id}] The SLACK_BOT_TOKEN is missing the 'chat:write' scope.")
            return False, f"Slack API Error: {error_detail}"
    except SlackApiError as e:
        error_detail = e.response['error']
        logger.error(f"[Request:{request_id}] Slack SDK error posting message: {error_detail}", exc_info=True)
        if error_detail == 'invalid_auth':
            logger.error(f"[Request:{request_id}] Invalid SLACK_BOT_TOKEN.")
        return False, f"Slack SDK Error: {error_detail}"
    except Exception as e:
        logger.error(f"[Request:{request_id}] Unexpected error posting to Slack: {e}", exc_info=True)
        return False, f"Unexpected Slack posting error: {e}"
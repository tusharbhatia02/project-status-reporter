import logging
import requests
from fastapi import HTTPException, status
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def get_trello_lists(api_key: str, token: str, board_id: str) -> List[Dict[str, Any]]:
    """Fetches lists from a Trello board."""
    url = f"https://api.trello.com/1/boards/{board_id}/lists"
    params = {"key": api_key, "token": token, "cards": "none"}
    logger.debug(f"Fetching Trello lists for board: {board_id}")
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        lists_data = response.json()
        logger.debug(f"Successfully fetched {len(lists_data)} Trello lists.")
        return lists_data
    except requests.exceptions.Timeout:
        logger.error("Error fetching Trello lists: Request timed out.")
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Trello API request timed out.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Trello lists: {e}", exc_info=True)
        status_code = e.response.status_code if hasattr(e, 'response') and e.response is not None else 503
        raise HTTPException(status_code=status_code, detail=f"Trello API Error: Could not fetch lists. {e}")

def get_cards_in_list(api_key: str, token: str, list_id: str) -> List[Dict[str, Any]]:
    """Fetches cards in a specific Trello list."""
    url = f"https://api.trello.com/1/lists/{list_id}/cards"
    params = {"key": api_key, "token": token, "fields": "name,due,dueComplete"}
    logger.debug(f"Fetching Trello cards for list: {list_id}")
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        cards_data = response.json()
        logger.debug(f"Successfully fetched {len(cards_data)} cards for list {list_id}.")
        return cards_data
    except requests.exceptions.Timeout:
        logger.warning(f"WARN: Trello card fetch timed out for list {list_id}.")
        return []
    except requests.exceptions.RequestException as e:
        logger.warning(f"WARN: Failed to fetch cards for Trello list {list_id}: {e}")
        return []

def fetch_all_trello_data(api_key: str, token: str, board_id: str) -> Dict[str, Any]:
    """Fetches all lists and their corresponding cards for a board."""
    logger.info("Fetching all Trello data (lists and cards)...")
    lists = get_trello_lists(api_key, token, board_id) # Can raise HTTPException
    cards_by_list = {}
    if lists:
         for trello_list in lists:
              list_id = trello_list.get('id')
              if list_id:
                   # Individual card list fetch errors are logged but don't stop overall process
                   cards_by_list[list_id] = get_cards_in_list(api_key, token, list_id)
    logger.info("Finished fetching Trello data.")
    return {"lists": lists, "cards_by_list": cards_by_list}
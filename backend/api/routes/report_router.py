# api/routes/report_router.py
import logging
import os
from datetime import date
import json
from fastapi import APIRouter, Depends, HTTPException, status

# Import settings and dependency function
from config.settings import Settings, settings as app_settings
def get_settings() -> Settings:
    
    if app_settings is None: raise HTTPException(status_code=503, detail="...")
    return app_settings

# Import schemas
from schemas.report_schema import ReportResponse

# Import service functions

from services import trello_service, gmail_service, slack_service, report_builder
from agents import analysis_agent

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get(
    "/report",
    response_model=ReportResponse,
    summary="Generate Project Status Report & Notify Slack",
    tags=["Status Reports"]
)
async def get_status_report(config: Settings = Depends(get_settings)):
    request_id = os.urandom(4).hex()
    logger.info(f"[Request:{request_id}] Handling request for /report endpoint.")

    try:
        # === Step 1: Fetch Data ===
        logger.info(f"[Request:{request_id}] Calling data fetcher services...")
        trello_data = trello_service.fetch_all_trello_data(
            config.TRELLO_API_KEY, config.TRELLO_TOKEN, config.TRELLO_BOARD_ID
        )
        email_data = gmail_service.get_project_emails(
            token_path=config.GMAIL_TOKEN_PATH,
            credentials_path=config.GMAIL_CREDENTIALS_PATH
        )
        slack_messages = slack_service.get_slack_messages(
            config.SLACK_CHANNEL_ID, config.SLACK_BOT_TOKEN
        )
        logger.info(f"[Request:{request_id}] Data fetching stage complete.")


        # === Step 2: Build Structured Raw Report ===
        logger.info(f"[Request:{request_id}] Building structured raw report...")
        
        structured_report_data = report_builder.build_structured_raw_report(
            trello_lists=trello_data.get("lists", []),
            trello_cards_by_list=trello_data.get("cards_by_list", {}),
            email_data=email_data,
            slack_data=slack_messages,
            request_id=request_id
        )
        
        raw_report_string_for_agent = "\n\n".join([
            "\n".join(structured_report_data["trello"]["lines"]),
            "\n".join(structured_report_data["email"]["lines"]),
            "\n".join(structured_report_data["slack"]["lines"])
        ])
        logger.info(f"[Request:{request_id}] Structured report built, string version created for agent.")


        # === Step 3: Agent Analysis ===
        logger.info(f"[Request:{request_id}] Performing agent analysis...")
        # Pass the string version to the agent
        agent_analysis = analysis_agent.run_analysis_agent(raw_report_string_for_agent, config, request_id)
        logger.info(f"[Request:{request_id}] Agent analysis finished.")


        # === Step 4: Post Analysis to Slack ===
        logger.info(f"[Request:{request_id}] Posting analysis to Slack...")
        slack_status = "Notification skipped or failed."
        if "error during agent analysis" not in agent_analysis.lower() and \
           "failed" not in agent_analysis.lower() and agent_analysis.strip():
            current_date_str = date.today().strftime('%Y-%m-%d')
            slack_message = f"📊 *Project Status Analysis - {current_date_str}*\n>>> {agent_analysis}" # Use block quote
            success, slack_status = slack_service.post_slack_message(
                bot_token=config.SLACK_BOT_TOKEN,
                channel_id=config.SLACK_CHANNEL_ID,
                message_text=slack_message,
                request_id=request_id
            )
        else:
             logger.warning(f"[Request:{request_id}] Skipping Slack notification due to agent analysis issues.")
             slack_status = f"Skipped: {agent_analysis}"


        # === Step 5: Prepare and Return API Response ===
        logger.info(f"[Request:{request_id}] Preparing final API response.")
        
        response_data = ReportResponse(
            raw_report=raw_report_string_for_agent, # Return the string version
            agent_analysis=agent_analysis,
            slack_notification_status=slack_status,
            request_id=request_id
        )
        logger.info(f"[Request:{request_id}] Request processed successfully.")
        return response_data

    except HTTPException as http_exc:
        # Logged in lower layers or here if raised directly
        logger.error(f"[Request:{request_id}] HTTPException in report router: {http_exc.status_code} - {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"[Request:{request_id}] Unexpected error in report router: {e}", exc_info=True)
        # Return a generic error but include request ID for tracing
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected server error. Please contact support with Request ID: {request_id}"
        )
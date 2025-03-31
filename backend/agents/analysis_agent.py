# agents/analysis_agent.py
import logging
from typing import Dict, Any

# Pica & LangChain Imports
from pica_langchain import PicaClient, create_pica_agent
from pica_langchain.models import PicaClientOptions
from langchain.agents import AgentType
from langchain_google_genai import ChatGoogleGenerativeAI

# Import settings type hint
from config.settings import Settings

logger = logging.getLogger(__name__)

def run_analysis_agent(raw_report: str, config: Settings, request_id: str) -> str:
    """
    Initializes PicaClient, Gemini LLM, creates a Pica-aware agent,
    and invokes it to analyze the raw report for summary, actions, and risks.
    """
    logger.info(f"[Request:{request_id}] Initializing agent for analysis...")
    analysis_output = "Agent analysis failed or did not complete."

    if not raw_report or not raw_report.strip():
         logger.warning(f"[Request:{request_id}] Raw report is empty, skipping agent analysis.")
         return "Analysis skipped: Input report was empty."

    try:
        # Initialize PicaClient
        # Note: PicaClientOptions can be configured via settings if needed
        pica_client = PicaClient(
            secret=config.PICA_SECRET,
            options=PicaClientOptions(server_url=config.PICA_BASE_URL)
        )
        logger.info(f"[Request:{request_id}] PicaClient initialized (URL: {config.PICA_BASE_URL}).")

        # Initialize Gemini LLM
        llm = ChatGoogleGenerativeAI(
                model=config.GEMINI_MODEL_NAME,
                google_api_key=config.GOOGLE_API_KEY,
                temperature=0.4,
                convert_system_message_to_human=True
            )
        logger.info(f"[Request:{request_id}] Gemini LLM initialized ({config.GEMINI_MODEL_NAME}).")

        # Create Pica-aware Agent
        agent = create_pica_agent(
            client=pica_client,
            llm=llm,
            agent_type=AgentType.OPENAI_FUNCTIONS,
            verbose=False
        )
        logger.info(f"[Request:{request_id}] Pica Agent created (verbose={agent.verbose}).")

        # Define the Analysis Prompt
        agent_input_prompt = (
            f"You are an expert project analyst. Analyze the following project status report:\n\n"
            f"--- Project Status Report ---\n"
            f"{raw_report}\n"
            f"--- End Report ---\n\n"
            f"Generate a response containing the following distinct sections, using Markdown for formatting. "
            f"**Ensure there is a newline between each section title and the first bullet point or text within that section.**\n\n" # Added instruction
            f"**1. Concise Summary:**\n" # Keep newline here
            f"- Provide 3-5 key bullet points summarizing the overall project status...\n\n" # Keep newline here
            f"**2. Potential Action Items:**\n" # Keep newline here
            f"- List any specific tasks... If none, state 'No specific action items identified'.\n\n" # Keep newline here
            f"**3. Identified Risks/Blockers:**\n" # Keep newline here
            f"- List any potential risks... If none, state 'No immediate risks/blockers identified'."
        )

        # Invoke the Agent
        logger.info(f"[Request:{request_id}] Invoking agent for analysis...")
        agent_result: Dict[str, Any] = agent.invoke({"input": agent_input_prompt})
        logger.info(f"[Request:{request_id}] Agent analysis completed.")
        logger.debug(f"[Request:{request_id}] Full Agent Result: {agent_result}")

        # Extract the analysis output
        if isinstance(agent_result, dict) and 'output' in agent_result:
            analysis_output = agent_result['output']
            # --- POST-PROCESSING ---
            # safety check/fix
            analysis_output = analysis_output.replace(":**\n*", ":**\n\n*")  
            analysis_output = analysis_output.replace(":**\n-", ":**\n\n-")
            # --- END POST-PROCESSING ---
            logger.info(f"[Request:{request_id}] Agent analysis extracted and potentially post-processed.")
        else:
             logger.warning(f"[Request:{request_id}] Could not extract analysis from agent result: {agent_result}")
             analysis_output = "Agent output format unexpected."

    except Exception as agent_error:
        logger.error(f"[Request:{request_id}] Error during agent analysis setup or invocation: {agent_error}", exc_info=True)
        analysis_output = f"Error during agent analysis: {str(agent_error)}. Check logs (Req ID: {request_id})."

    return analysis_output
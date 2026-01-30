from __future__ import annotations

from typing import Any, List

# Importing masai AgentManager (Assuming it's available as per user instruction context)
# In a real environment, if masai is not installed, this will fail. 
# We assume the user has configured the environment correctly or we are mocking it.
try:
    from masai.AgentManager.AgentManager import AgentManager, AgentDetails
except ImportError:
    # Mocking for standalone development if masai is missing
    print("Warning: masai module not found. Using mocks.")
    class AgentDetails:
        def __init__(self, capabilities, style, description):
            pass
    class AgentManager:
        def get_agent(self, name): return None
        def create_agent(self, **kwargs): 
            print(f"[Mock] Creating agent: {kwargs.get('agent_name')}")
            return None

from app.controllers.Agents.HONEYPOT.PROMPTS import (
    HONEYPOT_AGENT_NAME,
    HONEYPOT_AGENT_DESCRIPTION,
    HONEYPOT_AGENT_CAPABILITIES,
    HONEYPOT_AGENT_STYLE
)

# In a real scenario, we would import tools here. For now, empty list.
from app.controllers.Agents.Tools.scam_extraction_tools import save_scam_intel
from app.controllers.Agents.Tools.callable_tool import context_tool_callable


def create_honeypot_agent(
    manager: AgentManager,
):
    """
    Idempotently create or return the HONEYPOT agent on the given manager.
    """
    # If already exists, return it
    try:
        existing = manager.get_agent(HONEYPOT_AGENT_NAME)
        if existing:
            return existing
    except Exception:
        pass

    # Register Extraction Tool
    tools: List = [save_scam_intel]

    details = AgentDetails(
        capabilities=HONEYPOT_AGENT_CAPABILITIES,
        style=HONEYPOT_AGENT_STYLE,
        description=HONEYPOT_AGENT_DESCRIPTION,
    )

    manager.create_agent(
        agent_name=HONEYPOT_AGENT_NAME,
        tools=tools,
        memory_order=20, # Priority for recent conversation
        agent_details=details,
        # context_callable=context_tool_callable,
        callable_config={"router":context_tool_callable, "evaluator":context_tool_callable, "reflector":context_tool_callable, "planner":context_tool_callable},
        long_context=True,
        long_context_order=20, # Priority for retrieved context
        shared_memory_order=3, # Priority for shared context
        temperature=0.8, # Slightly creative/natural
        max_tool_output_words=3000
    )

    return manager.get_agent(HONEYPOT_AGENT_NAME)

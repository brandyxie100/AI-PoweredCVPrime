"""
LangChain Agent Service — ReAct Agent with Custom Tools.

This module sets up a **LangChain Agent** that can answer free-form
questions about a CV by autonomously choosing which tools to call.

Author: brandyxie
Email:  brandyxie100@qq.com

What is a LangChain Agent?
    An agent is an LLM that can **decide** which actions (tools) to take,
    in what order, and how to combine the results.  Unlike a static chain
    (prompt → llm → parser), an agent can loop:

        Thought  →  Action (tool call)  →  Observation (tool result)
           ↑                                         │
           └─────────────────────────────────────────┘

    This loop repeats until the agent is satisfied it has enough
    information to provide a final answer.

Agent Type: **create_react_agent** (ReAct pattern)
    ReAct = "Reasoning + Acting".  The LLM explicitly writes its
    reasoning ("I need to check the CV text for certifications")
    before selecting a tool.  This makes the agent's behaviour
    transparent and debuggable.

LangChain Components:
    - ``create_react_agent``      – Builds the agent graph.
    - ``ChatAnthropic``           – The brain of the agent.
    - ``ChatPromptTemplate``      – System instructions for the agent.
    - ``StructuredTool`` (via ``@tool``) – The actions the agent can take.

How to Modify the Agent:
    1. **Add a new tool**: Create a function with ``@tool`` in
       ``cv_tools.py``, add it to ``ALL_CV_TOOLS``, and the agent
       will automatically have access to it.
    2. **Change the system prompt**: Edit ``AGENT_SYSTEM_PROMPT`` below
       to alter the agent's personality or instructions.
    3. **Change the LLM**: Replace ``config.get_llm()`` with any
       LangChain-compatible chat model (e.g., ``ChatOpenAI``).
    4. **Limit iterations**: Pass ``recursion_limit`` to prevent
       infinite loops (default = 25 in LangGraph).
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from app.config import AppConfig
from app.models.schemas import AgentQueryResponse
from app.tools.cv_tools import ALL_CV_TOOLS, set_analyzer

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Agent system prompt
# ---------------------------------------------------------------------------

AGENT_SYSTEM_PROMPT = (
    "You are an intelligent CV analysis assistant.  You have access to "
    "tools that can retrieve CV text, search specific sections, and "
    "analyse formatting.  Use these tools to answer the user's question "
    "thoroughly and accurately.\n\n"
    "Guidelines:\n"
    "- Always retrieve relevant CV data before answering.\n"
    "- If the question is about a specific section, use the search tool.\n"
    "- Cite specific text from the CV when possible.\n"
    "- Be concise but complete."
)


# ---------------------------------------------------------------------------
# Agent Service
# ---------------------------------------------------------------------------

class CVAgentService:
    """
    Wraps a LangChain ReAct agent for interactive CV Q&A.

    The agent can:
        - Read the full CV text.
        - Search for specific sections / keywords.
        - Analyse formatting quality.
        - Combine results to answer complex questions.

    Usage::

        from app.services.cv_analyzer import CVAnalyzer
        analyzer = CVAnalyzer()
        agent_svc = CVAgentService(analyzer)
        resp = await agent_svc.query("abc123", "Does the CV mention AWS?")
    """

    def __init__(self, analyzer: Any) -> None:
        """
        Create the agent.

        Args:
            analyzer: A ``CVAnalyzer`` instance — injected into the tools
                      so they can access uploaded CV data.
        """
        # Inject the analyzer into the tools module
        set_analyzer(analyzer)

        config = AppConfig()
        self._llm = config.get_llm()

        # Build the ReAct agent graph using LangGraph's prebuilt helper.
        # ``create_react_agent`` wires up:
        #   - The LLM (for reasoning and tool selection)
        #   - The tools (actions the agent can take)
        #   - A message-based state graph (tracks conversation history)
        self._agent = create_react_agent(
            model=self._llm,
            tools=ALL_CV_TOOLS,
            prompt=AGENT_SYSTEM_PROMPT,
        )

        logger.info(
            "CVAgentService created with %d tools: %s",
            len(ALL_CV_TOOLS),
            [t.name for t in ALL_CV_TOOLS],
        )

    async def query(self, file_id: str, question: str) -> AgentQueryResponse:
        """
        Ask the agent a free-form question about a specific CV.

        The agent will autonomously decide which tools to call,
        execute them, and synthesise a final answer.

        Args:
            file_id : The unique ID of the uploaded CV.
            question: Any question about the CV.

        Returns:
            ``AgentQueryResponse`` with the answer, sources, and tool calls.
        """
        logger.info("Agent query — file_id=%s, question='%s'", file_id, question)

        # Inject the file_id into the question so tools know which CV to use
        augmented_question = (
            f"The CV file_id is '{file_id}'.  "
            f"User question: {question}"
        )

        # Invoke the agent — it runs the ReAct loop internally
        result = await self._agent.ainvoke(
            {"messages": [HumanMessage(content=augmented_question)]},
        )

        # Extract the final answer and tool call history
        messages = result.get("messages", [])
        final_answer = messages[-1].content if messages else "No answer generated."

        # Collect tool names that were called during the agent loop
        tool_calls_made: list[str] = []
        sources: list[str] = []
        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_calls_made.append(tc["name"])
            if hasattr(msg, "name") and msg.name:
                # ToolMessage — the observation from a tool
                sources.append(f"Tool '{msg.name}' output (first 100 chars): {msg.content[:100]}")

        logger.info("Agent answered with %d tool calls.", len(tool_calls_made))

        return AgentQueryResponse(
            answer=final_answer,
            sources=sources,
            tool_calls=tool_calls_made,
        )

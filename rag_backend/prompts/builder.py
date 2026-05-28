from langchain_core.prompts import ChatPromptTemplate
from prompts.system import SYSTEM_PROMPT
from prompts.few_shot import few_shot_prompt
from prompts.cot import COT_INSTRUCTION
from prompts.skills import build_main_agent_skills

# Loaded once at import time — no per-request disk I/O.
_MAIN_AGENT_SKILLS: str = build_main_agent_skills()


def build_simple_prompt() -> ChatPromptTemplate:
    """Minimal RAG prompt: system instructions + grounded human turn.

    Input variables: context, question
    (plus any dynamic slots in SYSTEM_PROMPT: company_name, user_department,
    user_role, fallback_contact)
    """
    return ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "CONTEXT:\n{context}\n\nQUESTION: {question}"),
    ])


def build_vaultmind_prompt() -> ChatPromptTemplate:
    """Full RAG prompt: system instructions + operational skills +
    chain-of-thought + few-shot examples + grounded human turn.

    Layer order:
      1. SYSTEM_PROMPT  — base persona, grounding rules, brief style notes
      2. Skills block   — detailed operational guidance per capability
      3. COT_INSTRUCTION — per-query reasoning scratchpad
      4. Few-shot examples
      5. Human turn

    Prefer this over build_simple_prompt() for higher-quality, structured
    responses. Input variables are the same.
    """
    system = SYSTEM_PROMPT
    if _MAIN_AGENT_SKILLS:
        system = system + "\n\n" + _MAIN_AGENT_SKILLS
    system = system + "\n\n" + COT_INSTRUCTION

    return ChatPromptTemplate.from_messages([
        ("system", system),
        few_shot_prompt,
        ("human", "CONTEXT:\n{context}\n\nQUESTION: {question}"),
    ])

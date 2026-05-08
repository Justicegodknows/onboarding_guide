from langchain_core.prompts import ChatPromptTemplate
from prompts.system import SYSTEM_PROMPT
from prompts.few_shot import few_shot_prompt
from prompts.cot import COT_INSTRUCTION


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
    """Full RAG prompt: system instructions + chain-of-thought + few-shot
    examples + grounded human turn.

    Prefer this over build_simple_prompt() for higher-quality, structured
    responses. Input variables are the same.
    """
    return ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT + "\n\n" + COT_INSTRUCTION),
        few_shot_prompt,
        ("human", "CONTEXT:\n{context}\n\nQUESTION: {question}"),
    ])

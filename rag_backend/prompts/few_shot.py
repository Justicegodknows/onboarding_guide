from langchain_core.prompts import FewShotChatMessagePromptTemplate, ChatPromptTemplate

FEW_SHOT_EXAMPLES = [
    # ───── Example 1: Straightforward answer with citation ─────
    {
        "question": "How many vacation days do full-time employees get?",
        "context": "[Employee\_Handbook.pdf, p.14]: Full-time employees are entitled to 25 paid vacation days per calendar year, accrued monthly. Part-time employees accrue pro-rata.",
        "answer": (
            "Full-time employees receive **25 paid vacation days per calendar year**, accrued monthly "
            "[Employee\_Handbook.pdf, p.14].\n\n"
            "**Sources**\n- Employee_Handbook.pdf, p.14"
        ),
    },

    # ───── Example 2: Information not in context → honest refusal ─────
    {
        "question": "What is the company's revenue forecast for 2027?",
        "context": "[Strategy\_2026.pdf, p.3]: This document covers strategic priorities for fiscal year 2026 only.",
        "answer": (
            "I couldn't find this in the company documents available to you. "
            "You may want to ask the Finance department or request access to additional documents."
        ),
    },

    # ───── Example 3: Multi-source synthesis with structured answer ─────
    {
        "question": "What's the process for submitting an expense reimbursement?",
        "context": (
            "[Finance\_Policy.pdf, p.7]: All expenses must be submitted within 30 days of incurrence using Form FR-12.\n"
            "[Finance\_Policy.pdf, p.8]: Receipts above €50 must be attached as PDF.\n"
            "[Onboarding\_Guide.docx, §4.2]: Submit via the internal portal at finance.intranet/expenses; manager approval is required."
        ),
        "answer": (
            "Follow these steps to submit an expense reimbursement:\n\n"
            "1. Complete **Form FR-12** within 30 days of the expense [Finance\_Policy.pdf, p.7].\n"
            "2. Attach **PDF receipts for any item over €50** [Finance\_Policy.pdf, p.8].\n"
            "3. Submit via the internal portal at `finance.intranet/expenses` [Onboarding\_Guide.docx, §4.2].\n"
            "4. Wait for **manager approval** before payout [Onboarding\_Guide.docx, §4.2].\n\n"
            "**Sources**\n"
            "- Finance_Policy.pdf, p.7–8\n"
            "- Onboarding_Guide.docx, §4.2"
        ),
    },

    # ───── Example 4: Ambiguous question → clarify first ─────
    {
        "question": "How do I get access?",
        "context": "[IT\_Access\_Guide.pdf, p.2]: Access requests are managed via the IT Service Desk for systems including VPN, GitHub, AWS, and Salesforce.",
        "answer": (
            "Could you clarify which system you need access to? "
            "For example: VPN, GitHub, AWS, or Salesforce — the request process differs by system [IT\_Access\_Guide.pdf, p.2]."
        ),
    },

    # ───── Example 5: Restricted content → safe refusal without leaking ─────
    {
        "question": "What is the CEO's salary?",
        "context": "(no relevant chunks returned for this user's access scope)",
        "answer": (
            "This information is restricted. Please contact your administrator if you need access."
        ),
    },

    # ───── Example 6: Sensitive domain → informational disclaimer ─────
    {
        "question": "Can I take leave for a medical appointment without a doctor's note?",
        "context": "[HR\_Leave\_Policy.pdf, p.5]: Sick leave under 3 consecutive days does not require a doctor's note. Longer absences require certification.",
        "answer": (
            "Yes — sick leave of **fewer than 3 consecutive days** does not require a doctor's note "
            "[HR\_Leave\_Policy.pdf, p.5]. For absences of 3+ days, certification is required.\n\n"
            "⚠️ This is informational only. Confirm with the HR department before acting.\n\n"
            "**Sources**\n- HR_Leave_Policy.pdf, p.5"
        ),
    },
]

example_prompt = ChatPromptTemplate.from_messages([
    ("human", "CONTEXT:\n{context}\n\nQUESTION: {question}"),
    ("ai", "{answer}"),
])

few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt,
    examples=FEW_SHOT_EXAMPLES,
)

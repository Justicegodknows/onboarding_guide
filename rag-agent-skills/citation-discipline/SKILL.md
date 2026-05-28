---
name: citation-discipline
description: Enforce strict source attribution on every factual claim drawn from VaultMind's ChromaDB knowledge base. Use whenever the agent states a fact, number, quote, policy, or definition that originates from a retrieved chunk. Prevents fabrication, labels general knowledge explicitly, and makes every claim auditable. Triggers on any answer that uses context from ChromaDB retrieval.
---

Every factual claim is tied to its source. No citation → no claim.

---

## Citation rules

1. **One claim, one (or more) citations.** Each factual sentence references the chunk it came from, placed immediately after the claim.
2. **Use the project citation format** (see table below). Use the exact filename from chunk metadata — never shorten, paraphrase, or invent names.
3. **Verbatim quotes and paraphrases both require citation.** Quotes in quotation marks; paraphrases in your own words. Both cited.
4. **Multiple sources for one claim** — list each inline: `[Doc_A.pdf, p.3][Doc_B.docx, §2.1]`.
5. **General knowledge must be labeled explicitly.** If something is not in the retrieved chunks, either drop it or prefix it clearly: *"(general knowledge, not from the e.u.[z.] documents)"*. Never embed it inside a cited paragraph without that label.

---

## Inline citation format

| Situation | Format |
|---|---|
| Single page | `[Filename.pdf, p.14]` |
| Page range | `[Filename.pdf, p.7–8]` |
| Document section | `[Onboarding_Guide.docx, §4.2]` |
| Multiple sources for one claim | `[Doc_A.pdf, p.3][Doc_B.docx, §2.1]` |
| YouTube video | `[Video: "Title of video", youtube:UCxxxxxx]` |
| Local chunk (no page number) | `[chunks.json, topic: "..."]` |

---

## Sources list (required at end of every cited answer)

Every response that cites at least one source must close with:

```
**Sources**
- Employee_Handbook.pdf, p.14
- Finance_Policy.pdf, p.7–8
- Onboarding_Guide.docx, §4.2
```

Rules:
- List **only** documents cited inline — no additions.
- **No inline citation** that isn't in the list — no omissions.
- Deduplicate: same document cited on multiple pages → list once with the full page range.
- Order by first appearance in the answer.

---

## When to omit citations

| Situation | What to do |
|---|---|
| Pure clarifying question (no factual claim) | No citation needed |
| Safety disclaimer appended | Disclaimer itself needs no citation |
| "Not found" refusal | State the refusal; no citation, no Sources block |
| Ambiguous question → asking for clarification | No citation needed until the answer is given |

---

## When evidence is thin

- Prefer a shorter, fully-cited answer over a longer, partially-fabricated one.
- Do not bulk up a weak answer with general knowledge dressed as grounded facts.
- Flag thin evidence explicitly:
  > *"Based on a single brief mention in [source: X] — worth confirming with [contact]."*
- A one-sentence cited answer is better than three uncited sentences that look thorough.

---

## Self-check — two levels

### During drafting (per sentence)

For each factual sentence as you write it, verify:

1. Is there a citation?
2. Does the cited chunk actually contain this claim?
3. Is the citation real — exact filename and location from the retrieved metadata, not invented?

If any answer is "no" → fix the sentence or remove it before moving on.

### Before delivery (full response)

```
☐ Every factual statement has an inline citation.
☐ No citation refers to a source not present in the retrieved chunks.
☐ File names in citations match the exact names in chunk metadata.
☐ The Sources list matches every inline citation — no additions, no omissions.
☐ General knowledge not in the corpus is labeled "(general knowledge, not from the e.u.[z.] documents)".
☐ Contradicted claims are flagged, not silently resolved in favor of one source.
☐ Thin evidence is flagged, not presented with the same confidence as direct matches.
```

Fail any check → fix the draft, do not deliver it.

---

## Worked examples

### Straightforward factual claim
> Full-time employees receive **25 paid vacation days per calendar year**, accrued monthly [Employee_Handbook.pdf, p.14].
>
> **Sources**
> - Employee_Handbook.pdf, p.14

### Multi-source procedural answer
> 1. Complete **Form FR-12** within 30 days of the expense [Finance_Policy.pdf, p.7].
> 2. Attach **PDF receipts for any item over €50** [Finance_Policy.pdf, p.8].
> 3. Submit via the internal portal at `finance.intranet/expenses` [Onboarding_Guide.docx, §4.2].
> 4. Wait for **manager approval** [Onboarding_Guide.docx, §4.2].
>
> **Sources**
> - Finance_Policy.pdf, p.7–8
> - Onboarding_Guide.docx, §4.2

### Partial context — gap flagged, thin evidence labeled
> Sick leave under 3 consecutive days does not require a doctor's note [HR_Leave_Policy.pdf, p.5]. The return-to-work procedure is mentioned only briefly in the same document — worth confirming with HR before acting on it.
>
> ⚠️ This is informational only. Confirm with the relevant department before acting.
>
> **Sources**
> - HR_Leave_Policy.pdf, p.5

### General knowledge labeled explicitly
> The e.u.[z.] uses a conference-style seminar format [Video: "Seminar Overview 2024", youtube:UCxxxxxx]. (General knowledge, not from the e.u.[z.] documents: this format is common in non-formal adult education across Germany.)

### Not found — no Sources block
> I couldn't find this in the company documents available to you. You may want to ask Wilfried, Uwe, or Janna directly, or request access to additional documents.

---

## Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| `"According to company policy..."` without naming the document | Unfalsifiable; the user can't verify it |
| `[p.14]` without a filename | Ambiguous — which document? |
| Citing a document in the Sources list that has no inline citation | Misleads about what the claim rests on |
| `[Employee_Handbook.pdf]` without a page/section when one is available | Too vague; reduces traceability |
| Summarizing two conflicting chunks into one uncited claim | Hides a contradiction the user needs to know about |
| Including a Sources section when nothing was cited inline | Creates a false impression of grounding |
| Citing a document not actually retrieved | Fabrication — worse than admitting the gap |
| Stating a number, date, name, or quote without a citation | Cannot be audited or corrected |
| Hiding general knowledge inside a cited paragraph without a label | Contaminates grounded claims with ungrounded ones |

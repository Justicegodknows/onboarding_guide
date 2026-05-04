# 📘 VaultMind User Guide

Welcome to **VaultMind**, your organization's private AI knowledge assistant. This guide will help you get started, from logging in to querying your corporate documents.

---

## 🚀 Getting Started

### 1. Accessing the Vault
To access VaultMind, navigate to the internal company URL provided by your IT department (e.g., `http://vaultmind.local`). 

### 2. Logging In
VaultMind uses secure JWT-based authentication to ensure your data stays private.
- Enter your company credentials on the login page.
- Your account is assigned to a specific **Department** (e.g., HR, Finance, IT).
- **Note**: You will only be able to retrieve information from documents that your department has permission to access.

---

## 💬 Using the Assistant

### Asking Questions
The interface is designed to be as simple as a standard chat app.
1. Type your question in the input box at the bottom.
2. Press **Enter** or click **Send**.
3. VaultMind will scan the encrypted document vault and generate a grounded answer.

### Understanding Citations (The "Grounded Truth")
VaultMind is designed to eliminate "hallucinations." Every answer it provides is based on actual company documents.
- **Citations**: Look for markers like `[1]` or `[2]` in the AI's response.
- **Source Cards**: Below every answer, you will find a **Sources** section. This lists the exact filename and a snippet of the text used to generate the answer.
- **Verification**: We encourage you to click these sources to verify the information against the original document.

---

## 🛠️ For Administrators

### Ingesting Documents
Only users with the `ADMIN` role can add information to the knowledge base.
1. Navigate to the **Admin Upload Dashboard**.
2. Drag and drop your PDFs, Word documents, or spreadsheets.
3. Assign the document to a **Department** (e.g., "Legal").
4. Click **Ingest**. VaultMind will chunk the text and create semantic embeddings for instant retrieval.

---

## 🛡️ Privacy & Security FAQ

**Q: Does my data go to the cloud?**
**A: No.** VaultMind runs 100% on-premise. All processing happens on your local GPU workstation. No data is sent to OpenAI, Microsoft, or any other third-party.

**Q: How does the AI know my department?**
**A: JWT Tokens.** When you log in, your identity token contains a "claim" about your department. The system uses this to filter the vector database, ensuring you never see documents you aren't authorized to view.

**Q: What happens if the AI doesn't know the answer?**
**A: It will tell you.** VaultMind is configured in "RAG-only" mode. If the answer is not present in your ingested documents, the AI will explicitly state that it does not have enough information rather than guessing.

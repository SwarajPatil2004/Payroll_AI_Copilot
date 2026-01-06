# ZENVY Payroll Copilot — Workflow (Tenth‑grader friendly)

This document explains how the Payroll AI Copilot works **step by step**, from the moment a user asks a question to the moment the system returns an answer.   
It follows a “Retrieval‑Augmented Generation (RAG)” idea: first *retrieve* the right policy text, then *generate* an answer using only that text. 

---

## Big picture: What the system does

The copilot is like an “open book” exam helper:
- The “book” is your payroll policy files (`.md` / `.txt`). 
- When a question comes, the system first finds the most relevant pages from the “book”. 
- Then it asks the AI model to answer **only using those pages**, so it doesn’t make things up. 

---

## The pipeline in one view

When someone calls `POST /chat`, the app does this pipeline:

1. **Receive request (FastAPI)**: Get role + question.
2. **Redact PII**: Hide sensitive data like PAN/Aadhaar/bank account in the question.
3. **Retrieve policy context**: Search your policy text and pick the best matching snippets.  
4. **Safety check (anti-hallucination)**: If the policy snippets are too weak/irrelevant, refuse to answer.  
5. **Build the prompt**: Create a message for the AI that includes (a) rules, (b) role style, (c) policy snippets, (d) user question.  
6. **Call the local AI model (Ollama)**: Send the prompt to `POST /api/chat`. 
7. **Return response**: Give back the answer + evidence snippets + safety notes.

---

## Step-by-step: What happens inside each stage

### 1) FastAPI receives the request
- A user (browser/Swagger UI) sends JSON to your server endpoint like `/chat`. 
- FastAPI validates the request using a schema (Pydantic models) so you get clean structured data (role, query, user_id).

Why this matters: validation stops “bad input” early and keeps the pipeline predictable.

### 2) PII redaction (privacy guard)
Before sending the question to the AI model, the system masks sensitive data:
- Example: `My PAN is ABCDE1234F` becomes `My PAN is <PAN>`. 
- This reduces the risk of leaking private data into logs, prompts, and model outputs.

Why this matters: the project requirements explicitly include “Redact sensitive data.”

### 3) Retrieval: find the right policy text (RAG)
Now the system searches your policy files for text related to the question:
- It breaks large documents into smaller chunks (like small paragraphs). 
- It converts chunks and the question into “searchable vectors” (in this project we use TF‑IDF, a classic text search method). 
- It picks the top matching chunks and treats them as **evidence**. 

Why this matters: RAG improves correctness because the AI is guided by the actual policy text instead of guessing.

### 4) Anti-hallucination safety gate (refusal)
Even with retrieval, sometimes the best match is still weak.
- If the top similarity score is below a threshold, the system refuses: “Insufficient policy context to answer safely.” 
- This is how “Prevent hallucinations” is enforced in code: if we don’t have evidence, we don’t pretend.

Why this matters: hallucinations are most likely when the model has to fill gaps with imagination.

### 5) Role-based prompting (HR vs Employee)
The system changes its “tone and details” depending on the role:
- **Employee role**: simpler explanations + next steps.   
- **HR role**: policy-focused + process and edge cases. 

This is done using a “system prompt” that adds rules and role style before the user message. 

### 6) Call the AI model (Ollama)
Once the prompt is ready, the app calls the local model using Ollama’s chat endpoint:
- URL: `http://localhost:11434/api/chat`   
- The request includes: `model`, `messages`, and typically `stream: false`. 

Why this matters: using a local model keeps costs at zero, matching the “no spend” constraint. 

### 7) Return a transparent response
The API returns a JSON response with:
- `answer`: the final text answer.   
- `evidence`: snippets used to answer (so you can verify it).   
- `redacted_query`: shows that masking happened.   
- `safety_notes`: e.g., “Redacted PAN” or “Refused: insufficient policy evidence.” 

Why this matters: transparency and evidence reduce risk and make debugging easier. 

---

## Two important “loops” in the system

### A) Offline loop: improving knowledge (policy updates)
Whenever you add/update policy documents in `sample_data/policies/`:
- The next time you restart the server, the retriever re-reads documents and rebuilds its search index.   
- Better policy text → better retrieval → better answers. 

### B) Online loop: improving answers (prompt + thresholds)
If the AI gives weak answers:
- Increase evidence quality (write clearer policy text).   
- Increase retrieval `TOP_K_CONTEXT` so more relevant chunks are provided.   
- Adjust refusal threshold so the agent refuses more often rather than hallucinating. 

---

## Mini example (end-to-end)

Question (employee):
> “What are payroll cut-off dates and what gets locked after cut-off?”

Workflow:
- PII redaction: none needed.   
- Retrieval: finds the “payroll cut-off & changes” section in the policy.   
- Safety gate: if that section exists, answer; if policy doesn’t define exact dates, the agent should say it’s not specified and ask HR/Payroll.   
- Output: answer + evidence snippets.
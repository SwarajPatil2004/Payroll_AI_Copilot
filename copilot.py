import json
from pathlib import Path
from typing import Dict, List, Tuple

from config import TOP_K_CONTEXT, MAX_CONTEXT_CHARS, CONFIDENCE_MIN, OLLAMA_BASE_URL, OLLAMA_MODEL
from models import ChatRequest, ChatResponse, EvidenceItem
from redaction import redact_pii
from retrieval import LocalTfidfRetriever, load_policy_corpus
from prompts import system_prompt, build_user_prompt
from llm_ollama import ollama_chat


def _format_context(evidence: List[Tuple[object, float]]) -> str:

    lines: List[str] = []
    for chunk, score in evidence:
        lines.append(f"[SOURCE: {chunk.source} | score={score:.3f}]\n{chunk.text}\n")
    text = "\n".join(lines)
    return text[:MAX_CONTEXT_CHARS]


class PayrollCopilot:

    def __init__(self, policy_folder: str = "sample_data/policies", employee_db_path: str = "sample_data/employees.json"):
        chunks = load_policy_corpus(policy_folder)
        self.retriever = LocalTfidfRetriever(chunks)

        self.employee_db: Dict[str, Dict] = {}
        p = Path(employee_db_path)
        if p.exists():
            self.employee_db = json.loads(p.read_text(encoding="utf-8", errors="ignore"))

    def chat(self, req: ChatRequest) -> ChatResponse:
        
        redacted_query, notes = redact_pii(req.query)

        retrieved = self.retriever.retrieve(redacted_query, top_k=TOP_K_CONTEXT)
        evidence_items = [
            EvidenceItem(source=ch.source, snippet=ch.text[:600], score=score)
            for ch, score in retrieved
        ]

        best_score = max([s for _, s in retrieved], default=0.0)
        if best_score < CONFIDENCE_MIN:
            return ChatResponse(
                answer=(
                    "Insufficient policy context to answer safely. "
                    "Please share the relevant policy section or ask HR/Payroll for confirmation."
                ),
                redacted_query=redacted_query,
                evidence=evidence_items,
                refusal=True,
                safety_notes=notes + ["Refused: insufficient policy evidence"],
            )

        context_block = _format_context(retrieved)
        sys = system_prompt(req.role)
        user = build_user_prompt(redacted_query, context_block, req.locale)

        try:
            answer = ollama_chat(
                base_url=OLLAMA_BASE_URL,
                model=OLLAMA_MODEL,
                system=sys,
                user=user,
            )
        except Exception as e:
            return ChatResponse(
                answer="I'm sorry, I encountered an issue connecting to the AI model. Please try again later.",
                redacted_query=redacted_query,
                evidence=evidence_items,
                refusal=True,
                safety_notes=notes + [f"LLM Error: {str(e)}"],
            )

        return ChatResponse(
            answer=answer.strip(),
            redacted_query=redacted_query,
            evidence=evidence_items,
            refusal=False,
            safety_notes=notes,
        )

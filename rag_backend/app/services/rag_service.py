# rag_service.py
# Ingest → Chunk → Embed → Retrieve → Generate

import datetime
from app.db import SessionLocal
from app.models.knowledge_base import KnowledgeChunk


class RAGService:
    def ingest(self, document):
        """
        Ingest a document chunk into the knowledge base, avoiding duplicates.
        document: dict with keys 'source', 'chunk_id', 'text', and optionally 'category_id', 'topic', 'tags'.
        """
        session = SessionLocal()
        chunk_uid = f"{document['source']}-{document['chunk_id']}"
        try:
            exists = session.query(KnowledgeChunk).filter_by(chunk_id=chunk_uid).first()
            if exists:
                print(f"Chunk {chunk_uid} already exists. Skipping.")
                return False

            chunk = KnowledgeChunk(
                chunk_id=chunk_uid,
                title=document.get('source', ''),
                content=document.get('text', ''),
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow(),
                category_id=document.get('category_id'),
                topic=document.get('topic'),
                tags=document.get('tags')
            )
            session.add(chunk)
            session.commit()
            print(f"Ingested chunk {chunk_uid}")
            return True
        except Exception as e:
            session.rollback()
            print(f"Error ingesting chunk {chunk_uid}: {e}")
            return False
        finally:
            session.close()

    def chunk(self, document):
        # Placeholder for chunking logic
        pass

    def embed(self, chunks):
        # Placeholder for embedding logic
        pass

    def retrieve(self, query):
        # Placeholder for retrieval logic
        pass

    async def generate(self, context: str, question: str, system_prompt: str | None = None) -> str:
        """
        Generate an answer using the LM Studio HTTP endpoint only.

        google/gemma-4-E4B-it must be loaded in LM Studio with the server
        started on port 1234.
        """
        from app.core.config import settings

        resolved_system_prompt = (
            system_prompt
            or "You are a helpful assistant for an employee onboarding guide."
        )
        messages = [
            {"role": "system", "content": resolved_system_prompt},
            {
                "role": "user",
                "content": (
                    f"Use the following context to answer the question.\n\n"
                    f"Context:\n{context}\n\n"
                    f"Question: {question}"
                ),
            },
        ]

        try:
            return await self._generate_via_openai_compat(messages, settings)
        except Exception as exc:
            import httpx

            _UNAVAILABLE = (
                "The AI model is currently unavailable. "
                "Please start LM Studio (port 1234) or Ollama (port 11434) with "
                "the gemma4 model loaded, then try again."
            )
            _UNAUTHORIZED = (
                "LM Studio rejected the request with 401 Unauthorized. "
                "Check the LM Studio server settings and any required API key, "
                "then try again."
            )
            if isinstance(exc, httpx.HTTPStatusError):
                if exc.response.status_code == 401:
                    try:
                        return await self._generate_via_ollama(messages, settings)
                    except Exception:
                        return _UNAUTHORIZED
                try:
                    return await self._generate_via_ollama(messages, settings)
                except Exception:
                    return (
                        f"LM Studio request failed with status {exc.response.status_code}, "
                        "and Ollama fallback was unavailable. "
                        "Check LM Studio/Ollama model configuration, then try again."
                    )
            # httpx connection errors — try Ollama before giving up
            _is_conn_error = (
                isinstance(exc, (httpx.ConnectError, httpx.ConnectTimeout, OSError))
                or (
                    getattr(exc, "exceptions", None)
                    and any(isinstance(e, OSError) for e in exc.exceptions)
                )
            )
            if _is_conn_error:
                try:
                    return await self._generate_via_ollama(messages, settings)
                except Exception:
                    return _UNAVAILABLE
            raise

    # Hugging Face/local transformers support is intentionally disabled.
    # Keep this implementation commented out for now so all responses route
    # through LM Studio.
    async def _generate_via_transformers(self, messages: list, settings) -> str:
        """
        Run google/gemma-4-E4B-it locally using AutoProcessor + AutoModelForCausalLM.
        Follows the official Gemma 4 usage pattern.
        The synchronous model call is offloaded to a thread pool to avoid blocking
        the async event loop.
        """
        import asyncio
        from functools import partial

        def _run() -> str:
            from transformers import AutoProcessor, AutoModelForCausalLM

            processor = AutoProcessor.from_pretrained(settings.LLM_MODEL_NAME)
            model = AutoModelForCausalLM.from_pretrained(
                settings.LLM_MODEL_NAME,
                dtype="auto",
                device_map="auto",
            )

            text = processor.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
            inputs = processor(text=text, return_tensors="pt").to(model.device)
            input_len = inputs["input_ids"].shape[-1]

            outputs = model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=1.0,
                top_p=0.95,
                top_k=64,
                do_sample=True,
            )
            response = processor.decode(outputs[0][input_len:], skip_special_tokens=False)
            return processor.parse_response(response)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _run)

    async def _generate_via_openai_compat(self, messages: list, settings) -> str:
        """Use LM Studio's OpenAI-compatible REST API (/v1/chat/completions)."""
        import httpx

        url = f"{settings.LM_STUDIO_BASE_URL}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        if settings.LLM_API_KEY and settings.LLM_API_KEY.strip():
            headers["Authorization"] = f"Bearer {settings.LLM_API_KEY.strip()}"
        payload = {
            "model": settings.LM_STUDIO_MODEL,
            "messages": messages,
            "max_tokens": 512,
            "temperature": 1.0,
            "top_p": 0.95,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

    async def _generate_via_ollama(self, messages: list, settings) -> str:
        """Use Ollama's OpenAI-compatible REST API as a fallback for LM Studio."""
        import httpx

        url = f"{settings.OLLAMA_BASE_URL}/v1/chat/completions"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": messages,
            "max_tokens": 512,
            "temperature": 1.0,
            "top_p": 0.95,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

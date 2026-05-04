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

    async def generate(self, context: str, question: str) -> str:
        """
        Generate an answer using the configured LLM provider.

        LLM_PROVIDER=lmstudio (default):
            google/gemma-4-E4B-it must be loaded in LM Studio with the server
            started on port 1234. Routes to MCP (LM_STUDIO_USE_MCP=true) or
            the plain OpenAI-compatible endpoint (LM_STUDIO_USE_MCP=false).

        LLM_PROVIDER=huggingface:
            Runs google/gemma-4-E4B-it locally via the transformers library using
            AutoProcessor + AutoModelForCausalLM. Requires sufficient RAM/VRAM.
        """
        from app.core.config import settings

        system_prompt = "You are a helpful assistant for an employee onboarding guide."
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Use the following context to answer the question.\n\n"
                    f"Context:\n{context}\n\n"
                    f"Question: {question}"
                ),
            },
        ]

        if settings.LLM_PROVIDER == "huggingface":
            return await self._generate_via_transformers(messages, settings)

        # lmstudio provider
        if settings.LM_STUDIO_USE_MCP:
            return await self._generate_via_mcp(messages, settings)
        return await self._generate_via_openai_compat(messages, settings)

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

    async def _generate_via_mcp(self, messages: list, settings) -> str:
        """Use LM Studio's MCP SSE endpoint (supports tool-calling)."""
        from mcp import ClientSession
        from mcp.client.sse import sse_client
        from mcp.types import TextContent, SamplingMessage

        # Combine all messages into a single user prompt for MCP sampling
        prompt = "\n".join(
            f"{m['role'].capitalize()}: {m['content']}" for m in messages
        )

        async with sse_client(settings.LM_STUDIO_MCP_URL) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.create_message(
                    messages=[
                        SamplingMessage(
                            role="user",
                            content=TextContent(type="text", text=prompt),
                        )
                    ],
                    max_tokens=512,
                )
                content = result.content
                if hasattr(content, "text"):
                    return content.text
                return str(content)

    async def _generate_via_openai_compat(self, messages: list, settings) -> str:
        """Use LM Studio's OpenAI-compatible REST API (/v1/chat/completions)."""
        import httpx

        url = f"{settings.LM_STUDIO_BASE_URL}/v1/chat/completions"
        payload = {
            "model": settings.LM_STUDIO_MODEL,
            "messages": messages,
            "max_tokens": 512,
            "temperature": 1.0,
            "top_p": 0.95,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

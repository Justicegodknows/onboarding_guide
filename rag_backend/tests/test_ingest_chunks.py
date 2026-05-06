from app.services import ingest_chunks as ingest_module


class _DummyRAG:
    def ingest(self, document):
        return True


def test_ingest_chunks_falls_back_to_local(monkeypatch):
    local_chunks = [{"source": "local", "chunk_id": 1, "text": "hello"}]

    def _raise_drive_error():
        raise RuntimeError("drive unavailable")

    monkeypatch.setattr(ingest_module, "_load_google_drive_chunks", _raise_drive_error)
    monkeypatch.setattr(
        ingest_module,
        "_load_local_chunks",
        lambda: (local_chunks, {"source": "local", "chunk_count": len(local_chunks)}),
    )
    monkeypatch.setattr(ingest_module, "RAGService", lambda: _DummyRAG())

    result = ingest_module.ingest_chunks(source="google_drive", allow_local_fallback=True)

    assert result["status"] == "success"
    assert result["ingest_source"] == "local"
    assert result["ingested"] == 1
    assert "fallback_reason" in result["meta"]


def test_ingest_chunks_rejects_unknown_source():
    try:
        ingest_module.ingest_chunks(source="not-valid")
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "source must be either" in str(exc)

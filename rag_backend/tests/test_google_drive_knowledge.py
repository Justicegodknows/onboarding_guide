from unittest.mock import MagicMock, patch

from app.services.google_drive_knowledge import GoogleDriveKnowledgeService


def test_extract_folder_id_from_drive_url():
    folder_url = (
        "https://drive.google.com/drive/folders/"
        "1vN7M2R14vNXCKvU2Y0ouCWeVZnuTEjAP?usp=drive_link"
    )
    folder_id = GoogleDriveKnowledgeService._extract_folder_id(folder_url)
    assert folder_id == "1vN7M2R14vNXCKvU2Y0ouCWeVZnuTEjAP"


def test_extract_folder_id_from_raw_id():
    folder_id = "1vN7M2R14vNXCKvU2Y0ouCWeVZnuTEjAP"
    assert GoogleDriveKnowledgeService._extract_folder_id(folder_id) == folder_id


def test_service_resolves_folder_id_from_url_when_id_missing():
    service = GoogleDriveKnowledgeService(
        api_key="dummy",
        folder_id="",
        folder_url=(
            "https://drive.google.com/drive/folders/"
            "1vN7M2R14vNXCKvU2Y0ouCWeVZnuTEjAP?usp=drive_link"
        ),
    )
    assert service.folder_id == "1vN7M2R14vNXCKvU2Y0ouCWeVZnuTEjAP"


def test_service_is_configured_with_service_account_file():
    with patch.object(
        GoogleDriveKnowledgeService,
        "_build_drive_service",
        return_value=MagicMock(),
    ):
        service = GoogleDriveKnowledgeService(
            api_key="",
            service_account_file="/tmp/google-drive.json",
            folder_id="folder-123",
        )

    assert service.configured is True


def test_request_json_uses_drive_client_with_service_account():
    mock_execute = MagicMock(return_value={"files": []})
    mock_files = MagicMock()
    mock_files.list.return_value.execute = mock_execute
    mock_drive_service = MagicMock()
    mock_drive_service.files.return_value = mock_files

    with patch.object(
        GoogleDriveKnowledgeService,
        "_build_drive_service",
        return_value=mock_drive_service,
    ):
        service = GoogleDriveKnowledgeService(
            api_key="",
            service_account_file="/tmp/google-drive.json",
            folder_id="folder-123",
        )

    result = service._request_json("/files", {"q": "'folder-123' in parents"})

    assert result == {"files": []}
    mock_files.list.assert_called_once_with(q="'folder-123' in parents")


def test_build_media_metadata_text_includes_core_fields():
    text = GoogleDriveKnowledgeService._build_media_metadata_text(
        {
            "name": "intro-video.mp4",
            "mimeType": "video/mp4",
            "webViewLink": "https://drive.google.com/file/d/abc/view",
            "modifiedTime": "2026-05-04T10:00:00.000Z",
            "size": "12345",
            "description": "Onboarding intro video",
        }
    )
    assert "video/mp4" in text
    assert "intro-video.mp4" in text
    assert "Open link" in text


# ---------------------------------------------------------------------------
# Image OCR tests
# ---------------------------------------------------------------------------

def test_extract_image_ocr_returns_text_when_ocr_available():
    """When pytesseract is available, extracted text is returned."""
    fake_image = MagicMock()
    with (
        patch("app.services.google_drive_knowledge._OCR_AVAILABLE", True),
        patch("app.services.google_drive_knowledge._PILImage") as mock_pil,
        patch("app.services.google_drive_knowledge.pytesseract") as mock_tess,
    ):
        mock_pil.open.return_value = fake_image
        mock_tess.image_to_string.return_value = "  Welcome to the company!  "
        result = GoogleDriveKnowledgeService._extract_image_ocr(b"fake-image-bytes")
    assert result == "Welcome to the company!"


def test_extract_image_ocr_returns_empty_when_unavailable():
    """When pytesseract is not installed, returns empty string."""
    with patch("app.services.google_drive_knowledge._OCR_AVAILABLE", False):
        result = GoogleDriveKnowledgeService._extract_image_ocr(b"fake")
    assert result == ""


def test_download_file_text_returns_ocr_text_for_image():
    """_download_file_text uses OCR result when OCR succeeds for image files."""
    service = GoogleDriveKnowledgeService(api_key="dummy", folder_id="dummy")
    file_meta = {
        "id": "img-id",
        "name": "org-chart.png",
        "mimeType": "image/png",
        "webViewLink": "https://drive.google.com/file/d/img-id/view",
    }
    with (
        patch.object(service, "_request_bytes", return_value=b"png-bytes"),
        patch.object(service, "_extract_image_ocr", return_value="CEO: Alice\nCTO: Bob"),
    ):
        text = service._download_file_text(file_meta)
    assert text == "CEO: Alice\nCTO: Bob"


def test_download_file_text_falls_back_to_metadata_when_ocr_empty():
    """_download_file_text returns metadata fallback when OCR yields nothing."""
    service = GoogleDriveKnowledgeService(api_key="dummy", folder_id="dummy")
    file_meta = {
        "id": "img-id",
        "name": "logo.jpg",
        "mimeType": "image/jpeg",
        "webViewLink": "https://drive.google.com/file/d/img-id/view",
    }
    with (
        patch.object(service, "_request_bytes", return_value=b"jpg-bytes"),
        patch.object(service, "_extract_image_ocr", return_value=""),
    ):
        text = service._download_file_text(file_meta)
    assert "image/jpeg" in text
    assert "logo.jpg" in text


# ---------------------------------------------------------------------------
# Audio transcription tests
# ---------------------------------------------------------------------------

def test_transcribe_audio_bytes_returns_empty_when_whisper_unavailable():
    with patch("app.services.google_drive_knowledge._WHISPER_AVAILABLE", False):
        result = GoogleDriveKnowledgeService._transcribe_audio_bytes(b"audio")
    assert result == ""


def test_download_file_text_returns_transcript_for_audio():
    """_download_file_text uses Whisper transcript for audio files."""
    service = GoogleDriveKnowledgeService(api_key="dummy", folder_id="dummy")
    file_meta = {
        "id": "aud-id",
        "name": "training.mp3",
        "mimeType": "audio/mpeg",
        "webViewLink": "https://drive.google.com/file/d/aud-id/view",
    }
    with (
        patch.object(service, "_request_bytes", return_value=b"mp3-bytes"),
        patch.object(service, "_transcribe_audio_bytes", return_value="Hello and welcome."),
    ):
        text = service._download_file_text(file_meta)
    assert text == "Hello and welcome."


def test_download_file_text_falls_back_to_metadata_when_transcript_empty():
    """_download_file_text returns metadata fallback when transcription yields nothing."""
    service = GoogleDriveKnowledgeService(api_key="dummy", folder_id="dummy")
    file_meta = {
        "id": "aud-id",
        "name": "silence.wav",
        "mimeType": "audio/wav",
        "webViewLink": "https://drive.google.com/file/d/aud-id/view",
    }
    with (
        patch.object(service, "_request_bytes", return_value=b"wav-bytes"),
        patch.object(service, "_transcribe_audio_bytes", return_value=""),
    ):
        text = service._download_file_text(file_meta)
    assert "audio/wav" in text
    assert "silence.wav" in text


# ---------------------------------------------------------------------------
# Video transcription tests
# ---------------------------------------------------------------------------

def test_extract_video_transcription_returns_empty_when_whisper_unavailable():
    with patch("app.services.google_drive_knowledge._WHISPER_AVAILABLE", False):
        result = GoogleDriveKnowledgeService._extract_video_transcription(b"video")
    assert result == ""


def test_download_file_text_returns_transcript_for_video():
    """_download_file_text uses Whisper transcript for video files."""
    service = GoogleDriveKnowledgeService(api_key="dummy", folder_id="dummy")
    file_meta = {
        "id": "vid-id",
        "name": "onboarding.mp4",
        "mimeType": "video/mp4",
        "webViewLink": "https://drive.google.com/file/d/vid-id/view",
    }
    with (
        patch.object(service, "_request_bytes", return_value=b"mp4-bytes"),
        patch.object(service, "_extract_video_transcription", return_value="Welcome aboard!"),
    ):
        text = service._download_file_text(file_meta)
    assert text == "Welcome aboard!"


def test_download_file_text_falls_back_to_metadata_when_video_transcript_empty():
    service = GoogleDriveKnowledgeService(api_key="dummy", folder_id="dummy")
    file_meta = {
        "id": "vid-id",
        "name": "demo.webm",
        "mimeType": "video/webm",
        "webViewLink": "https://drive.google.com/file/d/vid-id/view",
    }
    with (
        patch.object(service, "_request_bytes", return_value=b"webm-bytes"),
        patch.object(service, "_extract_video_transcription", return_value=""),
    ):
        text = service._download_file_text(file_meta)
    assert "video/webm" in text
    assert "demo.webm" in text

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


def test_download_file_text_uses_media_metadata_for_images():
    service = GoogleDriveKnowledgeService(api_key="dummy", folder_id="dummy")
    text = service._download_file_text(
        {
            "id": "img-id",
            "name": "org-chart.png",
            "mimeType": "image/png",
            "webViewLink": "https://drive.google.com/file/d/img-id/view",
        }
    )
    assert "image/png" in text
    assert "org-chart.png" in text

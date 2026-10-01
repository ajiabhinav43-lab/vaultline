import re
from io import BytesIO

from tests.conftest import register, login


def _upload_pdf(client, filename="report.pdf", content=b"%PDF-1.4 test content"):
    return client.post("/documents/upload", data={
        "file": (BytesIO(content), filename),
    }, content_type="multipart/form-data", follow_redirects=True)


def _extract_doc_id(html):
    m = re.search(r"/documents/view/(\d+)", html)
    return int(m.group(1)) if m else None


def test_upload_appears_on_dashboard(client):
    register(client, "Abhinav Kumar", "abhinav@example.com")
    login(client, "abhinav@example.com")
    resp = _upload_pdf(client)
    assert "uploaded successfully" in resp.get_data(as_text=True)
    assert "report.pdf" in resp.get_data(as_text=True)


def test_upload_rejects_disallowed_extension(client):
    register(client, "Abhinav Kumar", "abhinav@example.com")
    login(client, "abhinav@example.com")
    resp = _upload_pdf(client, filename="virus.exe", content=b"MZ...")
    assert "not permitted" in resp.get_data(as_text=True)


def test_upload_rejects_empty_file(client):
    register(client, "Abhinav Kumar", "abhinav@example.com")
    login(client, "abhinav@example.com")
    resp = _upload_pdf(client, content=b"")
    assert "empty" in resp.get_data(as_text=True).lower()


def test_owner_can_view_and_download(client):
    register(client, "Abhinav Kumar", "abhinav@example.com")
    login(client, "abhinav@example.com")
    resp = _upload_pdf(client)
    doc_id = _extract_doc_id(resp.get_data(as_text=True))
    assert doc_id is not None

    view_resp = client.get(f"/documents/view/{doc_id}")
    assert view_resp.status_code == 200

    download_resp = client.get(f"/documents/download/{doc_id}")
    assert download_resp.status_code == 200


def test_stranger_cannot_view_others_document(client):
    register(client, "Abhinav Kumar", "abhinav@example.com")
    login(client, "abhinav@example.com")
    resp = _upload_pdf(client)
    doc_id = _extract_doc_id(resp.get_data(as_text=True))
    client.get("/logout")

    register(client, "Rahul Sharma", "rahul@example.com")
    login(client, "rahul@example.com")
    resp = client.get(f"/documents/view/{doc_id}")
    assert resp.status_code == 403


def test_owner_can_delete_document(client):
    register(client, "Abhinav Kumar", "abhinav@example.com")
    login(client, "abhinav@example.com")
    resp = _upload_pdf(client)
    doc_id = _extract_doc_id(resp.get_data(as_text=True))

    del_resp = client.post(f"/documents/delete/{doc_id}", follow_redirects=True)
    assert "deleted" in del_resp.get_data(as_text=True)

    dashboard_html = client.get("/dashboard").get_data(as_text=True)
    assert "report.pdf" not in dashboard_html


def test_non_owner_cannot_delete_document(client):
    register(client, "Abhinav Kumar", "abhinav@example.com")
    login(client, "abhinav@example.com")
    resp = _upload_pdf(client)
    doc_id = _extract_doc_id(resp.get_data(as_text=True))
    client.get("/logout")

    register(client, "Rahul Sharma", "rahul@example.com")
    login(client, "rahul@example.com")
    resp = client.post(f"/documents/delete/{doc_id}")
    assert resp.status_code == 403

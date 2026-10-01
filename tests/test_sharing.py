import re
from io import BytesIO

from tests.conftest import register, login


def _upload_pdf(client, filename="certificate.pdf"):
    resp = client.post("/documents/upload", data={
        "file": (BytesIO(b"%PDF-1.4 test content"), filename),
    }, content_type="multipart/form-data", follow_redirects=True)
    m = re.search(r"/documents/view/(\d+)", resp.get_data(as_text=True))
    return int(m.group(1))


def _share(client, doc_id, recipient_email, permission="VIEW", expires_in="7d"):
    return client.post(f"/share/{doc_id}", data={
        "recipient_email": recipient_email,
        "permission": permission,
        "expires_in": expires_in,
    }, follow_redirects=True)


def _register_both(client):
    register(client, "Abhinav Kumar", "abhinav@example.com")
    client.get("/logout")
    register(client, "Rahul Sharma", "rahul@example.com")
    client.get("/logout")


def test_share_view_only_blocks_download(client):
    _register_both(client)
    login(client, "abhinav@example.com")
    doc_id = _upload_pdf(client)
    resp = _share(client, doc_id, "rahul@example.com", permission="VIEW")
    assert "shared with rahul@example.com" in resp.get_data(as_text=True)
    client.get("/logout")

    login(client, "rahul@example.com")
    view_resp = client.get(f"/documents/view/{doc_id}")
    assert view_resp.status_code == 200

    download_resp = client.get(f"/documents/download/{doc_id}")
    assert download_resp.status_code == 403


def test_share_download_permission_allows_download(client):
    _register_both(client)
    login(client, "abhinav@example.com")
    doc_id = _upload_pdf(client)
    _share(client, doc_id, "rahul@example.com", permission="DOWNLOAD")
    client.get("/logout")

    login(client, "rahul@example.com")
    download_resp = client.get(f"/documents/download/{doc_id}")
    assert download_resp.status_code == 200


def test_revoked_share_blocks_access(client):
    _register_both(client)
    login(client, "abhinav@example.com")
    doc_id = _upload_pdf(client)
    _share(client, doc_id, "rahul@example.com", permission="VIEW")

    shares_html = client.get(f"/documents/{doc_id}/shares").get_data(as_text=True)
    m = re.search(r"/shares/revoke/(\d+)", shares_html)
    assert m is not None, shares_html
    share_id = int(m.group(1))
    client.post(f"/shares/revoke/{share_id}", follow_redirects=True)
    client.get("/logout")

    login(client, "rahul@example.com")
    resp = client.get(f"/documents/view/{doc_id}")
    assert resp.status_code == 403


def test_cannot_share_with_unregistered_email(client):
    register(client, "Abhinav Kumar", "abhinav@example.com")
    login(client, "abhinav@example.com")
    doc_id = _upload_pdf(client)
    resp = _share(client, doc_id, "nobody@example.com")
    assert "No user with this email" in resp.get_data(as_text=True)


def test_non_owner_cannot_share_document(client):
    _register_both(client)
    login(client, "abhinav@example.com")
    doc_id = _upload_pdf(client)
    client.get("/logout")

    login(client, "rahul@example.com")
    resp = client.get(f"/share/{doc_id}")
    assert resp.status_code == 403

import http.client
import json
import threading
from contextlib import contextmanager

from openscribe.project import add_scene, create_chapter, create_part, init_project
from openscribe.word import export_word
from openscribe.word_bridge import WordBridge, write_addin_manifest


@contextmanager
def running_bridge(tmp_path):
    root = init_project(tmp_path, "Synthetic bridge")
    create_part(root, "Opening")
    create_chapter(root, "Arrival")
    add_scene(root, "Arrival", "Station", "Synthetic text.")
    payload = export_word(root, root / "build" / "roundtrip.docx").read_bytes()
    with WordBridge(root) as bridge:
        thread = threading.Thread(target=bridge.serve_forever, daemon=True)
        thread.start()
        try:
            yield bridge, payload
        finally:
            bridge.shutdown()
            thread.join(3)


def request(bridge, path, body, *, token=None, origin=None, extra=None):
    connection = http.client.HTTPConnection("127.0.0.1", bridge.server_port, timeout=5)
    headers = {"Authorization": "Bearer " + (token if token is not None else bridge.token),
               "Origin": origin if origin is not None else bridge.origin}
    headers.update(extra or {})
    try:
        connection.request("POST", path, body=body, headers=headers)
        response = connection.getresponse()
        return response.status, json.loads(response.read())
    finally:
        connection.close()


def test_bridge_preview_apply_and_replay_protection(tmp_path):
    with running_bridge(tmp_path) as (bridge, payload):
        status, preview = request(bridge, "/preview", payload)
        assert status == 200
        assert not preview["blocked"]
        request_body = json.dumps({"preview_id": preview["preview_id"], "document_hash": preview["document_hash"]})
        status, applied = request(bridge, "/apply", request_body)
        assert status == 200
        assert applied == {"applied": 0, "backup": None}
        assert request(bridge, "/apply", request_body)[0] == 400


def test_bridge_rejects_token_origin_host_size_and_project_injection(tmp_path):
    with running_bridge(tmp_path) as (bridge, payload):
        for _ in range(3):
            assert request(bridge, "/preview", payload, token="wrong")[0] == 401
            assert request(bridge, "/preview", payload, origin="https://unapproved.example.test")[0] == 403
            assert request(bridge, "/preview", payload, extra={"Host": "unapproved.example.test"})[0] == 403
        assert request(bridge, "/preview", b"", extra={"Content-Length": str(21 * 1024 * 1024)})[0] == 413
        assert request(bridge, "/unknown", payload)[0] == 404
        assert request(bridge, "/apply", json.dumps({"root": "C:/outside"}))[0] == 400
        assert request(bridge, "/preview", b"not a docx")[0] == 400


def test_bridge_serves_only_packaged_assets_and_requires_tls_for_manifest(tmp_path):
    import pytest

    with running_bridge(tmp_path) as (bridge, _):
        connection = http.client.HTTPConnection("127.0.0.1", bridge.server_port, timeout=5)
        connection.request("GET", "/taskpane.html")
        response = connection.getresponse()
        assert response.status == 200
        assert b"Local bridge session token" in response.read()
        connection.close()
        connection = http.client.HTTPConnection("127.0.0.1", bridge.server_port, timeout=5)
        connection.request("GET", "/../../project.yaml")
        response = connection.getresponse()
        assert response.status == 404
        response.read()
        connection.close()
        with pytest.raises(ValueError, match="requires HTTPS"):
            write_addin_manifest(bridge, tmp_path / "manifest.xml")

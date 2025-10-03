import io
import pytest


@pytest.mark.e2e
@pytest.mark.asyncio
class TestKnowledgeBaseE2E:
    async def test_full_flow(
        self,
        app,
        client,
        mcp_client,
        patch_external_services,
        api_key_value,
    ):
        """
        End-to-end flow:
        - Create KB
        - List KBs
        - Upload doc
        - Preview chunks
        - Process doc
        - Query KB via MCP
        - Delete KB
        """
        headers = {"Authorization": f"API-Key {api_key_value}"}

        # 1. Create KB
        create_url = app.url_path_for("v1_create_knowledge_base")
        resp = await client.post(
            create_url,
            json={"name": "E2E KB", "description": "test kb"},
            headers=headers,
        )
        assert resp.status_code == 200
        kb = resp.json()
        kb_id = kb["id"]

        # 2. List KBs
        list_url = app.url_path_for("v1_list_knowledge_bases")
        resp = await client.get(list_url, headers=headers)
        assert resp.status_code == 200
        assert any(k["id"] == kb_id for k in resp.json())

        # 3. Upload doc
        upload_url = app.url_path_for(
            "v1_upload_kb_documents", kb_id=str(kb_id)
        )
        file_content = b"Hello KB content"
        files = {"files": ("doc1.txt", io.BytesIO(file_content), "text/plain")}
        resp = await client.post(upload_url, files=files, headers=headers)
        assert resp.status_code == 200
        upload_results = resp.json()
        upload_id = upload_results[0]["upload_id"]

        # 4. Preview chunks
        preview_url = app.url_path_for(
            "v1_preview_kb_documents", kb_id=str(kb_id)
        )
        resp = await client.post(
            preview_url,
            json={
                "document_ids": [upload_id],
                "chunk_size": 200,
                "chunk_overlap": 50,
            },
            headers=headers,
        )
        assert resp.status_code == 200
        preview = resp.json()
        assert str(upload_id) in preview

        # 5. Process doc
        process_url = app.url_path_for(
            "v1_process_kb_documents", kb_id=str(kb_id)
        )
        resp = await client.post(
            process_url, json=upload_results, headers=headers
        )
        assert resp.status_code == 200
        tasks = resp.json()["tasks"]
        assert tasks

        # 6. Query KB via MCP
        res = await mcp_client.call_tool(
            "query_knowledge_base",
            {"query": "hello", "knowledge_base_ids": [kb_id], "top_k": 1},
        )
        assert "context" in res.data

        # 7. Delete KB
        delete_url = app.url_path_for(
            "v1_delete_knowledge_base", kb_id=str(kb_id)
        )
        resp = await client.delete(delete_url, headers=headers)
        assert resp.status_code == 200
        assert "deleted" in resp.text.lower()

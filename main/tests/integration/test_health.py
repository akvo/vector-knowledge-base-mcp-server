import pytest
from fastapi import FastAPI
from httpx import AsyncClient


class TestHealth:
    @pytest.mark.asyncio
    async def test_health_check(
        self, app: FastAPI, client: AsyncClient
    ) -> None:
        res = await client.get(app.url_path_for("dev:health"))
        assert res.status_code == 200
        assert res.json() == {"result": "ok"}

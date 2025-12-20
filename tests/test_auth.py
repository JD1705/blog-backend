import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@patch("src.services.auth_services.db.users", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_register_user_successfully(mock_collection):
    mock_collection.find_one = AsyncMock(return_value=None)

    fixed_date = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    with patch("src.services.auth_services.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_date
        mock_datetime.timezone.utc = timezone.utc

    with patch("src.services.auth_services.hash_password") as mock_hash:
        mock_hash.return_value = "hashed_password_123"

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/auth/register",
            json={
                "email": "testemail@example.com",
                "username": "test_user",
                "password": "12345",
                "confirm_password": "12345",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "test_user"
    mock_collection.find_one.assert_called_once_with({"email": "testemail@example.com"})


@patch("src.services.auth_services.db.users", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_register_user_already_exists(mock_collection):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/auth/register",
            json={
                "email": "testemail@example.com",
                "username": "test_user",
                "password": "12345",
                "confirm_password": "12345",
            },
        )

    assert response.status_code == 409
    data = response.json()
    assert data["detail"] == "User Already Exist"
    mock_collection.find_one.assert_called_once_with({"email": "testemail@example.com"})

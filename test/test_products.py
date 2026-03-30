"""
Tests for product CRUD endpoints.
"""
import pytest
from httpx import AsyncClient


PRODUCT_PAYLOAD = {
    "sku": "TEST-001",
    "name": "Test Widget",
    "cost_price": "5.00",
    "selling_price": "12.99",
    "current_stock": 100,
    "reorder_point": 20,
    "reorder_quantity": 50,
    "max_stock": 500,
}


@pytest.mark.asyncio
async def test_create_product(client: AsyncClient, admin_user, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = await client.post("/api/v1/products", json=PRODUCT_PAYLOAD, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["sku"] == "TEST-001"
    assert data["current_stock"] == 100
    assert data["is_low_stock"] is False


@pytest.mark.asyncio
async def test_create_duplicate_sku(client: AsyncClient, admin_user, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    await client.post("/api/v1/products", json=PRODUCT_PAYLOAD, headers=headers)
    resp = await client.post("/api/v1/products", json=PRODUCT_PAYLOAD, headers=headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_products(client: AsyncClient, admin_user, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    await client.post("/api/v1/products", json=PRODUCT_PAYLOAD, headers=headers)
    resp = await client.get("/api/v1/products", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body
    assert body["total"] >= 1


@pytest.mark.asyncio
async def test_get_product_by_id(client: AsyncClient, admin_user, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    create_resp = await client.post(
        "/api/v1/products", json=PRODUCT_PAYLOAD, headers=headers
    )
    pid = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/products/{pid}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == pid


@pytest.mark.asyncio
async def test_update_product(client: AsyncClient, admin_user, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    create_resp = await client.post(
        "/api/v1/products", json=PRODUCT_PAYLOAD, headers=headers
    )
    pid = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/products/{pid}",
        json={"name": "Updated Widget", "selling_price": "15.99"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Widget"


@pytest.mark.asyncio
async def test_adjust_stock(client: AsyncClient, admin_user, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {**PRODUCT_PAYLOAD, "sku": "STOCK-ADJ-001"}
    create_resp = await client.post("/api/v1/products", json=payload, headers=headers)
    pid = create_resp.json()["id"]
    initial_stock = create_resp.json()["current_stock"]

    resp = await client.post(
        f"/api/v1/products/{pid}/adjust-stock",
        json={"adjustment": -10, "reason": "manual correction"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["current_stock"] == initial_stock - 10


@pytest.mark.asyncio
async def test_delete_product(client: AsyncClient, admin_user, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {**PRODUCT_PAYLOAD, "sku": "DEL-001"}
    create_resp = await client.post("/api/v1/products", json=payload, headers=headers)
    pid = create_resp.json()["id"]

    resp = await client.delete(f"/api/v1/products/{pid}", headers=headers)
    assert resp.status_code == 200

    # Soft-deleted: should not appear in active list
    list_resp = await client.get("/api/v1/products?active_only=true", headers=headers)
    ids = [p["id"] for p in list_resp.json()["items"]]
    assert pid not in ids


@pytest.mark.asyncio
async def test_product_not_found(client: AsyncClient, admin_user, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    import uuid
    resp = await client.get(f"/api/v1/products/{uuid.uuid4()}", headers=headers)
    assert resp.status_code == 404

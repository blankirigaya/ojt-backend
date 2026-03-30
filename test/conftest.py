"""
Pytest configuration and shared fixtures.
Uses an in-memory SQLite database so tests run without PostgreSQL.

Key design decisions:
- Each test gets its own clean DB via function-scoped fixtures
- admin_user uses flush (not commit) so the session rollback on teardown
  keeps the DB clean between tests
"""
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.db.session import Base, get_db
from app.core.security import hash_password
from app.models.user import User, UserRole

# ── One engine per session, tables created once ───────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:?check_same_thread=false"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_tables():
    """Create tables once for the entire test session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    """
    Provide a transactional DB session per test.
    Everything is rolled back after the test so the DB stays clean.
    """
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """Async HTTP test client with the DB dependency overridden."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """
    Insert an admin user using flush (no commit) so the rollback
    at teardown removes it cleanly.
    """
    user = User(
        email=f"admin-{uuid.uuid4().hex[:8]}@test.com",  # unique per test
        full_name="Test Admin",
        hashed_password=hash_password("testpassword123"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, admin_user: User) -> str:
    """Login as the admin user and return the access token."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "testpassword123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]

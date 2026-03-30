#!/usr/bin/env bash
# exit on error
set -o errexit

# Upgrade pip and setuptools to ensure wheel compatibility
python -m pip install --upgrade pip setuptools wheel

# Install dependencies from requirements.txt
# We use --only-binary :all: for heavy packages to avoid compiling from source
python -m pip install -r requirements.txt

# Run database migrations to create tables
echo "Running database migrations..."
python -m alembic upgrade head

# Create initial admin user if it doesn't exist
echo "Seeding initial admin user..."
python -c "
import asyncio
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy import select

async def seed():
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.email == 'admin@warehouse.com')
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            user = User(
                email='admin@warehouse.com',
                hashed_password=get_password_hash('admin123'),
                full_name='Admin User',
                is_active=True,
                is_superuser=True
            )
            db.add(user)
            await db.commit()
            print('✅ Admin created: admin@warehouse.com / admin123')
        else:
            print('Admin already exists.')

asyncio.run(seed())
"

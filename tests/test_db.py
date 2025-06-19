import os
import sys
import pytest
import aiosqlite

# Ensure the project root is on the Python path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Provide dummy environment variables expected by bot.py during import
os.environ.setdefault("BOT_TOKEN", "dummy")
os.environ.setdefault("GUILD_ID", "0")
os.environ.setdefault("CHANNEL_ID", "0")

import bot

@pytest.mark.asyncio
async def test_init_db_creates_table_and_inserts(monkeypatch, tmp_path):
    db_path = tmp_path / "test.db"

    original_connect = aiosqlite.connect

    async def connect_patch(_):
        return await original_connect(db_path)

    monkeypatch.setattr(aiosqlite, "connect", connect_patch)

    await bot.init_db()
    assert bot.db is not None

    # table should exist
    async with bot.db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='developers'"
    ) as cursor:
        row = await cursor.fetchone()
        assert row is not None

    await bot.db.execute(
        "INSERT INTO developers (user_id, primary_role) VALUES (?, ?)",
        ("1", "Block Producer"),
    )
    await bot.db.commit()

    async with bot.db.execute(
        "SELECT primary_role FROM developers WHERE user_id=?",
        ("1",),
    ) as cursor:
        row = await cursor.fetchone()
        assert row[0] == "Block Producer"

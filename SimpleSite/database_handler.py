import asyncio
import aiosqlite


class Database:
    """
    An async SQLite wrapper for use in Quart routes.
    Reads run on a small pool of connections (SQLite allows concurrent readers
    in WAL mode). Writes go through a single connection serialized by a lock,
    since SQLite only allows one writer at a time.
    """

    def __init__(self, path: str = "database.db", read_pool_size: int = 4):
        self.path = path
        self.read_pool_size = read_pool_size
        self._read_pool: asyncio.Queue = None
        self._write_conn: aiosqlite.Connection = None
        self._write_lock = asyncio.Lock()
        self._initialized = False

    async def connect(self):
        """
        Opens the write connection and the read pool. Call once, e.g. during app startup.
        """
        if self._initialized:
            return

        self._write_conn = await aiosqlite.connect(self.path)
        await self._write_conn.execute("PRAGMA journal_mode=WAL")
        await self._write_conn.execute("PRAGMA foreign_keys=ON")
        await self._write_conn.commit()

        self._read_pool = asyncio.Queue()
        for _ in range(self.read_pool_size):
            conn = await aiosqlite.connect(self.path)
            conn.row_factory = aiosqlite.Row
            await conn.execute("PRAGMA journal_mode=WAL")
            await conn.execute("PRAGMA query_only=ON")
            self._read_pool.put_nowait(conn)

        self._initialized = True

    async def close(self):
        """
        Closes the write connection and every pooled read connection.
        """
        if not self._initialized:
            return

        await self._write_conn.close()
        while not self._read_pool.empty():
            conn = self._read_pool.get_nowait()
            await conn.close()

        self._initialized = False

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def query(self, sql: str, params: tuple = ()) -> list[dict]:
        """
        Runs a SELECT on a pooled read connection and returns all rows as dicts.
        """
        conn = await self._read_pool.get()
        try:
            async with conn.execute(sql, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        finally:
            self._read_pool.put_nowait(conn)

    async def query_one(self, sql: str, params: tuple = ()) -> dict | None:
        """
        Runs a SELECT on a pooled read connection and returns the first row as a
        dict, or None if there were no results.
        """
        conn = await self._read_pool.get()
        try:
            async with conn.execute(sql, params) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
        finally:
            self._read_pool.put_nowait(conn)

    async def execute(self, sql: str, params: tuple = ()) -> int:
        """
        Runs an INSERT/UPDATE/DELETE/DDL statement on the write connection.
        Returns the last inserted row id.
        """
        async with self._write_lock:
            cursor = await self._write_conn.execute(sql, params)
            await self._write_conn.commit()
            return cursor.lastrowid

    async def executemany(self, sql: str, seq_of_params) -> None:
        """
        Runs the same statement once per set of params, in one transaction.
        """
        async with self._write_lock:
            await self._write_conn.executemany(sql, seq_of_params)
            await self._write_conn.commit()

    def transaction(self):
        """
        Async context manager for grouping several writes into one atomic
        commit, e.g.:

            async with db.transaction() as conn:
                await conn.execute("INSERT INTO users (name) VALUES (?)", ("Bob",))
                await conn.execute("INSERT INTO logs (msg) VALUES (?)", ("created user",))
        """
        return _Transaction(self)


class _Transaction:
    def __init__(self, db: Database):
        self.db = db

    async def __aenter__(self) -> aiosqlite.Connection:
        await self.db._write_lock.acquire()
        return self.db._write_conn

    async def __aexit__(self, exc_type, exc, tb):
        try:
            if exc_type is None:
                await self.db._write_conn.commit()
            else:
                await self.db._write_conn.rollback()
        finally:
            self.db._write_lock.release()

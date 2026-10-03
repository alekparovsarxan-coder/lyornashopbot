import aiosqlite
from config import DB_PATH
from texts import PRODUCTS

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    price INTEGER NOT NULL,
    photo TEXT NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS cart (
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    qty INTEGER NOT NULL,
    PRIMARY KEY (user_id, product_id)
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT,
    full_name TEXT,
    phone TEXT,
    city TEXT,
    address TEXT,
    comment TEXT,
    pay TEXT,
    total INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER,
    name TEXT NOT NULL,
    price INTEGER NOT NULL,
    qty INTEGER NOT NULL
);
"""

async def db():
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys = ON")
    return conn

async def init_db():
    conn = await db()
    try:
        await conn.executescript(SCHEMA)
        cur = await conn.execute("SELECT COUNT(*) AS c FROM products")
        row = await cur.fetchone()
        if row["c"] == 0:
            await conn.executemany(
                "INSERT INTO products (category, name, description, price, photo, stock, active) VALUES (?, ?, ?, ?, ?, ?, 1)",
                PRODUCTS,
            )
        await conn.commit()
    finally:
        await conn.close()

async def touch_user(user_id: int, username: str | None, full_name: str):
    conn = await db()
    try:
        await conn.execute(
            "INSERT INTO users (user_id, username, full_name) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, full_name=excluded.full_name",
            (user_id, username, full_name),
        )
        await conn.commit()
    finally:
        await conn.close()

async def categories_with_counts():
    conn = await db()
    try:
        cur = await conn.execute(
            "SELECT category, COUNT(*) AS c FROM products WHERE active=1 GROUP BY category"
        )
        return {r["category"]: r["c"] for r in await cur.fetchall()}
    finally:
        await conn.close()

async def list_products(category: str):
    conn = await db()
    try:
        cur = await conn.execute(
            "SELECT * FROM products WHERE category=? AND active=1 ORDER BY id",
            (category,),
        )
        return await cur.fetchall()
    finally:
        await conn.close()

async def get_product(pid: int):
    conn = await db()
    try:
        cur = await conn.execute("SELECT * FROM products WHERE id=?", (pid,))
        return await cur.fetchone()
    finally:
        await conn.close()

async def all_products(include_hidden=True):
    conn = await db()
    try:
        q = "SELECT * FROM products ORDER BY category, id" if include_hidden else "SELECT * FROM products WHERE active=1 ORDER BY category, id"
        cur = await conn.execute(q)
        return await cur.fetchall()
    finally:
        await conn.close()

async def add_to_cart(user_id: int, product_id: int, qty: int = 1):
    conn = await db()
    try:
        await conn.execute(
            "INSERT INTO cart (user_id, product_id, qty) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id, product_id) DO UPDATE SET qty = qty + excluded.qty",
            (user_id, product_id, qty),
        )
        await conn.commit()
    finally:
        await conn.close()

async def set_qty(user_id: int, product_id: int, qty: int):
    conn = await db()
    try:
        if qty <= 0:
            await conn.execute("DELETE FROM cart WHERE user_id=? AND product_id=?", (user_id, product_id))
        else:
            await conn.execute("UPDATE cart SET qty=? WHERE user_id=? AND product_id=?", (qty, user_id, product_id))
        await conn.commit()
    finally:
        await conn.close()

async def clear_cart(user_id: int):
    conn = await db()
    try:
        await conn.execute("DELETE FROM cart WHERE user_id=?", (user_id,))
        await conn.commit()
    finally:
        await conn.close()

async def cart_items(user_id: int):
    conn = await db()
    try:
        cur = await conn.execute(
            """
            SELECT c.qty, p.* FROM cart c
            JOIN products p ON p.id = c.product_id
            WHERE c.user_id=?
            ORDER BY p.id
            """,
            (user_id,),
        )
        return await cur.fetchall()
    finally:
        await conn.close()

async def create_order(user, phone, city, address, comment, pay, items, total) -> int:
    conn = await db()
    try:
        cur = await conn.execute(
            """
            INSERT INTO orders (user_id, username, full_name, phone, city, address, comment, pay, total, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'new')
            """,
            (user.id, user.username, user.full_name, phone, city, address, comment, pay, total),
        )
        oid = cur.lastrowid
        for it in items:
            await conn.execute(
                "INSERT INTO order_items (order_id, product_id, name, price, qty) VALUES (?, ?, ?, ?, ?)",
                (oid, it["id"], it["name"], it["price"], it["qty"]),
            )
            await conn.execute("UPDATE products SET stock = MAX(stock - ?, 0) WHERE id=?", (it["qty"], it["id"]))
        await conn.execute("DELETE FROM cart WHERE user_id=?", (user.id,))
        await conn.commit()
        return oid
    finally:
        await conn.close()

async def list_orders(limit=15):
    conn = await db()
    try:
        cur = await conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,))
        return await cur.fetchall()
    finally:
        await conn.close()

async def get_order(oid: int):
    conn = await db()
    try:
        cur = await conn.execute("SELECT * FROM orders WHERE id=?", (oid,))
        order = await cur.fetchone()
        cur = await conn.execute("SELECT * FROM order_items WHERE order_id=?", (oid,))
        items = await cur.fetchall()
        return order, items
    finally:
        await conn.close()

async def set_order_status(oid: int, status: str):
    conn = await db()
    try:
        await conn.execute("UPDATE orders SET status=? WHERE id=?", (status, oid))
        await conn.commit()
    finally:
        await conn.close()

async def update_product_field(pid: int, field: str, value):
    allowed = {"name", "description", "price", "photo", "stock", "category", "active"}
    if field not in allowed:
        raise ValueError("field")
    conn = await db()
    try:
        await conn.execute(f"UPDATE products SET {field}=? WHERE id=?", (value, pid))
        await conn.commit()
    finally:
        await conn.close()

async def delete_product(pid: int):
    conn = await db()
    try:
        await conn.execute("DELETE FROM cart WHERE product_id=?", (pid,))
        await conn.execute("DELETE FROM products WHERE id=?", (pid,))
        await conn.commit()
    finally:
        await conn.close()

async def insert_product(category, name, description, price, photo, stock):
    conn = await db()
    try:
        cur = await conn.execute(
            "INSERT INTO products (category, name, description, price, photo, stock, active) VALUES (?, ?, ?, ?, ?, ?, 1)",
            (category, name, description, price, photo, stock),
        )
        await conn.commit()
        return cur.lastrowid
    finally:
        await conn.close()

async def stats():
    conn = await db()
    try:
        users = (await (await conn.execute("SELECT COUNT(*) c FROM users")).fetchone())["c"]
        products = (await (await conn.execute("SELECT COUNT(*) c FROM products")).fetchone())["c"]
        orders = (await (await conn.execute("SELECT COUNT(*) c FROM orders")).fetchone())["c"]
        revenue = (await (await conn.execute("SELECT COALESCE(SUM(total),0) s FROM orders WHERE status!='cancelled'")).fetchone())["s"]
        return users, products, orders, revenue
    finally:
        await conn.close()

import aiosqlite
from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gender TEXT NOT NULL,
    mood TEXT NOT NULL,
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    stars INTEGER NOT NULL,
    photo TEXT NOT NULL,
    sizes TEXT NOT NULL,
    colors TEXT NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    gender TEXT,
    mood TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS cart (
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    size TEXT NOT NULL,
    color TEXT NOT NULL,
    qty INTEGER NOT NULL,
    PRIMARY KEY (user_id, product_id, size, color)
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
    stars INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    paid INTEGER NOT NULL DEFAULT 0,
    charge_id TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER,
    name TEXT NOT NULL,
    stars INTEGER NOT NULL,
    size TEXT,
    color TEXT,
    qty INTEGER NOT NULL
);
"""

SEED = [
    ("women", "city", "Одежда", "Пальто «Северный кадр»", "Шерсть, прямой крой, мокрый графит. Для города после полудня.", 220, "https://images.unsplash.com/photo-1539533018447-63fcce2678e3?auto=format&fit=crop&w=1200&q=80", "XS S M L", "графит", 6),
    ("women", "night", "Одежда", "Платье «Линия полуночи»", "Сатин, лодочка, миди. Свет только по кромке.", 180, "https://images.unsplash.com/photo-1566174053879-31528523f8ae?auto=format&fit=crop&w=1200&q=80", "XS S M L", "чёрный", 5),
    ("women", "city", "Обувь", "Лоферы «Архив»", "Замша цвета табака, низкий каблук.", 140, "https://images.unsplash.com/photo-1543163521-1bf539c55dd2?auto=format&fit=crop&w=1200&q=80", "36 37 38 39 40", "табак", 7),
    ("women", "home", "Дом", "Плед «Снег в комнате»", "Меринос, крупная вязка, слоновая кость.", 90, "https://images.unsplash.com/photo-1616628188859-7a11abb6fcc9?auto=format&fit=crop&w=1200&q=80", "one", "молочный", 11),
    ("women", "night", "Красота", "Парфюм «После дождя»", "30 мл. Мокрый камень, лист, тёплая кожа.", 70, "https://images.unsplash.com/photo-1541643600914-78b084683601?auto=format&fit=crop&w=1200&q=80", "30 мл", "дым", 20),
    ("men", "city", "Одежда", "Пальто «Сухой дождь»", "Плотная шерсть, скрытая планка, чуть длиннее классики.", 240, "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?auto=format&fit=crop&w=1200&q=80", "S M L XL", "уголь", 5),
    ("men", "night", "Одежда", "Рубашка «Тихий лён»", "Тёмный лён, роговые пуговицы. Носится открытой.", 95, "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=1200&q=80", "S M L XL", "чёрный", 12),
    ("men", "city", "Обувь", "Ботинки «Мокрый асфальт»", "Кожа, толстая подошва, для длинных переходов.", 190, "https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=1200&q=80", "40 41 42 43 44", "чёрный", 8),
    ("men", "home", "Дом", "Лампа «Низкий свет»", "Латунь и молочное стекло. Свет ложится на стол.", 110, "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=1200&q=80", "one", "латунь", 9),
    ("men", "night", "Аксессуары", "Часы «Одна стрелка»", "Матовый корпус, почти пустой циферблат.", 210, "https://images.unsplash.com/photo-1524805444758-089113d48a6d?auto=format&fit=crop&w=1200&q=80", "one", "графит", 4),
    ("all", "home", "Подарки", "Набор «Первый визит»", "Свеча, открытка ателье, мини-флакон.", 60, "https://images.unsplash.com/photo-1549465220-1a8b9238cd48?auto=format&fit=crop&w=1200&q=80", "one", "ночь", 18),
    ("all", "city", "Аксессуары", "Сумка «Конверт»", "Структурная кожа, магнит вместо замка.", 160, "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?auto=format&fit=crop&w=1200&q=80", "one", "чёрный", 9),
]

async def db():
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    return conn

async def init_db():
    conn = await db()
    try:
        await conn.executescript(SCHEMA)
        cur = await conn.execute("SELECT COUNT(*) c FROM products")
        if (await cur.fetchone())["c"] == 0:
            await conn.executemany(
                "INSERT INTO products (gender, mood, category, name, description, stars, photo, sizes, colors, stock, active) VALUES (?,?,?,?,?,?,?,?,?,?,1)",
                SEED,
            )
        await conn.commit()
    finally:
        await conn.close()

async def touch_user(uid, username, full_name):
    conn = await db()
    try:
        await conn.execute(
            "INSERT INTO users (user_id, username, full_name) VALUES (?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, full_name=excluded.full_name",
            (uid, username, full_name),
        )
        await conn.commit()
    finally:
        await conn.close()

async def set_pref(uid, gender=None, mood=None):
    conn = await db()
    try:
        if gender is not None:
            await conn.execute("UPDATE users SET gender=? WHERE user_id=?", (gender, uid))
        if mood is not None:
            await conn.execute("UPDATE users SET mood=? WHERE user_id=?", (mood, uid))
        await conn.commit()
    finally:
        await conn.close()

async def get_user(uid):
    conn = await db()
    try:
        cur = await conn.execute("SELECT * FROM users WHERE user_id=?", (uid,))
        return await cur.fetchone()
    finally:
        await conn.close()

async def list_products(gender=None, mood=None):
    conn = await db()
    try:
        q = "SELECT * FROM products WHERE active=1"
        args = []
        if gender and gender != "all":
            q += " AND gender IN (?, 'all')"
            args.append(gender)
        if mood and mood != "all":
            q += " AND (mood=? OR mood='all')"
            args.append(mood)
        q += " ORDER BY id"
        cur = await conn.execute(q, args)
        return await cur.fetchall()
    finally:
        await conn.close()

async def get_product(pid):
    conn = await db()
    try:
        cur = await conn.execute("SELECT * FROM products WHERE id=?", (pid,))
        return await cur.fetchone()
    finally:
        await conn.close()

async def all_products():
    conn = await db()
    try:
        cur = await conn.execute("SELECT * FROM products ORDER BY id")
        return await cur.fetchall()
    finally:
        await conn.close()

async def add_to_cart(uid, pid, size, color, qty=1):
    conn = await db()
    try:
        await conn.execute(
            "INSERT INTO cart (user_id, product_id, size, color, qty) VALUES (?,?,?,?,?) "
            "ON CONFLICT(user_id, product_id, size, color) DO UPDATE SET qty=qty+excluded.qty",
            (uid, pid, size, color, qty),
        )
        await conn.commit()
    finally:
        await conn.close()

async def cart_items(uid):
    conn = await db()
    try:
        cur = await conn.execute(
            "SELECT c.qty, c.size, c.color, p.* FROM cart c JOIN products p ON p.id=c.product_id WHERE c.user_id=? ORDER BY p.id",
            (uid,),
        )
        return await cur.fetchall()
    finally:
        await conn.close()

async def clear_cart(uid):
    conn = await db()
    try:
        await conn.execute("DELETE FROM cart WHERE user_id=?", (uid,))
        await conn.commit()
    finally:
        await conn.close()

async def create_order(user, phone, city, address, comment, items, stars):
    conn = await db()
    try:
        cur = await conn.execute(
            "INSERT INTO orders (user_id, username, full_name, phone, city, address, comment, stars, status, paid) VALUES (?,?,?,?,?,?,?,?, 'wait', 0)",
            (user.id, user.username, user.full_name, phone, city, address, comment, stars),
        )
        oid = cur.lastrowid
        for it in items:
            await conn.execute(
                "INSERT INTO order_items (order_id, product_id, name, stars, size, color, qty) VALUES (?,?,?,?,?,?,?)",
                (oid, it["id"], it["name"], it["stars"], it["size"], it["color"], it["qty"]),
            )
        await conn.commit()
        return oid
    finally:
        await conn.close()

async def mark_paid(oid, charge_id):
    conn = await db()
    try:
        cur = await conn.execute("SELECT paid FROM orders WHERE id=?", (oid,))
        row = await cur.fetchone()
        if not row or row["paid"]:
            return False
        await conn.execute("UPDATE orders SET paid=1, status='paid', charge_id=? WHERE id=?", (charge_id, oid))
        cur = await conn.execute("SELECT product_id, qty FROM order_items WHERE order_id=?", (oid,))
        for it in await cur.fetchall():
            await conn.execute("UPDATE products SET stock=MAX(stock-?,0) WHERE id=?", (it["qty"], it["product_id"]))
        await conn.commit()
        return True
    finally:
        await conn.close()

async def get_order(oid):
    conn = await db()
    try:
        cur = await conn.execute("SELECT * FROM orders WHERE id=?", (oid,))
        order = await cur.fetchone()
        cur = await conn.execute("SELECT * FROM order_items WHERE order_id=?", (oid,))
        return order, await cur.fetchall()
    finally:
        await conn.close()

async def user_orders(uid):
    conn = await db()
    try:
        cur = await conn.execute("SELECT * FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 8", (uid,))
        return await cur.fetchall()
    finally:
        await conn.close()

async def list_orders():
    conn = await db()
    try:
        cur = await conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 12")
        return await cur.fetchall()
    finally:
        await conn.close()

async def set_status(oid, status):
    conn = await db()
    try:
        await conn.execute("UPDATE orders SET status=? WHERE id=?", (status, oid))
        await conn.commit()
    finally:
        await conn.close()

async def update_field(pid, field, value):
    if field not in {"name", "description", "stars", "photo", "stock", "active", "gender"}:
        raise ValueError(field)
    conn = await db()
    try:
        await conn.execute(f"UPDATE products SET {field}=? WHERE id=?", (value, pid))
        await conn.commit()
    finally:
        await conn.close()

async def insert_product(gender, name, description, stars, photo, stock):
    conn = await db()
    try:
        cur = await conn.execute(
            "INSERT INTO products (gender, mood, category, name, description, stars, photo, sizes, colors, stock, active) VALUES (?,?,?,?,?,?,?,?,?,?,1)",
            (gender, "city", "Новое", name, description, stars, photo, "one", "—", stock),
        )
        await conn.commit()
        return cur.lastrowid
    finally:
        await conn.close()

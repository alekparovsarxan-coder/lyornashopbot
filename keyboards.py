from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from texts import CATEGORIES, CAT_MAP
from config import CURRENCY

def money(n: int) -> str:
    return f"{n:,}".replace(",", " ") + f" {CURRENCY}"

def main_menu(is_admin: bool):
    rows = [
        [InlineKeyboardButton(text="Витрина", callback_data="catalog")],
        [InlineKeyboardButton(text="Сумка", callback_data="cart"),
         InlineKeyboardButton(text="Ателье", callback_data="about")],
        [InlineKeyboardButton(text="Как заказать", callback_data="howto")],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton(text="İdarə paneli", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def back_main():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← В зал", callback_data="menu")]
    ])

def catalog_kb(counts: dict):
    rows = []
    for key, title, _ in CATEGORIES:
        c = counts.get(key, 0)
        if c:
            rows.append([InlineKeyboardButton(text=f"{title}  ·  {c}", callback_data=f"cat:{key}")])
    rows.append([InlineKeyboardButton(text="← В зал", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def product_kb(pid: int, category: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="В сумку", callback_data=f"add:{pid}")],
        [InlineKeyboardButton(text="Ещё в этой зале", callback_data=f"cat:{category}"),
         InlineKeyboardButton(text="Сумка", callback_data="cart")],
        [InlineKeyboardButton(text="Витрина", callback_data="catalog")],
    ])

def cart_kb(items):
    rows = []
    for it in items:
        pid = it["id"]
        rows.append([
            InlineKeyboardButton(text="−", callback_data=f"qty:{pid}:-1"),
            InlineKeyboardButton(text=f"{it['qty']} × {it['name'][:18]}", callback_data=f"open:{pid}"),
            InlineKeyboardButton(text="+", callback_data=f"qty:{pid}:1"),
        ])
    if items:
        rows.append([InlineKeyboardButton(text="Оформить заказ", callback_data="checkout")])
        rows.append([InlineKeyboardButton(text="Очистить сумку", callback_data="clearcart")])
    rows.append([InlineKeyboardButton(text="← В зал", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def pay_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Перевод на карту", callback_data="pay:card")],
        [InlineKeyboardButton(text="При получении", callback_data="pay:cod")],
        [InlineKeyboardButton(text="Отмена", callback_data="cart")],
    ])

def confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подтвердить заказ", callback_data="order:yes")],
        [InlineKeyboardButton(text="Назад в сумку", callback_data="cart")],
    ])

def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Mallar", callback_data="adm:goods"),
         InlineKeyboardButton(text="Sifarişlər", callback_data="adm:orders")],
        [InlineKeyboardButton(text="Yeni mal", callback_data="adm:new")],
        [InlineKeyboardButton(text="Hesabat", callback_data="adm:stats")],
        [InlineKeyboardButton(text="← Zal", callback_data="menu")],
    ])

def goods_kb(products):
    rows = []
    for p in products:
        mark = "" if p["active"] else " · gizli"
        rows.append([InlineKeyboardButton(
            text=f"#{p['id']} {p['name'][:26]}{mark}",
            callback_data=f"adm:p:{p['id']}",
        )])
    rows.append([InlineKeyboardButton(text="← Panel", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def product_admin_kb(pid: int, active: int):
    toggle = "Gizlət" if active else "Göstər"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ad", callback_data=f"edit:{pid}:name"),
         InlineKeyboardButton(text="Qiymət", callback_data=f"edit:{pid}:price")],
        [InlineKeyboardButton(text="Şəkil", callback_data=f"edit:{pid}:photo"),
         InlineKeyboardButton(text="Qalıq", callback_data=f"edit:{pid}:stock")],
        [InlineKeyboardButton(text="Təsvir", callback_data=f"edit:{pid}:description"),
         InlineKeyboardButton(text="Zal", callback_data=f"edit:{pid}:category")],
        [InlineKeyboardButton(text=toggle, callback_data=f"toggle:{pid}"),
         InlineKeyboardButton(text="Sil", callback_data=f"del:{pid}")],
        [InlineKeyboardButton(text="← Mallar", callback_data="adm:goods")],
    ])

def orders_kb(orders):
    rows = []
    for o in orders:
        rows.append([InlineKeyboardButton(
            text=f"#{o['id']} · {o['total']} · {o['status']}",
            callback_data=f"adm:o:{o['id']}",
        )])
    rows.append([InlineKeyboardButton(text="← Panel", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def order_admin_kb(oid: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="İşdə", callback_data=f"ost:{oid}:work"),
         InlineKeyboardButton(text="Göndərildi", callback_data=f"ost:{oid}:sent")],
        [InlineKeyboardButton(text="Bağlandı", callback_data=f"ost:{oid}:done"),
         InlineKeyboardButton(text="Ləğv", callback_data=f"ost:{oid}:cancelled")],
        [InlineKeyboardButton(text="← Sifarişlər", callback_data="adm:orders")],
    ])

def cat_pick_kb(prefix: str):
    rows = [[InlineKeyboardButton(text=title, callback_data=f"{prefix}:{key}")] for key, title, _ in CATEGORIES]
    rows.append([InlineKeyboardButton(text="Ləğv", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def skip_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Без комментария", callback_data="skip:comment")]
    ])

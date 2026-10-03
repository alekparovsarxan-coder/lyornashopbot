from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def stars(n: int) -> str:
    return f"{n} ⭐"

def main_menu(is_admin: bool):
    rows = [
        [InlineKeyboardButton(text="🛍 Витрина", callback_data="catalog"),
         InlineKeyboardButton(text="⚡ Купить сейчас", callback_data="buynow")],
        [InlineKeyboardButton(text="🛒 Сумка", callback_data="cart"),
         InlineKeyboardButton(text="📦 Заказы", callback_data="myorders")],
        [InlineKeyboardButton(text="❓ Вопросы", callback_data="faq"),
         InlineKeyboardButton(text="🚚 Доставка", callback_data="delivery")],
        [InlineKeyboardButton(text="↻ Для кого", callback_data="regender")],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton(text="🛠 İdarə", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def with_buy(rows):
    rows.append([InlineKeyboardButton(text="⚡ Купить сейчас", callback_data="buynow")])
    rows.append([InlineKeyboardButton(text="← Зал", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def gender_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👩 Для неё", callback_data="gender:women"),
         InlineKeyboardButton(text="👨 Для него", callback_data="gender:men")],
        [InlineKeyboardButton(text="✨ Смотреть всё", callback_data="gender:all")],
    ])

def mood_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌆 Город", callback_data="mood:city")],
        [InlineKeyboardButton(text="🌙 Вечер", callback_data="mood:night")],
        [InlineKeyboardButton(text="🕯 Дом", callback_data="mood:home")],
        [InlineKeyboardButton(text="Всё сразу", callback_data="mood:all")],
    ])

def product_kb(pid: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Купить сейчас", callback_data=f"buy:{pid}")],
        [InlineKeyboardButton(text="🛒 В сумку", callback_data=f"add:{pid}")],
        [InlineKeyboardButton(text="🛍 Ещё вещи", callback_data="catalog"),
         InlineKeyboardButton(text="← Зал", callback_data="menu")],
    ])

def size_kb(pid: int, sizes: str, mode: str):
    rows = []
    chunk = []
    for s in sizes.split():
        chunk.append(InlineKeyboardButton(text=s, callback_data=f"{mode}size:{pid}:{s}"))
        if len(chunk) == 3:
            rows.append(chunk)
            chunk = []
    if chunk:
        rows.append(chunk)
    rows.append([InlineKeyboardButton(text="← Назад", callback_data=f"open:{pid}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Оплатить Stars", callback_data="paystars")],
        [InlineKeyboardButton(text="← Сумка", callback_data="cart")],
    ])

def faq_kb(items):
    rows = [[InlineKeyboardButton(text=title, callback_data=key)] for key, title, _ in items]
    rows.append([InlineKeyboardButton(text="⚡ Купить сейчас", callback_data="buynow")])
    rows.append([InlineKeyboardButton(text="← Зал", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Mallar", callback_data="adm:goods"),
         InlineKeyboardButton(text="Sifarişlər", callback_data="adm:orders")],
        [InlineKeyboardButton(text="← Zal", callback_data="menu")],
    ])

def goods_kb(products):
    rows = [[InlineKeyboardButton(text=f"#{p['id']} {p['name'][:24]}", callback_data=f"adm:p:{p['id']}")] for p in products]
    rows.append([InlineKeyboardButton(text="← Panel", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def product_admin_kb(pid: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ad", callback_data=f"edit:{pid}:name"),
         InlineKeyboardButton(text="Stars", callback_data=f"edit:{pid}:stars")],
        [InlineKeyboardButton(text="Şəkil", callback_data=f"edit:{pid}:photo"),
         InlineKeyboardButton(text="Qalıq", callback_data=f"edit:{pid}:stock")],
        [InlineKeyboardButton(text="← Mallar", callback_data="adm:goods")],
    ])

def order_admin_kb(oid: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Yığılır", callback_data=f"ost:{oid}:pack"),
         InlineKeyboardButton(text="Yolda", callback_data=f"ost:{oid}:ship")],
        [InlineKeyboardButton(text="Çatdı", callback_data=f"ost:{oid}:done")],
        [InlineKeyboardButton(text="← Sifarişlər", callback_data="adm:orders")],
    ])

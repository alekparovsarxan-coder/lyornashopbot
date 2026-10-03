import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice,
    Message, PreCheckoutQuery, URLInputFile,
)
from aiogram.client.default import DefaultBotProperties

from config import ADMIN_IDS, BOT_TOKEN
from db import (
    init_db, touch_user, set_pref, get_user, list_products, get_product, all_products,
    add_to_cart, cart_items, clear_cart, create_order, mark_paid, get_order, user_orders,
    list_orders, set_status, update_field,
)
from keyboards import (
    stars, main_menu, gender_kb, mood_kb, product_kb, size_kb, confirm_kb, faq_kb,
    admin_kb, goods_kb, product_admin_kb, order_admin_kb,
)
from texts import INTRO, WOMEN, MEN, CITY, NIGHT, HOME, FAQ, DELIVERY

logging.basicConfig(level=logging.INFO)
router = Router()

class Checkout(StatesGroup):
    phone = State()
    city = State()
    address = State()
    confirm = State()

class Pick(StatesGroup):
    size = State()

class Edit(StatesGroup):
    value = State()

def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS

async def photo(message: Message, url: str, caption: str, kb=None):
    try:
        await message.answer_photo(URLInputFile(url), caption=caption, reply_markup=kb)
    except Exception:
        await message.answer(caption, reply_markup=kb)

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    u = message.from_user
    await touch_user(u.id, u.username, u.full_name or "")
    for url, caption in INTRO:
        await photo(message, url, caption)
    await photo(
        message, WOMEN,
        "👩 Для неё  ·  👨 Для него\n\nКому собираем зал?\nОт этого зависят вещи на витрине.",
        gender_kb(),
    )

@router.callback_query(F.data == "regender")
async def regender(cb: CallbackQuery):
    await photo(cb.message, WOMEN, "Кому собираем зал?", gender_kb())
    await cb.answer()

@router.callback_query(F.data.startswith("gender:"))
async def gender(cb: CallbackQuery):
    g = cb.data.split(":")[1]
    await set_pref(cb.from_user.id, gender=g)
    url = WOMEN if g == "women" else MEN if g == "men" else CITY
    title = {"women": "Для неё", "men": "Для него", "all": "Весь зал"}.get(g, "Зал")
    await photo(cb.message, url, f"{title}\n\nКуда вещь пойдёт?", mood_kb())
    await cb.answer()

@router.callback_query(F.data.startswith("mood:"))
async def mood(cb: CallbackQuery):
    m = cb.data.split(":")[1]
    await set_pref(cb.from_user.id, mood=m)
    url = {"city": CITY, "night": NIGHT, "home": HOME}.get(m, CITY)
    await photo(
        cb.message, url,
        "Зал открыт.\nМожно смотреть спокойно — оплата только когда сам нажмёшь Stars.",
        main_menu(is_admin(cb.from_user.id)),
    )
    await cb.answer()

@router.callback_query(F.data == "menu")
async def menu(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.answer("LYORNA · зал", reply_markup=main_menu(is_admin(cb.from_user.id)))
    await cb.answer()

@router.message(Command("menu"))
async def menu_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("LYORNA · зал", reply_markup=main_menu(is_admin(message.from_user.id)))

@router.callback_query(F.data == "catalog")
async def catalog(cb: CallbackQuery):
    user = await get_user(cb.from_user.id)
    gender = user["gender"] if user else "all"
    mood = user["mood"] if user else "all"
    items = await list_products(gender, mood)
    if not items:
        items = await list_products("all", "all")
    lines = ["🛍 Витрина под твой выбор\n"]
    rows = []
    for p in items:
        lines.append(f"{p['name']}\n{stars(p['stars'])} · {p['category']}")
        rows.append([InlineKeyboardButton(text=p["name"][:34], callback_data=f"open:{p['id']}")])
    rows.append([InlineKeyboardButton(text="⚡ Купить сейчас", callback_data="buynow")])
    rows.append([InlineKeyboardButton(text="← Зал", callback_data="menu")])
    await cb.message.answer("\n\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await cb.answer()

@router.callback_query(F.data == "buynow")
async def buynow(cb: CallbackQuery):
    user = await get_user(cb.from_user.id)
    items = await list_products(user["gender"] if user else "all", user["mood"] if user else "all")
    if not items:
        items = await list_products("all", "all")
    rows = [[InlineKeyboardButton(text=f"⚡ {p['name'][:28]}", callback_data=f"buy:{p['id']}")] for p in items[:8]]
    rows.append([InlineKeyboardButton(text="← Зал", callback_data="menu")])
    await cb.message.answer("⚡ Купить сейчас\nВыбери вещь — дальше размер и Stars.", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await cb.answer()

@router.callback_query(F.data.startswith("open:"))
async def open_product(cb: CallbackQuery):
    p = await get_product(int(cb.data.split(":")[1]))
    if not p or not p["active"]:
        await cb.answer("Снято", show_alert=True)
        return
    caption = (
        f"{p['name']}\n{p['description']}\n\n"
        f"{stars(p['stars'])}\n"
        f"размер: {p['sizes']}\nцвет: {p['colors']}\nв ателье: {p['stock']}"
    )
    await photo(cb.message, p["photo"], caption, product_kb(p["id"]))
    await cb.answer()

@router.callback_query(F.data.startswith("add:"))
async def add(cb: CallbackQuery, state: FSMContext):
    pid = int(cb.data.split(":")[1])
    p = await get_product(pid)
    if not p:
        return
    await state.set_state(Pick.size)
    await state.update_data(pid=pid, mode="cart")
    await cb.message.answer("Размер", reply_markup=size_kb(pid, p["sizes"], "cart"))
    await cb.answer()

@router.callback_query(F.data.startswith("buy:"))
async def buy(cb: CallbackQuery, state: FSMContext):
    pid = int(cb.data.split(":")[1])
    p = await get_product(pid)
    if not p or p["stock"] <= 0:
        await cb.answer("Нет в ателье", show_alert=True)
        return
    await state.set_state(Pick.size)
    await state.update_data(pid=pid, mode="buy")
    await cb.message.answer("Размер для этого заказа", reply_markup=size_kb(pid, p["sizes"], "buy"))
    await cb.answer()

@router.callback_query(F.data.startswith("cartsize:"))
async def cart_size(cb: CallbackQuery, state: FSMContext):
    _, pid, size = cb.data.split(":")
    p = await get_product(int(pid))
    await add_to_cart(cb.from_user.id, int(pid), size, p["colors"], 1)
    await state.clear()
    await cb.message.answer(f"🛒 {p['name']} · {size} в сумке.", reply_markup=main_menu(is_admin(cb.from_user.id)))
    await cb.answer("В сумке")

@router.callback_query(F.data.startswith("buysize:"))
async def buy_size(cb: CallbackQuery, state: FSMContext):
    _, pid, size = cb.data.split(":")
    p = await get_product(int(pid))
    item = {"id": p["id"], "name": p["name"], "stars": p["stars"], "size": size, "color": p["colors"], "qty": 1}
    await state.set_state(Checkout.phone)
    await state.update_data(items=[item], stars=p["stars"])
    await cb.message.answer("Телефон для доставки.")
    await cb.answer()

@router.callback_query(F.data == "cart")
async def cart(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    items = await cart_items(cb.from_user.id)
    if not items:
        await cb.message.answer("Сумка пустая.", reply_markup=main_menu(is_admin(cb.from_user.id)))
        await cb.answer()
        return
    total = sum(i["stars"] * i["qty"] for i in items)
    lines = ["🛒 Сумка\n"]
    for i in items:
        lines.append(f"{i['qty']} × {i['name']} · {i['size']} — {stars(i['stars'] * i['qty'])}")
    lines.append(f"\nИтого {stars(total)}")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Оформить и оплатить", callback_data="checkout")],
        [InlineKeyboardButton(text="Очистить", callback_data="clearcart")],
        [InlineKeyboardButton(text="← Зал", callback_data="menu")],
    ])
    await cb.message.answer("\n".join(lines), reply_markup=kb)
    await cb.answer()

@router.callback_query(F.data == "clearcart")
async def clear(cb: CallbackQuery):
    await clear_cart(cb.from_user.id)
    await cb.message.answer("Сумка пустая.", reply_markup=main_menu(is_admin(cb.from_user.id)))
    await cb.answer()

@router.callback_query(F.data == "checkout")
async def checkout(cb: CallbackQuery, state: FSMContext):
    items = await cart_items(cb.from_user.id)
    if not items:
        await cb.answer("Пусто", show_alert=True)
        return
    packed = [{"id": i["id"], "name": i["name"], "stars": i["stars"], "size": i["size"], "color": i["color"], "qty": i["qty"]} for i in items]
    await state.set_state(Checkout.phone)
    await state.update_data(items=packed, stars=sum(i["stars"] * i["qty"] for i in items))
    await cb.message.answer("Телефон для доставки.")
    await cb.answer()

@router.message(Checkout.phone)
async def phone(message: Message, state: FSMContext):
    if len((message.text or "").strip()) < 6:
        await message.answer("Телефон короткий.")
        return
    await state.update_data(phone=message.text.strip())
    await state.set_state(Checkout.city)
    await message.answer("Город в России.")

@router.message(Checkout.city)
async def city(message: Message, state: FSMContext):
    await state.update_data(city=(message.text or "").strip())
    await state.set_state(Checkout.address)
    await message.answer("Адрес или пункт выдачи.")

@router.message(Checkout.address)
async def address(message: Message, state: FSMContext):
    await state.update_data(address=(message.text or "").strip())
    data = await state.get_data()
    lines = ["Проверь\n"]
    for i in data["items"]:
        lines.append(f"{i['qty']} × {i['name']} · {i['size']}")
    lines.append(f"\n{stars(data['stars'])}\n{data['city']}, {data['address']}\n{data['phone']}")
    await state.set_state(Checkout.confirm)
    await message.answer("\n".join(lines), reply_markup=confirm_kb())

@router.callback_query(Checkout.confirm, F.data == "paystars")
async def paystars(cb: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    oid = await create_order(cb.from_user, data["phone"], data["city"], data["address"], "", data["items"], data["stars"])
    await clear_cart(cb.from_user.id)
    await state.clear()
    await bot.send_invoice(
        cb.from_user.id,
        title=f"Lyorna · заказ #{oid}",
        description="Вещь ателье, доставка по России",
        payload=f"order:{oid}",
        currency="XTR",
        prices=[LabeledPrice(label="Заказ", amount=int(data["stars"]))],
        provider_token="",
    )
    await cb.answer()

@router.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery):
    await q.answer(ok=True)

@router.message(F.successful_payment)
async def paid(message: Message, bot: Bot):
    payload = message.successful_payment.invoice_payload
    oid = int(payload.split(":")[1])
    charge = message.successful_payment.telegram_payment_charge_id
    fresh = await mark_paid(oid, charge)
    await message.answer(
        f"✅ Заказ #{oid} оплачен.\nАтелье собирает и напишет статус сюда.",
        reply_markup=main_menu(is_admin(message.from_user.id)),
    )
    if fresh:
        for admin in ADMIN_IDS:
            try:
                await bot.send_message(admin, f"⭐ Ödənildi #{oid}", reply_markup=order_admin_kb(oid))
            except Exception:
                pass

@router.callback_query(F.data == "faq")
async def faq(cb: CallbackQuery):
    await cb.message.answer("❓ Вопросы\nНажми — ответ откроется здесь.", reply_markup=faq_kb(FAQ))
    await cb.answer()

@router.callback_query(F.data.startswith("faq:"))
async def faq_item(cb: CallbackQuery):
    item = next((x for x in FAQ if x[0] == cb.data), None)
    if not item:
        return
    await cb.message.answer(f"{item[1]}\n\n{item[2]}", reply_markup=faq_kb(FAQ))
    await cb.answer()

@router.callback_query(F.data == "delivery")
async def delivery(cb: CallbackQuery):
    await cb.message.answer("🚚 Доставка по России", reply_markup=faq_kb(DELIVERY))
    await cb.answer()

@router.callback_query(F.data.startswith("dl:"))
async def delivery_item(cb: CallbackQuery):
    item = next((x for x in DELIVERY if x[0] == cb.data), None)
    if not item:
        return
    await cb.message.answer(f"{item[1]}\n\n{item[2]}", reply_markup=faq_kb(DELIVERY))
    await cb.answer()

@router.callback_query(F.data == "myorders")
async def myorders(cb: CallbackQuery):
    orders = await user_orders(cb.from_user.id)
    if not orders:
        await cb.message.answer("Заказов ещё нет.", reply_markup=main_menu(is_admin(cb.from_user.id)))
        await cb.answer()
        return
    lines = ["📦 Заказы\n"]
    for o in orders:
        flag = "✅" if o["paid"] else "⏳"
        lines.append(f"{flag} #{o['id']} · {stars(o['stars'])} · {o['status']}")
    await cb.message.answer("\n".join(lines), reply_markup=main_menu(is_admin(cb.from_user.id)))
    await cb.answer()

@router.callback_query(F.data == "admin")
async def admin(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("Bağlıdır", show_alert=True)
        return
    await cb.message.answer("İdarə paneli", reply_markup=admin_kb())
    await cb.answer()

@router.message(Command("admin"))
async def admin_cmd(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("İdarə paneli", reply_markup=admin_kb())

@router.callback_query(F.data == "adm:goods")
async def adm_goods(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    await cb.message.answer("Mallar", reply_markup=goods_kb(await all_products()))
    await cb.answer()

@router.callback_query(F.data.startswith("adm:p:"))
async def adm_p(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    p = await get_product(int(cb.data.split(":")[2]))
    await cb.message.answer(f"#{p['id']} {p['name']}\n{stars(p['stars'])} · qalıq {p['stock']}", reply_markup=product_admin_kb(p["id"]))
    await cb.answer()

@router.callback_query(F.data.startswith("edit:"))
async def edit(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        return
    _, pid, field = cb.data.split(":")
    await state.set_state(Edit.value)
    await state.update_data(pid=int(pid), field=field)
    hint = {"name": "Yeni ad", "stars": "Ulduz sayı, rəqəm", "stock": "Qalıq", "photo": "Şəkil və ya link"}[field]
    await cb.message.answer(hint)
    await cb.answer()

@router.message(Edit.value, F.photo)
async def edit_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("field") != "photo":
        return
    await update_field(data["pid"], "photo", message.photo[-1].file_id)
    await state.clear()
    await message.answer("Şəkil yeniləndi.", reply_markup=admin_kb())

@router.message(Edit.value)
async def edit_value(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data["field"]
    text = (message.text or "").strip()
    value = int(text) if field in {"stars", "stock"} and text.isdigit() else text
    if field in {"stars", "stock"} and not text.isdigit():
        await message.answer("Rəqəm yaz.")
        return
    await update_field(data["pid"], field, value)
    await state.clear()
    await message.answer("Saxlandı.", reply_markup=admin_kb())

@router.callback_query(F.data == "adm:orders")
async def adm_orders(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    orders = await list_orders()
    rows = [[InlineKeyboardButton(text=f"#{o['id']} {o['status']}", callback_data=f"adm:o:{o['id']}")] for o in orders]
    rows.append([InlineKeyboardButton(text="← Panel", callback_data="admin")])
    await cb.message.answer("Sifarişlər", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows or [[InlineKeyboardButton(text="←", callback_data="admin")]]))
    await cb.answer()

@router.callback_query(F.data.startswith("adm:o:"))
async def adm_o(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    oid = int(cb.data.split(":")[2])
    order, items = await get_order(oid)
    lines = [f"#{order['id']} {order['status']}", order["phone"] or "", f"{order['city']}, {order['address']}"]
    for it in items:
        lines.append(f"{it['qty']} × {it['name']} {it['size']}")
    await cb.message.answer("\n".join(lines), reply_markup=order_admin_kb(oid))
    await cb.answer()

STATUS = {"pack": "собирается", "ship": "в пути", "done": "доставлен"}

@router.callback_query(F.data.startswith("ost:"))
async def ost(cb: CallbackQuery, bot: Bot):
    if not is_admin(cb.from_user.id):
        return
    _, oid, status = cb.data.split(":")
    await set_status(int(oid), status)
    order, _ = await get_order(int(oid))
    if order:
        try:
            await bot.send_message(order["user_id"], f"LYORNA · заказ #{oid}: {STATUS.get(status, status)}")
        except Exception:
            pass
    await cb.answer("Yeniləndi")

async def main():
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN boşdur. Railway Variables və ya .env-ə yaz.")
    await init_db()
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties())
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

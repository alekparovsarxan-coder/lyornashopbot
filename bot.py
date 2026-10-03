import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, URLInputFile
from aiogram.client.default import DefaultBotProperties

from config import ADMIN_IDS, BOT_TOKEN, SHOP_NAME
from db import (
    init_db, touch_user, categories_with_counts, list_products, get_product,
    all_products, add_to_cart, set_qty, clear_cart, cart_items, create_order,
    list_orders, get_order, set_order_status, update_product_field, insert_product,
    delete_product, stats,
)
from keyboards import (
    money, main_menu, back_main, catalog_kb, product_kb, cart_kb, pay_kb, confirm_kb,
    admin_kb, goods_kb, product_admin_kb, orders_kb, order_admin_kb, cat_pick_kb, skip_kb,
)
from texts import INTRO, CAT_MAP

logging.basicConfig(level=logging.INFO)
router = Router()

class Checkout(StatesGroup):
    phone = State()
    city = State()
    address = State()
    comment = State()
    pay = State()
    confirm = State()

class Edit(StatesGroup):
    value = State()

class NewItem(StatesGroup):
    category = State()
    name = State()
    description = State()
    price = State()
    photo = State()
    stock = State()

def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS

def cart_total(items) -> int:
    return sum(i["price"] * i["qty"] for i in items)

async def send_photo(message: Message, photo: str, caption: str, kb):
    try:
        media = URLInputFile(photo) if str(photo).startswith("http") else photo
        await message.answer_photo(media, caption=caption, reply_markup=kb)
    except Exception:
        await message.answer(caption + "\n\n(фото сейчас не открылось — ссылку можно сменить в админке)", reply_markup=kb)

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    u = message.from_user
    await touch_user(u.id, u.username, u.full_name or "")
    for i, block in enumerate(INTRO):
        if i < len(INTRO) - 1:
            await message.answer(block)
            await asyncio.sleep(1.1)
        else:
            await message.answer(block, reply_markup=main_menu(is_admin(u.id)))

@router.message(Command("menu"))
async def menu_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(f"{SHOP_NAME}\nзал открыт.", reply_markup=main_menu(is_admin(message.from_user.id)))

@router.message(Command("admin"))
async def admin_cmd(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Bu zal yalnız idarə üçündür.")
        return
    await message.answer(
        "Lyorna idarə paneli.\n\nMallar — ad, qiymət, şəkil, qalıq.\nSifarişlər — status, müştəriyə yazı.\nYeni mal — addım-addım.",
        reply_markup=admin_kb(),
    )

@router.callback_query(F.data == "menu")
async def cb_menu(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.answer(f"{SHOP_NAME}\nзал открыт.", reply_markup=main_menu(is_admin(cb.from_user.id)))
    await cb.answer()

@router.callback_query(F.data == "about")
async def about(cb: CallbackQuery):
    await cb.message.answer(
        "LYORNA — ателье, не витрина скидок.\n\n"
        "Вещи собраны малым кругом: одежда, обувь, дом, запах, тихая техника.\n"
        "Доставка по России. Упаковка плотная, внутри карточка ателье.",
        reply_markup=back_main(),
    )
    await cb.answer()

@router.callback_query(F.data == "howto")
async def howto(cb: CallbackQuery):
    await cb.message.answer(
        "Ритуал заказа\n\n"
        "Витрина → карточка → «В сумку».\n"
        "В сумке меняешь количество.\n"
        "Оформление: телефон, город, адрес, способ оплаты.\n"
        "Ателье подтверждает заказ и пишет в этот чат.\n\n"
        "Перевод: реквизиты приходят после подтверждения.\n"
        "При получении: курьер или пункт выдачи.",
        reply_markup=back_main(),
    )
    await cb.answer()

@router.callback_query(F.data == "catalog")
async def catalog(cb: CallbackQuery):
    counts = await categories_with_counts()
    await cb.message.answer("Витрина\nСемь залов. В каждом — только то, что ателье оставило.", reply_markup=catalog_kb(counts))
    await cb.answer()

@router.callback_query(F.data.startswith("cat:"))
async def open_cat(cb: CallbackQuery):
    key = cb.data.split(":", 1)[1]
    title, blurb = CAT_MAP.get(key, ("Зал", ""))
    items = await list_products(key)
    if not items:
        await cb.answer("Зал пуст", show_alert=True)
        return
    lines = [f"{title}\n{blurb}\n"]
    for p in items:
        lines.append(f"#{p['id']}  {p['name']}\n{money(p['price'])}  ·  осталось {p['stock']}")
    rows = [[InlineKeyboardButton(text=p["name"][:40], callback_data=f"open:{p['id']}")] for p in items]
    rows.append([InlineKeyboardButton(text="← Витрина", callback_data="catalog")])
    await cb.message.answer("\n\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await cb.answer()

@router.callback_query(F.data.startswith("open:"))
async def open_product(cb: CallbackQuery):
    pid = int(cb.data.split(":")[1])
    p = await get_product(pid)
    if not p or not p["active"]:
        await cb.answer("Вещь снята с витрины", show_alert=True)
        return
    title, _ = CAT_MAP.get(p["category"], ("", ""))
    caption = f"{title}\n\n{p['name']}\n{p['description']}\n\n{money(p['price'])}\nв ателье: {p['stock']}"
    await send_photo(cb.message, p["photo"], caption, product_kb(p["id"], p["category"]))
    await cb.answer()

@router.callback_query(F.data.startswith("add:"))
async def add(cb: CallbackQuery):
    pid = int(cb.data.split(":")[1])
    p = await get_product(pid)
    if not p or not p["active"] or p["stock"] <= 0:
        await cb.answer("Этой вещи уже нет", show_alert=True)
        return
    await add_to_cart(cb.from_user.id, pid, 1)
    await cb.answer("В сумке")
    await cb.message.answer(f"{p['name']} — в сумке.", reply_markup=main_menu(is_admin(cb.from_user.id)))

@router.callback_query(F.data == "cart")
async def cart(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    items = await cart_items(cb.from_user.id)
    if not items:
        await cb.message.answer("Сумка пустая. Витрина ждёт.", reply_markup=back_main())
        await cb.answer()
        return
    lines = ["Сумка\n"] + [f"{it['qty']} × {it['name']} — {money(it['price'] * it['qty'])}" for it in items]
    lines.append(f"\nИтого {money(cart_total(items))}")
    await cb.message.answer("\n".join(lines), reply_markup=cart_kb(items))
    await cb.answer()

@router.callback_query(F.data.startswith("qty:"))
async def qty(cb: CallbackQuery):
    _, pid, delta = cb.data.split(":")
    pid = int(pid)
    items = await cart_items(cb.from_user.id)
    current = next((i["qty"] for i in items if i["id"] == pid), 0)
    new = current + int(delta)
    p = await get_product(pid)
    if p and new > p["stock"]:
        await cb.answer("Больше, чем есть в ателье", show_alert=True)
        return
    await set_qty(cb.from_user.id, pid, new)
    items = await cart_items(cb.from_user.id)
    if not items:
        await cb.message.edit_text("Сумка пустая.", reply_markup=back_main())
        await cb.answer()
        return
    lines = ["Сумка\n"] + [f"{it['qty']} × {it['name']} — {money(it['price'] * it['qty'])}" for it in items]
    lines.append(f"\nИтого {money(cart_total(items))}")
    await cb.message.edit_text("\n".join(lines), reply_markup=cart_kb(items))
    await cb.answer()

@router.callback_query(F.data == "clearcart")
async def clear(cb: CallbackQuery):
    await clear_cart(cb.from_user.id)
    await cb.message.edit_text("Сумка очищена.", reply_markup=back_main())
    await cb.answer()

@router.callback_query(F.data == "checkout")
async def checkout(cb: CallbackQuery, state: FSMContext):
    items = await cart_items(cb.from_user.id)
    if not items:
        await cb.answer("Сумка пустая", show_alert=True)
        return
    await state.set_state(Checkout.phone)
    await state.update_data(items=[{k: i[k] for k in ("id", "name", "price", "qty")} for i in items])
    await cb.message.answer("Телефон для связи.")
    await cb.answer()

@router.message(Checkout.phone)
async def st_phone(message: Message, state: FSMContext):
    phone = (message.text or "").strip()
    if len(phone) < 6:
        await message.answer("Телефон слишком короткий.")
        return
    await state.update_data(phone=phone)
    await state.set_state(Checkout.city)
    await message.answer("Город доставки по России.")

@router.message(Checkout.city)
async def st_city(message: Message, state: FSMContext):
    city = (message.text or "").strip()
    if len(city) < 2:
        await message.answer("Напиши город.")
        return
    await state.update_data(city=city)
    await state.set_state(Checkout.address)
    await message.answer("Адрес: улица, дом, квартира. Или пункт выдачи.")

@router.message(Checkout.address)
async def st_addr(message: Message, state: FSMContext):
    addr = (message.text or "").strip()
    if len(addr) < 5:
        await message.answer("Адрес слишком короткий.")
        return
    await state.update_data(address=addr)
    await state.set_state(Checkout.comment)
    await message.answer("Комментарий — или пропусти.", reply_markup=skip_kb())

@router.callback_query(Checkout.comment, F.data == "skip:comment")
async def skip_comment(cb: CallbackQuery, state: FSMContext):
    await state.update_data(comment="")
    await state.set_state(Checkout.pay)
    await cb.message.answer("Как удобнее оплатить?", reply_markup=pay_kb())
    await cb.answer()

@router.message(Checkout.comment)
async def st_comment(message: Message, state: FSMContext):
    await state.update_data(comment=(message.text or "").strip())
    await state.set_state(Checkout.pay)
    await message.answer("Как удобнее оплатить?", reply_markup=pay_kb())

@router.callback_query(Checkout.pay, F.data.startswith("pay:"))
async def st_pay(cb: CallbackQuery, state: FSMContext):
    pay = "Перевод на карту" if cb.data.endswith("card") else "При получении"
    data = await state.get_data()
    items = data["items"]
    total = sum(i["price"] * i["qty"] for i in items)
    await state.update_data(pay=pay, total=total)
    await state.set_state(Checkout.confirm)
    lines = ["Проверь заказ\n"] + [f"{i['qty']} × {i['name']} — {money(i['price'] * i['qty'])}" for i in items]
    lines.append(f"\nИтого {money(total)}\n{data['city']}, {data['address']}\n{data['phone']}\n{pay}")
    if data.get("comment"):
        lines.append(data["comment"])
    await cb.message.answer("\n".join(lines), reply_markup=confirm_kb())
    await cb.answer()

@router.callback_query(Checkout.confirm, F.data == "order:yes")
async def st_yes(cb: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    items = data.get("items") or []
    if not items:
        await cb.answer("Сумка уже пустая", show_alert=True)
        return
    oid = await create_order(cb.from_user, data["phone"], data["city"], data["address"], data.get("comment", ""), data["pay"], items, data["total"])
    await state.clear()
    await cb.message.answer(
        f"Заказ #{oid} принят.\nАтелье напишет в этот чат, когда подтвердит.",
        reply_markup=main_menu(is_admin(cb.from_user.id)),
    )
    note = (
        f"Yeni sifariş #{oid}\n{cb.from_user.full_name} @{cb.from_user.username or '—'}\n"
        f"{data['phone']}\n{data['city']}, {data['address']}\n{data['pay']} · {money(data['total'])}"
    )
    for admin in ADMIN_IDS:
        try:
            await bot.send_message(admin, note, reply_markup=order_admin_kb(oid))
        except Exception:
            pass
    await cb.answer("Заказ ушёл в ателье")

@router.callback_query(F.data == "admin")
async def admin(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        await cb.answer("Bağlıdır", show_alert=True)
        return
    await state.clear()
    await cb.message.answer("İdarə paneli\n\nMallar · Sifarişlər · Yeni mal · Hesabat", reply_markup=admin_kb())
    await cb.answer()

@router.callback_query(F.data == "adm:stats")
async def adm_stats(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    users, products, orders, revenue = await stats()
    await cb.message.answer(
        f"Hesabat\nqonaq: {users}\nmal: {products}\nsifariş: {orders}\nləğv olunmayan məbləğ: {money(revenue)}",
        reply_markup=admin_kb(),
    )
    await cb.answer()

@router.callback_query(F.data == "adm:goods")
async def adm_goods(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    products = await all_products()
    await cb.message.answer("Bütün mallar. Dəyişmək üçün birinə bas.", reply_markup=goods_kb(products))
    await cb.answer()

@router.callback_query(F.data.startswith("adm:p:"))
async def adm_product(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    pid = int(cb.data.split(":")[2])
    p = await get_product(pid)
    if not p:
        await cb.answer("Yoxdur", show_alert=True)
        return
    title, _ = CAT_MAP.get(p["category"], (p["category"], ""))
    text = (
        f"#{p['id']}  {p['name']}\n{title} · {'vitrində' if p['active'] else 'gizli'}\n"
        f"{money(p['price'])} · qalıq {p['stock']}\n\n{p['description']}"
    )
    await cb.message.answer(text, reply_markup=product_admin_kb(p["id"], p["active"]))
    await cb.answer()

@router.callback_query(F.data.startswith("toggle:"))
async def toggle(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    pid = int(cb.data.split(":")[1])
    p = await get_product(pid)
    await update_product_field(pid, "active", 0 if p["active"] else 1)
    p = await get_product(pid)
    await cb.message.answer(f"#{p['id']} indi {'vitrində' if p['active'] else 'gizli'}.", reply_markup=product_admin_kb(p["id"], p["active"]))
    await cb.answer("Hazırdır")

@router.callback_query(F.data.startswith("del:"))
async def remove(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    pid = int(cb.data.split(":")[1])
    await delete_product(pid)
    await cb.message.answer(f"Mal #{pid} silindi.", reply_markup=admin_kb())
    await cb.answer("Silindi")

@router.callback_query(F.data.startswith("edit:"))
async def edit_start(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        return
    _, pid, field = cb.data.split(":")
    await state.set_state(Edit.value)
    await state.update_data(pid=int(pid), field=field)
    hints = {
        "name": "Yeni adı yaz.",
        "price": "Yeni qiymət, yalnız rəqəm. Məsələn: 12900",
        "stock": "Qalıq, tam rəqəm.",
        "description": "Yeni təsviri yaz.",
        "photo": "Şəkil göndər və ya şəkil linki yapışdır.",
        "category": "Zalı seç.",
    }
    if field == "category":
        await cb.message.answer(hints[field], reply_markup=cat_pick_kb("setcat"))
    else:
        await cb.message.answer(hints[field])
    await cb.answer()

@router.callback_query(Edit.value, F.data.startswith("setcat:"))
async def edit_cat(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await update_product_field(data["pid"], "category", cb.data.split(":")[1])
    await state.clear()
    await cb.message.answer("Zal yeniləndi.", reply_markup=admin_kb())
    await cb.answer()

@router.message(Edit.value, F.photo)
async def edit_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("field") != "photo":
        await message.answer("İndi mətn gözləyirəm.")
        return
    await update_product_field(data["pid"], "photo", message.photo[-1].file_id)
    await state.clear()
    await message.answer("Şəkil yeniləndi.", reply_markup=admin_kb())

@router.message(Edit.value)
async def edit_value(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data["field"]
    text = (message.text or "").strip()
    if field in {"price", "stock"}:
        if not text.isdigit():
            await message.answer("Tam rəqəm yaz.")
            return
        value = int(text)
    elif field == "photo":
        value = text
    elif field == "category":
        await message.answer("Zalı düymədən seç.")
        return
    else:
        if len(text) < 2:
            await message.answer("Çox qısadır.")
            return
        value = text
    await update_product_field(data["pid"], field, value)
    await state.clear()
    await message.answer("Saxlandı.", reply_markup=admin_kb())

@router.callback_query(F.data == "adm:new")
async def new_item(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id):
        return
    await state.set_state(NewItem.category)
    await cb.message.answer("Yeni mal. Əvvəl zalı seç.", reply_markup=cat_pick_kb("newcat"))
    await cb.answer()

@router.callback_query(NewItem.category, F.data.startswith("newcat:"))
async def new_cat(cb: CallbackQuery, state: FSMContext):
    await state.update_data(category=cb.data.split(":")[1])
    await state.set_state(NewItem.name)
    await cb.message.answer("Adı yaz.")
    await cb.answer()

@router.message(NewItem.name)
async def new_name(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("Ad qısadır.")
        return
    await state.update_data(name=name)
    await state.set_state(NewItem.description)
    await message.answer("Təsviri yaz.")

@router.message(NewItem.description)
async def new_desc(message: Message, state: FSMContext):
    await state.update_data(description=(message.text or "").strip())
    await state.set_state(NewItem.price)
    await message.answer("Qiymət, yalnız rəqəm. Məsələn 8900")

@router.message(NewItem.price)
async def new_price(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer("Yalnız rəqəm.")
        return
    await state.update_data(price=int(text))
    await state.set_state(NewItem.photo)
    await message.answer("Şəkil göndər və ya link yapışdır (http ilə).")

@router.message(NewItem.photo, F.photo)
async def new_photo_file(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await state.set_state(NewItem.stock)
    await message.answer("Neçə ədəd qalıb? Rəqəm yaz.")

@router.message(NewItem.photo)
async def new_photo_url(message: Message, state: FSMContext):
    url = (message.text or "").strip()
    if not url.startswith("http"):
        await message.answer("Link http ilə başlamalıdır, ya da şəkil göndər.")
        return
    await state.update_data(photo=url)
    await state.set_state(NewItem.stock)
    await message.answer("Neçə ədəd qalıb? Rəqəm yaz.")

@router.message(NewItem.stock)
async def new_stock(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer("Rəqəm yaz.")
        return
    data = await state.get_data()
    pid = await insert_product(data["category"], data["name"], data["description"], data["price"], data["photo"], int(text))
    await state.clear()
    await message.answer(f"Mal #{pid} vitrinə düşdü.", reply_markup=admin_kb())

@router.callback_query(F.data == "adm:orders")
async def adm_orders(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    orders = await list_orders()
    if not orders:
        await cb.message.answer("Hələ sifariş yoxdur.", reply_markup=admin_kb())
        await cb.answer()
        return
    await cb.message.answer("Son sifarişlər.", reply_markup=orders_kb(orders))
    await cb.answer()

@router.callback_query(F.data.startswith("adm:o:"))
async def adm_order(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    oid = int(cb.data.split(":")[2])
    order, items = await get_order(oid)
    if not order:
        await cb.answer("Yoxdur", show_alert=True)
        return
    lines = [
        f"Sifariş #{order['id']} · {order['status']}",
        f"{order['full_name']} @{order['username'] or '—'}",
        order["phone"],
        f"{order['city']}, {order['address']}",
        order["pay"],
        "",
    ]
    for it in items:
        lines.append(f"{it['qty']} × {it['name']} — {money(it['price'] * it['qty'])}")
    lines.append(f"\nCəmi {money(order['total'])}")
    if order["comment"]:
        lines.append(order["comment"])
    await cb.message.answer("\n".join(lines), reply_markup=order_admin_kb(oid))
    await cb.answer()

STATUS_RU = {"work": "в работе", "sent": "отправлен", "done": "закрыт", "cancelled": "отменён"}

@router.callback_query(F.data.startswith("ost:"))
async def order_status(cb: CallbackQuery, bot: Bot):
    if not is_admin(cb.from_user.id):
        return
    _, oid, status = cb.data.split(":")
    oid = int(oid)
    await set_order_status(oid, status)
    order, _ = await get_order(oid)
    label = STATUS_RU.get(status, status)
    await cb.message.answer(f"Sifariş #{oid}: {label}")
    if order:
        try:
            await bot.send_message(order["user_id"], f"Lyorna · заказ #{oid}: {label}.")
        except Exception:
            pass
    await cb.answer("Status yeniləndi")

async def main():
    if not BOT_TOKEN or BOT_TOKEN.startswith("buraya"):
        raise SystemExit("BOT_TOKEN boşdur. Railway Variables və ya .env-ə yaz.")
    if not ADMIN_IDS:
        raise SystemExit("ADMIN_IDS boşdur.")
    await init_db()
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties())
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

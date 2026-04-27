import asyncio
from contextlib import suppress
from aiogram import Router, F, types
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramAPIError

import config
from database import db
from keyboards import MAIN_MENU_KB, EASY_BRIEF_KB, PHONE_KB, WantCB, DoneCB, generate_promo

router = Router()

class Brief(StatesGroup):
    task = State(); phone = State()

async def send_welcome(chat_id: int, user: types.User, bot):
    greeting = f"{user.first_name}, добро пожаловать" if user.first_name else "Добро пожаловать"
    text = (f"<tg-emoji emoji-id='5348252551546442951'>🔥</tg-emoji> <b>{greeting} в K&K Digital Agency!</b>\n\n"
            "Мы создаем IT-решения, которые <b>увеличивают вашу прибыль</b> и <b>автоматизируют процессы</b>. <tg-emoji emoji-id='5355227866197957666'>🔥</tg-emoji>\n\n"
            "<b>Почему именно мы:</b>\n"
            "<tg-emoji emoji-id='5354960590383126885'>🔥</tg-emoji> Мы создаем IT решение, которое приносит плоды на протяжении всей жизни.\n"
            "<tg-emoji emoji-id='5354960590383126885'>🔥</tg-emoji> Проекты выполняются в кратчайшие сроки и соблюдают все дедлайны.\n"
            "<tg-emoji emoji-id='5354960590383126885'>🔥</tg-emoji> Являемся лучшими на рынке, создаем из простых букв целую вселенную.\n\n"
            "<tg-emoji emoji-id='5354960590383126885'>🔥</tg-emoji> <i>Выберите интересующее направление:</i>")
    with suppress(TelegramAPIError):
        await bot.send_photo(chat_id, photo=config.WELCOME_BANNER, caption=text, reply_markup=MAIN_MENU_KB)

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext, bot):
    await state.clear()
    asyncio.create_task(db.add_user(message.from_user.id, message.from_user.username or "Скрыт"))
    await send_welcome(message.chat.id, message.from_user, bot)

@router.callback_query(F.data == "to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext, bot):
    await callback.answer()
    await state.clear()
    with suppress(TelegramAPIError): await callback.message.delete()
    await send_welcome(callback.message.chat.id, callback.from_user, bot) 

@router.message(F.text == "❌ Отменить", StateFilter(Brief.task, Brief.phone))
async def cancel_brief(message: types.Message, state: FSMContext, bot):
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=ReplyKeyboardRemove())
    await send_welcome(message.chat.id, message.from_user, bot)

@router.callback_query(WantCB.filter())
async def start_brief(callback: types.CallbackQuery, callback_data: WantCB, state: FSMContext):
    await callback.answer()
    await state.update_data(service=callback_data.s)
    with suppress(TelegramAPIError): await callback.message.delete()
    await callback.message.answer(
        "<tg-emoji emoji-id='5355089078624754801'>🔥</tg-emoji> <b>Отличный выбор!</b>\n\n"
        "В двух словах опишите вашу задачу (ниша, что нужно сделать).\n\n"
        "💡 <i>Не знаете с чего начать и как правильно написать? Не проблема! Просто нажмите кнопку <b>«Консультация»</b> внизу, и мы сами зададим нужные вопросы. <tg-emoji emoji-id='5354822550134240805'>🔥</tg-emoji> </i>",
        reply_markup=EASY_BRIEF_KB
    )
    await state.set_state(Brief.task)

@router.message(Brief.task)
async def get_task(message: types.Message, state: FSMContext, bot):
    await state.update_data(task=message.text or message.caption or "Медиафайл / Голосовое (переслано ниже)")
    if not message.from_user.username:
        await message.answer(
            "⏳ <b>Почти готово!</b>\n\n"
            "У вас скрыт никнейм (username) в настройках Telegram, поэтому наш менеджер не сможет вам написать.\n\n"
            "Пожалуйста, нажмите кнопку <b>«Отправить мой номер»</b> ниже 👇",
            reply_markup=PHONE_KB
        )
        await state.set_state(Brief.phone)
        return
    await finish_order(message, state, bot, message.from_user.username, "-")

@router.message(Brief.phone, F.contact)
async def get_phone(message: types.Message, state: FSMContext, bot):
    await finish_order(message, state, bot, "Скрыт", message.contact.phone_number)

@router.message(Brief.phone)
async def phone_fallback(message: types.Message):
    await message.answer("👆 Пожалуйста, <b>нажмите на кнопку «📱 Отправить мой номер»</b> внизу экрана, чтобы мы получили ваш контакт!")

async def finish_order(message: types.Message, state: FSMContext, bot, username: str, phone: str):
    data = await state.get_data()
    uid = message.from_user.id
    task = data.get('task', 'Консультация')
    service = data.get('service', 'Не указано')
    
    asyncio.create_task(db.insert_order(uid, username, service, task, phone))

    await message.answer(
        "<tg-emoji emoji-id='5354822550134240805'>🔥</tg-emoji> <b>Заявка успешно принята!</b>\nНаша команда свяжется с вами в ближайшее время. <tg-emoji emoji-id='5348252551546442951'>🔥</tg-emoji>",
        reply_markup=ReplyKeyboardRemove()
    )
    
    contact_info = f"@{username}" if username != "Скрыт" else f"📞 {phone}"
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Проект сдан", callback_data=DoneCB(u=uid).pack())]])
    if username != "Скрыт":
        admin_kb.inline_keyboard.insert(0, [InlineKeyboardButton(text="💬 Написать клиенту", url=f"t.me/{username}")])
    
    with suppress(TelegramAPIError):
        await bot.send_message(
            config.GROUP_ID,
            f"🚨 <b>НОВЫЙ ЛИД!</b>\n\n"
            f"👤 <b>Клиент:</b> {contact_info} (ID: <code>{uid}</code>)\n"
            f"🛠 <b>Интересует:</b> {service}\n"
            f"🎯 <b>Задача:</b> <i>{task[:800]}</i>",
            reply_markup=admin_kb
        )
        await message.forward(config.GROUP_ID)
    await state.clear()

@router.callback_query(DoneCB.filter())
async def complete_order(callback: types.CallbackQuery, callback_data: DoneCB, bot):
    promo_code = generate_promo()
    final_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="☕️ Оставить нашей команде на чай", callback_data="show_tip_menu")],
        [InlineKeyboardButton(text="🎁 Забрать купон на скидку", callback_data=f"coupon_{promo_code}")]
    ])
    try:
        await bot.send_message(
            callback_data.u,
            "<tg-emoji emoji-id='5348042308602336483'>🔥</tg-emoji> <b>Проект успешно завершен!</b>\n\n"
            "Спасибо, что доверили работу <b>K&K Digital Agency</b>. Для нашей команды было <b>большой честью</b> работать над вашим проектом! <tg-emoji emoji-id='5355227866197957666'>🔥</tg-emoji>\n\n"
            "Если вы довольны результатом, наша команда будет очень рада чаевым — это лучшая мотивация для нас. <tg-emoji emoji-id='5352567361591354696'>🔥</tg-emoji>\n\n"
            "В качестве благодарности дарим вам <b>скидку 25%</b> на следующий заказ от 50,000₽!",
            reply_markup=final_kb
        )
        await callback.message.edit_reply_markup(reply_markup=None) 
        await callback.message.reply(f"✅ Уведомление отправлено.\n🎟 Выдан промокод: <code>{promo_code}</code>")
        await callback.answer()
    except TelegramAPIError:
        await callback.answer("⚠️ Ошибка. Пользователь заблокировал бота.", show_alert=True)

@router.callback_query(F.data == "show_tip_menu")
async def show_tip_methods(callback: types.CallbackQuery):
    await callback.answer()
    tip_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="USDT (TRC-20)", callback_data="copy_usdt")],
        [InlineKeyboardButton(text="TON / Telegram Wallet", callback_data="copy_ton")],
        [InlineKeyboardButton(text="Другие способы (Карта/СБП)", url=f"tg://user?id={config.ADMIN_ID}")]
    ])
    text = (
        "<b>☕<tg-emoji emoji-id='5353049317051506775'>🔥</tg-emoji> Выберите удобный способ для чаевых:</b>\n\n"
        "<tg-emoji emoji-id='5355227866197957666'>🔥</tg-emoji> <b>Криптовалюта:</b> USDT или TON — это безопасно, без комиссий и задержек.\n\n"
        "<i>Если вам удобнее отправить переводом на карту (СБП), напишите нашему менеджеру по кнопке ниже. Спасибо за поддержку!</i>"
    )
    await callback.message.answer(text, reply_markup=tip_kb)

@router.callback_query(F.data == "copy_usdt")
async def tip_usdt(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer("<tg-emoji emoji-id='5355227866197957666'>🔥</tg-emoji> <b>Hаш адрес USDT (TRC-20):</b>\n\n<code>TTo9em6dmmMoXi52dVeEm5q2vCb5U2amJ7</code>\n\n<i>Нажмите на адрес, чтобы скопировать.</i>")

@router.callback_query(F.data == "copy_ton")
async def tip_ton(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer("<tg-emoji emoji-id='5355227866197957666'>🔥</tg-emoji> <b>Hаш адрес TON:</b>\n\n<code>UQAGNOJUAPtzUCbARDrfJALHyx1BUBroC_oo3HUQ6GYkVENi</code>\n\n<i>Нажмите на адрес, чтобы скопировать.</i>")

@router.callback_query(F.data.startswith("coupon_"))
async def show_coupon(callback: types.CallbackQuery):
    promo = callback.data.split('_')[1]
    await callback.answer(f"Ваш промокод: {promo}\n\nСделайте скриншот или перешлите менеджеру при следующем заказе!", show_alert=True)
import asyncio
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import config
from database import db

router = Router()
router.message.filter(F.from_user.id == config.ADMIN_ID)

class AdminPanel(StatesGroup):
    broadcast_msg = State()

@router.message(Command("admin"))
async def admin_menu(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🔄 Обновить портфолио", callback_data="admin_reload_json")],
        [InlineKeyboardButton(text="💾 Скачать БД", callback_data="admin_backup_db")],
        [InlineKeyboardButton(text="📢 Рассылка всем", callback_data="admin_broadcast")]
    ])
    await message.answer("👨‍💻 <b>Панель администратора</b>", reply_markup=kb)

@router.callback_query(F.data == "admin_stats")
async def show_stats(callback: types.CallbackQuery):
    users, orders, today = await db.get_stats()
    conv = round((orders / users * 100), 2) if users > 0 else 0
    text = (f"📊 <b>Аналитика:</b>\n\n👥 Всего юзеров: <b>{users}</b>\n💎 Лидов (уник.): <b>{orders}</b>\n"
            f"📈 Конверсия: <b>{conv}%</b>\n\n🔥 Заявок за сегодня: <b>{today}</b>")
    await callback.message.edit_text(text, reply_markup=callback.message.reply_markup)

@router.callback_query(F.data == "admin_reload_json")
async def reload_json(callback: types.CallbackQuery):
    config.reload_portfolio()
    await callback.answer("✅ Портфолио обновлено!", show_alert=True)

@router.callback_query(F.data == "admin_backup_db")
async def send_backup(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer_document(FSInputFile(config.DB_NAME), caption="💾 Актуальный бэкап базы данных.")

@router.callback_query(F.data == "admin_broadcast")
async def ask_broadcast(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Отправь сообщение для рассылки всем пользователям (или напиши 'отмена'):")
    await state.set_state(AdminPanel.broadcast_msg)

@router.message(AdminPanel.broadcast_msg)
async def send_broadcast(message: types.Message, state: FSMContext, bot):
    if message.text and message.text.lower() == 'отмена':
        await state.clear()
        return await message.answer("Рассылка отменена.")

    users = await db.get_all_users()
    await message.answer(f"🚀 Начинаю рассылку по {len(users)} пользователям...")
    
    success, fail = 0, 0
    for uid in users:
        try:
            await bot.copy_message(uid, message.chat.id, message.message_id)
            success += 1
        except Exception: fail += 1
        await asyncio.sleep(0.05)
        
    await message.answer(f"✅ <b>Рассылка завершена!</b>\nДоставлено: {success}\nЗаблокировали: {fail}")
    await state.clear()

@router.message(F.video | F.photo, F.chat.type == "private")
async def admin_get_media_id(message: types.Message):
    file_id = message.video.file_id if message.video else message.photo[-1].file_id
    await message.answer(f"✅ <b>File ID получен:</b>\n\n<code>{file_id}</code>\n\n<i>Скопируй и вставь в `portfolio.json`.</i>")

@router.message(F.entities, F.chat.type == "private")
async def admin_get_emoji_id(message: types.Message):
    emojis = [e.custom_emoji_id for e in message.entities if e.type == "custom_emoji"]
    if emojis:
        text = "✅ <b>ID премиум-эмодзи найдены:</b>\n\n"
        text += "\n".join([f"<code>{eid}</code>" for eid in emojis])
        text += "\n\n<i>Вставляй в код так:</i>\n<code>&lt;tg-emoji emoji-id='ТУТ_ID'&gt;🔥&lt;/tg-emoji&gt;</code>"
        await message.answer(text)
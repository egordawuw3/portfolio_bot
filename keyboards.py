import random
import string
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import config

class CategoryCB(CallbackData, prefix="cat"): 
    c: str; page: int = 0
class ProjectCB(CallbackData, prefix="p"): 
    c: str; i: int
class WantCB(CallbackData, prefix="w"): 
    s: str
class ReviewCB(CallbackData, prefix="r"): 
    m: int
class DoneCB(CallbackData, prefix="d"): 
    u: int

MAIN_MENU_KB = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🌐 Сайты под ключ", callback_data=CategoryCB(c="sites").pack())],
    [
        InlineKeyboardButton(text="🤖 Умные Боты", callback_data=CategoryCB(c="bots").pack()),
        InlineKeyboardButton(text="📱 Автоматизация", callback_data=CategoryCB(c="apps").pack())
    ],
    [InlineKeyboardButton(text="📢 Наш Telegram-канал", url=config.CHANNEL_LINK)]
])

EASY_BRIEF_KB = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Консультация 💬")], [KeyboardButton(text="❌ Отменить")]],
    resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Опишите задачу или нажмите кнопку 👇"
)

PHONE_KB = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📱 Отправить мой номер", request_contact=True)], [KeyboardButton(text="❌ Отменить")]], 
    resize_keyboard=True, one_time_keyboard=True
)

def get_project_kb(cat: str, review_msg_id: int) -> InlineKeyboardMarkup:
    actions_row = []
    if review_msg_id > 0:
        actions_row.append(InlineKeyboardButton(text="Смотреть отзыв ✅", callback_data=ReviewCB(m=review_msg_id).pack()))
    actions_row.append(InlineKeyboardButton(text="Рассчитать мой проект 💎", callback_data=WantCB(s=cat).pack()))
    return InlineKeyboardMarkup(inline_keyboard=[
        actions_row,
        [InlineKeyboardButton(text="🔙 К списку", callback_data=CategoryCB(c=cat).pack())],
        [InlineKeyboardButton(text="Меню 🏠", callback_data="to_main")]
    ])

def generate_promo(): 
    return "KK-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=5))

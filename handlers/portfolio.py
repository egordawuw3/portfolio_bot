import urllib.parse
from contextlib import suppress
from aiogram import Router, F, types
from aiogram.exceptions import TelegramAPIError
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import config
from keyboards import CategoryCB, ProjectCB, ReviewCB, get_project_kb

router = Router()

@router.callback_query(CategoryCB.filter())
async def show_project_list(callback: types.CallbackQuery, callback_data: CategoryCB):
    await callback.answer()
    cat, page = callback_data.c, callback_data.page
    projects = config.PROJECTS.get(cat, [])

    if cat in ["bots", "apps"] and not projects:
        case_name = "боты в телеграмм" if cat == "bots" else "автоматизация бизнеса"
        text = (f"{'🤖' if cat == 'bots' else '📱'} <b>Направление пока что в оформлении</b>\n\n"
                "Детали по данному направлению вы можете уточнить напрямую у нашего менеджера.\n\n"
                "<tg-emoji emoji-id='5352994848276258576'>🔥</tg-emoji> <i>Нажмите кнопку ниже, чтобы перейти в диалог.</i>")
        url = f"https://t.me/{config.MANAGER_USERNAME}?text={urllib.parse.quote(f'Здравствуйте, хочу узнать детали по направлению: {case_name}')}"
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Узнать детали 💬", url=url)], [InlineKeyboardButton(text="Меню 🏠", callback_data="to_main")]])
        await callback.message.edit_text(text, reply_markup=kb)
        return 

    ITEMS_PER_PAGE = 5
    start_idx, end_idx = page * ITEMS_PER_PAGE, (page + 1) * ITEMS_PER_PAGE
    current_projects = projects[start_idx:end_idx]

    kb_list = [[InlineKeyboardButton(text=p['title'], callback_data=ProjectCB(c=cat, i=start_idx+idx).pack())] for idx, p in enumerate(current_projects)]
    
    nav_row = []
    if page > 0: nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=CategoryCB(c=cat, page=page-1).pack()))
    if end_idx < len(projects): nav_row.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=CategoryCB(c=cat, page=page+1).pack()))
    if nav_row: kb_list.append(nav_row)
    
    kb_list.append([InlineKeyboardButton(text="Меню 🏠", callback_data="to_main")])
    text = f"<tg-emoji emoji-id='5348252551546442951'>🔥</tg-emoji> <b>Портфолио (Стр. {page+1}):</b>\n\n<tg-emoji emoji-id='5352542124363522127'>🔥</tg-emoji> <i>Выберите интересующий вас кейс:</i>"
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_list))

@router.callback_query(ProjectCB.filter())
async def show_case(callback: types.CallbackQuery, callback_data: ProjectCB):
    await callback.answer()
    project = config.PROJECTS[callback_data.c][callback_data.i]
    with suppress(TelegramAPIError): await callback.message.delete()
    await callback.message.answer_video(video=project['media_id'], caption=project['text'], reply_markup=get_project_kb(callback_data.c, project['review_msg_id']))

@router.callback_query(ReviewCB.filter())
async def send_review(callback: types.CallbackQuery, callback_data: ReviewCB, bot):
    try:
        await bot.forward_message(callback.message.chat.id, config.REVIEWS_CHANNEL_ID, callback_data.m)
        await callback.answer("Отзыв загружен")
    except TelegramAPIError:
        await callback.answer("Ошибка загрузки отзыва.", show_alert=True)
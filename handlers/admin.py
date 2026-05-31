import json
import os
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import settings

router = Router()
STATS_FILE = "stats.json"

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE) as f:
            return json.load(f)
    return {"total_downloads": 0, "total_users": [], "video_downloads": 0, "audio_downloads": 0, "errors": 0}

def make_admin_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
         InlineKeyboardButton(text="🔄 Сбросить", callback_data="admin_reset")],
    ])
    return kb

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != settings.ADMIN_ID:
        await message.answer("⛔️ Нет доступа.")
        return
    stats = load_stats()
    await message.answer(
        "👑 <b>Админ панель</b>\n\n"
        f"👥 Пользователей: <b>{len(stats['total_users'])}</b>\n"
        f"📥 Скачиваний: <b>{stats['total_downloads']}</b>\n"
        f"🎬 Видео: <b>{stats['video_downloads']}</b>\n"
        f"🎵 Аудио: <b>{stats['audio_downloads']}</b>\n"
        f"❌ Ошибок: <b>{stats['errors']}</b>",
        parse_mode="HTML",
        reply_markup=make_admin_keyboard()
    )

@router.callback_query(lambda c: c.data.startswith("admin_"))
async def process_admin(callback: CallbackQuery):
    if callback.from_user.id != settings.ADMIN_ID:
        await callback.answer("⛔️ Нет доступа!", show_alert=True)
        return
    if callback.data == "admin_stats":
        stats = load_stats()
        await callback.message.edit_text(
            "📊 <b>Статистика</b>\n\n"
            f"👥 Пользователей: <b>{len(stats['total_users'])}</b>\n"
            f"📥 Скачиваний: <b>{stats['total_downloads']}</b>\n"
            f"🎬 Видео: <b>{stats['video_downloads']}</b>\n"
            f"🎵 Аудио: <b>{stats['audio_downloads']}</b>\n"
            f"❌ Ошибок: <b>{stats['errors']}</b>",
            parse_mode="HTML",
            reply_markup=make_admin_keyboard()
        )
    elif callback.data == "admin_reset":
        with open(STATS_FILE, "w") as f:
            json.dump({"total_downloads": 0, "total_users": [], "video_downloads": 0, "audio_downloads": 0, "errors": 0}, f)
        await callback.answer("✅ Сброшено!", show_alert=True)
    await callback.answer()

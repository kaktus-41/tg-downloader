import os
import glob
import asyncio
import tempfile
import time
import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import yt_dlp
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
user_urls = {}
user_requests = defaultdict(list)
MAX_REQUESTS = 3
TIME_WINDOW = 60
executor_pool = ThreadPoolExecutor(max_workers=3)

STATS_FILE = "stats.json"

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE) as f:
            return json.load(f)
    return {"total_downloads": 0, "total_users": [], "video_downloads": 0, "audio_downloads": 0, "errors": 0}

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f)

def record_download(user_id, download_type):
    stats = load_stats()
    stats["total_downloads"] += 1
    if str(user_id) not in stats["total_users"]:
        stats["total_users"].append(str(user_id))
    if download_type == "video":
        stats["video_downloads"] += 1
    else:
        stats["audio_downloads"] += 1
    save_stats(stats)

def record_error():
    stats = load_stats()
    stats["errors"] += 1
    save_stats(stats)

def is_spam(user_id):
    now = time.time()
    reqs = [t for t in user_requests[user_id] if now - t < TIME_WINDOW]
    user_requests[user_id] = reqs
    if len(reqs) >= MAX_REQUESTS:
        return True
    user_requests[user_id].append(now)
    return False

def make_format_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🎬 360p", callback_data="video_360"),
        InlineKeyboardButton("🎬 720p", callback_data="video_720"),
        InlineKeyboardButton("🎬 1080p", callback_data="video_1080"),
        InlineKeyboardButton("🎵 MP3", callback_data="audio_mp3"),
    )
    kb.add(InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
    return kb

def make_main_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("📥 Как скачать", callback_data="how_to"),
        InlineKeyboardButton("🌍 Поддерживаемые сайты", callback_data="sites"),
        InlineKeyboardButton("❓ Помощь", callback_data="help"),
    )
    return kb

def make_admin_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast"),
        InlineKeyboardButton("🔄 Сбросить статистику", callback_data="admin_reset"),
    )
    return kb

def _download_video(url, output_dir, quality):
    fmt = {"360": "bestvideo[height<=360]+bestaudio/best", "720": "bestvideo[height<=720]+bestaudio/best"}.get(quality, "bestvideo+bestaudio/best")
    ydl_opts = {"outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"), "format": fmt, "merge_output_format": "mp4", "quiet": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if not os.path.exists(filename):
            filename = filename.rsplit(".", 1)[0] + ".mp4"
        return filename, info.get("title", "video")

def _download_audio(url, output_dir):
    ydl_opts = {
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "format": "bestaudio/best",
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
        "quiet": True, "no_warnings": True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title", "audio")
    mp3_files = glob.glob(os.path.join(output_dir, "*.mp3"))
    if not mp3_files:
        raise Exception("MP3 файл не найден")
    return mp3_files[0], title

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет, <b>{}</b>!\n\n"
        "🤖 Я <b>DownAny Bot</b> — скачиваю видео и музыку\n"
        "с любых сайтов прямо в Telegram.\n\n"
        "📎 Просто отправь мне ссылку на видео!\n\n"
        "🌍 Поддерживаю <b>1000+ сайтов</b>:\n"
        "YouTube • TikTok • Instagram • Twitter/X\n"
        "ВКонтакте • Rutube • Facebook и другие\n\n"
        "⚡️ Лимит: <b>3 запроса в минуту</b>".format(message.from_user.first_name),
        parse_mode="HTML",
        reply_markup=make_main_keyboard()
    )

@dp.message_handler(commands=["admin"])
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔️ У вас нет доступа.")
        return
    stats = load_stats()
    await message.answer(
        "👑 <b>Админ панель</b>\n\n"
        "📊 Быстрая статистика:\n"
        f"👥 Пользователей: <b>{len(stats['total_users'])}</b>\n"
        f"📥 Всего скачиваний: <b>{stats['total_downloads']}</b>\n"
        f"🎬 Видео: <b>{stats['video_downloads']}</b>\n"
        f"🎵 Аудио: <b>{stats['audio_downloads']}</b>\n"
        f"❌ Ошибок: <b>{stats['errors']}</b>",
        parse_mode="HTML",
        reply_markup=make_admin_keyboard()
    )

@dp.message_handler(commands=["stats"])
async def cmd_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔️ У вас нет доступа.")
        return
    stats = load_stats()
    await message.answer(
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Уникальных пользователей: <b>{len(stats['total_users'])}</b>\n"
        f"📥 Всего скачиваний: <b>{stats['total_downloads']}</b>\n"
        f"🎬 Видео скачано: <b>{stats['video_downloads']}</b>\n"
        f"🎵 Аудио скачано: <b>{stats['audio_downloads']}</b>\n"
        f"❌ Ошибок: <b>{stats['errors']}</b>\n\n"
        f"📈 Успешность: <b>{round(stats['total_downloads'] / max(stats['total_downloads'] + stats['errors'], 1) * 100)}%</b>",
        parse_mode="HTML"
    )

@dp.callback_query_handler(lambda c: c.data.startswith("admin_"))
async def process_admin(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔️ Нет доступа!", show_alert=True)
        return
    if callback.data == "admin_stats":
        stats = load_stats()
        await callback.message.edit_text(
            "📊 <b>Подробная статистика</b>\n\n"
            f"👥 Уникальных пользователей: <b>{len(stats['total_users'])}</b>\n"
            f"📥 Всего скачиваний: <b>{stats['total_downloads']}</b>\n"
            f"🎬 Видео: <b>{stats['video_downloads']}</b>\n"
            f"🎵 Аудио: <b>{stats['audio_downloads']}</b>\n"
            f"❌ Ошибок: <b>{stats['errors']}</b>\n\n"
            f"📈 Успешность: <b>{round(stats['total_downloads'] / max(stats['total_downloads'] + stats['errors'], 1) * 100)}%</b>",
            parse_mode="HTML",
            reply_markup=make_admin_keyboard()
        )
    elif callback.data == "admin_reset":
        save_stats({"total_downloads": 0, "total_users": [], "video_downloads": 0, "audio_downloads": 0, "errors": 0})
        await callback.answer("✅ Статистика сброшена!", show_alert=True)
    elif callback.data == "admin_broadcast":
        await callback.message.edit_text(
            "📢 <b>Рассылка</b>\n\n"
            "Отправь сообщение командой:\n"
            "<code>/broadcast Текст сообщения</code>",
            parse_mode="HTML"
        )
    await callback.answer()

@dp.message_handler(commands=["broadcast"])
async def cmd_broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔️ У вас нет доступа.")
        return
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        await message.answer("Укажи текст: /broadcast Привет всем!")
        return
    stats = load_stats()
    sent = 0
    failed = 0
    for user_id in stats["total_users"]:
        try:
            await bot.send_message(int(user_id), f"📢 <b>Сообщение от администратора:</b>\n\n{text}", parse_mode="HTML")
            sent += 1
        except:
            failed += 1
    await message.answer(f"✅ Отправлено: {sent}\n❌ Не доставлено: {failed}")

@dp.callback_query_handler(lambda c: c.data in ["how_to", "sites", "help", "cancel"])
async def process_menu(callback: types.CallbackQuery):
    if callback.data == "how_to":
        await callback.message.edit_text(
            "📎 <b>Как скачать видео:</b>\n\n"
            "1️⃣ Скопируй ссылку на видео\n"
            "2️⃣ Отправь её мне\n"
            "3️⃣ Выбери формат (видео или MP3)\n"
            "4️⃣ Получи файл!",
            parse_mode="HTML"
        )
    elif callback.data == "sites":
        await callback.message.edit_text(
            "🌍 <b>Поддерживаемые сайты:</b>\n\n"
            "YouTube • TikTok • Instagram\n"
            "Twitter/X • Facebook • Vimeo\n"
            "Twitch • Rutube • ВКонтакте\n"
            "SoundCloud • Bandcamp\n\n"
            "И ещё <b>1000+</b> сайтов! 🚀",
            parse_mode="HTML"
        )
    elif callback.data == "help":
        await callback.message.edit_text(
            "❓ <b>Помощь:</b>\n\n"
            "• Максимальный файл: <b>50 МБ</b>\n"
            "• Лимит: <b>3 запроса в минуту</b>\n"
            "• Если файл большой — выбери качество пониже\n\n"
            "По вопросам: @DownAny_bot",
            parse_mode="HTML"
        )
    elif callback.data == "cancel":
        await callback.message.edit_text("❌ Отменено. Отправь новую ссылку.")
    await callback.answer()

@dp.message_handler()
async def handle_url(message: types.Message):
    url = message.text.strip()
    if not url.startswith(("http://", "https://")):
        await message.answer(
            "⚠️ Это не похоже на ссылку.\n"
            "Отправь ссылку начинающуюся с <b>http://</b> или <b>https://</b>",
            parse_mode="HTML"
        )
        return
    if is_spam(message.from_user.id):
        await message.answer("⛔️ Слишком много запросов! Подожди минуту.")
        return
    user_urls[message.from_user.id] = url
    await message.answer(
        "🎯 Ссылка получена! Выбери формат:",
        reply_markup=make_format_keyboard()
    )

@dp.callback_query_handler(lambda c: c.data.startswith("video_") or c.data.startswith("audio_"))
async def process_download(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    url = user_urls.get(user_id)
    if not url:
        await callback.message.edit_text("⚠️ Сначала отправь ссылку!")
        return
    await callback.message.edit_text("⏳ Скачиваю... Подожди немного.")
    loop = asyncio.get_event_loop()
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            if callback.data.startswith("video_"):
                quality = callback.data.split("_")[1]
                filepath, title = await loop.run_in_executor(executor_pool, _download_video, url, tmpdir, quality)
                file_size = os.path.getsize(filepath)
                if file_size > 50 * 1024 * 1024:
                    await callback.message.edit_text(
                        "❌ Файл больше 50 МБ\nПопробуй качество пониже.",
                        reply_markup=make_format_keyboard()
                    )
                    return
                await callback.message.edit_text("📤 Отправляю...")
                with open(filepath, "rb") as f:
                    await bot.send_video(callback.message.chat.id, f, caption=f"✅ {title}")
                record_download(user_id, "video")
            else:
                filepath, title = await loop.run_in_executor(executor_pool, _download_audio, url, tmpdir)
                file_size = os.path.getsize(filepath)
                if file_size > 50 * 1024 * 1024:
                    await callback.message.edit_text("❌ Файл больше 50 МБ.")
                    return
                await callback.message.edit_text("📤 Отправляю...")
                with open(filepath, "rb") as f:
                    await bot.send_audio(callback.message.chat.id, f, title=title, caption=f"🎵 {title}")
                record_download(user_id, "audio")
        await callback.message.delete()
    except Exception as e:
        record_error()
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    user_urls.pop(user_id, None)
    await callback.answer()

async def set_commands():
    await bot.set_my_commands([
        BotCommand("start", "Главное меню"),
        BotCommand("admin", "Админ панель"),
        BotCommand("stats", "Статистика"),
        BotCommand("help", "Помощь"),
    ])

async def on_startup(dp):
    await set_commands()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

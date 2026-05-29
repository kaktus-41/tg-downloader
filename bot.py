import os
import glob
import asyncio
import tempfile
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import yt_dlp
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from aiogram.utils.exceptions import MessageNotModified

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
user_urls = {}
user_requests = defaultdict(list)
MAX_REQUESTS = 3
TIME_WINDOW = 60
executor_pool = ThreadPoolExecutor(max_workers=3)

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
        InlineKeyboardButton("🎵 MP3 аудио", callback_data="audio_mp3"),
    )
    kb.add(InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
    return kb

def make_main_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("📥 Скачать видео", callback_data="how_to"),
        InlineKeyboardButton("ℹ️ Поддерживаемые сайты", callback_data="sites"),
        InlineKeyboardButton("❓ Помощь", callback_data="help"),
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
        "quiet": True,
        "no_warnings": True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title", "audio")
    mp3_files = glob.glob(os.path.join(output_dir, "*.mp3"))
    if not mp3_files:
        raise Exception("MP3 файл не найден")
    return mp3_files[0], title

async def set_commands():
    await bot.set_my_commands([
        BotCommand("start", "Главное меню"),
        BotCommand("help", "Помощь"),
        BotCommand("sites", "Поддерживаемые сайты"),
    ])

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

@dp.message_handler(commands=["help"])
async def cmd_help(message: types.Message):
    await message.answer(
        "❓ <b>Как пользоваться:</b>\n\n"
        "1️⃣ Скопируй ссылку на видео\n"
        "2️⃣ Отправь её мне\n"
        "3️⃣ Выбери формат и качество\n"
        "4️⃣ Получи файл!\n\n"
        "⚠️ <b>Ограничения:</b>\n"
        "• Максимальный размер файла: 50 МБ\n"
        "• Лимит запросов: 3 в минуту\n\n"
        "🆘 Если что-то не работает — попробуй другое качество",
        parse_mode="HTML"
    )

@dp.message_handler(commands=["sites"])
async def cmd_sites(message: types.Message):
    await message.answer(
        "🌍 <b>Поддерживаемые сайты:</b>\n\n"
        "🎬 <b>Видео:</b>\n"
        "• YouTube\n• TikTok\n• Instagram\n• Twitter/X\n"
        "• Facebook\n• Vimeo\n• Twitch\n• Rutube\n• ВКонтакте\n\n"
        "🎵 <b>Музыка:</b>\n"
        "• SoundCloud\n• Bandcamp\n\n"
        "И ещё 1000+ сайтов! 🚀",
        parse_mode="HTML"
    )

@dp.callback_query_handler(lambda c: c.data in ["how_to", "sites", "help", "cancel"])
async def process_menu(callback: types.CallbackQuery):
    if callback.data == "how_to":
        await callback.message.edit_text(
            "📎 <b>Отправь мне ссылку на видео!</b>\n\n"
            "Просто скопируй ссылку из браузера и вставь сюда.",
            parse_mode="HTML"
        )
    elif callback.data == "sites":
        await callback.message.edit_text(
            "🌍 <b>Поддерживаемые сайты:</b>\n\n"
            "YouTube • TikTok • Instagram • Twitter/X\n"
            "Facebook • Vimeo • Twitch • Rutube\n"
            "ВКонтакте • SoundCloud • и 1000+ других!",
            parse_mode="HTML"
        )
    elif callback.data == "help":
        await callback.message.edit_text(
            "❓ <b>Как пользоваться:</b>\n\n"
            "1️⃣ Скопируй ссылку на видео\n"
            "2️⃣ Отправь её мне\n"
            "3️⃣ Выбери формат (видео или MP3)\n"
            "4️⃣ Получи файл!",
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
        await message.answer("⛔️ Слишком много запросов! Подожди минуту и попробуй снова.")
        return
    user_urls[message.from_user.id] = url
    await message.answer(
        "🎯 Ссылка получена!\nВыбери формат и качество:",
        reply_markup=make_format_keyboard()
    )

@dp.callback_query_handler(lambda c: c.data.startswith("video_") or c.data.startswith("audio_"))
async def process_download(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    url = user_urls.get(user_id)
    if not url:
        await callback.message.edit_text("⚠️ Сначала отправь ссылку!")
        return
    await callback.message.edit_text("⏳ Скачиваю... Это может занять минуту.")
    loop = asyncio.get_event_loop()
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            if callback.data.startswith("video_"):
                quality = callback.data.split("_")[1]
                filepath, title = await loop.run_in_executor(executor_pool, _download_video, url, tmpdir, quality)
                file_size = os.path.getsize(filepath)
                if file_size > 50 * 1024 * 1024:
                    await callback.message.edit_text(
                        "❌ Файл больше 50 МБ\n"
                        "Попробуй выбрать качество пониже (360p или 720p)",
                        reply_markup=make_format_keyboard()
                    )
                    return
                await callback.message.edit_text("📤 Отправляю...")
                with open(filepath, "rb") as f:
                    await bot.send_video(callback.message.chat.id, f, caption=f"✅ {title}")
            else:
                filepath, title = await loop.run_in_executor(executor_pool, _download_audio, url, tmpdir)
                file_size = os.path.getsize(filepath)
                if file_size > 50 * 1024 * 1024:
                    await callback.message.edit_text("❌ Файл больше 50 МБ.")
                    return
                await callback.message.edit_text("📤 Отправляю...")
                with open(filepath, "rb") as f:
                    await bot.send_audio(callback.message.chat.id, f, title=title, caption=f"🎵 {title}")
        await callback.message.delete()
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    user_urls.pop(user_id, None)
    await callback.answer()

async def on_startup(dp):
    await set_commands()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

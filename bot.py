import os
import glob
import asyncio
import tempfile
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import yt_dlp
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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

def make_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("360p", callback_data="video_360"),
        InlineKeyboardButton("720p", callback_data="video_720"),
        InlineKeyboardButton("1080p", callback_data="video_1080"),
        InlineKeyboardButton("MP3", callback_data="audio_mp3"),
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

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! 👋\n"
        "Отправь ссылку на видео.\n\n"
        "Поддерживаются: YouTube, TikTok, Instagram, Twitter/X и 1000+ сайтов.\n"
        "Лимит: 3 запроса в минуту."
    )

@dp.message_handler()
async def handle_url(message: types.Message):
    url = message.text.strip()
    if not url.startswith(("http://", "https://")):
        await message.answer("Отправь ссылку начинающуюся с http")
        return
    if is_spam(message.from_user.id):
        await message.answer("Слишком много запросов! Подожди минуту.")
        return
    user_urls[message.from_user.id] = url
    await message.answer("Выбери формат:", reply_markup=make_keyboard())

@dp.callback_query_handler(lambda c: c.data.startswith("video_") or c.data.startswith("audio_"))
async def process_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    url = user_urls.get(user_id)
    if not url:
        await callback.message.edit_text("Сначала отправь ссылку!")
        return
    await callback.message.edit_text("Скачиваю...")
    loop = asyncio.get_event_loop()
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            if callback.data.startswith("video_"):
                quality = callback.data.split("_")[1]
                filepath, title = await loop.run_in_executor(executor_pool, _download_video, url, tmpdir, quality)
                file_size = os.path.getsize(filepath)
                if file_size > 50 * 1024 * 1024:
                    await callback.message.edit_text("Файл больше 50 МБ, попробуй качество пониже.")
                    return
                await callback.message.edit_text("Отправляю...")
                with open(filepath, "rb") as f:
                    await bot.send_video(callback.message.chat.id, f, caption=title)
            else:
                filepath, title = await loop.run_in_executor(executor_pool, _download_audio, url, tmpdir)
                file_size = os.path.getsize(filepath)
                if file_size > 50 * 1024 * 1024:
                    await callback.message.edit_text("Файл больше 50 МБ.")
                    return
                await callback.message.edit_text("Отправляю...")
                with open(filepath, "rb") as f:
                    await bot.send_audio(callback.message.chat.id, f, title=title)
        await callback.message.delete()
    except Exception as e:
        await callback.message.edit_text(f"Ошибка: {e}")
    user_urls.pop(user_id, None)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

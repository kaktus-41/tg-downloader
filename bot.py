import os
import tempfile
import yt_dlp
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

user_urls = {}

def make_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🎬 360p", callback_data="video_360"),
        InlineKeyboardButton("🎬 720p", callback_data="video_720"),
        InlineKeyboardButton("🎬 1080p", callback_data="video_1080"),
        InlineKeyboardButton("🎵 MP3", callback_data="audio_mp3"),
    )
    return kb

def download_video(url, output_dir, quality):
    if quality == "360":
        fmt = "bestvideo[height<=360]+bestaudio/best[height<=360]/best"
    elif quality == "720":
        fmt = "bestvideo[height<=720]+bestaudio/best[height<=720]/best"
    else:
        fmt = "bestvideo+bestaudio/best"

    ydl_opts = {
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "format": fmt,
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "max_filesize": 50 * 1024 * 1024,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if not os.path.exists(filename):
            filename = filename.rsplit(".", 1)[0] + ".mp4"
        return filename, info.get("title", "video")

def download_audio(url, output_dir):
    ydl_opts = {
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
        "no_warnings": True,
        "max_filesize": 50 * 1024 * 1024,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title", "audio")
        filename = os.path.join(output_dir, title + ".mp3")
        return filename, title

@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! 👋\n"
        "Отправь ссылку на видео — выберешь формат и качество.\n\n"
        "Поддерживаются: YouTube, TikTok, Instagram, Twitter/X, ВКонтакте и 1000+ сайтов."
    )

@dp.message_handler()
async def handle_url(message: types.Message):
    url = message.text.strip()
    if not url.startswith(("http://", "https://")):
        await message.answer("Отправь ссылку начинающуюся с http")
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

    await callback.message.edit_text("⏳ Скачиваю...")

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            if callback.data.startswith("video_"):
                quality = callback.data.split("_")[1]
                filepath, title = download_video(url, tmpdir, quality)
                file_size = os.path.getsize(filepath)
                if file_size > 50 * 1024 * 1024:
                    await callback.me
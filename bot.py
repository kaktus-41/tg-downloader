import asyncio
import os
import tempfile
import yt_dlp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def download_media(url: str, output_dir: str) -> str:
    ydl_opts = {
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
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
        return filename

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! 👋\n"
        "Отправь мне ссылку на видео — скачаю откуда угодно.\n\n"
        "Поддерживаются: YouTube, TikTok, Instagram, Twitter/X, "
        "ВКонтакте, Rutube и ещё 1000+ сайтов."
    )

@dp.message(F.text)
async def handle_url(message: types.Message):
    url = message.text.strip()
    if not url.startswith(("http://", "https://")):
        await message.answer("Пожалуйста, отправь ссылку (начинающуюся с http/https)")
        return
    status_msg = await message.answer("⏳ Скачиваю...")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = download_media(url, tmpdir)
            file_size = os.path.getsize(filepath)
            if file_size > 50 * 1024 * 1024:
                await status_msg.edit_text("❌ Файл больше 50 МБ — Telegram не позволяет.")
                return
            await status_msg.edit_text("📤 Отправляю...")
            with open(filepath, "rb") as f:
                await message.answer_video(
                    video=types.BufferedInputFile(f.read(), filename=os.path.basename(filepath)),
                    caption="✅ Готово!"
                )
        await status_msg.delete()
    except yt_dlp.utils.DownloadError as e:
        await status_msg.edit_text(f"❌ Не удалось скачать:\n<code>{e}</code>", parse_mode="HTML")
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

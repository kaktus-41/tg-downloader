from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import os
import tempfile
from config import settings
from database.requests import log_download
from keyboards.inline import make_format_keyboard, make_playlist_keyboard
from services.downloader import get_playlist_info, download_video, download_audio

router = Router()

class DownloadStates(StatesGroup):
    waiting_for_format = State()

def is_playlist(url: str) -> bool:
    return "playlist" in url or "list=" in url

def is_telegram_link(url: str) -> bool:
    return "t.me" in url or "telegram.me" in url

@router.message(F.text.startswith("http://") | F.text.startswith("https://"))
async def handle_url(message: Message, state: FSMContext):
    url = message.text.strip()
    if is_telegram_link(url):
        await message.answer("Ссылки из Telegram не поддерживаются. Отправь ссылку с YouTube, TikTok, Instagram или другого сайта.")
        return
    await state.update_data(current_url=url)
    if is_playlist(url):
        status = await message.answer("Получаю информацию о плейлисте...")
        try:
            title, count, entries = await get_playlist_info(url)
            count = min(count, settings.PLAYLIST_LIMIT)
            await status.edit_text(
                f"Плейлист найден!\n\n{title}\nВидео: {count}\n\nВыбери что скачать:",
                reply_markup=make_playlist_keyboard()
            )
            await state.set_state(DownloadStates.waiting_for_format)
        except Exception as e:
            await status.edit_text(f"Ошибка: {e}")
    else:
        await message.answer("Выбери формат:", reply_markup=make_format_keyboard())
        await state.set_state(DownloadStates.waiting_for_format)

@router.message()
async def handle_non_url(message: Message):
    await message.answer("Отправь ссылку начинающуюся с http:// или https://")

@router.callback_query(DownloadStates.waiting_for_format, F.data.startswith("video_") | F.data.startswith("audio_"))
async def process_single_download(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()
    url = data.get("current_url")
    if not url:
        await callback.message.edit_text("Ссылка потерялась. Отправь заново!")
        await state.clear()
        return
    await callback.message.edit_text("Скачиваю... Подожди.")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            if callback.data.startswith("video_"):
                quality = callback.data.split("_")[1]
                filepath, title = await download_video(url, tmpdir, quality)
                file_size = os.path.getsize(filepath)
                if file_size > settings.MAX_FILE_SIZE:
                    await callback.message.edit_text(f"Файл {file_size // 1024 // 1024} МБ — больше 50 МБ. Попробуй качество пониже.")
                    return
                await callback.message.edit_text("Отправляю...")
                with open(filepath, "rb") as f:
                    file_data = f.read()
                await callback.message.answer_video(
                    video=BufferedInputFile(file_data, filename=os.path.basename(filepath)),
                    caption=title
                )
                await log_download(user_id, "video", "success")
            else:
                filepath, title = await download_audio(url, tmpdir)
                file_size = os.path.getsize(filepath)
                if file_size > settings.MAX_FILE_SIZE:
                    await callback.message.edit_text(f"Файл {file_size // 1024 // 1024} МБ — больше 50 МБ.")
                    return
                await callback.message.edit_text("Отправляю...")
                with open(filepath, "rb") as f:
                    file_data = f.read()
                await callback.message.answer_audio(
                    audio=BufferedInputFile(file_data, filename=os.path.basename(filepath)),
                    title=title,
                    caption=title
                )
                await log_download(user_id, "audio", "success")
        await callback.message.delete()
    except Exception as e:
        await log_download(user_id, "unknown", "error")
        await callback.message.edit_text(f"Ошибка при загрузке: {e}")
    finally:
        await state.clear()
    await callback.answer()

@router.callback_query(DownloadStates.waiting_for_format, F.data.startswith("playlist_"))
async def process_playlist_download(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()
    url = data.get("current_url")
    mode = callback.data.split("_")[1]
    if not url:
        await callback.message.edit_text("Ссылка потерялась. Отправь заново!")
        await state.clear()
        return
    await callback.message.edit_text("Начинаю скачивание плейлиста...")
    try:
        _, count, entries = await get_playlist_info(url)
        count = min(count, settings.PLAYLIST_LIMIT)
        success, failed = 0, 0
        for i, entry in enumerate(entries[:settings.PLAYLIST_LIMIT]):
            video_url = entry.get("url") or f"https://youtube.com/watch?v={entry.get('id')}"
            try:
                await callback.message.edit_text(f"Скачиваю {i+1} из {count}...")
                with tempfile.TemporaryDirectory() as tmpdir:
                    if mode == "video":
                        filepath, title = await download_video(video_url, tmpdir, "720")
                        with open(filepath, "rb") as f:
                            file_data = f.read()
                        await callback.message.answer_video(
                            video=BufferedInputFile(file_data, filename=os.path.basename(filepath)),
                            caption=title
                        )
                        await log_download(user_id, "video", "success")
                    else:
                        filepath, title = await download_audio(video_url, tmpdir)
                        with open(filepath, "rb") as f:
                            file_data = f.read()
                        await callback.message.answer_audio(
                            audio=BufferedInputFile(file_data, filename=os.path.basename(filepath)),
                            title=title,
                            caption=title
                        )
                        await log_download(user_id, "audio", "success")
                success += 1
            except Exception:
                failed += 1
                await log_download(user_id, mode, "error")
                continue
        await callback.message.edit_text(f"Плейлист обработан!\nУспешно: {success}\nОшибок: {failed}")
    except Exception as e:
        await callback.message.edit_text(f"Критическая ошибка: {e}")
    finally:
        await state.clear()
    await callback.answer()

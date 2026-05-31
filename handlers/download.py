from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
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
    return "t.me" in url or "telegram.me" in url or "telegram.org" in url

@router.message(F.text.startswith("http://") | F.text.startswith("https://"))
async def handle_url(message: Message, state: FSMContext):
    url = message.text.strip()
    await state.update_data(current_url=url)
    
    if is_telegram_link(url):
        await message.answer("❌ Ссылки из Telegram не поддерживаются.
Отправь ссылку с YouTube, TikTok, Instagram или другого сайта.")
        await state.clear()
        return

    if is_playlist(url):
        status = await message.answer("🔍 Получаю информацию о плейлисте...")
        try:
            title, count, entries = await get_playlist_info(url)
            count = min(count, settings.PLAYLIST_LIMIT)
            await status.edit_text(
                f"📋 <b>Плейлист найден!</b>\n\n"
                f"📌 {title}\n"
                f"🎬 Видео: <b>{count}</b> (макс. {settings.PLAYLIST_LIMIT})\n\n"
                f"Выбери что скачать:",
                parse_mode="HTML",
                reply_markup=make_playlist_keyboard()
            )
            await state.set_state(DownloadStates.waiting_for_format)
        except Exception as e:
            await status.edit_text(f"❌ Ошибка парсинга плейлиста: {e}")
    else:
        await message.answer("🎯 Выбери формат:", reply_markup=make_format_keyboard())
        await state.set_state(DownloadStates.waiting_for_format)

@router.message()
async def handle_non_url(message: Message):
    await message.answer("⚠️ Пожалуйста, отправь корректную ссылку, начинающуюся с http:// или https://")

@router.callback_query(DownloadStates.waiting_for_format, F.data.startswith("video_") | F.data.startswith("audio_"))
async def process_single_download(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()
    url = data.get("current_url")
    
    if not url:
        await callback.message.edit_text("⚠️ Ссылка потерялась. Отправь её заново!")
        await state.clear()
        return

    await callback.message.edit_text("⏳ Скачиваю медиафайл... Пожалуйста, подождите.")
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            if callback.data.startswith("video_"):
                quality = callback.data.split("_")[1]
                filepath, title = await download_video(url, tmpdir, quality)
                
                if os.path.getsize(filepath) > settings.MAX_FILE_SIZE:
                    await callback.message.edit_text("❌ Файл превышает лимит в 2 ГБ.")
                    return
                    
                await callback.message.edit_text("📤 Отправляю видео в Telegram...")
                with open(filepath, "rb") as f:
                    await callback.message.answer_video(video=f, caption=f"🎬 {title}")
                await log_download(user_id, "video", "success")
            else:
                filepath, title = await download_audio(url, tmpdir)
                
                if os.path.getsize(filepath) > settings.MAX_FILE_SIZE:
                    await callback.message.edit_text("❌ Файл превышает лимит в 2 ГБ.")
                    return
                    
                await callback.message.edit_text("📤 Отправляю аудио в Telegram...")
                with open(filepath, "rb") as f:
                    await callback.message.answer_audio(audio=f, title=title, caption=f"🎵 {title}")
                await log_download(user_id, "audio", "success")
                
        await callback.message.delete()
    except Exception as e:
        await log_download(user_id, "unknown", "error")
        await callback.message.edit_text(f"❌ Ошибка при загрузке: {e}")
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
        await callback.message.edit_text("⚠️ Ссылка потерялась. Отправь её заново!")
        await state.clear()
        return

    await callback.message.edit_text("⏳ Начинаю скачивание плейлиста... Это займет время.")
    
    try:
        _, count, entries = await get_playlist_info(url)
        count = min(count, settings.PLAYLIST_LIMIT)
        success, failed = 0, 0
        
        for i, entry in enumerate(entries[:settings.PLAYLIST_LIMIT]):
            video_url = entry.get("url") or f"https://youtube.com/watch?v={entry.get('id')}"
            try:
                await callback.message.edit_text(f"⏳ Скачиваю элемент {i+1} из {count}...")
                with tempfile.TemporaryDirectory() as tmpdir:
                    if mode == "video":
                        filepath, title = await download_video(video_url, tmpdir, "720")
                        with open(filepath, "rb") as f:
                            await callback.message.answer_video(video=f, caption=f"🎬 {title}")
                        await log_download(user_id, "video", "success")
                    else:
                        filepath, title = await download_audio(video_url, tmpdir)
                        with open(filepath, "rb") as f:
                            await callback.message.answer_audio(audio=f, title=title, caption=f"🎵 {title}")
                        await log_download(user_id, "audio", "success")
                success += 1
            except Exception:
                failed += 1
                await log_download(user_id, mode, "error")
                continue
                
        await callback.message.edit_text(
            f"✅ <b>Плейлист успешно обработан!</b>\n\n"
            f"✔️ Успешно отправлено: <b>{success}</b>\n"
            f"❌ Ошибок скачивания: <b>{failed}</b>",
            parse_mode="HTML"
        )
    except Exception as e:
        await callback.message.edit_text(f"❌ Критическая ошибка при работе с плейлистом: {e}")
    finally:
        await state.clear()
    await callback.answer()

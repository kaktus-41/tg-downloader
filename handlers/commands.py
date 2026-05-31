from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import settings

router = Router()

def make_main_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Как скачать", callback_data="how_to")],
        [InlineKeyboardButton(text="🌍 Поддерживаемые сайты", callback_data="sites")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")],
    ])
    return kb

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        "🤖 Я <b>DownAny Bot</b> — скачиваю видео и музыку\n"
        "с любых сайтов прямо в Telegram.\n\n"
        "📎 Отправь мне ссылку на видео!\n\n"
        "🌍 <b>1000+ сайтов:</b>\n"
        "YouTube • TikTok • Instagram • Twitter/X\n"
        "ВКонтакте • Rutube • и другие\n\n"
        "📦 До <b>50 МБ</b> | ⚡️ Лимит: <b>3 запроса/мин</b>",
        parse_mode="HTML",
        reply_markup=make_main_keyboard()
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "❓ <b>Помощь:</b>\n\n"
        "1️⃣ Скопируй ссылку на видео\n"
        "2️⃣ Отправь её мне\n"
        "3️⃣ Выбери формат\n"
        "4️⃣ Получи файл!\n\n"
        "• Файлы до <b>50 МБ</b>\n"
        "• Лимит: <b>3 запроса в минуту</b>",
        parse_mode="HTML"
    )

@router.callback_query(F.data.in_(["how_to", "sites", "help"]))
async def process_menu(callback: CallbackQuery):
    if callback.data == "how_to":
        await callback.message.edit_text(
            "📎 <b>Как скачать:</b>\n\n"
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
            "SoundCloud • и 1000+ других!",
            parse_mode="HTML"
        )
    elif callback.data == "help":
        await callback.message.edit_text(
            "❓ <b>Помощь:</b>\n\n"
            "• Файлы до <b>50 МБ</b>\n"
            "• Лимит: <b>3 запроса в минуту</b>\n"
            "• Большой файл — выбери качество пониже",
            parse_mode="HTML"
        )
    await callback.answer()

@router.callback_query(F.data == "cancel")
async def process_cancel(callback: CallbackQuery):
    await callback.message.edit_text("❌ Отменено. Отправь новую ссылку.")
    await callback.answer()

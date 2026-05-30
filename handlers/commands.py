from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
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
        "📦 До <b>2 ГБ</b> | ⚡️ Лимит: <b>3 запроса/мин</b>",
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
        "• Файлы до <b>2 ГБ</b>\n"
        "• Лимит: <b>3 запроса в минуту</b>",
        parse_mode="HTML"
    )

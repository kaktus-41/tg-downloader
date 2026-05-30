import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.types import BotCommand

from config import settings
from database.connection import init_db
from handlers import commands, admin, download
from middlewares.throttling import ThrottlingMiddleware

logging.basicConfig(level=logging.INFO)

async def set_commands(bot: Bot):
    commands_list = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="admin", description="Админ панель"),
    ]
    await bot.set_my_commands(commands_list)

async def main():
    await init_db()

    # 1. Создаем сервер с обязательным флагом is_local=True
    local_server = TelegramAPIServer(
        base=f"{settings.LOCAL_BOT_API_URL}/bot{{token}}",
        file=f"{settings.LOCAL_BOT_API_URL}/file/bot{{token}}/{{path}}",
        is_local=True
    )

    # 2. Подключаем сервер через сессию (правило aiogram 3)
    session = AiohttpSession(api=local_server)

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
        session=session
    )
    dp = Dispatcher()

    dp.message.middleware(ThrottlingMiddleware(rate_limit=settings.THROTTLING_RATE))

    dp.include_router(admin.router)
    dp.include_router(commands.router)
    dp.include_router(download.router)

    if settings.ADMIN_ID:
        try:
            await bot.send_message(settings.ADMIN_ID, "🟢 Бот запущен! Лимит 50 МБ снят, качаем до 2 ГБ.")
        except Exception:
            pass

    await set_commands(bot)
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")

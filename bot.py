import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
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

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher()

    dp.message.middleware(ThrottlingMiddleware(rate_limit=settings.THROTTLING_RATE))

    dp.include_router(admin.router)
    dp.include_router(commands.router)
    dp.include_router(download.router)

    if settings.ADMIN_ID:
        try:
            await bot.send_message(settings.ADMIN_ID, "🟢 Бот запущен!")
        except Exception:
            pass

    await set_commands(bot)
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")

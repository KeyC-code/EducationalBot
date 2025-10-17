import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config
from app.handlers import router
from app.utils.scheduler_utils import new_day
from db import Database

db = Database("database.db")
scheduler = AsyncIOScheduler()

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
    dp = Dispatcher()

    # Регистрация роутеров
    dp.include_router(router)

    # Настройка планировщика
    scheduler.start()
    scheduler.add_job(new_day, 'cron', hour=config.TIME, args=[db])

    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print('Bot stopped')
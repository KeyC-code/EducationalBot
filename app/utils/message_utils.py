import logging
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

async def safe_delete_message(message):
    try:
        await message.delete()
    except TelegramBadRequest as e:
        if "message to delete not found" in str(e):
            logging.warning(f"Message {message.message_id} already deleted or too old")
        else:
            logging.error(f"Error deleting message: {e}")

async def edit_or_send_message(bot: Bot, chat_id: int, message_id: int | None, text: str, **kwargs):
    try:
        if message_id:
            return await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, **kwargs)
        else:
            return await bot.send_message(chat_id=chat_id, text=text, **kwargs)
    except TelegramBadRequest as e:
        logging.error(f"Error editing/sending message: {e}")
        return await bot.send_message(chat_id=chat_id, text=text, **kwargs)

async def delete_previous_messages(bot: Bot, chat_id: int, message_ids: list[int]):
    for msg_id in message_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except TelegramBadRequest:
            pass
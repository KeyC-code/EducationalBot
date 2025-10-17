import glom
from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

import config
from db import Database

db = Database("database.db")

mainMenu = InlineKeyboardBuilder()
mainMenu.add(InlineKeyboardButton(text="Добавить новость", callback_data="btnAddNews"))
mainMenu.add(
    InlineKeyboardButton(text="Заблокировать пользователя", callback_data="btnBan")
)
mainMenu.add(
    InlineKeyboardButton(text="Разблокировать пользователя", callback_data="btnUnban")
)
mainMenu = mainMenu.adjust(1).as_markup()

# payMenu = InlineKeyboardBuilder()
# payMenu.add(InlineKeyboardButton(text="Стандартная (149р)", callback_data="subscribe:standard"))
# payMenu.add(InlineKeyboardButton(text="Премиальная (249р)", callback_data="subscribe:premium"))
# payMenu = payMenu.adjust(1).as_markup()


def get_payment_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="1 месяц - 65 ⭐️", callback_data="pay_1")],
            [InlineKeyboardButton(text="3 месяца - 110 ⭐️", callback_data="pay_3")],
        ]
    )
    return keyboard


topicMenu = InlineKeyboardBuilder()
topicMenu.add(InlineKeyboardButton(text="Название", callback_data="btnName"))
topicMenu.add(
    InlineKeyboardButton(text="Текст (ссылку Telegraph)", callback_data="btnText")
)
topicMenu.add(InlineKeyboardButton(text="Ссылка", callback_data="btnUrl"))
topicMenu.add(InlineKeyboardButton(text="Медиа", callback_data="btnMedia"))
topicMenu.add(InlineKeyboardButton(text="Удалить", callback_data="btnDell"))
topicMenu.add(InlineKeyboardButton(text="Назад", callback_data="btnBack"))
topicMenu = topicMenu.adjust(2, 2, 1, 1).as_markup()

changeBackMenu = InlineKeyboardBuilder()
changeBackMenu.add(InlineKeyboardButton(text="Назад", callback_data="btnChangeBack"))
changeBackMenu = changeBackMenu.adjust(1).as_markup()

backMenu = InlineKeyboardBuilder()
backMenu.add(InlineKeyboardButton(text="Назад", callback_data="btnBack"))
backMenu = backMenu.adjust(1).as_markup()

agreeMenu = InlineKeyboardBuilder()
agreeMenu.add(InlineKeyboardButton(text="Да", callback_data="btnYes"))
agreeMenu.add(InlineKeyboardButton(text="Нет", callback_data="btnNo"))
agreeMenu = agreeMenu.adjust(2).as_markup()

cancelMenu = ReplyKeyboardBuilder()
cancelMenu.add(KeyboardButton(text="Отмена"))
cancelMenu = cancelMenu.adjust(1).as_markup()


def pathMenu(topics, path, id, back=False):
    if back:
        key = path[-2]
    else:
        key = path[-1]
    if key == "main":
        tops = topics
    else:
        tops = glom.glom(topics, f"**.{key}")[0]
    keyboard = InlineKeyboardBuilder()
    for topic in tops:
        # Используем topic напрямую как callback_data
        keyboard.add(
            InlineKeyboardButton(text=db.get_item_name(topic), callback_data=topic)
        )
    if id == config.ADMIN_ID:
        keyboard.add(
            InlineKeyboardButton(text="➕📖Добавить подтему", callback_data="btnAdd")
        )
    if key != "main":
        if id == config.ADMIN_ID:
            keyboard.add(
                InlineKeyboardButton(
                    text="✏️📖Редактировать подтему", callback_data="btnChange"
                )
            )
        prev_topic = path[-2]
        # Используем prev_topic напрямую как callback_data
        keyboard.add(InlineKeyboardButton(text="Назад", callback_data=prev_topic))
    return keyboard.adjust(1).as_markup()


prepayMenu = InlineKeyboardBuilder()
prepayMenu.add(InlineKeyboardButton(text="Подписаться", callback_data="btnPrepay"))
prepayMenu = prepayMenu.adjust(1).as_markup()


def choiseMenu(results):
    keyboard = ReplyKeyboardBuilder()
    for result in results:
        keyboard.add(KeyboardButton(text=result))
    return keyboard.adjust(1).as_markup()

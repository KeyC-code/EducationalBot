import glom
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.callback_data import CallbackData

import config
from db import Database

db = Database("database.db")

mainMenu = InlineKeyboardMarkup(row_width=1)

btnAddNews = InlineKeyboardButton(text="Добавить новость", callback_data="btnAddNews")
btnBan = InlineKeyboardButton(text="Заблокировать пользователя", callback_data="btnBan")
btnUnban = InlineKeyboardButton(
    text="Разблокировать пользователя", callback_data="btnUnban"
)

mainMenu.insert(btnAddNews)
mainMenu.insert(btnBan)
mainMenu.insert(btnUnban)

topicMenu = InlineKeyboardMarkup(row_width=1)

btnName = InlineKeyboardButton(text="Название", callback_data="btnName")
btnText = InlineKeyboardButton(text="Текст (ссылку Telegraph)", callback_data="btnText")
btnUrl = InlineKeyboardButton(text="Ссылка", callback_data="btnUrl")
btnMedia = InlineKeyboardButton(text="Медиа", callback_data="btnMedia")
btnDell = InlineKeyboardButton(text="Удалить", callback_data="btnDell")
btnBack = InlineKeyboardButton(text="Назад", callback_data="btnBack")


topicMenu.row(btnName, btnText)
topicMenu.row(btnUrl, btnMedia)
topicMenu.insert(btnDell)
topicMenu.insert(btnBack)


changeBackMenu = InlineKeyboardMarkup(row_width=1).insert(
    InlineKeyboardButton(text="Назад", callback_data="btnChangeBack")
)


backMenu = InlineKeyboardMarkup(row_width=1).insert(
    InlineKeyboardButton(text="Назад", callback_data="btnBack")
)

agreeMenu = InlineKeyboardMarkup(row_width=1)

btnYes = InlineKeyboardButton(text="Да", callback_data="btnYes")
btnNo = InlineKeyboardButton(text="Нет", callback_data="btnNo")

agreeMenu.insert(btnYes)
agreeMenu.insert(btnNo)

cancelMenu = ReplyKeyboardMarkup(resize_keyboard=True).insert(
    KeyboardButton(text="Отмена")
)


def pathMenu(topics, path, id, back=False):
    if back:
        key = path[-2]
    else:
        key = path[-1]
    if key == "main":
        tops = topics
    else:
        tops = glom.glom(topics, f"**.{key}")[0]
    keyboard = InlineKeyboardMarkup(row_width=1)
    for topic in tops:
        callbackData = CallbackData(topic)
        button = InlineKeyboardButton(
            text=db.get_item_name(topic), callback_data=callbackData.new()
        )
        keyboard.insert(button)
    if id == config.ADMIN_ID:
        btnAdd = InlineKeyboardButton(
            text="➕📖Добавить подтему", callback_data="btnAdd"
        )
        keyboard.insert(btnAdd)
    if key != "main":
        if id == config.ADMIN_ID:
            btnChange = InlineKeyboardButton(
                text="✏️📖Редактировать подтему", callback_data="btnChange"
            )
            keyboard.insert(btnChange)
        prev_topic = path[-2]
        backCallbackData = CallbackData(prev_topic)
        button = InlineKeyboardButton(
            text="Назад", callback_data=backCallbackData.new()
        )
        keyboard.insert(button)
    return keyboard


# МЕНЮ ОПЛАТЫ
def payMenu(url1, url3):
    btnPay1 = InlineKeyboardButton(
        text=f"💳 1 месяц {config.LOWER_PRICE} RUB", url=url1
    )
    btnPay3 = InlineKeyboardButton(
        text=f"💳 3 месяца {config.HIGHER_PRICE} RUB", url=url3
    )
    return InlineKeyboardMarkup(row_width=1).insert(btnPay1).insert(btnPay3)


prepayMenu = InlineKeyboardMarkup(row_width=1)
btnPrepay = InlineKeyboardButton(text="Подписаться", callback_data="btnPrepay")
prepayMenu.insert(btnPrepay)


def choiseMenu(results):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for result in results:
        btn = KeyboardButton(text=result)
        keyboard.insert(btn)
    return keyboard

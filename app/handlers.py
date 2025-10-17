import ast
import json
import os
import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

import docx2txt
import glom
from aiogram import Bot, F, Router, types
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import LabeledPrice, PreCheckoutQuery
from aiogram.types.input_file import FSInputFile
from aiogram.utils.markdown import hide_link
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dateutil import relativedelta
from docx2python import docx2python

import app.keyboards as kb
import config
from app.states import State
from db import Database

router = Router()

db = Database("database.db")
scheduler = AsyncIOScheduler(timezone="Europe/Moscow")


def read_json(name):
    with open(name + ".json", "r") as file:
        data = json.load(file)
    return data


def save_json(dict={}, name=""):
    with open(name + ".json", "w") as file:
        json.dump(dict, file, ensure_ascii=True, indent=1)


@router.message(CommandStart())
async def Start(message: types.Message, bot: Bot):
    id = message.from_user.id
    # if id  == config.admin:
    #     await bot.send_message(id, "Добро пожаловать!")
    # else:
    if db.user_exists(id):
        if db.get_subed(id) == 1:
            await bot.send_message(
                id,
                """Вы уже зарегистрированы🤔

✍️ Напишите название интересующей темы в строке или проследуйте в меню и выберите разделы📚 (команда /topics)

Желаем удачи😉""",
            )
            try:
                now = datetime.now(timezone.utc) + timedelta(hours=config.UTC_STEP)
                sub = db.get_sub(id)
                year, month, day = sub.split(",")
                sub_date = datetime(
                    year=int(year), month=int(month), day=int(day), tzinfo=timezone.utc
                )
                delta = now - sub_date
                if id == config.ADMIN_ID:
                    pass
                elif delta.days <= 0:
                    await bot.send_message(
                        id, "⌚ Ваша подписка закончилась", reply_markup=kb.prepayMenu
                    )
                else:
                    await bot.send_message(
                        id, f"⌚ До конца подписки осталось <b>{delta.days}</b> дней"
                    )
            except:
                pass

        else:
            await bot.send_message(
                id, "Вы еще не зарегистрировались до конца, продолжите регистрацию"
            )
    else:
        db.add_user(id)
        db.set_step("name", id)
        db.set_blocked(0, id)
        db.set_subed(1, id)
        date = (
            datetime.now(timezone.utc)
            + timedelta(hours=config.UTC_STEP)
            + relativedelta.relativedelta(days=3)
        )
        db.set_sub(f"{date.year},{date.month},{date.day}", id)
        await bot.send_message(
            id,
            """👋🏼Уважаемый коллега! Бот🤖с удовольствием поможет Вашему обучению👨🏼‍🎓👨🏼‍⚕️ Вас ждёт обширная база информации на медицинскую тему🏥, из разных источников, включающие в себя научные статьи📑, популярные учебники отечественных и зарубежных авторов📚, клинические рекомендации📋, национальные руководства 📔и др.""",
        )
        await bot.send_message(id, "Напишите ваше ФИО полностью")


@router.message(Command("info"))
async def Info(message: types.Message, bot: Bot):
    id = message.from_user.id
    await bot.send_message(id, config.INFO)


@router.message(Command("topics"))
async def Menu(message: types.Message, bot: Bot):
    id = message.from_user.id
    db.set_path("main", id)
    topics = read_json("topics")

    if topics:
        await bot.send_message(
            id, "Меню:", reply_markup=kb.pathMenu(topics, ["main"], id)
        )
    else:
        await bot.send_message(
            id, "Тем пока нет", reply_markup=kb.pathMenu(topics, ["main"], id)
        )


@router.message(Command("news"))
async def News(message: types.Message, bot: Bot):
    id = message.from_user.id
    last_client_news = db.get_news_number(id)
    try:
        last_news = db.get_news_max_number()

    except:
        last_news = None
    if last_news:
        if last_client_news <= last_news:
            for num in range(last_client_news, last_news + 1):
                message_id = db.get_message_id(num)
                await bot.copy_message(id, config.ADMIN_ID, message_id)
                db.set_news_number(num + 1, id)
        else:
            await bot.send_message(id, "На данный момент новостей больше нет)")
    else:
        await bot.send_message(id, "На данный момент новостей нет)")


@router.message(Command("menu"))
async def Menu(message: types.Message, bot: Bot):
    id = message.from_user.id
    if id == config.ADMIN_ID:
        await bot.send_message(id, "Меню управляющего:", reply_markup=kb.mainMenu)


@router.callback_query(F.data == "btnAddNews")
async def AddNews(call: types.CallbackQuery, bot: Bot, state: FSMContext):
    id = call.from_user.id
    message = call.message.message_id
    await call.answer("")
    if id == config.ADMIN_ID:
        try:
            await bot.delete_message(id, message)
        except:
            pass
        await bot.send_message(id, "Пришлите новость", reply_markup=kb.cancelMenu)
        await state.set_state(State.add_news)


@router.message(
    F.content_type.in_({"photo", "text", "video", "document"}),
    StateFilter(State.add_news),
)
async def add_news(message: types.Message, bot: Bot, state: FSMContext):
    id = message.from_user.id
    if id == config.ADMIN_ID:
        if message.text == "Отмена":
            await bot.send_message(id, "Меню управляющего:", reply_markup=kb.mainMenu)
            message = await bot.send_message(
                id, "Загрузка...", reply_markup=types.ReplyKeyboardRemove()
            )
            mess_id = message.message_id
            try:
                await bot.delete_message(id, mess_id)
            except:
                pass
            await state.clear()
        else:
            db.add_news(message.message_id)
            await bot.send_message(id, "Записал!")
            await bot.send_message(id, "Меню управляющего:", reply_markup=kb.mainMenu)
            message = await bot.send_message(
                id, "Загрузка...", reply_markup=types.ReplyKeyboardRemove()
            )
            mess_id = message.message_id
            try:
                await bot.delete_message(id, mess_id)
            except:
                pass
            await state.clear()


@router.callback_query(F.data == "btnAdd")
async def Add(call: types.CallbackQuery, bot: Bot, state: FSMContext):
    id = call.from_user.id
    message = call.message.message_id
    await call.answer("")
    if id == config.ADMIN_ID:
        try:
            await bot.delete_message(id, message - 1)
        except:
            pass
        try:
            await bot.edit_message_text(
                f"Напишите название новой темы или сразу пришлите документ", id, message
            )
            await bot.edit_message_reply_markup(
                chat_id=id, message_id=message, reply_markup=kb.backMenu
            )
        except:
            await bot.send_message(
                id,
                f"Напишите название новой темы или сразу пришлите документ",
                reply_markup=kb.backMenu,
            )

        await state.set_state(State.add)


@router.message(
    F.content_type.in_({"photo", "text", "video", "document"}), StateFilter(State.add)
)
async def add(message: types.Message, bot: Bot, state: FSMContext):
    id = message.from_user.id
    if id == config.ADMIN_ID:
        if message.document:
            if message.document.file_name.lower().endswith(".docx"):
                file_name = message.document.file_name
                await message.document.download(destination_file=f"files/{file_name}")
                data = docx2python(f"files/{file_name}")
                doc = data.document[0][0][0]
                title = doc[0]
                text = ""
                for par in doc[1:]:
                    if par == "" and text != "":
                        if text[-1] != "\n":
                            text += "\n"
                    elif par == "…" and text != "":
                        if text[-1] != "\n":
                            text += "\n"
                    elif "Ссылка на электронный источник" in par:
                        try:
                            url = re.search(r"(?<=\().*?(?=\))", par).group(0)
                        except:
                            pass
                    elif "----media" in par:
                        text += ""

                    else:
                        try:
                            if par[0].isdigit() and ")" in par:
                                beg = par.index(")")
                                text += f"<b>{par[beg + 2 :]}</b>"
                            else:
                                text += par
                        except:
                            pass

                if len(text) <= 4082:
                    try:
                        Path("files/img").mkdir(parents=True, exist_ok=True)
                        docx2txt.process(f"files/{file_name}", "files/img/")
                        docx2txt.process(f"files/{file_name}", "files/")
                        try:
                            photo = FSInputFile("files/img/image1.jpeg")
                        except:
                            photo = FSInputFile("files/img/image1.png")

                    except:
                        photo = None
                    if not db.item_exists(title.lower()):
                        db.add_item(title.lower())
                        item_id = db.get_item_id(title.lower())
                        db.set_text(text, item_id)
                        try:
                            db.set_url(url, item_id)
                        except:
                            pass
                        if photo:
                            photo_message = await bot.send_photo(id, photo)
                            photo_id = photo_message.photo[0]["file_id"]
                            await photo_message.delete()
                            db.set_media(str({"photo": photo_id}), item_id)

                        db.set_item_step("done", item_id)
                        topics = read_json("topics")
                        path = db.get_path(id)
                        if path == "main":
                            topics[str(item_id)] = {}
                        else:
                            path = f"{path[5:]}.{item_id}"
                            glom.assign(topics, path, {})
                        save_json(topics, "topics")

                        await send_menu(message, bot)
                        await state.clear()
                    else:
                        await bot.send_message(
                            id,
                            "Эта статья уже есть в базе, но вы можете поменять её в основном меню",
                        )
                else:
                    await bot.send_message(
                        id,
                        "Текст в документе слишком большой, он должен удлжиться в 4082 символа",
                    )
                data.close()
            try:
                os.remove(f"files/{file_name}")
                shutil.rmtree("files/img")
            except:
                pass
        else:
            if db.undone_item_exists():
                item_id = db.get_undone_item_id()
                step = db.get_item_step(item_id)
                if step == "name":
                    db.set_item_name(message.text, item_id)
                    if (
                        db.get_item_name(item_id)
                        and db.get_text(item_id)
                        and db.get_url(item_id)
                        and db.get_media(item_id)
                    ):
                        db.set_item_step("change", item_id)
                        await bot.send_message(
                            id,
                            f"Меню изменения <b>{db.get_item_name(item_id)}</b>",
                            reply_markup=kb.topicMenu,
                        )
                        await state.clear()

                if step == "text":
                    if len(message.text) <= 4082:
                        db.set_text(message.text, item_id)
                        if (
                            db.get_item_name(item_id)
                            and db.get_text(item_id)
                            and db.get_url(item_id)
                            and db.get_media(item_id)
                        ):
                            db.set_item_step("change", item_id)
                            await bot.send_message(
                                id,
                                f"Меню изменения <b>{db.get_item_name(item_id)}</b>",
                                reply_markup=kb.topicMenu,
                            )
                            await state.clear()
                        else:
                            if not "https://telegra.ph" in message.text:
                                db.set_item_step("url", item_id)
                                await bot.send_message(
                                    id,
                                    "Напишите ссылку на полную статью",
                                    reply_markup=kb.backMenu,
                                )
                            else:
                                await send_menu(message, bot)
                                message = await bot.send_message(
                                    id,
                                    "Загрузка...",
                                    reply_markup=types.ReplyKeyboardRemove(),
                                )
                                mess_id = message.message_id
                                try:
                                    await bot.delete_message(id, mess_id)
                                except:
                                    pass
                                db.set_url("-", item_id)
                                db.set_media("-", item_id)
                                db.set_item_step("done", item_id)
                                await state.clear()
                    else:
                        await bot.send_message(
                            id,
                            "Текст слишком длинный, пожалуйста используйте не более чем 4082 символа",
                            reply_markup=kb.backMenu,
                        )

                if step == "url":
                    db.set_url(message.text, item_id)
                    if (
                        db.get_item_name(item_id)
                        and db.get_text(item_id)
                        and db.get_url(item_id)
                        and db.get_media(item_id)
                    ):
                        db.set_item_step("change", item_id)
                        await bot.send_message(
                            id,
                            f"Меню изменения <b>{db.get_item_name(item_id)}</b>",
                            reply_markup=kb.topicMenu,
                        )
                        await state.clear()
                    else:
                        db.set_item_step("media", item_id)
                        await bot.send_message(
                            id,
                            "Пришлите фотографию или видео для этой темы",
                            reply_markup=kb.backMenu,
                        )

                if step == "media":
                    if message.photo:
                        db.set_media(str({"photo": message.photo[0].file_id}), item_id)
                        await send_menu(message, bot)
                        message = await bot.send_message(
                            id, "Загрузка...", reply_markup=types.ReplyKeyboardRemove()
                        )
                        mess_id = message.message_id
                        try:
                            await bot.delete_message(id, mess_id)
                        except:
                            pass
                        db.set_item_step("done", item_id)
                        await state.clear()

                    elif message.video:
                        db.set_media(str({"video": message.video.file_id}), item_id)
                        await send_menu(message, bot)
                        message = await bot.send_message(
                            id, "Загрузка...", reply_markup=types.ReplyKeyboardRemove()
                        )
                        mess_id = message.message_id
                        try:
                            await bot.delete_message(id, mess_id)
                        except:
                            pass
                        db.set_item_step("done", item_id)
                        await state.clear()

                if step == "change_media":
                    if message.photo:
                        db.set_media(str({"photo": message.photo[0].file_id}), item_id)
                        db.set_item_step("change", item_id)
                        await bot.send_message(
                            id,
                            f"Меню изменения <b>{db.get_item_name(item_id)}</b>",
                            reply_markup=kb.topicMenu,
                        )
                        message = await bot.send_message(
                            id, "Загрузка...", reply_markup=types.ReplyKeyboardRemove()
                        )
                        mess_id = message.message_id
                        try:
                            await bot.delete_message(id, mess_id)
                        except:
                            pass
                        await state.clear()

                    elif message.video:
                        db.set_media(str({"video": message.video.file_id}), item_id)
                        db.set_item_step("change", item_id)
                        await bot.send_message(
                            id,
                            f"Меню изменения <b>{db.get_item_name(item_id)}</b>",
                            reply_markup=kb.topicMenu,
                        )
                        message = await bot.send_message(
                            id, "Загрузка...", reply_markup=types.ReplyKeyboardRemove()
                        )
                        mess_id = message.message_id
                        try:
                            await bot.delete_message(id, mess_id)
                        except:
                            pass
                        await state.clear()

                    else:
                        await bot.send_message(
                            id,
                            "Поддерживаются только фото и видео",
                            reply_markup=kb.backMenu,
                        )

            elif not db.item_exists(message.text):
                db.add_item(message.text)
                item_id = db.get_undone_item_id()
                topics = read_json("topics")
                path = db.get_path(id)
                if path == "main":
                    topics[str(item_id)] = {}
                else:
                    path = f"{path[5:]}.{item_id}"
                    glom.assign(topics, path, {})
                save_json(topics, "topics")
                db.set_item_step("text", item_id)
                await bot.send_message(
                    id,
                    "Напишите краткую сводку статьи, или ссылку на статью в telegraph",
                    reply_markup=kb.backMenu,
                )


@router.callback_query(F.data == "btnChange")
async def Change(call: types.CallbackQuery, bot: Bot):
    id = call.from_user.id
    message = call.message.message_id
    await call.answer("")
    if id == config.ADMIN_ID:
        await bot.edit_message_reply_markup(
            chat_id=id, message_id=message, reply_markup=kb.topicMenu
        )
        item_id = db.get_path(id).split(".")[-1]
        db.set_item_step("change", item_id)


@router.callback_query(F.data == "btnName")
async def Name(call: types.CallbackQuery, bot: Bot, state: FSMContext):
    id = call.from_user.id
    message = call.message.message_id
    await call.answer("")
    if id == config.ADMIN_ID:
        try:
            await bot.delete_message(id, message)
        except:
            pass
        await bot.send_message(
            id, "Напишите новое имя для этого раздела", reply_markup=kb.backMenu
        )
        item_id = db.get_undone_item_id()
        db.set_item_step("name", item_id)
        await state.set_state(State.add)


@router.callback_query(F.data == "btnText")
async def Text(call: types.CallbackQuery, bot: Bot, state: FSMContext):
    id = call.from_user.id
    message = call.message.message_id
    await call.answer("")
    if id == config.ADMIN_ID:
        try:
            await bot.delete_message(id, message)
        except:
            pass
        await bot.send_message(
            id, "Пришлите новый короткий текст темы", reply_markup=kb.backMenu
        )
        item_id = db.get_undone_item_id()
        db.set_item_step("text", item_id)
        await state.set_state(State.add)


@router.callback_query(F.data == "btnUrl")
async def Url(call: types.CallbackQuery, bot: Bot, state: FSMContext):
    id = call.from_user.id
    message = call.message.message_id
    await call.answer("")
    if id == config.ADMIN_ID:
        try:
            await bot.delete_message(id, message)
        except:
            pass
        await bot.send_message(
            id, "Пришлите новую ссылку на полную статью", reply_markup=kb.backMenu
        )
        item_id = db.get_undone_item_id()
        db.set_item_step("url", item_id)
        await state.set_state(State.add)


@router.callback_query(F.data == "btnMedia")
async def Media(call: types.CallbackQuery, bot: Bot, state: FSMContext):
    id = call.from_user.id
    await call.answer("")
    if id == config.ADMIN_ID:
        await bot.send_message(
            id, "Пришлите фотографию или видео для этой темы", reply_markup=kb.backMenu
        )
        item_id = db.get_undone_item_id()
        db.set_item_step("change_media", item_id)
        await state.set_state(State.add)


@router.callback_query(F.data == "btnBack", StateFilter)
async def Back(call: types.CallbackQuery, bot: Bot, state: FSMContext):
    id = call.from_user.id
    message = call.message
    await call.answer("")
    if id == config.ADMIN_ID:
        await state.clear()
        try:
            undone = db.get_undone_item_id()

            if (
                db.get_item_name(undone)
                and db.get_text(undone)
                and db.get_url(undone)
                and db.get_media(undone)
            ):
                db.set_item_step("done", undone)
            else:
                db.delete_item(undone)
        except TypeError:
            undone = None
        topics = read_json("topics")
        path = db.get_path(id)
        if path != "main":
            temp_path = f"{path[5:]}.{undone}"
        else:
            temp_path = f"{undone}"
        try:
            glom.delete(topics, temp_path)
        except glom.mutation.PathDeleteError:
            pass
        save_json(topics, "topics")
        await send_menu(message, bot)


@router.callback_query(F.data == "btnBack")
async def Back(call: types.CallbackQuery, bot: Bot, state: FSMContext):
    id = call.from_user.id
    message = call.message
    await call.answer("")
    if id == config.ADMIN_ID:
        await state.clear()
        try:
            undone = db.get_undone_item_id()
            if (
                db.get_item_name(undone)
                and db.get_text(undone)
                and db.get_url(undone)
                and db.get_media(undone)
            ):
                db.set_item_step("done", undone)
            else:
                db.delete_item(undone)
        except TypeError:
            undone = None
        topics = read_json("topics")
        path = db.get_path(id)
        if path != "main":
            temp_path = f"{path[5:]}.{undone}"
        else:
            temp_path = f"{undone}"
        try:
            glom.delete(topics, temp_path)
        except glom.mutation.PathDeleteError:
            pass
        save_json(topics, "topics")
        await send_menu(message, bot)


@router.callback_query(F.data == "btnDell")
async def Dell(call: types.CallbackQuery, bot: Bot):
    id = call.from_user.id
    message = call.message.message_id
    await call.answer("")
    if id == config.ADMIN_ID:
        change_id = db.get_id_by_step("change")
        change_name = db.get_item_name(change_id)
        db.set_item_step("dell", change_id)
        try:
            await bot.edit_message_text(
                f"Вы действительно хотите удалить раздел <b>'{change_name}'</b>?",
                id,
                message,
            )
            await bot.edit_message_reply_markup(
                chat_id=id, message_id=message, reply_markup=kb.agreeMenu
            )
        except:
            await bot.send_message(
                id,
                f"Вы действительно хотите удалить раздел <b>'{change_name}'</b>?",
                reply_markup=kb.agreeMenu,
            )


@router.callback_query(F.data == "btnYes")
async def Yes(call: types.CallbackQuery, bot: Bot):
    id = call.from_user.id
    await call.answer("")
    if id == config.ADMIN_ID:
        change_id = db.get_id_by_step("dell")
        db.delete_item(change_id)
        topics = read_json("topics")
        path = db.get_path(id)
        if path != "main":
            temp_path = f"{path[5:]}"

            glom.delete(topics, temp_path)

        save_json(topics, "topics")
        await send_menu(call.message, bot, True)
        new_path = ""
        for key in path.split(".")[:-1]:
            new_path += key + "."
        new_path = new_path[:-1]
        db.set_path(new_path, id)


@router.callback_query(F.data == "btnNo")
async def No(call: types.CallbackQuery, bot: Bot):
    id = call.from_user.id
    await call.answer("")
    if id == config.ADMIN_ID:
        change_id = db.get_id_by_step("dell")
        db.set_item_step("change", change_id)
        await send_menu(call.message, bot)


@router.callback_query(F.data == "btnBan")
async def Ban(call: types.CallbackQuery, bot: Bot, state: FSMContext):
    id = call.from_user.id
    await call.answer("")
    if id == config.ADMIN_ID:
        await bot.send_message(
            id,
            f"Напишите email человека, которого хотите заблокировать",
            reply_markup=kb.cancelMenu,
        )
        await state.set_state(State.ban)


@router.message(StateFilter(State.ban))
async def ban(message: types.Message, bot: Bot, state: FSMContext):
    id = message.from_user.id
    if id == config.ADMIN_ID:
        if message.text == "Отмена":
            await bot.send_message(id, "Меню управляющего:", reply_markup=kb.mainMenu)
            message = await bot.send_message(
                id, "Загрузка...", reply_markup=types.ReplyKeyboardRemove()
            )
            mess_id = message.message_id
            try:
                await bot.delete_message(id, mess_id)
            except:
                pass
            await state.clear()

        else:
            try:
                email = message.text.lower()
                user_id = db.get_id_by_mail(email)
                try:
                    db.set_blocked(1, user_id)
                    await bot.send_message(
                        id, f"Пользователь {db.get_name(user_id)} заблокирован"
                    )
                    await bot.send_message(
                        id, "Меню управляющего:", reply_markup=kb.mainMenu
                    )
                    await state.clear()
                except:
                    await bot.send_message(id, "Пользователь с такой почтой не найнен")
            except:
                pass


@router.callback_query(F.data == "btnUnban")
async def Unban(call: types.CallbackQuery, bot: Bot, state: FSMContext):
    id = call.from_user.id
    message = call.message.message_id
    await call.answer("")
    if id == config.ADMIN_ID:
        try:
            await bot.delete_message(id, message)
        except:
            pass
        await bot.send_message(
            id,
            f"Напишите email человека, которого хотите разблокировать",
            reply_markup=kb.cancelMenu,
        )
        await state.set_state(State.unban)


@router.message(StateFilter(State.unban))
async def unban(message: types.Message, bot: Bot, state: FSMContext):
    id = message.from_user.id
    if id == config.ADMIN_ID:
        if message.text == "Отмена":
            await bot.send_message(id, "Меню управляющего:", reply_markup=kb.mainMenu)
            message = await bot.send_message(
                id, "Загрузка...", reply_markup=types.ReplyKeyboardRemove()
            )
            mess_id = message.message_id
            try:
                await bot.delete_message(id, mess_id)
            except:
                pass
            await state.clear()
        else:
            try:
                email = message.text.lower()
                user_id = db.get_id_by_mail(email)
                try:
                    db.set_blocked(0, user_id)
                    await bot.send_message(
                        id, f"Пользователь {db.get_name(user_id)} разблокирован"
                    )
                    await bot.send_message(
                        id, "Меню управляющего:", reply_markup=kb.mainMenu
                    )
                    await state.clear()
                except:
                    await bot.send_message(id, "Пользователь с такой почтой не найнен")
            except:
                pass


@router.callback_query(F.data == "btnPrepay")
async def prepay(call: types.CallbackQuery):
    await call.answer()
    await show_payment_options(call.message)


async def show_payment_options(message: types.Message):
    await message.answer(
        "Выберите вариант подписки:", reply_markup=kb.get_payment_keyboard()
    )


@router.callback_query(F.data.startswith("pay_"))
async def process_payment(call: types.CallbackQuery, bot: Bot):
    await call.answer()
    option = call.data.split("_")[1]
    if option == "1":
        amount = config.LOWER_PRICE
        title = "Подписка на 1 месяц"
        description = "Доступ ко всем функциям бота на 1 месяц"
    elif option == "3":
        amount = config.HIGHER_PRICE
        title = "Подписка на 3 месяца"
        description = "Доступ ко всем функциям бота на 3 месяца"
    else:
        await call.message.answer("Неверный вариант оплаты")
        return

    await bot.send_invoice(
        chat_id=call.from_user.id,
        title=title,
        description=description,
        payload=f"sub_{option}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=title, amount=amount)],
        start_parameter="create_invoice_subscription",
    )


@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@router.message(F.content_type.in_({"successful_payment"}))
async def process_successful_payment(message: types.Message, bot: Bot):
    payment_info = message.successful_payment
    duration = payment_info.invoice_payload.split("_")[1]
    id = message.from_user.id
    if db.user_exists(id):
        db.set_subed(1, id)
        db.set_step("search", id)
        sub = db.get_sub(id)
        if not sub:
            date = (
                datetime.now(timezone.utc)
                + timedelta(hours=config.UTC_STEP)
                + relativedelta.relativedelta(months=duration)
            )
            db.set_sub(f"{date.year},{date.month},{date.day}", id)
        year, month, day = sub.split(",")
        if datetime.now(timezone.utc) + timedelta(hours=config.UTC_STEP) < datetime(
            year=int(year),
            month=int(month),
            day=int(day),
            tzinfo=timezone.utc,
        ):
            date = datetime(
                year=int(year),
                month=int(month),
                day=int(day),
                tzinfo=timezone.utc,
            ) + relativedelta.relativedelta(months=duration)
            db.set_sub(f"{date.year},{date.month},{date.day}", id)
        else:
            date = (
                datetime.now(timezone.utc)
                + timedelta(hours=config.UTC_STEP)
                + relativedelta.relativedelta(months=duration)
            )
            db.set_sub(f"{date.year},{date.month},{date.day}", id)
        await bot.send_message(
            id,
            f'Спасибо за подписку, теперь можете ввести запрос. Например, "Трапециевидная мышца", или используйте команду /topics для досту',
        )


@router.message()
async def main(message: types.Message, bot: Bot):
    id = message.from_user.id
    if db.get_blocked(id) == 0:
        step = db.get_step(id)
        if step == "name":
            db.set_name(message.text, id)
            db.set_step("mail", id)
            await bot.send_message(id, "Теперь ваш Email")
        if step == "mail":
            db.set_mail(message.text, id)
            db.set_step("search", id)
            await bot.send_message(id, "У вас есть 3 дня бесплатного использования!")
        if step == "search":
            sub = db.get_sub(id)
            year, month, day = sub.split(",")
            if db.get_subed(id) == 1 and datetime.now(timezone.utc) + timedelta(
                hours=config.UTC_STEP
            ) < datetime(
                year=int(year), month=int(month), day=int(day), tzinfo=timezone.utc
            ):
                request = message.text.lower()
                data = db.get_items()

                results = []
                for item in data:
                    name = item[1]

                    if request.lower() == name.lower():
                        results.append(name)
                if not results:
                    for item in data:
                        name = item[1]
                        if check_substring(request, name, 3):
                            results.append(name)
                if not results:
                    await bot.send_message(
                        id,
                        "Я не смог найти разделы по вашему запросу, возможно допущена ошибка в написании, пожалуйста, проверьте.",
                    )
                elif len(results) == 1:
                    item_id = db.get_item_id(results[0])
                    text = db.get_text(item_id)
                    url = db.get_url(item_id)
                    if url != "None":
                        if "https://telegra.ph" in text:
                            caption = f"{hide_link(text)}"
                        else:
                            caption = (
                                f"{text}\n<b><a href='{url}'>Полная статья</a></b>"
                            )
                    else:
                        caption = f"{text}"
                    try:
                        media = ast.literal_eval(db.get_media(item_id))
                    except:
                        media = None
                    if media:
                        try:
                            try:
                                media_id = media["video"]
                                file = types.InputMediaVideo(media=media_id)
                                await message.answer_media_group([file])
                            except:
                                media_id = media["photo"]
                                file = types.InputMediaPhoto(media=media_id)
                                await message.answer_media_group([file])
                        except:
                            pass
                    await bot.send_message(id, caption)

                elif len(results) > 1:
                    await bot.send_message(
                        id,
                        "Выберите тему из вариантов ниже",
                        reply_markup=kb.choiseMenu(results),
                    )
            else:
                await bot.send_message(
                    id,
                    "Чтобы пользоваться поиском дальше вам нужно подписаться",
                    reply_markup=kb.prepayMenu,
                )


@router.callback_query()
async def ThemeSearch(call: types.CallbackQuery, bot: Bot):
    id = call.from_user.id
    message = call.message
    await call.answer("")
    sub = db.get_sub(id)
    year, month, day = sub.split(",")
    if db.get_subed(id) == 0 or datetime.now(timezone.utc) + timedelta(
        hours=config.UTC_STEP
    ) >= datetime(year=int(year), month=int(month), day=int(day), tzinfo=timezone.utc):
        await message.answer(
            "Чтобы пользоваться поиском дальше вам нужно подписаться",
            reply_markup=kb.prepayMenu,
        )
    else:
        key = str(call.data)
        topics = read_json("topics")
        if topics:
            path = db.get_path(id).split(".")
            if key in path:
                path = path[: path.index(key) + 1]
            else:
                path.append(key)
            str_path = ""
            for dir in path:
                str_path += dir + "."
            str_path = str_path[:-1]
            db.set_path(str_path, id)

            if key == "main":
                try:
                    await message.delete()
                except:
                    pass
                try:
                    await bot.edit_message_text("Меню:", id, message.message_id)
                    await bot.edit_message_reply_markup(
                        id,
                        message.message_id,
                        reply_markup=kb.pathMenu(topics, path, id),
                    )

                except:
                    await bot.send_message(
                        id, "Меню:", reply_markup=kb.pathMenu(topics, path, id)
                    )
            else:
                text = db.get_text(key)
                url = db.get_url(key)
                if url != "None":
                    if "https://telegra.ph" in text:
                        caption = f"{hide_link(text)}"
                    else:
                        caption = f"{text}\n<b><a href='{url}'>Полная статья</a></b>"
                else:
                    caption = f"{text}"
                try:
                    media = ast.literal_eval(db.get_media(key))
                except:
                    media = None
                try:
                    await message.delete()
                except:
                    pass
                if media:
                    try:
                        try:
                            media_id = media["video"]
                            file = types.InputMediaVideo(media=media_id)
                            await message.answer_media_group([file])
                        except:
                            media_id = media["photo"]
                            file = types.InputMediaPhoto(media=media_id)
                            await message.answer_media_group([file])
                    except:
                        pass
                    try:
                        await message.delete()
                    except:
                        pass
                    await bot.send_message(
                        id, caption, reply_markup=kb.pathMenu(topics, path, id)
                    )
                else:
                    try:
                        await bot.edit_message_text(caption, id, message.message_id)
                        await bot.edit_message_reply_markup(
                            chat_id=id,
                            message_id=message.message_id,
                            reply_markup=kb.pathMenu(topics, path, id),
                        )
                    except:
                        await bot.send_message(
                            id, caption, reply_markup=kb.pathMenu(topics, path, id)
                        )

        else:
            try:
                await message.delete()
            except:
                pass
            try:
                await bot.edit_message_text("Тем пока нет", id, message.message_id)
                await bot.edit_message_reply_markup(
                    chat_id=id,
                    message_id=message.message_id,
                    reply_markup=kb.pathMenu(topics, path, id),
                )
            except:
                await bot.send_message(
                    id, "Тем пока нет", reply_markup=kb.pathMenu(topics, path, id)
                )


async def send_menu(message, bot, back=False):
    id = message.chat.id
    topics = read_json("topics")
    path = db.get_path(id).split(".")
    if back:
        key = path[-2]
    else:
        key = path[-1]
    if topics:
        if key == "main":
            try:
                await message.delete()
            except:
                pass
            try:
                await bot.edit_message_text("Меню:", id, message.message_id)
                await bot.edit_message_reply_markup(
                    chat_id=id,
                    message_id=message.message_id,
                    reply_markup=kb.pathMenu(topics, ["main"], id),
                )
            except:
                await bot.send_message(
                    id, "Меню:", reply_markup=kb.pathMenu(topics, ["main"], id)
                )
        else:
            text = db.get_text(key)
            url = db.get_url(key)
            if url != "None":
                if "https://telegra.ph" in text:
                    caption = f"{hide_link(text)}"
                else:
                    caption = f"{text}\n<b><a href='{url}'>Полная статья</a></b>"
            else:
                caption = f"{text}"
            try:
                media = ast.literal_eval(db.get_media(key))
            except:
                media = None
            try:
                await message.delete()
            except:
                pass
            if media:
                try:
                    try:
                        media_id = media["video"]
                        file = types.InputMediaVideo(media=media_id)
                        await message.answer_media_group([file])
                    except:
                        media_id = media["photo"]
                        file = types.InputMediaPhoto(media=media_id)
                        await message.answer_media_group([file])
                except:
                    pass
                try:
                    await message.delete()
                except:
                    pass
                await bot.send_message(
                    id, caption, reply_markup=kb.pathMenu(topics, path, id, back)
                )
            else:
                try:
                    await bot.edit_message_text(caption, id, message.message_id)
                    await bot.edit_message_reply_markup(
                        chat_id=id,
                        message_id=message.message_id,
                        reply_markup=kb.pathMenu(topics, path, id, back),
                    )
                except:
                    await bot.send_message(
                        id, caption, reply_markup=kb.pathMenu(topics, path, id, back)
                    )
    else:
        try:
            await message.delete()
        except:
            pass
        try:
            await bot.edit_message_text("Тем пока нет", id, message.message_id)
            await bot.edit_message_reply_markup(
                chat_id=id,
                message_id=message.message_id,
                reply_markup=kb.pathMenu(topics, path, id, back),
            )
        except:
            await bot.send_message(
                id, "Тем пока нет", reply_markup=kb.pathMenu(topics, path, id, back)
            )


def get_substrings(string):
    return re.split("\W+", string)


def get_distance(s1, s2):
    d, len_s1, len_s2 = {}, len(s1), len(s2)
    for i in range(-1, len_s1 + 1):
        d[(i, -1)] = i + 1
    for j in range(-1, len_s2 + 1):
        d[(-1, j)] = j + 1
    for i in range(len_s1):
        for j in range(len_s2):
            if s1[i] == s2[j]:
                cost = 0
            else:
                cost = 1
            d[(i, j)] = min(
                d[(i - 1, j)] + 1, d[(i, j - 1)] + 1, d[(i - 1, j - 1)] + cost
            )
            if i and j and s1[i] == s2[j - 1] and s1[i - 1] == s2[j]:
                d[(i, j)] = min(d[(i, j)], d[i - 2, j - 2] + cost)
    return d[len_s1 - 1, len_s2 - 1]


def check_substring(search_request, original_text, max_distance):
    substring_list_1 = get_substrings(search_request)
    substring_list_2 = get_substrings(original_text)

    not_found_count = len(substring_list_1)

    for substring_1 in substring_list_1:
        for substring_2 in substring_list_2:
            if get_distance(substring_1, substring_2) <= max_distance:
                not_found_count -= 1

    return not not_found_count

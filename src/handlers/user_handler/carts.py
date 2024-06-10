from datetime import datetime, timezone, timedelta

import aiogram.exceptions
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import default_state
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError
from aiogram.types import ReplyKeyboardRemove

from src.db import DB_mongo
from src.callbacks.cart_callback import CartCallbackFactory
from src.callbacks.place import PlaceCallbackFactory
from src.db.postgre.dao import AsyncOrm
from src.keyboards.keyboard_carts import get_keyboard
from src.keyboards.keyboard import create_places_kb, create_cancel_kb
from src.lexicon.lexicon_ru import TO_RENTING, TO_FREE, RUSSIAN_WEEK_DAYS
from src.middlewares.throttling_middleware import ThrottlingMiddleware
from src.fsm.fsm import FSMCarts
from src.config import settings
from src.db import cached_places
import logging

router_carts = Router()
router_carts.callback_query.middleware(middleware=ThrottlingMiddleware())
logger = logging.getLogger(__name__)


@router_carts.message(Command(commands="carts"), StateFilter(default_state))
async def create_carts_command(message: Message, state: FSMContext):
    await message.answer(
        text="Пожалуйста, выберите свою рабочую точку из списка <b>ниже</b>",
        reply_markup=await create_places_kb(),
        parse_mode="html",
    )
    await state.set_state(FSMCarts.place)


@router_carts.callback_query(StateFilter(FSMCarts.place), PlaceCallbackFactory.filter())
async def process_place_command(callback: CallbackQuery, callback_data: PlaceCallbackFactory, state: FSMContext):
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Пожалуйста, выберите свою рабочую точку из списка <b>ниже</b>\n\n"
             f"➢ {callback_data.title}",
        parse_mode="html",
    )
    await state.update_data(place=callback_data.title)

    # если база пустая, то создаю для конкретной точки коллекцию с тележками
    if not DB_mongo.check_for_carts_today_collection_by_place(place=callback_data.title):
        await DB_mongo.reset_carts_from_place(place=callback_data.title)
        DB_mongo.reset_today_from_place(chat_id=callback.message.chat.id, place=callback_data.title)

    msg = await callback.message.answer(
        text="🛒<b>Список тележек:</b>",
        reply_markup=await get_keyboard(place=callback_data.title),
        parse_mode="html",
    )

    DB_mongo.update_today(
        place=callback_data.title,
        message_id=msg.message_id,
        chat_id=callback.message.chat.id,
    )

    await callback.answer()
    await state.set_state(FSMCarts.working_day)


@router_carts.callback_query(StateFilter(FSMCarts.working_day), CartCallbackFactory.filter())
async def process_carts_command(callback: CallbackQuery, callback_data: CartCallbackFactory, bot: Bot):
    time_now = datetime.now(tz=timezone(timedelta(hours=3.0)))

    # тележка свободна и меняем ее на арендованную
    if callback_data.status == 'free':
        status = DB_mongo.update_info_cart_from_place(
            place=callback_data.title_place,
            number_of_cart=callback_data.number,
            to_status=TO_RENTING,
            time=time_now.strftime("%H:%M"),
        )

    # тележка в аренде и меняем ее на свободную
    else:
        status = DB_mongo.update_info_cart_from_place(
            place=callback_data.title_place,
            number_of_cart=callback_data.number,
            to_status=TO_FREE,
        )

    for chat_id, message_id in DB_mongo.get_inline_markup_message_chat_ids_from_place(place=callback_data.title_place):
        try:
            await bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=await get_keyboard(place=callback_data.title_place),
            )

            DB_mongo.update_today(
                place=callback_data.title_place,
                message_id=callback.message.message_id,
                chat_id=callback.message.chat.id,
            )
        except TelegramAPIError:
            # Тут произошла попытка изменить сообщение у всех людей, кто есть в базе тележек.
            # Причин, по которым что-то могло пойти не так - много.
            # Поэтому ничего не буду обновлять, если что-то пошло не так у человека, который не
            # использует команду /carts в данный момент.
            pass

    await callback.answer(
        text="Тележка арендована❌" if status == TO_RENTING else "Тележка освободилась✅"
    )


@router_carts.callback_query(StateFilter(FSMCarts.working_day), F.data == "report_carts")
async def process_report_carts_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="➢ Оформить отчёт"
    )

    place = (await state.get_data())['place']
    data = DB_mongo.get_total_time_carts_from_place(place=place)

    day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
    current_date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(f'%d/%m/%Y - {RUSSIAN_WEEK_DAYS[day_of_week]}')

    report = "📝Прокат тележек:\n\n"
    report += f"Дата: {current_date}\n"
    report += f"Точка: {place}\n"
    report += f"Имя: {await AsyncOrm.get_current_name(user_id=callback.message.chat.id)}\n\n"

    for cart, total_time_list in data:  # cart = "cart_N", total_time_list = [time_1, time_2, time_3, ...]
        if total_time_list:
            report += f"🛒<b>Тележка {cart.split('_')[1]}</b>\n<b>└</b>"
            report += "<em>" + ", ".join([time for time in total_time_list]) + "</em>\n\n"
        else:
            report += f"🛒<b>Тележка {cart.split('_')[1]}</b>\n<b>└</b>"
            report += "<em>тележку не арендовывали</em>\n\n"

    for chat_id, message_id in DB_mongo.get_inline_markup_message_chat_ids_from_place(place=place):
        try:
            await callback.message.bot.delete_message(
                chat_id=chat_id,
                message_id=message_id,
            )
        except TelegramAPIError:
            # Это значит, что у другого человека, который есть в базе тележек, не получилось удалить сообщение в боте.
            # Причины могут быть разными, почему так вышло.
            # Основная догадка - человек не в боте, человек не в телеграм, человек заблокировал бота и т.д.
            #
            # И поэтому на всякий случай мы обнуляем все значения чатов и id-сообщений для этого человека
            # в базе тележек, и каждый раз будем это делать, чтобы работа бота не конфликтовала с пользователями,
            # которые в данный момент не имеют непосредственного отношения к /carts в данный момент
            DB_mongo.drop_today_for_current_person_on_place(
                chat_id=chat_id,
                place=place,
            )

        try:
            if chat_id != callback.message.chat.id:
                # если кнопку нажали, то для всех остальных людей, кто находится в базе тележек,
                # но которые не пользовались командой, мы вышлем это:
                await callback.message.bot.send_message(
                    chat_id=chat_id,
                    text="Был сформирован отчёт! Сообщение с тележками удалено, так как оно обнулилось",
                )
                await callback.message.bot.send_message(
                    chat_id=chat_id,
                    text='Напишите <b>"Отмена"</b> в чат или нажмите на кнопку ниже, чтобы вернуться в главное меню\n\n'
                         'Если Вы не были ни в какой команде - проигнорируйте это сообщение!',
                    reply_markup=create_cancel_kb(),
                    parse_mode="html",
                )
            else:
                await DB_mongo.reset_carts_from_place(place=place)
                DB_mongo.reset_today_from_place(
                    chat_id=callback.message.chat.id,
                    place=place,
                )
                # но если кнопку нажал человек, который пользовался командой, то для него вышлем успешное оформление
                # отчета, вот такое:
                await callback.message.answer(
                    text="Отчёт успешно отправлен!👍🏻",
                    reply_markup=ReplyKeyboardRemove(),
                )
                await callback.message.answer(
                    text="Я полностью обнулил все значения в таблице тележек⚠️"
                )
                await callback.message.answer(
                    text="Вы вернулись в главное меню",
                )

                await callback.message.bot.send_message(
                    chat_id=cached_places[place],
                    text=report,
                    parse_mode="html",
                )

                # Вызываю эти методы только для того человека, который пользовался командой и нажал оформление отчета.
                # Всем остальным людям нет смысла это высылать, им я вышлю кнопку, по которой они смогут выйти.
                await callback.answer()
        except TelegramAPIError as e:
            # Ничего не делать, если у бота не получилось отправить отчет у человека,
            # который не был на данный момент в боте
            pass
        finally:
            await state.clear()


@router_carts.callback_query(StateFilter(FSMCarts.working_day), F.data == "go_back_to_menu")
async def process_go_back_to_menu_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="➢ Вернуться в меню",
    )
    await callback.message.answer(
        text="Вы вернулись в главное меню",
    )
    await callback.answer()
    await state.clear()


@router_carts.message(StateFilter(FSMCarts.working_day))
async def warning_working_day_command(message: Message):
    await message.answer(
        text="Не нужно ничего мне писать, нажимайте на кнопки тележек "
             'или напишите <b>"Отмена"</b> в чат',
        parse_mode="html",
    )
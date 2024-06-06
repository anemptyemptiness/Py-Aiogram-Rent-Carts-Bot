from typing import Any, Dict, Union
from datetime import datetime, timezone, timedelta

from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InputMediaPhoto
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError

from src.config import settings
from src.db.postgre.dao import AsyncOrm
from src.fsm.fsm import FSMEncashment
from src.keyboards.keyboard import create_places_kb, create_cancel_kb
from src.middlewares.album_middleware import AlbumsMiddleware
from src.callbacks.place import PlaceCallbackFactory
from src.lexicon.lexicon_ru import RUSSIAN_WEEK_DAYS
from src.db import cached_places
import logging

router_encashment = Router()
router_encashment.message.middleware(middleware=AlbumsMiddleware(2))
logger = logging.getLogger(__name__)


async def report(data: Dict[str, Any], date: str, user_id: Union[str, int]) -> str:
    return "📝Открытие смены:\n\n" \
           f"Дата: {date}\n" \
           f"Точка: {data['place']}\n" \
           f"Имя: {await AsyncOrm.get_current_name(user_id=user_id)}\n\n" \
           f"Сумма и дата, за которую инкассируют: <em>{data['summary_and_date']}</em>\n"


async def send_report(message: Message, state: FSMContext, data: dict, date: str, chat_id: Union[str, int]):
    try:
        await message.bot.send_message(
            chat_id=chat_id,
            text=await report(
                data=data,
                date=date,
                user_id=message.chat.id,
            ),
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="html",
        )

        receipt_photo = [
            InputMediaPhoto(
                media=photo_file_id,
                caption="Фото чека" if i == 0 else ''
            ) for i, photo_file_id in enumerate(data['receipt_photo'])
        ]

        await message.bot.send_media_group(
            media=receipt_photo,
            chat_id=chat_id,
        )

        await message.answer(
            text="Отлично! Отчёт успешно отправлен👍🏻",
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer(
            text="Вы вернулись в главное меню"
        )

    except Exception as e:
        logger.exception("Ошибка не с телеграм в encashment.py")
        await message.bot.send_message(
            text=f"Encashment report error: {e}\n"
                 f"User id: {message.chat.id}",
            chat_id=settings.ADMIN_ID,
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer(
            text="Упс... что-то пошло не так, сообщите руководству!",
            reply_markup=ReplyKeyboardRemove(),
        )
    except TelegramAPIError as e:
        logger.exception("Ошибка с телеграм в encashment.py")
        await message.bot.send_message(
            text=f"Encashment report error: {e}\n"
                 f"User id: {message.chat.id}",
            chat_id=settings.ADMIN_ID,
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer(
            text="Упс... что-то пошло не так, сообщите руководству!",
            reply_markup=ReplyKeyboardRemove(),
        )
    finally:
        await message.answer(
            text="Вы вернулись в главное меню"
        )

        await state.clear()


@router_encashment.message(Command(commands="encashment"), StateFilter(default_state))
async def process_encashment_command(message: Message, state: FSMContext):
    await message.answer(
        text="Пожалуйста, выберите свою рабочую точку из списка <b>ниже</b>",
        reply_markup=await create_places_kb(),
        parse_mode="html",
    )
    await state.set_state(FSMEncashment.place)


@router_encashment.callback_query(StateFilter(FSMEncashment.place), PlaceCallbackFactory.filter())
async def process_select_place_command(callback: CallbackQuery, callback_data: PlaceCallbackFactory, state: FSMContext):
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Пожалуйста, выберите свою рабочую точку из списка <b>ниже</b>\n\n"
             f"➢ {callback_data.title}",
        parse_mode="html",
    )
    await state.update_data(place=callback_data.title)
    await callback.message.answer(
        text="Пожалуйста, сделайте фотографию чека",
        reply_markup=create_cancel_kb(),
    )
    await callback.answer()
    await state.set_state(FSMEncashment.receipt_photo)


@router_encashment.message(StateFilter(FSMEncashment.receipt_photo))
async def process_receipt_photo_command(message: Message, state: FSMContext):
    if message.photo:
        if "receipt_photo" not in await state.get_data():
            await state.update_data(receipt_photo=[message.photo[-1].file_id])

        await message.answer(
            text="Напишите сумму и дату, за которую инкассируют\n\n"
                 "<em>Например: 10000 31.01.2024</em>",
            reply_markup=create_cancel_kb(),
            parse_mode="html",
        )
        await state.set_state(FSMEncashment.summary_and_date)
    else:
        await message.answer(
            text="Пожалуйста, сделайте фотографию чека",
            reply_markup=create_cancel_kb(),
        )


@router_encashment.message(StateFilter(FSMEncashment.summary_and_date), F.text)
async def process_summary_and_date_command(message: Message, state: FSMContext):
    await state.update_data(summary_and_date=message.text)

    encashment_dict = await state.get_data()

    day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
    current_date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(f'%d/%m/%Y - {RUSSIAN_WEEK_DAYS[day_of_week]}')

    await send_report(
        message=message,
        state=state,
        data=encashment_dict,
        date=current_date,
        chat_id=cached_places[encashment_dict['place']],
    )


@router_encashment.message(StateFilter(FSMEncashment.summary_and_date))
async def warning_summary_and_date_command(message: Message):
    await message.answer(
        text="Напишите сумму и дату, за которую инкассируют\n\n"
             "<em>Например: 10000 31.01.2024</em>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )

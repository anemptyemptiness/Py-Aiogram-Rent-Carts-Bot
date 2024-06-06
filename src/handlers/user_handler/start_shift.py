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
from src.fsm.fsm import FSMStartShift
from src.keyboards.keyboard import create_places_kb, create_cancel_kb, create_yes_no_kb
from src.middlewares.album_middleware import AlbumsMiddleware
from src.callbacks.place import PlaceCallbackFactory
from src.lexicon.lexicon_ru import RUSSIAN_WEEK_DAYS
from src.db import DB
from src.db import cached_places
import logging

router_start_shift = Router()
router_start_shift.message.middleware(middleware=AlbumsMiddleware(2))
logger = logging.getLogger(__name__)

async def report(data: Dict[str, Any], date: str, user_id: Union[str, int]) -> str:
    return "📝Открытие смены:\n\n" \
           f"Дата: {date}\n" \
           f"Точка: {data['place']}\n" \
           f"Имя: {await AsyncOrm.get_current_name(user_id=user_id)}\n\n" \
           f"Тележки чистые: <em>{'да' if data['is_carts_clean'] == 'да' else 'нет⚠️'}</em>\n" \
           f"Пол чистый: <em>{'да' if data['is_floor_clean'] == 'да' else 'нет⚠️'}</em>\n" \
           f"Есть ли дефекты у тележек: <em>{'да⚠️' if data['is_carts_defects'] == 'да' else 'нет'}</em>"


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

        await message.bot.send_photo(
            chat_id=chat_id,
            photo=data['employee_photo'],
            caption="Фото сотрудника",
        )

        object_photo = [
            InputMediaPhoto(
                media=photo_file_id,
                caption="Фото объекта" if i == 0 else ''
            ) for i, photo_file_id in enumerate(data['object_photo'])
        ]

        await message.bot.send_media_group(
            media=object_photo,
            chat_id=chat_id,
        )

        if data['is_carts_defects'] == 'да':
            carts_defects = [
                InputMediaPhoto(
                    media=photo_file_id,
                    caption="Фото дефектов тележек" if i == 0 else ''
                ) for i, photo_file_id in enumerate(data['defects_photo'])
            ]

            await message.bot.send_media_group(
                media=carts_defects,
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
        logger.exception("Ошибка не с телеграм в start_shift.py")
        await message.bot.send_message(
            text=f"Start shift report error: {e}\n"
                 f"User id: {message.chat.id}",
            chat_id=settings.ADMIN_ID,
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer(
            text="Упс... что-то пошло не так, сообщите руководству!",
            reply_markup=ReplyKeyboardRemove(),
        )
    except TelegramAPIError as e:
        logger.exception("Ошибка с телеграм в start_shift.py")
        await message.bot.send_message(
            text=f"Start shift report error: {e}\n"
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


@router_start_shift.message(Command(commands="start_shift"), StateFilter(default_state))
async def process_start_shift_command(message: Message, state: FSMContext):
    await message.answer(
        text="Пожалуйста, выберите свою рабочую точку из списка <b>ниже</b>",
        reply_markup=await create_places_kb(),
        parse_mode="html",
    )
    await state.set_state(FSMStartShift.place)


@router_start_shift.callback_query(StateFilter(FSMStartShift.place), PlaceCallbackFactory.filter())
async def process_select_place_command(callback: CallbackQuery, callback_data: PlaceCallbackFactory, state: FSMContext):
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Пожалуйста, выберите свою рабочую точку из списка <b>ниже</b>\n\n"
             f"➢ {callback_data.title}",
        parse_mode="html",
    )
    await state.update_data(place=callback_data.title)
    await callback.message.answer(
        text="Пожалуйста, сделайте Ваше фото на рабочем месте",
        reply_markup=create_cancel_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.employee_photo)


@router_start_shift.message(StateFilter(FSMStartShift.employee_photo))
async def process_employee_photo_command(message: Message, state: FSMContext):
    if message.photo:
        await state.update_data(employee_photo=message.photo[-1].file_id)

        await message.answer(
            text="Сфотографируйте объект с трёх ракурсов\n"
                 "(соответственно, нужно 3 фотографии)",
            reply_markup=create_cancel_kb(),
        )
        await state.set_state(FSMStartShift.object_photo)
    else:
        await message.answer(
            text="Пожалуйста, сделайте Ваше фото на рабочем месте",
            reply_markup=create_cancel_kb(),
        )


@router_start_shift.message(StateFilter(FSMStartShift.object_photo))
async def process_object_photo_command(message: Message, state: FSMContext):
    if message.photo:
        if "object_photo" not in await state.get_data():
            await state.update_data(object_photo=[message.photo[-1].file_id])

        await message.answer(
            text="Тележки чистые?",
            reply_markup=create_yes_no_kb(),
        )
        await state.set_state(FSMStartShift.is_carts_clean)
    else:
        await message.answer(
            text="Сфотографируйте объект с трёх ракурсов\n"
                 "(соответственно, нужно 3 фотографии)",
            reply_markup=create_cancel_kb(),
        )


@router_start_shift.callback_query(StateFilter(FSMStartShift.is_carts_clean), F.data == "yes")
async def process_is_carts_clean_yes_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Тележки чистые?\n\n"
             "➢ Да",
    )
    await state.update_data(is_carts_clean="да")
    await callback.message.answer(
        text="Пол чистый?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.is_floor_clean)


@router_start_shift.callback_query(StateFilter(FSMStartShift.is_carts_clean), F.data == "no")
async def process_is_carts_clean_no_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Тележки чистые?\n\n"
             "➢ Нет\n\n"
             "⚠️Нужно почистить тележки!⚠️",
    )
    await state.update_data(is_carts_clean="нет")
    await callback.message.answer(
        text="Пол чистый?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.is_floor_clean)


@router_start_shift.message(StateFilter(FSMStartShift.is_carts_clean))
async def warning_is_carts_clean_command(message: Message):
    await message.answer(
        text="Нажмите на нужную кнопку под сообщением с вопросом",
    )


@router_start_shift.callback_query(StateFilter(FSMStartShift.is_floor_clean), F.data == "yes")
async def process_is_floor_clean_yes_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Пол чистый?\n\n"
             "➢ Да",
    )
    await state.update_data(is_floor_clean="да")
    await callback.message.answer(
        text="Есть ли дефекты на тележках?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.is_carts_defects)


@router_start_shift.callback_query(StateFilter(FSMStartShift.is_floor_clean), F.data == "no")
async def process_is_floor_clean_no_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Пол чистый?\n\n"
             "➢ Нет",
    )
    await state.update_data(is_floor_clean="нет")
    await callback.message.answer(
        text="Есть ли дефекты на тележках?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.is_carts_defects)


@router_start_shift.message(StateFilter(FSMStartShift.is_floor_clean))
async def warning_is_floor_clean_command(message: Message):
    await message.answer(
        text="Нажмите на нужную кнопку под сообщением с вопросом",
    )


@router_start_shift.callback_query(StateFilter(FSMStartShift.is_carts_defects), F.data == "yes")
async def process_is_carts_defects_yes_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Есть ли дефекты на тележках?\n\n"
             "➢ Да",
    )
    await state.update_data(is_carts_defects="да")
    await callback.message.answer(
        text="Пришлите фотографии дефектов",
        reply_markup=create_cancel_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.defects_photo)


@router_start_shift.callback_query(StateFilter(FSMStartShift.is_carts_defects), F.data == "no")
async def process_is_carts_defects_no_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Есть ли дефекты на тележках?\n\n"
             "➢ Нет",
    )
    await state.update_data(is_carts_defects="нет")

    start_shift_dict = await state.get_data()

    day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
    current_date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(
        f'%d/%m/%Y - {RUSSIAN_WEEK_DAYS[day_of_week]}')

    await send_report(
        message=callback.message,
        state=state,
        data=start_shift_dict,
        date=current_date,
        chat_id=cached_places[start_shift_dict['place']],
    )


@router_start_shift.message(StateFilter(FSMStartShift.defects_photo))
async def process_defects_photo_command(message: Message, state: FSMContext):
    if message.photo:
        if "defects_photo" not in await state.get_data():
            await state.update_data(defects_photo=[message.photo[-1].file_id])

        start_shift_dict = await state.get_data()

        day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
        current_date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(f'%d/%m/%Y - {RUSSIAN_WEEK_DAYS[day_of_week]}')

        await send_report(
            message=message,
            state=state,
            data=start_shift_dict,
            date=current_date,
            chat_id=cached_places[start_shift_dict['place']],
        )
    else:
        await message.answer(
            text="Пришлите фотографии дефектов",
            reply_markup=create_cancel_kb(),
        )


@router_start_shift.message(StateFilter(FSMStartShift.is_carts_defects))
async def warning_is_carts_defects_command(message: Message):
    await message.answer(
        text="Нажмите на нужную кнопку под сообщением с вопросом",
    )

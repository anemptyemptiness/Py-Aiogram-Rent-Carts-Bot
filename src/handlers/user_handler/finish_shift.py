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
from src.fsm.fsm import FSMFinishShift
from src.keyboards.keyboard import create_places_kb, create_cancel_kb
from src.middlewares.album_middleware import AlbumsMiddleware
from src.callbacks.place import PlaceCallbackFactory
from src.lexicon.lexicon_ru import RUSSIAN_WEEK_DAYS
from src.db import cached_places
import logging

router_finish_shift = Router()
router_finish_shift.message.middleware(middleware=AlbumsMiddleware(2))
logger = logging.getLogger(__name__)


async def report(data: Dict[str, Any], date: str, user_id: Union[str, int]) -> str:
    return "📝Закрытие смены:\n\n" \
           f"Дата: {date}\n" \
           f"Точка: {data['place']}\n" \
           f"Имя: {await AsyncOrm.get_current_name(user_id=user_id)}\n\n" \
           f"Общая выручка: <em>{data['summary']}</em>\n" \
           f"Наличка: <em>{data['cash']}</em>\n" \
           f"Безнал: <em>{data['online_cash']}</em>\n" \
           f"QR-код: <em>{data['qr_code']}</em>\n\n" \
           f"Расход: <em>{data['expenditure']}</em>\n" \
           f"Зарплата: <em>{data['salary']}</em>\n\n" \
           f"Инкассация: <em>{data['encashment']}</em>\n\n" \
           f"Количество парковок тележек из Ашана: <em>{data['count_aushan']}</em>\n" \
           f"Количество продаж доп.товара: <em>{data['count_additionally']}</em>"


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

        necessary = [
            InputMediaPhoto(
                media=photo_file_id,
                caption="Необходимые фото за смену (чеки, льготы, тетрадь и т.д)" if i == 0 else ''
            ) for i, photo_file_id in enumerate(data['necessary_photos'])
        ]

        await message.bot.send_media_group(
            media=necessary,
            chat_id=chat_id,
        )

        await AsyncOrm.set_data_to_reports(
            user_id=message.chat.id,
            place=data["place"],
            visitors=data["visitors"],
            revenue=data["summary"],
        )

        await message.answer(
            text="Отлично! Отчёт успешно отправлен👍🏻",
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer(
            text="Вы вернулись в главное меню",
        )

    except Exception as e:
        logger.exception("Ошибка не с телеграм в finish_shift.py")
        await message.bot.send_message(
            text=f"Finish shift report error: {e}\n"
                 f"User id: {message.chat.id}",
            chat_id=settings.ADMIN_ID,
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer(
            text="Упс... что-то пошло не так, сообщите руководству!",
            reply_markup=ReplyKeyboardRemove(),
        )
    except TelegramAPIError as e:
        logger.exception("Ошибка с телеграм в finish_shift.py")
        await message.bot.send_message(
            text=f"Finish shift report error: {e}\n"
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


@router_finish_shift.message(Command(commands="finish_shift"), StateFilter(default_state))
async def process_finish_shift_command(message: Message, state: FSMContext):
    await message.answer(
        text="Пожалуйста, выберите свою рабочую точку из списка <b>ниже</b>",
        reply_markup=await create_places_kb(),
        parse_mode="html",
    )
    await state.set_state(FSMFinishShift.place)


@router_finish_shift.callback_query(StateFilter(FSMFinishShift.place), PlaceCallbackFactory.filter())
async def process_select_place_command(callback: CallbackQuery, callback_data: PlaceCallbackFactory, state: FSMContext):
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Пожалуйста, выберите свою рабочую точку из списка <b>ниже</b>\n\n"
             f"➢ {callback_data.title}",
        parse_mode="html",
    )
    await state.update_data(place=callback_data.title)
    await callback.message.answer(
        text="Напишите общее число посетителей <b>целым числом</b>\n\n",
        parse_mode="html",
        reply_markup=create_cancel_kb(),
    )
    await callback.answer()
    await state.set_state(FSMFinishShift.visitors)


@router_finish_shift.message(StateFilter(FSMFinishShift.visitors), F.text.isdigit())
async def process_finish_shift_visitors_command(message: Message, state: FSMContext):
    await state.update_data(visitors=int(message.text))
    await message.answer(
        text="Напишите общую выручку <b>целым числом</b>\n\n"
             "<em>Например: 10000</em>\n\n"
             "Если выручки нет, напишите 0",
        parse_mode="html",
        reply_markup=create_cancel_kb(),
    )
    await state.set_state(FSMFinishShift.summary)


@router_finish_shift.message(StateFilter(FSMFinishShift.visitors))
async def warning_finish_shift_visitors_command(message: Message):
    await message.answer(
        text="Введите количество посетителей <b>целым числом</b>",
        parse_mode="html",
    )


@router_finish_shift.message(StateFilter(FSMFinishShift.summary), F.text.isdigit())
async def process_finish_shift_summary_command(message: Message, state: FSMContext):
    await state.update_data(summary=int(message.text))
    await message.answer(
        text="Введите суммарное количество наличными за сегодня <b>целым числом</b>\n\n"
             "<em>Например: 10000</em>\n\n",
        parse_mode="html",
        reply_markup=create_cancel_kb(),
    )
    await state.set_state(FSMFinishShift.cash)


@router_finish_shift.message(StateFilter(FSMFinishShift.summary))
async def warning_finish_shift_summary_command(message: Message):
    await message.answer(
        text="Напишите общую выручку <b>целым числом</b>\n\n"
             "<em>Например: 10000</em>\n\n"
             "Если выручки нет, напишите 0",
        parse_mode="html",
        reply_markup=create_cancel_kb(),
    )


@router_finish_shift.message(StateFilter(FSMFinishShift.cash), F.text.isdigit())
async def process_finish_shift_cash_command(message: Message, state: FSMContext):
    await state.update_data(cash=message.text)
    await message.answer(
        text="Введите суммарное количество безнала за сегодня <b>целым числом</b>\n\n"
             "<em>Например: 10000</em>\n\n",
        parse_mode="html",
        reply_markup=create_cancel_kb(),
    )
    await state.set_state(FSMFinishShift.online_cash)


@router_finish_shift.message(StateFilter(FSMFinishShift.cash))
async def warning_finish_shift_cash_command(message: Message):
    await message.answer(
        text="Введите суммарное количество наличными за сегодня <b>целым числом</b>\n\n"
             "<em>Например: 10000</em>\n\n",
        parse_mode="html",
        reply_markup=create_cancel_kb(),
    )


@router_finish_shift.message(StateFilter(FSMFinishShift.online_cash), F.text.isdigit())
async def process_finish_shift_online_cash_command(message: Message, state: FSMContext):
    await state.update_data(online_cash=message.text)
    await message.answer(
        text="Введите суммарное количество по QR-коду за сегодня <b>целым числом</b>\n\n"
             "<em>Например: 10000</em>\n\n",
        parse_mode="html",
        reply_markup=create_cancel_kb(),
    )
    await state.set_state(FSMFinishShift.qr_code)


@router_finish_shift.message(StateFilter(FSMFinishShift.online_cash))
async def warning_finish_shift_online_cash_command(message: Message):
    await message.answer(
        text="Введите суммарное количество безнала за сегодня <b>целым числом</b>\n\n"
             "<em>Например: 10000</em>\n\n",
        parse_mode="html",
        reply_markup=create_cancel_kb(),
    )


@router_finish_shift.message(StateFilter(FSMFinishShift.qr_code), F.text.isdigit())
async def process_finish_shift_qr_code_command(message: Message, state: FSMContext):
    await state.update_data(qr_code=message.text)
    await message.answer(
        text="Введите сумму расхода за сегодня <b>целым числом</b>\n\n"
             "<em>Например: 500</em>\n\n",
        parse_mode="html",
        reply_markup=create_cancel_kb(),
    )
    await state.set_state(FSMFinishShift.expenditure)


@router_finish_shift.message(StateFilter(FSMFinishShift.qr_code))
async def warning_finish_shift_qr_code_command(message: Message):
    await message.answer(
        text="Введите суммарное количество по QR-коду за сегодня <b>целым числом</b>\n\n"
             "<em>Например: 10000</em>\n\n",
        parse_mode="html",
        reply_markup=create_cancel_kb(),
    )


@router_finish_shift.message(StateFilter(FSMFinishShift.expenditure), F.text.isdigit())
async def process_finish_shift_expenditure_command(message: Message, state: FSMContext):
    await state.update_data(expenditure=message.text)
    await message.answer(
        text="Введите сумму, сколько Вы взяли сегодня зарплатой\n\n"
             "Если Вы не брали зарплату, напишите 0\n\n",
        reply_markup=create_cancel_kb(),
    )
    await state.set_state(FSMFinishShift.salary)


@router_finish_shift.message(StateFilter(FSMFinishShift.expenditure))
async def warning_finish_shift_expenditure_command(message: Message):
    await message.answer(
        text="Введите сумму расхода за сегодня <b>целым числом</b>\n\n"
             "<em>Например: 500</em>\n\n",
        parse_mode="html",
        reply_markup=create_cancel_kb(),
    )


@router_finish_shift.message(StateFilter(FSMFinishShift.salary), F.text.isdigit())
async def process_finish_shift_salary_command(message: Message, state: FSMContext):
    await state.update_data(salary=message.text)
    await message.answer(
        text="Введите, сколько денег остается в инкассацию",
        reply_markup=create_cancel_kb(),
    )
    await state.set_state(FSMFinishShift.encashment)


@router_finish_shift.message(StateFilter(FSMFinishShift.salary))
async def warning_finish_shift_salary_command(message: Message):
    await message.answer(
        text="Введите сумму, сколько Вы взяли сегодня зарплатой <b>числом</b>\n\n"
             "Если Вы не брали зарплату, напишите 0\n\n",
        parse_mode="html",
        reply_markup=create_cancel_kb(),
    )


@router_finish_shift.message(StateFilter(FSMFinishShift.encashment), F.text)
async def process_finish_shift_encashment_command(message: Message, state: FSMContext):
    await state.update_data(encashment=message.text)
    await message.answer(
        text="Напишите количество парковок тележек из Ашана <b>числом</b>\n\n"
             "<em>Например: 15</em>",
        parse_mode="html",
        reply_markup=create_cancel_kb(),
    )
    await state.set_state(FSMFinishShift.count_aushan)


@router_finish_shift.message(StateFilter(FSMFinishShift.encashment))
async def warning_finish_shift_encashment_command(message: Message):
    await message.answer(
        text="Введите, сколько денег остается в инкассацию",
        reply_markup=create_cancel_kb(),
    )


@router_finish_shift.message(StateFilter(FSMFinishShift.count_aushan), F.text.isdigit())
async def process_finish_shift_count_aushan_command(message: Message, state: FSMContext):
    await state.update_data(count_aushan=message.text)
    await message.answer(
        text="Напишите общее количество продаж доп.товара за день(шарики и т.д) "
             "<b>числом</b>\n\n"
             "<em>Например: 10</em>",
        parse_mode="html",
        reply_markup=create_cancel_kb(),
    )
    await state.set_state(FSMFinishShift.count_additionally)


@router_finish_shift.message(StateFilter(FSMFinishShift.count_aushan))
async def warning_finish_shift_count_aushan_command(message: Message):
    await message.answer(
        text="Напишите количество парковок тележек из Ашана <b>числом</b>\n\n"
             "<em>Например: 15</em>",
        parse_mode="html",
        reply_markup=create_cancel_kb(),
    )


@router_finish_shift.message(StateFilter(FSMFinishShift.count_additionally), F.text.isdigit())
async def process_finish_shift_count_additionally_command(message: Message, state: FSMContext):
    await state.update_data(count_additionally=message.text)
    await message.answer(
        text="Пришлите необходимые фото за смену (чеки, льготы, тетрадь и т.д)",
        reply_markup=create_cancel_kb(),
    )
    await state.set_state(FSMFinishShift.necessary_photos)


@router_finish_shift.message(StateFilter(FSMFinishShift.count_additionally))
async def warning_finish_shift_count_additionally_command(message: Message):
    await message.answer(
        text="Напишите общее количество продаж доп.товара за день(шарики и т.д) "
             "<b>числом</b>\n\n"
             "<em>Например: 10</em>",
        parse_mode="html",
        reply_markup=create_cancel_kb(),
    )


@router_finish_shift.message(StateFilter(FSMFinishShift.necessary_photos))
async def process_finish_shift_necessary_photos_command(message: Message, state: FSMContext):
    if message.photo:
        if "necessary_photos" not in await state.get_data():
            await state.update_data(necessary_photos=[message.photo[-1].file_id])

        await message.answer(
            text="Сфотографируйте объект (1 фото)",
            reply_markup=create_cancel_kb(),
        )
        await state.set_state(FSMFinishShift.object_photo)
    else:
        await message.answer(
            text="Пришлите необходимые фото за смену (чеки, льготы, тетрадь и т.д)",
            reply_markup=create_cancel_kb(),
        )


@router_finish_shift.message(StateFilter(FSMFinishShift.object_photo))
async def process_finish_shift_object_photo_command(message: Message, state: FSMContext):
    if message.photo:
        if "object_photo" not in await state.get_data():
            await state.update_data(object_photo=[message.photo[-1].file_id])

        finish_shift_dict = await state.get_data()

        day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
        current_date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(f'%d/%m/%Y - {RUSSIAN_WEEK_DAYS[day_of_week]}')

        await send_report(
            message=message,
            state=state,
            data=finish_shift_dict,
            date=current_date,
            chat_id=cached_places[finish_shift_dict['place']],
        )
    else:
        await message.answer(
            text="Сфотографируйте объект (1 фото)",
            reply_markup=create_cancel_kb(),
        )

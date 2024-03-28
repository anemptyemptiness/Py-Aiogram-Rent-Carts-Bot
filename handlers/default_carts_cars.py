from datetime import datetime, timezone, timedelta

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import default_state
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from db import DB_mongo
from keyboards.keyboard_helper import KeyboardHelper
from lexicon.lexicon_ru import TO_RENTING, TO_FREE
from fsm.fsm import FSMWorkingDay

router_carts = Router()


@router_carts.message(Command(commands="carts_cars"), StateFilter(default_state))
async def create_carts_command(message: Message, state: FSMContext):
    await message.answer(
        text="🛒<b>Список тележек:</b>",
        reply_markup=KeyboardHelper.reset_keyboard(),
        parse_mode="html",
    )

    DB_mongo.reset_carts()

    await state.update_data(buttons=KeyboardHelper().buttons)
    await state.set_state(FSMWorkingDay.working_day)


@router_carts.message(Command(commands="carts_cars"), StateFilter(FSMWorkingDay.working_day))
async def upload_existing_kb_command(message: Message, state: FSMContext, bot: Bot):
    msg = await message.answer(
        text="🛒<b>Список тележек:</b>",
        reply_markup=KeyboardHelper.get_kb(buttons=(await state.get_data())["buttons"]),
        parse_mode="html",
    )

    last_msg_id = DB_mongo.get_last_message_id_info(message.from_user.id)

    await bot.delete_message(
        chat_id=message.chat.id,
        message_id=last_msg_id,
    )

    DB_mongo.update_today(
        message_id=msg.message_id,
        chat_id=message.chat.id,
    )


@router_carts.callback_query(StateFilter(FSMWorkingDay.working_day), F.data == "cart_1")
async def process_cart_1_command(callback: CallbackQuery, state: FSMContext):
    time_now = datetime.now(tz=timezone(timedelta(hours=3.0)))
    buttons = (await state.get_data())["buttons"]

    # тележка свободна и меняем ее на арендованную
    if "✅" in buttons["cart_1"]:
        KeyboardHelper.change_btn_to_rent(buttons=buttons, num_of_button=1)
        await state.update_data(buttons=buttons)
        status = DB_mongo.update_info_cart(
            number_of_cart=1,
            to_status=TO_RENTING,
            time=time_now.strftime("%H:%M"),
        )

    # тележка в аренде и меняем ее на свободную
    else:
        KeyboardHelper.change_btn_to_free(buttons=buttons, num_of_button=1)
        await state.update_data(buttons=buttons)
        status = DB_mongo.update_info_cart(
            number_of_cart=1,
            to_status=TO_FREE,
        )

    DB_mongo.update_today(
        message_id=callback.message.message_id,
        chat_id=callback.message.chat.id,
    )

    await callback.message.edit_reply_markup(
        reply_markup=KeyboardHelper.get_kb(buttons=buttons),
    )

    await callback.answer(
        text="Тележка арендована" if status == TO_RENTING else "Тележка освободилась"
    )

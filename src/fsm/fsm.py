from aiogram.fsm.state import StatesGroup, State


class Authorise(StatesGroup):
    fullname = State()


class FSMCarts(StatesGroup):
    place = State()
    first_time = State()  # первый запуск, чтобы залить новую клавиатуру
    working_day = State()  # запуск клавиатур в рамках рабочего дня


class FSMStartShift(StatesGroup):
    place = State()
    employee_photo = State()
    object_photo = State()
    is_carts_clean = State()
    is_floor_clean = State()
    is_carts_defects = State()
    defects_photo = State()


class FSMFinishShift(StatesGroup):
    place = State()
    visitors = State()
    summary = State()
    cash = State()
    online_cash = State()
    qr_code = State()
    expenditure = State()
    salary = State()
    encashment = State()
    count_aushan = State()
    count_additionally = State()
    necessary_photos = State()
    object_photo = State()


class FSMEncashment(StatesGroup):
    place = State()
    receipt_photo = State()
    summary_and_date = State()


class FSMAdmin(StatesGroup):
    # главное меню
    rules = State()
    in_adm = State()

    # добавление сотрудника в БД
    add_employee_id = State()
    add_employee_name = State()
    add_employee_username = State()
    add_employee_phone = State()
    check_employee = State()
    rename_employee = State()
    reid_employee = State()
    reusername_employee = State()

    # удаление сотрудника из БД
    which_employee_to_delete = State()
    deleting_employee = State()

    # получить список сотрудников
    watching_employees = State()
    current_employee = State()

    # добавить админа в БД
    add_admin_id = State()
    add_admin_name = State()
    add_admin_username = State()
    add_admin_phone = State()
    check_admin = State()
    rename_admin = State()
    reid_admin = State()
    reusername_admin = State()

    # удалить админа в БД
    which_admin_to_delete = State()
    deleting_admin = State()

    # получить список админов
    watching_admin = State()
    current_admin = State()

    # добавить рабочую точку в БД
    add_place = State()
    add_place_id = State()
    add_place_count_carts = State()  # !!!
    check_place = State()
    rename_place = State()
    reid_place = State()
    recount_carts_place = State()  # !!!

    # удалить рабочую точку в БД
    which_place_to_delete = State()
    deleting_place = State()

    # получить список рабочих точек
    watching_place = State()
    current_place = State()

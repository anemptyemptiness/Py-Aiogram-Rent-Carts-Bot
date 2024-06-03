from src.handlers.admin_handler.adding.add_employee import router_admin
from src.handlers.admin_handler.deleting.delete_employee import router_del_emp
from src.handlers.admin_handler.watching.employee_list import router_show_emp
from src.handlers.admin_handler.adding.add_admin import router_add_adm
from src.handlers.admin_handler.deleting.delete_admin import router_del_adm
from src.handlers.admin_handler.watching.admin_list import router_show_admins
from src.handlers.admin_handler.adding.add_place import router_add_place
from src.handlers.admin_handler.deleting.delete_place import router_del_place
from src.handlers.admin_handler.watching.place_list import router_show_places

__all__ = [
    "router_admin",
    "router_del_emp",
    "router_show_emp",
    "router_add_adm",
    "router_del_adm",
    "router_show_admins",
    "router_add_place",
    "router_del_place",
    "router_show_places",
]

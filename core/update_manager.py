import os
from core.net_time import get_network_datetime
from core.generate_config import generate_config  # 正确引用 generate_config.py


UPDATE_FLAG = os.path.join("config", "last_update.txt")


def need_update():
    now = get_network_datetime().strftime("%Y%m%d")

    if not os.path.exists(UPDATE_FLAG):
        return True

    with open(UPDATE_FLAG, "r", encoding="utf-8") as f:
        last = f.read().strip()

    return last != now


def update_if_needed():
    if not need_update():
        return False

    generate_config()

    os.makedirs("config", exist_ok=True)
    with open(UPDATE_FLAG, "w", encoding="utf-8") as f:
        f.write(get_network_datetime().strftime("%Y%m%d"))

    return True

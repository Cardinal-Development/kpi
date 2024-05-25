from global_path import zaber_pos
import json
import logging
from kpi.motion_control.Sever import Controller


logger = logging.getLogger(__name__)


def read_json(_path):
    with open(_path, "r", encoding="utf8") as f:
        return json.load(f)


class zaber_motion:
    def __init__(self):
        self.sever = Controller
        self.position = read_json(zaber_pos)

    def move_ab(self, pos: dict):
        para = {"set_positions": pos}
        command = f"zaber_motion({para})"
        return self.sever.send(command)

    def home(self):
        para = {"go_home": None}
        command = f"zaber_motion({para})"
        logger.info(f"zaber home")
        return self.sever.send(command)

    def move_by_name(self, group_name, position_name):
        val = self.position[group_name][position_name]
        axis_names = ["x_axis_left", "x_axis_right", "y_axis", "z_axis"]
        _ = dict(zip(axis_names, val))
        logger.info(f"{_}")
        return self.move_ab(_)


zaber_controller = zaber_motion()

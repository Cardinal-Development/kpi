from global_path import robot_pos
import json
import logging
import time

from kpi.motion_control.Sever import Controller

logger = logging.getLogger(__name__)


class GP8:
    def __init__(self):
        self.sever = Controller
        self.position_data = read_json(robot_pos)

    def robot_connect(self):
        return self.sever.connect()

    def reset_fixture(self):
        command = "cmd_reset_fixture()"
        return self.sever.send(command)

    def release_fixture(self):
        command = "cmd_release_fixture()"
        return self.sever.send(command)

    def move_joint_rel(self, data):
        val = ["Jog_01", "Jog_02", "Jog_03", "Jog_04", "Jog_05", "Jog_06"]
        _ = zip(val, data)
        command = f'cmd_move_joint_increment({dict(zip(val, data))})'
        print(command)
        ret = self.sever.send(command)
        return ret

    def move_pos_rel(self, data):
        val = ["x", "y", "z", "rx", "ry", "rz"]
        command = f"cmd_move_position_increment({dict(zip(val, data))})"
        ret = self.sever.send(command)
        return ret

    def move_pos_ab(self, data):
        val = ["x", "y", "z", "rx", "ry", "rz"]
        command = f"cmd_move_position_absolute({dict(zip(val, data))})"
        ret = self.sever.send(command)
        if ret[0]:
            return self.__check_joint(data, 5, 10)
        else:
            return ret

    def move_joint_ab(self, data: dict):
        val = ["Jog_01", "Jog_02", "Jog_03", "Jog_04", "Jog_05", "Jog_06"]
        command = f"cmd_move_joint_absolute({dict(zip(val, data))})"
        ret = self.sever.send(command)
        logger.info(f"{command}")
        if ret[0]:
            return self.__check_joint(data, 5, 10)
        else:
            return ret

    def call_job(self, job_name, timeout=5):
        command = f"run_job('{job_name}')"
        ret = self.sever.send(command)
        time.sleep(2)
        if ret[0]:
            st = time.time()
            while time.time() - st < timeout:
                time.sleep(0.5)
                _ = self.check_di('a job is running')
                if _[0]:
                    logger.info(f"job_running is {_[1]}---{type(_[1])}")
                    if not _[1]['a job is running']:
                        logger.info(f"job:{job_name} is complete")
                        return True, f"job is complete"
                else:
                    return _
            return False, f"job:{job_name} running time_out!!!"
        else:
            return ret

    def __check_joint(self, tar_joint: list, check_range, time_out):
        start_time = time.time()
        result = False, f"move check time out"
        while time.time() - start_time < time_out:
            command = f"cmd_check_joint()"
            ret = self.sever.send(command)
            if ret[0]:
                joint = eval(ret[1].split("check_joint:")[-1])
                cur_joint = [v for k, v in joint.items()]
                if check_list_data(cur_joint, tar_joint, check_range):
                    result = True, f"robot move complete"
                    break
            else:
                result = False, f"{command} is error:{ret[1]}"
                break
            time.sleep(0.3)
        return result

    def __check_pos(self, tar_joint: list, check_range, time_out):
        start_time = time.time()
        result = False, f"move check time out"
        while time.time() - start_time < time_out:
            command = f"cmd_check_position()"
            ret = self.sever.send(command)
            if ret[0]:
                joint = eval(ret[1].split("check_position:")[-1])
                cur_joint = [v for k, v in joint.items()]
                if check_list_data(cur_joint, tar_joint, check_range):
                    result = True, f"robot move complete"
            else:
                result = False, f"{command} is error:{ret[1]}"
                break
            time.sleep(0.3)
        return result

    def move_joint_by_name(self, group_name, position_name):
        val = self.position_data[group_name][position_name]
        return self.move_joint_ab(val)

    def check_robot_alarm(self):
        if not self.robot_connect_state():
            return False
        else:
            for __di in ["e_stop_satisfied", "gate"]:
                ret = self.check_di(__di)
                if ret[0]:
                    for k, v in ret[1].items():
                        if not v:
                            logger.error(f"=====>robot alarm:{k} is {v}!<=======")
                            return False
                else:
                    logger.error(f"robot alarm:{ret[1]}!")
                    return False
            return True

    def robot_connect_state(self):
        command = f"cmd_robot_connect()"
        ret = self.sever.send(command)
        if ret[0]:
            _data: str = ret[1]
            __ = _data.split("robot_connect:")[-1]
            if eval(__):
                return True
            else:
                logger.error(f"=====>robot  disconnect!!!!!<=======")
                return False
        else:
            return False

    def check_di(self, name):
        command = f"cmd_check_input('{name}')"
        ret = self.sever.send(command)
        if ret[0]:
            _data: str = ret[1]
            __ = _data.split("check_input:")[-1]
            return True, eval(__)
        else:
            return ret

    def set_do(self, state):
        if isinstance(state, dict):
            command = f"cmd_set_output({state})"
            ret = self.sever.send(command)
            return ret
        else:
            return False, f"{state} type is not dict"

    # 11.24  发送控制门的信号
    def set_usb_door(self, state):
        command = f"set_usb_4750('{state}')"
        ret = self.sever.send(command)
        return ret


def check_list_data(a: list, b: list, check_range: float):
    __sum = []
    for _a, _b in zip(a, b):
        ret = abs(float(_a) - float(_b))
        if ret < check_range:
            _ = True
        else:
            _ = False
        __sum.append(_)
    return not (False in __sum)


def read_json(_path):
    with open(_path, "r", encoding="utf8") as f:
        return json.load(f)


GP8_Robot = GP8()

if __name__ == '__main__':
    print(read_json())
    pass
    # robot = GP8()
    # print(robot.robot_connect())
    # print(robot.reset_fixture())
    # print(robot.move_joint_rel([400, 0, 0, 0, 0, 0]))
    # data = read_json('../config/robot_position.json')
    # a = data['series_01']['c_005']
    # print(a)
    # print(robot.move_joint_by_name("series_01", "c_002"))

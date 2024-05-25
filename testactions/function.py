import logging
import os.path
import os
import time
from datetime import datetime
from typing import Mapping
from arvr.projects.manufacturing.cardinal.testactions.results import (
    Fail,
    Pass,
    ExceptionFail,
)

from arvr.projects.manufacturing.cardinal.testactions.testaction import (
    Context,
    TestAction,
)
from arvr.projects.manufacturing.cardinal.testactions.prompt import (
    Prompt,
    PromptResponse,
)
from arvr.projects.manufacturing.cardinal.testactions.exceptions import (
    PromptNotConsumedError,
)

from kpi.motion_control.GP8.robot_control import GP8_Robot as Robot

# from kpi.motion_control.light.light_control import light_controller

# from kpi.motion_control.zaber_motion.zaber_motion import zaber_controller

# from kpi.dut.metaCommandYaml import camera, dut, commandRunner

from kpi.dut.dut_record import run_properties

from kpi.dut.adb_CommandYaml_ import camera_adbDut

from global_path import adbTool_path

TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
logger = logging.getLogger(__name__)

dut_record = run_properties()
cmdPara = {}


#############################################################
# TEST ACTIONS BEGIN HERE:
# TestActions can only be run by TestPlans
#############################################################


class TAExceptionFail(TestAction):
    def run(self, context, nesting_level):
        return ExceptionFail(self, nesting_level, Exception())


# 5.8整合chico===========⬇=======================
class TestInformationDisplay(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.time_out = action_data.get("timeout", 90)
        self.messages = action_data.get("message")
        self.skip = action_data.get("skip", True)

    def execute_prompt(self, context: Context, prompt: Prompt) -> PromptResponse:
        """
        add prompt to context
        wait for prompt response
        timeout otherwise

        context.prompt should be None before and after this function

        Args:
            context (Context): Context object containing
            prompt: Prompt object

        Return:
            PromptResponse

        """
        if context.prompt:
            raise PromptNotConsumedError("prompt already exists in context")

        context.prompt = prompt

        logger.info("Waiting for prompt response")
        while not isinstance(context.prompt, PromptResponse):
            if prompt.time_remaining <= 0:
                context.prompt = PromptResponse(
                    result=PromptResponse.PromptResult("TIMEOUT")
                )

            time.sleep(0.5)

        prompt_response = context.prompt
        context.prompt = None
        return prompt_response

    def run(self, context: Context, nesting_level: int):
        if self.skip:
            return Pass(self, nesting_level)
        prompt = Prompt(message=self.messages, timeout=self.time_out, enable_text_input=True)
        response = self.execute_prompt(context, prompt)
        if response.result != PromptResponse.PromptResult.OK:
            logger.info("I did not get OK got %s", response.result)
            return Fail(self, nesting_level)
        logger.info(f"enable_text_input-->{response}")
        try:
            # if 'p' not in response.text_input.lower():
            if len(response.text_input) < 1:
                return Fail(self, nesting_level)

            temp_id = response.text_input
            context.test_id = context.test_id + '_' + temp_id
            context.temp_id = temp_id

            logger.info(f"enable_text_input-->{response.text_input}")
            logger.info(f"context.temp_id -->{context.temp_id}")
        except Exception as e:
            logger.error(f"显示text错误>{e}")
            return Fail(self, nesting_level)
        logger.info(f"step:TestInformationDisplay -->finish")
        return Pass(self, nesting_level)


class TestInformationDisplay_2(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.time_out = action_data.get("timeout", 90)
        self.messages = action_data.get("message")
        self.skip = action_data.get("skip", True)

    def run(self, context: Context, nesting_level: int):
        if self.skip:
            return Pass(self, nesting_level)
        prompt = Prompt(message=self.messages, timeout=10, enable_text_input=False)
        context.prompt = prompt
        while not isinstance(context.prompt, PromptResponse):
            if prompt.time_remaining <= 0:
                context.prompt = PromptResponse(
                    result=PromptResponse.PromptResult("TIMEOUT")
                )
            time.sleep(0.5)

        if context.prompt.result != PromptResponse.PromptResult.OK:
            logger.info("I did not get OK got %s", context.prompt.result)
            return Fail(self, nesting_level)

        # context.prompt = prompt
        # time.sleep(5)
        logger.info(f'test_id:{context.test_id}')
        return Pass(self, nesting_level)


class TestInformationDisplay_3(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.time_out = action_data.get("timeout", 90)
        self.messages = action_data.get("message")
        self.skip = action_data.get("skip", True)

    def run(self, context: Context, nesting_level: int):
        if self.skip:
            return Pass(self, nesting_level)
        try:
            message = context.temp_id
            logger.info(f"获取到的message是{message}")
            path_ = 'D:\\MESSAGES'
            if not os.path.exists(path_):
                os.makedirs(path_)
            with open(f'{path_}\\log.txt', 'w') as f:
                f.write(message)
        except Exception as e:
            logger.info(f"获取context.temp_id出错>{message}")
        return Pass(self, nesting_level)


class TestActionCallChicoPrepare(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.skip = action_data.get("skip", True)
        self.timeout = action_data.get("timeout", 80)

    def run(self, context: Context, nesting_level: int):
        if self.skip:
            return Pass(self, nesting_level)

        test_id = context.temp_id
        try:
            command = f'python chico.par prepare_device --rtm {test_id} --reboot'
            res, err_res,recode = camera_adbDut.chico_cmd(command, self.timeout)
            logger.info(f"command is {command}")
            logger.info(f"recode------>: {recode} ")

            if recode == 0:
                logger.info(f"step:call_chico_prepare_device--->finish")
                return Pass(self, nesting_level)
            else:
                return Fail(self, nesting_level)
        except Exception as e:
            logger.info(f"让chico准备运行时出错，->{e}")
            return Fail(self, nesting_level)


class TestActionInvokingChico(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.skip = action_data.get("skip", True)
        self.timeout = action_data.get("timeout", 3000)

    def run(self, context: Context, nesting_level: int):
        if self.skip:
            return Pass(self, nesting_level)
        try:
            output_dir = adbTool_path["output_dir"]
            chico_config_path = adbTool_path["Chico_config_path"]
            time_file = context.serial_number + "_" + context.temp_id + "_" + time.strftime('%Y%m%d_%H%M%S')+"_"+adbTool_path["root_job_name"]
            output_dir_ = output_dir+os.sep+time_file
            if not os.path.exists(output_dir_):
                os.makedirs(output_dir_)
            command = (
                f"$env:OPTITRACK_IP='192.168.1.200'; python chico.par --disable-ui config_collect --check_db_state "
                f"--upload --output_dir {output_dir_} --config_file {chico_config_path}")

            logger.info(f"chico_thread_command-->{command}")

            camera_adbDut.call_chico_thread(command, timeout=self.timeout)
        except Exception as e:
            logger.error(F"调用chico线程时出错：{e}")
            return Fail(self, nesting_level)
        logger.info(f"step:invokingChico--->finish")
        return Pass(self, nesting_level)

# 5.22 chico
class TestActionWaitChicoRecord(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.skip = action_data.get("skip", True)
        self.wait_timeout = action_data.get("wait_timeout", 300)

    def run(self, context: Context, nesting_level: int):
        if self.skip:
            return Pass(self, nesting_level)
        try:
            start_time = time.time()
            while True:
                command = f'adb shell pidof vrs-recorder'
                res, err_res, recode = camera_adbDut.chico_cmd(command, self.timeout)
                logger.info(f"command is {command}")
                logger.info(f"res:{res} ")
                logger.info(f"err_res: {err_res} ")
                logger.info(f"recode------>: {recode} ")

                if recode == 0:
                    break
                else:
                    time.sleep(0.1)
                if time.time() - start_time > self.wait_timeout:
                    logger.error(f"等待chico录制超时")
                    return Fail(self, nesting_level)
            logger.info(f"step:wait_chico_record--->finish")
            return Pass(self, nesting_level)

        except Exception as e:
            logger.info(f"让chico准备运行时出错，->{e}")
            return Fail(self, nesting_level)

class TestActionRobotChicoCallJob(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.skip = action_data.get('skip', False)
        self.job_name = action_data.get('job_name', "")
        self.time_out = action_data.get('job_timeout', 1500)

    def run(self, context: Context, nesting_level: int):

        self.job_name = adbTool_path["root_job_name"]
        logger.info(f"job_name ->{self.job_name}")

        if self.skip:
            return Pass(self, nesting_level)

        if not Robot.check_robot_alarm():
            return Fail(self, nesting_level)

        if "HOME" not in self.job_name:
            camera_adbDut.job_name = self.job_name

        _ret = Robot.call_job(self.job_name, self.time_out)
        logger.info(f"job_name ->{self.job_name}")
        if _ret[0]:
            logger.info(f"step:ChicoRootCallJob-jobname->{self.job_name}-->finish")
            return Pass(self, nesting_level)
        else:
            return Fail(self, nesting_level)


class TestActionJudgingTestResult(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.skip = action_data.get('skip', False)
        self.out_time_ = action_data.get("timeout", 650)

    def run(self, context: Context, nesting_level: int):
        for i in range(int(self.out_time_)):
            if i == 200:
                logger.info(f"i-->:{i}")
                logger.info(f"camera_adbDut-chico_result-->:{camera_adbDut.chico_result}")

            if camera_adbDut.chico_result is None:
                time.sleep(1)
                continue
            else:
                break
        if camera_adbDut.chico_result:
            camera_adbDut.chico_result = None
            logger.info(f"JudgingTestResult-->finish")
            return Pass(self, nesting_level)
        else:
            camera_adbDut.chico_result = None
            return Fail(self, nesting_level)


# chico====================⬆==================


class TestActionRobotServoControl(TestAction):
    """
    Addy: Robot_initial
    james: add robot servo on and off
    """

    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.skip = action_data.get('skip', False)
        self.value = action_data.get('value', "off")

    def run(self, context: Context, nesting_level: int):
        if self.skip:
            return Pass(self, nesting_level)
        if not Robot.check_robot_alarm():
            return Fail(self, nesting_level)
        if self.value.lower() == "on":
            ret = Robot.reset_fixture()
        else:
            ret = Robot.release_fixture()
        if ret[0]:
            logger.info(f"step:TestActionRobotServoControl----->finish")
            return Pass(self, nesting_level)
        else:
            return Fail(self, nesting_level)


class Robot_reset(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.skip = action_data.get('skip', False)

    def run(self, context: Context, nesting_level: int):
        if self.skip:
            return Pass(self, nesting_level)
        if not Robot.check_robot_alarm():
            return Fail(self, nesting_level)

        ret = Robot.reset_fixture()
        if ret[0]:
            return Pass(self, nesting_level)
        else:
            return Fail(self, nesting_level)


class Robot_Move_Joint(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.skip = action_data.get('skip', False)
        self.joint_group = action_data.get('group_name', False)
        self.joint_pos = action_data.get('pos_name', False)

    def run(self, context: Context, nesting_level: int):
        if self.skip:
            return Pass(self, nesting_level)

        if not Robot.check_robot_alarm():
            return Fail(self, nesting_level)

        if self.joint_group and self.joint_pos:
            logger.info(f"======go:{self.joint_group}---{self.joint_pos}")
            _ret = Robot.move_joint_by_name(self.joint_group, self.joint_pos)
            if _ret[0]:
                return Pass(self, nesting_level)
            else:
                return Fail(self, nesting_level)


class TestActionRobotCallJob(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.skip = action_data.get('skip', False)
        self.job_name = action_data.get('job_name', "")
        self.time_out = action_data.get('job_timeout', 10)

    def run(self, context: Context, nesting_level: int):
        if self.skip:
            return Pass(self, nesting_level)

        if not Robot.check_robot_alarm():
            return Fail(self, nesting_level)

        if "HOME" not in self.job_name:
            camera_adbDut.job_name = self.job_name

        _ret = Robot.call_job(self.job_name, self.time_out)
        if _ret[0]:
            logger.info(f"step:calljob-->{self.job_name}---->finish")
            return Pass(self, nesting_level)
        else:
            return Fail(self, nesting_level)


# 11.20
class TestActionInitializeADB_DUT(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.skip = action_data.get('skip', False)

    def run(self, context: Context, nesting_level: int):
        if self.skip:
            return Pass(self, nesting_level)

        ret = camera_adbDut.adb_devices()
        if ret:
            context.serial_number = camera_adbDut.dut_sn
            logger.info(f"step:read_sn---->finish")
            return Pass(self, nesting_level)
        else:
            return Fail(self, nesting_level)


# 11.22
class TestActionInitialize_dut_other_command(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.skip = action_data.get('skip', False)
        self.command: list = action_data.get("command", [])

    def run(self, context: Context, nesting_level: int):
        if self.skip:
            return Pass(self, nesting_level)
        if len(self.command) == 0:
            logger.error("执行命令不能为空！！！")
            return Fail(self, nesting_level)
        else:
            for com in self.command:
                ret = camera_adbDut.simple_command(com)
                if not ret:
                    logger.error(f"执行{com}对应的命令时出错")
                    return Fail(self, nesting_level)
            return Pass(self, nesting_level)


# 11.20
class TestActionInitializeADB_DutVRS(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.skip = action_data.get('skip', False)
        self.timeout = action_data.get('timeout', 500)

    def run(self, context: Context, nesting_level: int):
        if self.skip:
            return Pass(self, nesting_level)

        # ret = camera_adbDut.adb_record()
        #
        # if ret:
        #     ret = camera_adbDut.adb_pull_vrs(self.pull_vrs_path)
        #
        # if ret:
        #     return Pass(self, nesting_level)
        # else:
        #     return Fail(self, nesting_level)
        camera_adbDut.adb_record(self.timeout)
        time.sleep(0.5)
        return Pass(self, nesting_level)


class TestActionInitialize_ADB_VRS_result(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.skip = action_data.get('skip', False)
        self.out_time_ = action_data.get('out_time_', 500)
        self.outputPath = action_data.get("outputPath", "D:/Temp_VRS_PATH")

    def run(self, context: Context, nesting_level: int):
        logger.info(f"判断VRS录制结果，并进行拉取。时间为：{datetime.now().strftime('%Y%m%dT%H%M%S')}")
        T_ = time.time()
        if self.skip:
            return Pass(self, nesting_level)
        #  12.11 把这个超时时间设置为self.out_time 以可控
        for i in range(int(self.out_time_)):  # 1/10 已修改
            # for i in range(106):
            if camera_adbDut.record_res is None:
                time.sleep(1)
                continue
            else:
                break
        # logger.info(f"拉取VRS的文件的地址--》{self.outputPath}")
        if camera_adbDut.record_res:
            # time_ = camera_adbDut.time_dict.get(camera_adbDut.dut_sn)
            # outpath = os.path.join(self.outputPath, camera_adbDut.dut_sn)
            # out_path = os.path.join(outpath, time_)
            time_ = camera_adbDut.time_dict.get(camera_adbDut.dut_sn)
            sn = camera_adbDut.dut_sn
            job_name = camera_adbDut.job_name
            out_path = os.path.join(self.outputPath, time_ + "_" + sn + "_" + job_name)

            if not os.path.exists(out_path):
                os.makedirs(out_path)
            print(f"拉取VRS的文件的地址--》{time_}，{out_path}")

            camera_adbDut.file_data_dict.update({"vrs_path": out_path})
            ret = camera_adbDut.adb_pull_vrs(out_path, self.out_time_)

            camera_adbDut.record_res = None
            if ret:
                logger.info(f"拉取结束时间为：{datetime.now().strftime('%Y%m%dT%H%M%S')}")
                logger.info(f"用时：{time.time() - T_}(s)")
                return Pass(self, nesting_level)
            else:
                return Fail(self, nesting_level)
        else:
            # 12.11 当失败的时候 这里也应该加上camera_adbDut.record_res = None
            # 1/10/24已修改
            camera_adbDut.record_res = None
            return Fail(self, nesting_level)


class TestActionCopyDatafile(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.skip = action_data.get('skip', False)
        self.copy_file_path = action_data.get('copy_file_path', "C:/Temp_VRS_PATH")

    def run(self, context: Context, nesting_level: int):
        if self.skip:
            return Pass(self, nesting_level)

        ret = camera_adbDut.copy_file_function(self.copy_file_path)
        if ret:
            return Pass(self, nesting_level)
        else:
            logger.info(f"拉取出来的Track文件大小不对，或者复制文件使出错。请检查！！！")
            return Fail(self, nesting_level)


class wait_time(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.skip = action_data.get('skip', False)
        self.wait_time = action_data.get('wait_time', False)

    def run(self, context: Context, nesting_level: int):
        if self.skip:
            return Pass(self, nesting_level)
        if self.wait_time:
            time.sleep(self.wait_time)
        return Pass(self, nesting_level)


class TestActionControl_light(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.skip = action_data.get('skip', False)
        self.light_S_H_V = action_data.get('light_S_H_V', [])

    def run(self, context: Context, nesting_level: int):
        if self.skip:
            return Pass(self, nesting_level)
        if len(self.light_S_H_V) == 3:
            cmd_light = f'python vortex_sacn.pex --set_hsv {self.light_S_H_V[0]} {self.light_S_H_V[1]} {self.light_S_H_V[2]}'
            res, err_res = camera_adbDut.track_cmd(cmd_light, 5)
            logger.info(f"控制灯返回的信息为：res: {res}\n err_res: {err_res}")
            if not err_res and 'finished' in res:
                return Pass(self, nesting_level)
            else:
                return Fail(self, nesting_level)
        # 3.4/24
        else:
            logger.info(f"控制灯设置值格式 数量不对，请检查！")
            return Fail(self, nesting_level)


class TestActionStartTest(TestAction):
    """
    11.24
    :start test
    """

    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.skip = action_data.get('skip', False)

    def run(self, context: Context, nesting_level: int):
        if self.skip:
            return Pass(self, nesting_level)
        ret = Robot.set_usb_door('start')
        if not ret[0]:
            logger.error(f"do:testing-{True} error!!!!!")
            return Fail(self, nesting_level)
        elif 'True' not in ret[1]:
            logger.error(f"请关闭门再启动测试！！！！！！！！！！")
            return Fail(self, nesting_level)
        logger.info(f"step:TestActionStartTest---finish")
        return Pass(self, nesting_level)


class TestActionFinishTest(TestAction):
    """
    james:end_test
    """

    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.skip = action_data.get('skip', False)

    def run(self, context: Context, nesting_level: int):
        # if not Robot.robot_connect():
        #     return Fail(self, nesting_level)

        ret = Robot.set_do({"light": True})

        ret = Robot.set_do({"door open": True, "door close": False, "testing": False,
                            "pc_control": False})

        return Pass(self, nesting_level)


# 1.10.24

class TestActionVrsToolToCsv(TestAction):
    """
    把VRS用vrstool解析为csv保存到vrs的同一文件夹下
    """

    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.skip = action_data.get('skip', False)
        self.outputPath = action_data.get("outputPath", "D:/Temp_VRS_PATH")
        self.vrs_name = action_data.get("vrs_name", "rec.vrs")

    def run(self, context: Context, nesting_level: int):
        logger.info(f"把vrs视频通过vrstool解析为csv")

        if self.skip:
            return Pass(self, nesting_level)

        time_ = camera_adbDut.time_dict.get(camera_adbDut.dut_sn)
        sn = camera_adbDut.dut_sn
        job_name = camera_adbDut.job_name
        out_path = os.path.join(self.outputPath, time_ + "_" + sn + "_" + job_name)

        if not os.path.exists(out_path):
            os.makedirs(out_path)

        # out_path = camera_adbDut.file_data_dict.get("vrs_path")
        cmd = rf".\vrstool {out_path}\{self.vrs_name} --serialize-imu {out_path}\ "

        logger.info(f"转VRS的指令是-->{cmd}")
        res, err_res = camera_adbDut.VrsTool_cmd(cmd)

        if res and not err_res:
            logger.info(f"把vrs通过vrstool解析为csv成功，res:{res}")
            return Pass(self, nesting_level)
        else:
            logger.info(f"把vrs通过vrstool解析为csv失败，res:{res}\n err_res:{err_res}")
            return Fail(self, nesting_level)


# 11.20
class TestActionFinishTest_KPI(TestAction):
    """
    james:end_test
    """

    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.skip = action_data.get('skip', False)

    def run(self, context: Context, nesting_level: int):
        """
        如果测试的过程中要锁门的话，在测试的最后解锁门
        """
        _ret = Robot.call_job("HEAD_HOME", 30)
        _ret = Robot.set_usb_door("end")
        logger.info(f"step:TestActionFinishTest---->finish")
        return Pass(self, nesting_level)


# 11.20
class TestActionInitialize_startTracking(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.skip = action_data.get('skip', False)
        self.duration = action_data.get('duration', 100)
        self.outputPathPrefix = action_data.get("outputPathPrefix", "C:/Temp_VRS_PATH")

    def run(self, context: Context, nesting_level: int):

        if self.skip:
            return Pass(self, nesting_level)
        try:
            time_out = self.duration + 30
            time_ = camera_adbDut.time_dict.get(camera_adbDut.dut_sn)
            print(401, f"time_-->{time_}")
            outpath = os.path.join(self.outputPathPrefix, camera_adbDut.dut_sn)
            print(403, f"outpath-->{outpath}")
            out_path = os.path.join(outpath, time_)
            if not os.path.exists(out_path):
                os.makedirs(out_path)
            # 11.21 添加文件拉取的地址到变量中，但是因为不知道具体的文件名，后期估计还要修改
            camera_adbDut.file_data_dict.update({"tracking_path": out_path})
            print(f"拉取track文件的地址是--》{out_path}")
            cmd_shell = f"vrpn_client_recorder --serverIpAddress 192.168.1.200 --duration {self.duration} --outputPathPrefix {out_path}\\ --log_level trace"
            # vrpn_client_recorder --serverIpAddress 192.168.1.200 --duration 10 --outputPathPrefix D:\sw\vrpn\ --log_level trace
            ret = camera_adbDut.func_track_record(cmd_shell, time_out)

            return Pass(self, nesting_level)
        except Exception as e:
            print(e)
            return Fail(self, nesting_level)


class robot_alarm(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.skip = action_data.get('skip', False)

    def run(self, context: Context, nesting_level: int):
        if not Robot.check_robot_alarm():
            return Fail(self, nesting_level)

        logger.info(f"step:robot_alarm----ok")
        return Pass(self, nesting_level)

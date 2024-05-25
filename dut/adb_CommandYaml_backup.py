import os
import signal
import subprocess

from global_path import config_data, order_data, adb_shell_command, adbTool_path
from datetime import datetime
import yaml
import logging
import telnetlib
import time
import re
import paramiko
import threading

logger = logging.getLogger(__name__)


class CommandDut:
    def __init__(self):
        self.dut_sn = None
        self.adb_command = adb_shell_command
        self.AdbTool_path = adbTool_path

    def adb_cmd(self, adb_shell: str):
        """
        使用adb工具执行指定的adb命令并返回结果
        :param adb_shell: 执行的adb命令
        :return: adb命令执行结果
        """
        # 根据adb_shell和adb_tool_path构建实际执行的cmd命令
        adb_tool_path = self.AdbTool_path["adb_path"]
        # 执行命令
        cmd = "cd {} && {}".format(adb_tool_path, adb_shell)
        timeout = 60
        if "vrs-recorder" in adb_shell:
            timeout = 120
        if "pull" in adb_shell:
            timeout = 120
        proc = None
        try:
            proc = subprocess.Popen(cmd,
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    bufsize=-1)
            res, err_res = proc.communicate(timeout=timeout)
            res = res.decode('utf8')
            err_res = err_res.decode('utf8')
            return res, err_res
        # except:
        #     proc.kill()
        #     res = ""
        #     err_res = "timeout"
        #     return res, err_res
        except:
            try:
                if proc is not None:
                    # NULL ""
                    os.kill(proc.pid, signal.Signals.SIGINT)
                    # os.kill(proc.pid,signal.SIGINT)
                    # os.killpg(proc.pid, signal.SIGTERM)
                    time.sleep(1)
            except Exception as e:
                print(f"os.kill(proc.pid, signal.Signals.SIGINT)--->{e}")

            res = ""
            err_res = "timeout"
            return res, err_res

    def track_cmd(self,adb_shell,time_out):
        """
        使用adb工具执行指定的adb命令并返回结果
        :param adb_shell: 执行的adb命令
        :param time_out: 超时
        :return: adb命令执行结果
        """
        # 根据adb_shell和adb_tool_path构建实际执行的cmd命令
        adb_tool_path = self.AdbTool_path["Tracker_path"]
        # 执行命令
        cmd = "cd {} && {}".format(adb_tool_path, adb_shell)

        proc = None
        try:
            proc = subprocess.Popen(cmd,
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    bufsize=-1)
            res, err_res = proc.communicate(timeout=time_out)
            res = res.decode('utf8')
            err_res = err_res.decode('utf8')
            return res, err_res
        except:
            proc.kill()
            res = ""
            err_res = "timeout"
            return res, err_res


    def adb_devices(self):
        adb_shell = self.adb_command.get('sn_read')[0]
        i = 0
        while True:
            res, err_res = self.adb_cmd(adb_shell)
            # 获取所有设备的SN
            pattern = re.compile(r'\n(.*)\tdevice')
            search_res = pattern.findall(res)

            # 当前连接的DUT数量
            current_dut_count = len(search_res)
            if current_dut_count == 0 and i < 8:
                time.sleep(0.5)
                i += 1
            else:
                break
        print(f"read-sn_shell:{adb_shell}")

        if current_dut_count == 0:
            logger.info(f"读取SN失败")
            return False

        self.dut_sn = search_res[0]
        logger.info(f"读取到的sn为:{self.dut_sn}")
        return True

    def adb_record(self):
        adb_shell = self.adb_command.get('recorder')[0]

        res, error = self.adb_cmd(adb_shell)
        if error:
            logger.info(f"录像失败:error: {error}  res:{res}")
            return False
        else:
            logger.info(f"录像成功:{res}")
            return True

    def adb_pull_vrs(self, pull_file_path):
        shell1 = self.adb_command.get('adb_pull_vrs')[0]
        file_path = os.path.join(pull_file_path, self.dut_sn)
        adb_shell = shell1.replace("[local_vrs_path]", file_path)
        res, err_res = self.adb_cmd(adb_shell)
        # 拉取失败
        if err_res or '[100%]' not in res:
            print(logger)
            logger.debug(f"CMD: {adb_shell}")
            logger.debug(f"failed:pull fail--err_res:{err_res}")
            return False

        else:
            logger.debug(f"CMD: {adb_shell}")
            # file_name = filename
            # pull_time = round(end_pull_time - start_pull_time, 3)  # 拉取耗时
            # file_path = os.path.join(pull_file_path, file_name).replace("\\", "/")  # vrs文件路径，\\ -> /
            # file_size = os.stat(file_path).st_size  # file total bytes
            # pull_rate_b = file_size / pull_time  # pull rate: bytes/s
            # pull_rate_mb = pull_rate_b / 1024 / 1024  # pull rate: MB/s
            # pull_rate = round(pull_rate_mb, 3)
            # file_mb = file_size / 1024 / 1024  # 保留3位小数

            # log
            # self.succeed_msg(f"{sn} filename: {filename}.vrs", logger, namespace, "DEBUG")
            # self.succeed_msg(f"{sn} pull finished", logger, namespace, "DEBUG")
            # self.succeed_msg(f"{sn} pull rate: {pull_rate} MB/s ({file_size} bytes in {pull_time}s)", logger, namespace,
            #                  "DEBUG")
            # self.succeed_msg(f"{sn} file size:{file_mb}MB", logger, namespace, "DEBUG")
            # self.main_win.message_show(f"&nbsp;&nbsp;{sn} pull finished, {pull_rate}MB/s", TIP_INFO_COLOR)
            # self.main_win.message_show(f"&nbsp;&nbsp;{sn} pull time:{pull_time}s", TIP_INFO_COLOR)
            # self.main_win.message_show(f"&nbsp;&nbsp;{sn} file size:{file_mb}MB", TIP_INFO_COLOR)
            # file_size_limit = self.config_dict.get("SIZE_LIMIT", 120)
            # if file_mb < file_size_limit:
            #     self.main_win.message_show(f"&nbsp;&nbsp;failed: {sn}File size is less than {file_size_limit}MB",
            #                                ERROR_INFO_COLOR)
            #     logger.error(f"[{namespace}][error]file size")
            #     return False
            # self.main_win.message_show(f"&nbsp;&nbsp;passed:{sn} File size", TIP_INFO_COLOR)
            # self.succeed_msg(f"{sn} file size qualified", logger, namespace, "DEBUG")
            return True


camera_adbDut = CommandDut()

if __name__ == '__main__':
    # with dut() as xavier:
    #     print(xavier.load_xavier())
    #     print(xavier.read_sn())
    #     print(f"============")
    #     print(xavier.board_id())
    #     print(xavier.fw_version())
    # print(av_cam_server.start_server())
    # camera.save_para({"sn_read": "295ZB3BF320002"})
    # print(dut_server.start_server())
    # print(camera.get_sn('wocr'))
    # print(camera.get_sn('docl'))
    # print(camera.enter_display_path())
    # print(camera.load_venv())
    # print(camera.active_venv())
    # print(camera.load_image("calibu_17X13_1856mmX1472mm_4453718387"))
    # print(camera.set_color('red'))
    # print(camera.de_active_venv())
    # print(camera.back_path())
    # print(camera.snap_image_tool('wocr', "see_thru.wocr.tl1.001.png"))
    # print(camera.snap_image_tool('docl', "see_thru.docl.tl1.001.png"))
    # print(camera.get_exposure('docl'))
    # print(camera.set_exposure('docl', 2000))
    # print(camera.get_exposure('docl'))
    # print(camera.enter_display_path())
    # print(camera.load_venv())
    # print(camera.active_venv())
    # print(camera.set_color('green'))
    # print(camera.de_active_venv())
    # print(camera.back_path())
    # print(camera.snap_image_tool('wocr', "see_thru.wocr.tl1.001.png"))
    # print(camera.snap_image_tool('docl', "see_thru.docl.tl1.001.png"))
    # print(camera.snap_image_tool('wocl', "see_thru.wocl.tl1.001.png"))
    # print(camera.snap_image_tool('wocr', "see_thru.wocr.tl1.001.png"))
    # print(camera.dut_snap("slf", "see_thru.slf.tl1.001.png"))
    # print(camera.dut_snap("sls", "see_thru.sls.tl1.001.png"))
    # print(camera.dut_snap("srf", "see_thru.srf.tl1.001.png"))
    # print(camera.dut_snap("srs", "see_thru.srs.tl1.001.png"))
    # print(camera.dut_server_close())
    # print(camera.av_server_close())
    # print(camera.dut_server_close())

    # ret = camera.get_meta_data('wocr')
    # camera.get_exposure("wocr")
    # camera.get_exposure("docl")
    # ret = camera.runCommand(_cmd, _cmdPara, delimiter="[Jabil@fedora ~]$", timeout=10)
    # print(ret)
    # cmdrun = commandRunner()
    # cmdrun.loadyaml(r'C:\Users\Administrator.DESKTOP-OB9UGLS\Desktop\Cardinal\adb_shell.yml')
    # ret = cmdrun.login_host('192.168.1.3', 'Jabil', 'Test_lab1!')
    # print(ret)
    # cmdPara = {"camera_name": 'wocr', "command": "set-exposure", "args": "1000"}
    # cmd = "camera_parameter"
    # st = time.time()
    # ret = cmdrun.runCommand(cmd, cmdPara, delimiter="[Jabil@fedora ~]$", timeout=10)
    # print(f"{ret}------>{time.time() - st}")
    # print('hello world')
    # camera = Command_Camera()
    #
    # print(camera.get_exposure('wocr'))
    # print(camera.snap_image('wocr', "2023"))
    # print(camera.get_gain('wocr'))
    pass

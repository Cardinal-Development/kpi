import os
import shutil
import signal
import subprocess
import threading

from global_path import config_data, order_data, adb_shell_command, adbTool_path

# from kpi.motion_control.GP8.robot_control import GP8_Robot as Robot
from datetime import datetime
import yaml
import logging
import telnetlib
import time
import re
import paramiko

logger = logging.getLogger(__name__)


class CommandDut:
    def __init__(self):

        self.track_result = True
        self.record_res = None
        self.dut_sn = None
        self.adb_command = adb_shell_command
        self.AdbTool_path = adbTool_path
        self.time_dict = {}
        self.file_data_dict = {}
        self.job_name = ''
        # 5.8 chico
        self.chico_result = None

    def adb_cmd(self, adb_shell: str, timeout=500):
        """
        使用adb工具执行指定的adb命令并返回结果
        :param adb_shell: 执行的adb命令
        :return: adb命令执行结果
        """
        # 根据adb_shell和adb_tool_path构建实际执行的cmd命令
        adb_tool_path = self.AdbTool_path["adb_path"]
        # 执行命令
        cmd = "cd {} && {}".format(adb_tool_path, adb_shell)
        # timeout = 60
        # if "vrs-recorder" in adb_shell:
        #     timeout = 120
        # if "pull" in adb_shell:
        #     timeout = 120
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

    def VrsTool_cmd(self, adb_shell: str):
        """
        使用adb工具执行指定的adb命令并返回结果
        :param adb_shell: 执行的adb命令
        :return: adb命令执行结果
        """
        # 根据adb_shell和adb_tool_path构建实际执行的cmd命令
        # 执行命令
        VrsTool_path = self.AdbTool_path["VrsTool_path"]
        cmd = "cd {} && {}".format(VrsTool_path, adb_shell)
        timeout = 25
        # cmd = adb_shell
        logger.info(f"执行的命令是--》{cmd}")
        try:

            proc = subprocess.Popen(cmd,
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    bufsize=-1)
            res, err_res = proc.communicate(timeout=timeout)
            res = res.decode('utf8')
            err_res = err_res.decode('utf8')
            self.time_dict.clear()
            self.file_data_dict.clear()
            return res, err_res
        except:
            proc.kill()
            res = ""
            err_res = "timeout"
            self.time_dict.clear()
            self.file_data_dict.clear()
            return res, err_res

    def func_track_record(self, adb_shell, out_time):
        # 执行命令

        dut_thread = threading.Thread(target=self.track_record_thread,
                                      args=(adb_shell, out_time),
                                      name="track_thread")

        dut_thread.setDaemon(True)
        dut_thread.start()

    def track_cmd(self, adb_shell, time_out):
        """
        使用adb工具执行指定的adb命令并返回结果
        :param adb_shell: 执行的adb命令
        :param time_out: 超时
        :return: adb命令执行结果
        """
        # 根据adb_shell和adb_tool_path构建实际执行的cmd命令
        adb_tool_path = self.AdbTool_path["Tracker_path"]

        cmd = "cd {} && {}".format(adb_tool_path, adb_shell)
        print(f"tarck_cmd -->{cmd}")

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

    def track_record_thread(self, adb_shell, out_time):
        res, error = self.track_cmd(adb_shell, out_time)
        # logger.info(f"tracking-res->{res}")
        logger.info(f"tracking-error->{error}")
        if 'timeout' in error:
            self.track_result = False

    def adb_devices(self):

        adb_shell = 'adb devices'

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
        self.time_dict.update({self.dut_sn: datetime.now().strftime("%Y%m%dT%H%M%S")})
        logger.info(f"读取到的sn为:{self.dut_sn}")
        return True

    def simple_command(self, command):

        try:
            adb_shell = self.adb_command.get(command, "")[0]
        except Exception as e:
            logger.error(f"获取{command}对应的指令时失败，请检查{command}是否有对应的指令！！！--》error{e}")
            return False
        res, err_res = self.adb_cmd(adb_shell)
        if err_res:
            logger.error(f"执行{command}命令-》{adb_shell}时失败-->err:{err_res},res:{res}")
            return False
        else:
            logger.info(f"执行{command}命令-》{adb_shell}成功-->err:{err_res},res:{res}")
            return True

    def adb_record(self, timeout):

        adb_shell = self.adb_command.get('adb_vrs-recorder')[0]
        dut_thread = threading.Thread(target=self.adb_record_thread,
                                      args=(adb_shell, timeout),
                                      name="dut_thread")
        dut_thread.setDaemon(True)
        dut_thread.start()

    def adb_record_thread(self, adb_shell, timeout):
        print(f"vrs_cmd-->{adb_shell}")
        res, error = self.adb_cmd(adb_shell, timeout)
        if 'Recording done' not in res:
            logger.info(f"录像失败:error: {error}  res:{res}")
            print(f"录像失败:error: {error}  res:{res}")
            self.record_res = False
        else:
            logger.info(f" 录像成功:res:{res}\n, err:{error}")
            print(f"录像失败:error: {error}  res:{res}")
            self.record_res = True

    def call_chico_thread(self, command, timeout=1500):
        chico_thread = threading.Thread(target=self.chico_thread_func, args=(command, timeout), name='chico_thread')
        chico_thread.setDaemon(True)
        chico_thread.start()

    def chico_cmd(self, command, timeout):
        chico_path = adbTool_path["chico_CmdPath"]
        # 执行命令
        # cmd = "cd /d {} && {}".format(chico_path, command)
        os.chdir(chico_path)
        # logger.info(f"chico_cmd--->{cmd}")
        proc = None
        try:
            proc = subprocess.Popen(['powershell.exe', '-Command', command], stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,bufsize=-1)

            res, err_res = proc.communicate(timeout=timeout)
            res = res.decode('utf8')
            err_res = err_res.decode('utf8')
            recode = proc.returncode

            logger.info(f"chico_cmd--->{command}\n---->res:{res}\nerr_res:{err_res}\n returncode--------->{recode}")
            return res, err_res,recode
        except:
            try:
                if proc is not None:
                    os.kill(proc.pid, signal.Signals.SIGINT)
                    time.sleep(1)
            except Exception as e:
                print(f"os.kill(proc.pid, signal.Signals.SIGINT)--->{e}")
                logger.info(f"os.kill(proc.pid, signal.Signals.SIGINT)--->{e}")
            res = ""
            err_res = "timeout"
            recode = 2
            return res, err_res, recode


    def chico_thread_func(self, command, timeout):
        res, err_res,recode = self.chico_cmd(command, timeout)
        logger.info(f"chico_res:-->{res},chico_err_res:-->{err_res}\n"
                    f"recode-->{recode}")

        if recode == 0:
            self.chico_result = True
        else:
            self.chico_result = False
















    def wait_thread_end(self):
        while True:
            is_exist = False

            thread_name = [thread.getName() for thread in threading.enumerate()]
            for t_name in thread_name:
                if re.match(r"(dut_thread|robot_thread)", t_name):
                    # dut或plc仍在运行
                    is_exist = True
                    break
                is_exist = False
            if not is_exist:
                # 退出等待
                break
            time.sleep(0.5)
            print(thread_name)

        if self.record_res and self.robot_ret:
            return True
        else:
            return False

    def adb_pull_vrs(self, pull_file_path, timeout):
        shell1 = self.adb_command.get('adb_pull_vrs')[0]
        adb_shell = shell1.replace("[local_vrs_path]", pull_file_path)
        res, err_res = self.adb_cmd(adb_shell, timeout)

        # 拉取失败
        if err_res or '[100%]' not in res:
            print(logger)
            logger.debug(f"CMD: {adb_shell}")
            logger.info(f"err:{err_res}\n")
            #             f"res:{res}")
            logger.debug(f"failed:pull fail--err_res:{err_res}")
            return False

        else:
            logger.debug(f"CMD: {adb_shell}")
            logger.info(f"err:{err_res}\n"
                        f"res:{res}")
            return True

    def copy_file_function(self, base_path):
        try:
            # vrs_path = self.file_data_dict.get("vrs_path")
            tracking_path = self.file_data_dict.get("tracking_path")
            # for i in os.listdir(p):
            #     i = os.path.join(p, i)
            #     shutil.copy(i, out_path)
            # 11.21
            # shutil.copytree(p,out_path,dirs_exist_ok=True)

            # ===============
            # lf = os.path.split(vrs_path)[-1]
            # af = os.path.join(out_path,lf)
            # shutil.copytree(vrs_path,af)
            out_path = base_path
            path_time = self.time_dict.get(self.dut_sn)
            if self.job_name:
                outpath_ = path_time + "_" + self.dut_sn + "_" + self.job_name
                out_path = os.path.join(base_path, outpath_)

            logger.info(f"打印出所有的文件路径："
                        f"tracking_path:{tracking_path}\n"
                        f"最后转存的路径：{out_path}")

            if not os.path.exists(out_path):
                os.makedirs(out_path)
            # for i in os.listdir(vrs_path):
            #     path1 = os.path.join(vrs_path,i)
            #     shutil.copy2(path1, out_path)
            for i in os.listdir(tracking_path):
                path2 = os.path.join(tracking_path, i)
                # 12.8=============判断文件大小
                file_size = os.stat(path2).st_size  # file total bytes

                file_mb = file_size / 1024 / 1024
                if file_mb < self.AdbTool_path["track_file_size"]:
                    logger.info(f"拉取出来的Track文件大小不对，请检查："
                                f"文件大小为:{file_mb}\n")
                    return False
                shutil.copy2(path2, out_path)
            return True
        except Exception as ex:
            logger.error(f"复制文件时出错-->{ex}")
            # self.time_dict.clear()
            # self.file_data_dict.clear()
            return False


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
    # pass
    light_S_H_V = [0, 0, 1]
    cmd_light = f'python vortex_sacn.pex --set_hsv {light_S_H_V[0]} {light_S_H_V[1]} {light_S_H_V[2]}'
    ew = camera_adbDut.track_cmd(cmd_light, 5)
    print(ew[0])
    print(ew[1])

from global_path import config_data, order_data
from datetime import datetime
import yaml
import logging
import telnetlib
import time
import re
import paramiko

StationVRS_Min_Size = 1  # MB
BBCalVRS_Min_Size = 1  # MB
Illu_Min_Size = 1  # MB

logger = logging.getLogger(__name__)


class TelnetClient:
    def __init__(self, ):
        self.tn = telnetlib.Telnet()

    # 此函数实现telnet登录主机
    def login_host(self, host_ip, username, password):
        print(f"{host_ip}--{username}---{password}")
        try:
            # self.tn = telnetlib.Telnet(host_ip,port=23)
            self.tn.open(host_ip, port=23)
        except:
            logging.debug('%s网络连接失败' % host_ip)
            return False
        # 等待login出现后输入用户名，最多等待10秒
        self.tn.read_until(b'login: ', timeout=10)
        self.tn.write(username.encode('ascii') + b'\n')
        # 等待Password出现后输入用户名，最多等待10秒
        self.tn.read_until(b'Password: ', timeout=10)
        self.tn.write(password.encode('ascii') + b'\n')
        # 延时两秒再收取返回结果，给服务端足够响应时间
        time.sleep(2)
        # 获取登录结果
        # read_very_eager()获取到的是的是上次获取之后本次获取之前的所有输出
        command_result = self.tn.read_very_eager().decode('ascii')
        if 'Login incorrect' not in command_result:
            logging.debug('%slogin success' % host_ip)
            return True
        else:
            logging.error('%slogin fail, incorrect username and password.' % host_ip)
            return False

    # 此函数实现执行传过来的命令，并输出其执行结果
    def execute_some_command(self, command):
        # 执行命令
        self.tn.write(command.encode('ascii') + b'\n')
        time.sleep(2)
        # 获取命令结果
        command_result = self.tn.read_very_eager().decode('utf-8')
        logging.debug('command: %s' % command)
        logging.debug('command execute result:\n%s' % command_result)
        command_result = command_result.split('\r\n')
        return command_result

    def execute_until(self, command: str, delimiter: str = "->", timeout: int = 30):
        # 执行命令
        self.tn.write(command.encode('ascii') + b'\n')
        # time.sleep(2)
        # 获取命令结果
        start_time = time.time()
        command_result = self.tn.read_until(delimiter.encode('utf-8'), timeout).decode('utf-8')
        # elapse_time = time.time() - start_time
        # if elapse_time >= timeout:
        #     time.sleep(20)
        #     command_result = command_result + self.tn.read_until(delimiter.encode('utf-8'), timeout).decode('utf-8')
        #     logging.warning('-----------------------------------------------------------')
        #     logging.warning('warning time out')
        #     logging.warning('---------------------------------------------------------------')
        logging.debug('command:%s' % command)
        logging.debug('command execute result:\n%s' % command_result)
        command_result = command_result.split('\r\n')

        if delimiter in command_result[-1] or delimiter in command_result[-2]:
            logging.debug(f"send:{command} is success")
            print(f"send:{command} is success")
            return True, command_result
        logging.error(f"===========>telnet time out <=========")
        logging.error(f"send:{command} not find:{delimiter}")
        logging.error(f"result:{command_result}")
        return False, command_result

    def read_until(self, delimiter: str = "->", timeout: int = 30):
        start_time = time.time()
        command_result = self.tn.read_until(delimiter.encode('utf-8'), timeout).decode('utf-8')
        elapse_time = time.time() - start_time
        if elapse_time >= timeout:
            time.sleep(20)
            command_result = command_result + self.tn.read_until(delimiter.encode('utf-8'), timeout).decode('utf-8')
            logging.debug('-----------------------------------------------------------')
            logging.debug('warning time out')
            logging.debug('---------------------------------------------------------------')
        logging.debug('command execute result:\n%s' % command_result)
        command_result = command_result.split('\r\n')
        # aa = len(command_result)
        return command_result

    # 退出telnet
    def logout_host(self):
        self.tn.write(b"exit\n")


class commandRunner:
    def __init__(self):
        self.yaml_path = ''
        self.client = TelnetClient()
        self.command_yaml = order_data
        self.host_ip = ''
        self.username = ''
        self.password = ''
        self.command_result = ()

    # def __del__(self):
    #     self.client.logout_host()

    def login_host(self):
        self.host_ip = config_data["telnet_ip"]
        self.username = config_data["telnet_name"]
        self.password = config_data["telnet_password"]
        ret = self.client.login_host(self.host_ip, self.username, self.password)
        return ret
    
    def login_and_launch_xavier(self):
        ret = self.login_host()
        if ret:
            self.client.execute_until('/home/frl/xavier_shell.pex')
            response = self.client.execute_until('sn_read')
        return ret

    def loadyaml(self, path: str):
        self.yaml_path = path
        try:
            with open(path, "r", encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            f.close()
            raise FileNotFoundError
        self.command_yaml = yaml.full_load(content)
        f.close()
        if len(self.command_yaml) == 0:
            return False
        else:
            return True
        
    def sendCommand(self, command: str):
        response = self.client.execute_some_command(command)
        return response

    def runCommand(self, command: str, replacePara=None, delimiter: str = "->", timeout=None):
        replaceCmd = {}
        self.command_result = ()
        cmdStr = ''

        if command in self.command_yaml:
            cmdStr = self.command_yaml[command][0]
            replaceCmd = re.findall(r'\[.*?\]', cmdStr)
            if len(replaceCmd) != 0 and len(replaceCmd) != 0:
                for key in replacePara:
                    if ('[' + key + ']') in replaceCmd:
                        cmdStr = cmdStr.replace('[' + key + ']', replacePara[key])
                        # else:
            #             print("can't find replacePara")
            #             return False,''
            # elif len(replaceCmd) != 0 and len(replaceCmd) == 0:
            #     print('need replace para')
            #     return False,''
            logger.info(f"{cmdStr}")
        else:
            logger.error("can't find command")
            return False, ''

        logger.debug('CMD: ' + cmdStr + '\n')

        if timeout == None:
            ret = self.client.execute_some_command(cmdStr)
            self.command_result = (True, ret)
            return True, ret
        else:
            ret = self.client.execute_until(cmdStr, delimiter, timeout=timeout)
            self.command_result = (True, ret)
            return ret
        # print(cmdStr)
        # return True,ret

    def re_back_command(self, delimiter: str = "->", timeout=10):
        ret = self.client.read_until(delimiter, timeout)
        self.command_result = (True, ret)
        return True, ret

    def XOR_mask(self, key1, key2='46f6ba419969cd7ecdae9058faed178'):

        # Replace the strings above 'F' with hex numbers in the dictionary below

        for string, hex_val in {'g': '7', 'h': '8', 'i': '9', 'j': 'A', 'k': 'B', 'l': 'C', 'm': 'D', 'n': 'E',
                                'o': 'F', 'p': '0', 'q': '1', 'r': '2', 's': '3', 't': '4', 'u': '5', 'v': '6',
                                'w': '7',
                                'x': '8', 'y': '9', 'z': 'A'}.items():
            key1 = key1.lower().replace(string.lower(), hex_val)
            key2 = key2.lower().replace(string.lower(), hex_val)

        # XOR the key1 with the key2 and convert to hex

        result = hex(int(key1, 16) ^ int(key2, 16))
        result = result.lstrip('0x')
        return result

    def check_limits(self, name, value, lower_limit, upper_limit=9999 * 1024 ** 2):

        if isinstance(value, int):
            if value < lower_limit or value > upper_limit:
                logger.error("%s:%d out range of <%d,%d>" % (name, value, lower_limit, upper_limit))
                return False
            else:
                logger.info("%s:%d in range of <%d,%d" % (name, value, lower_limit, upper_limit))
                return True
        elif isinstance(value, float):
            if value < lower_limit or value > upper_limit:
                logger.error("%s:%.2f out range of <%.2f,%.2f>" % (name, value, lower_limit, upper_limit))
                return False
            else:
                logger.info("%s:%2f in range of <%.2f,%.2f" % (name, value, lower_limit, upper_limit))
                return True
        else:
            logger.error('value type is wrong')

    def check_result(self, result: str):
        k = 0
        for item in self.command_result[1]:
            if result in item:
                return True, k
            k = k + 1
        return False, -1

    def push_file(self, local_filepath, remote_filepath):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
            transport = paramiko.Transport(self.host_ip, 22)
            transport.connect(username=self.username, password=self.password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            sftp.put(local_filepath, remote_filepath)
        except Exception as e:
            logger.error(f"Error transferring file: {e}")
            ssh.close()
            return False
        ssh.close()
        return True
        # try:
        #     with paramiko.SSHClient() as ssh:
        #         ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #         ssh.connect(self.host_ip, 22, self.username, self.password, timeout = 5)
        #         #stdin,stdout,stderr = ssh.exec_command('ls -l')
        #     try:
        #         with ssh.open_sftp() as sftp:
        #             sftp.put(local_filepath, remote_filepath)
        #             return True
        #     except Exception as e:
        #         logger.error(f"Error transferring file: {e}")
        #         return False
        # except Exception as e:
        #     logger.error(f"Error connecting to remote host: {e}")
        #     return False

    # def find_order(self, command, replacePara=None):
    #     order = False, None
    #     self.command_result = ()
    #     cmdStr = {}
    #     if command in self.command_yaml:
    #         cmdStr = self.command_yaml[command][0]
    #         replaceCmd = re.findall(r'\[.*?\]', cmdStr)
    #         if len(replaceCmd) != 0 and len(replaceCmd) != 0:
    #             for key in replacePara:
    #                 if ('[' + key + ']') in replaceCmd:
    #                     cmdStr = cmdStr.replace('[' + key + ']', replacePara[key]) \
    #                         #         else:
    #         #             print("can't find replacePara")
    #         #             return False,''
    #         # elif len(replaceCmd) != 0 and len(replaceCmd) == 0:
    #         #     print('need replace para')
    #         #     return False,''
    #         order = True, cmdStr
    #     else:
    #         print(f"can't find command-->{cmdStr}")
    #     return order
    #
    # def run_command_EOF(self, command, replacePara=None):
    #     _ret = self.find_order(command, replacePara)
    #     if _ret[0]:
    #         pass


class Command_Camera(commandRunner):
    def __init__(self, ):
        super().__init__()
        self.dut_data = {}
        self.time = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        self.sn = {}
        self.command_end = "$"
        self.login_host()
        self.connect = False

    def time_record(self):
        self.time = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        self.dut_data = {}
        self.connect = True

    def is_sn(self):
        return "sn_read" in self.dut_data.keys()

    def snap_image_tool(self, camera_name, image_name, _type="see_thru"):
        logger.debug(f"sn list :{self.sn}")
        if self.is_sn():
            sn = self.dut_data["sn_read"]
            folder = f"Delphi_Disp_{sn}_{self.time}/{_type}"
            if camera_name in self.sn.keys():
                image_name = folder + "/" + camera_name + "/" + image_name
                _cmdPara = {'image_name': image_name, "camera_name": camera_name}
                _cmd = "snap_image"
                return self.runCommand(_cmd, _cmdPara, delimiter=self.command_end, timeout=10)
            else:
                return False, f"{camera_name} not in camera list, {self.sn.keys()}!!!!"
        else:
            return False, f"DUT must read sn before!!!"

    def set_exposure(self, camera_name, val):
        _cmdPara = {"camera_name": camera_name, "command": "set-exposure", "args": str(val)}
        _cmd = "camera_parameter"
        return self.runCommand(_cmd, _cmdPara, delimiter=self.command_end, timeout=10)

    def set_gain(self, camera_name, val):
        _cmdPara = {"camera_name": camera_name, "command": "set-gain", "args": str(val)}
        _cmd = "camera_parameter"
        return self.runCommand(_cmd, _cmdPara, delimiter=self.command_end, timeout=10)

    def set_id(self, camera_name, val):
        _cmdPara = {"camera_name": camera_name, "command": "set-id", "args": str(val)}
        _cmd = "camera_parameter"
        return self.runCommand(_cmd, _cmdPara, delimiter=self.command_end, timeout=10)

    def set_pixel_format(self, camera_name, val):
        _cmdPara = {"camera_name": camera_name, "command": "set-pixel-format", "args": str(val)}
        _cmd = "camera_parameter"
        return self.runCommand(_cmd, _cmdPara, delimiter=self.command_end, timeout=10)

    def set_trigger_mode(self, camera_name, val):
        _cmdPara = {"camera_name": camera_name, "command": "set-trigger-mode", "args": str(val)}
        _cmd = "camera_parameter"
        return self.runCommand(_cmd, _cmdPara, delimiter=self.command_end, timeout=10)

    def set_viewport(self, camera_name, val):
        _cmdPara = {"camera_name": camera_name, "command": "set-viewport", "args": str(val)}
        _cmd = "camera_parameter"
        return self.runCommand(_cmd, _cmdPara, delimiter=self.command_end, timeout=10)

    def get_exposure(self, camera_name):
        _cmdPara = {"camera_name": camera_name, "command": "get-exposure", "args": ""}
        _cmd = "camera_parameter"
        _ret = self.runCommand(_cmd, _cmdPara, delimiter=self.command_end, timeout=10)
        result = False, None
        if _ret[0]:
            result = True, _ret[1][2].split('Result:')[-1].strip()
        return result

    def get_gain(self, camera_name):
        _cmdPara = {"camera_name": camera_name, "command": "get-gain", "args": ""}
        _cmd = "camera_parameter"
        _ret = self.runCommand(_cmd, _cmdPara, delimiter=self.command_end, timeout=10)
        result = False, None
        if _ret[0]:
            result = True, _ret[1][2].split('Result:')[-1].strip()
        return result

    def get_id(self, camera_name):
        _cmdPara = {"camera_name": camera_name, "command": "get-id", "args": ""}
        _cmd = "camera_parameter"
        _ret = self.runCommand(_cmd, _cmdPara, delimiter=self.command_end, timeout=10)
        result = False, None
        if _ret[0]:
            result = True, _ret[1][2].split('Result:')[-1].strip()
        return result

    def get_meta_data(self, camera_name):
        _cmdPara = {"camera_name": camera_name, "command": "get-metadata", "args": ""}
        _cmd = "camera_parameter"
        _ret = self.runCommand(_cmd, _cmdPara, delimiter=self.command_end, timeout=10)
        result = False, None
        if _ret[0]:
            result = True, _ret[1][2].split('Result:')[-1].strip()
        return result

    def get_pixel_format(self, camera_name):
        _cmdPara = {"camera_name": camera_name, "command": "get-pixel-format", "args": ""}
        _cmd = "camera_parameter"
        _ret = self.runCommand(_cmd, _cmdPara, delimiter=self.command_end, timeout=10)
        result = False, None
        if _ret[0]:
            result = True, _ret[1][2].split('Result:')[-1].strip()
        return result

    def get_trigger_mode(self, camera_name):
        _cmdPara = {"camera_name": camera_name, "command": "get-trigger-mode", "args": ""}
        _cmd = "camera_parameter"
        _ret = self.runCommand(_cmd, _cmdPara, delimiter=self.command_end, timeout=10)
        result = False, None
        if _ret[0]:
            result = True, _ret[1][2].split('Result:')[-1].strip()
        return result

    def get_viewport(self, camera_name):
        _cmdPara = {"camera_name": camera_name, "command": "get-viewport", "args": ""}
        _cmd = "camera_parameter"
        _ret = self.runCommand(_cmd, _cmdPara, delimiter=self.command_end, timeout=10)
        result = False, None
        if _ret[0]:
            result = True, _ret[1][2].split('Result:')[-1].strip()
        return result

    def get_sn(self, camera_name):
        _ret = self.get_meta_data(camera_name)
        if _ret[0]:
            sn = _ret[1].split('serial_number=')[-1].split(',')[0]
            now = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            folder_name = f"Delphi_Disp_{eval(sn)}_{now}"
            print(folder_name)
            self.sn.update({camera_name: folder_name})
        return _ret

    def dut_snap(self, camera_name, image_name, _type="see_thru"):
        cameras = ["slf", "sls", "srf", "srs"]
        if self.is_sn():
            sn = self.dut_data["sn_read"]
            folder = f"Delphi_Disp_{sn}_{self.time}/{_type}"
            if camera_name in cameras:
                image_name = folder + "/" + camera_name + "/" + image_name
                _cmdPara = {'image_name': image_name, "camera_name": camera_name}
                _cmd = "dut_snap"
                return self.runCommand(_cmd, _cmdPara, delimiter=self.command_end, timeout=10)
            else:
                return False, f"{camera_name} is error ||||||| dut_list----->{cameras}!!!!"
        else:
            return False, f"DUT must read sn before!!!"

    def av_server_close(self):
        _cmd = "av_server_close"
        return self.runCommand(_cmd, delimiter=self.command_end, timeout=10)

    def dut_server_close(self):
        _cmd = "dut_server_close"
        return self.runCommand(_cmd, delimiter=self.command_end, timeout=10)

    def save_para(self, data: dict):
        self.dut_data.update(data)

    def load_image(self, image_name):
        _cmdPara = {"image_name": image_name}
        _cmd = "load_image"
        ret = self.runCommand(_cmd, _cmdPara, delimiter=self.command_end, timeout=1000)
        if ret[0]:
            if "load_image is fail" in ret[1][-2]:
                return False, f"load_image is fail--->{image_name}"
            else:
                return True, f"load_image is success--->{image_name}"
        else:
            return ret

    def set_color(self, color):
        _cmdPara = {"color": color}
        _cmd = "set_color"
        ret = self.runCommand(_cmd, _cmdPara, delimiter=self.command_end, timeout=100)
        if ret[0]:
            if "set_color is fail" in ret[1][-2]:
                return False, f"set_color is fail--->{color}"
            else:
                return True, f"set_color is success--->{color}"
        else:
            return ret

    def display_initial(self):
        ret = self.enter_display_path()

    def back_path(self):
        _cmd = "back_path"
        return self.runCommand(_cmd, delimiter=self.command_end, timeout=10)

    def enter_display_path(self):
        _cmd = "enter_path"
        return self.runCommand(_cmd, delimiter=self.command_end, timeout=10)

    def load_venv(self):
        _cmd = "load_venv"
        return self.runCommand(_cmd, delimiter=self.command_end, timeout=10)

    def active_venv(self):
        _cmd = "active_venv"
        return self.runCommand(_cmd, delimiter=self.command_end, timeout=10)

    def de_active_venv(self):
        _cmd = "de_active_venv"
        return self.runCommand(_cmd, delimiter=self.command_end, timeout=10)


class dut_camera(commandRunner):

    def __init__(self):
        super().__init__()
        self.login_host()

    def start_server(self):
        _cmd = "dut_server"
        return self.runCommand(_cmd, delimiter="Resource pools check complete - allowed", timeout=30)


class av_cam_server(commandRunner):
    def __init__(self):
        super().__init__()
        self.login_host()

    def start_server(self):
        _cmd = "av_cam_server"
        cmdParams = {}
        cmdParams['docl_dev_id'] = config_data["av_camera"]["docl_dev_id"]
        cmdParams['docr_dev_id'] = config_data["av_camera"]["docr_dev_id"]
        cmdParams['wocl_dev_id'] = config_data["av_camera"]["wocl_dev_id"]
        cmdParams['wocr_dev_id'] = config_data["av_camera"]["wocr_dev_id"]

        #TODO: Kill any old server before starting a new one
        ret, response = self.runCommand('av_server_close')

        return self.runCommand(_cmd, replacePara = cmdParams, timeout=45)


class display(commandRunner):
    def __init__(self):
        super().__init__()
        self.command_end = "$"
        self.login_host()
        # self.enter_display_path()
        # self.load_venv()
        # self.active_venv()

    def load_image(self, image_name):
        _cmdPara = {"image_name": image_name}
        _cmd = "load_image"
        ret = self.runCommand(_cmd, _cmdPara, delimiter=self.command_end, timeout=1000)
        if ret[0]:
            if "load_image is fail" in ret[1][-2]:
                return False, f"load_image is fail--->{image_name}"
            else:
                return True, f"load_image is success--->{image_name}"
        else:
            return ret

    def set_color(self, color):
        _cmdPara = {"color": color}
        _cmd = "set_color"
        ret = self.runCommand(_cmd, _cmdPara, delimiter=self.command_end, timeout=100)
        if ret[0]:
            if "set_color is fail" in ret[1][-2]:
                return False, f"set_color is fail--->{color}"
            else:
                return True, f"set_color is success--->{color}"
        else:
            return ret

    def display_initial(self):
        ret = self.enter_display_path()

    def back_path(self):
        _cmd = "back_path"
        return self.runCommand(_cmd, delimiter=self.command_end, timeout=10)

    def enter_display_path(self):
        _cmd = "enter_path"
        return self.runCommand(_cmd, delimiter=self.command_end, timeout=10)

    def load_venv(self):
        _cmd = "load_venv"
        return self.runCommand(_cmd, delimiter=self.command_end, timeout=10)

    def active_venv(self):
        _cmd = "active_venv"
        return self.runCommand(_cmd, delimiter=self.command_end, timeout=10)

    def de_active_venv(self):
        _cmd = "de_active_venv"
        return self.runCommand(_cmd, delimiter=self.command_end, timeout=10)


class dut(commandRunner):
    def __init__(self):
        super().__init__()
        self.login_host()
        self.command_end = "$"

    def __enter__(self):
        logger.info(f"start xavier=========")
        return self

    def load_xavier(self):
        cmd = "xavier_shell"
        ret = self.runCommand(cmd, timeout=20)
        if ret[0]:
            xavier_para = {}
            for __val in ret[1]:
                if "shell version" in __val:
                    __data = __val.split(':')[-1].strip()
                    xavier_para.update({"shell_version": __data})

                elif "build hash" in __val:
                    __data = __val.split(':')[-1].strip()
                    xavier_para.update({"build_hash": __data})

                elif "FW Version" in __val:
                    __data = __val.split(':')[-1].strip()
                    xavier_para.update({"FW_Version": __data})

                elif "Commit Hash" in __val:
                    __data = __val.split(':')[-1].strip()
                    xavier_para.update({"Commit_Hash": __data})

                elif "Temple Revision" in __val:
                    __data = __val.split(':')[-1].strip()
                    xavier_para.update({"Temple_Revision": __data})

                elif "Left Temple Board" in __val:
                    __data = __val.split(':')[-1].strip()
                    xavier_para.update({"Left_Board": __data})

                elif "Right Temple Board" in __val:
                    __data = __val.split(':')[-1].strip()
                    xavier_para.update({"Right_Board": __data})
            return True, xavier_para
        else:
            return ret

    def __exit__(self, exc_type, exc_val, exc_tb):
        cmd = "exit"
        return self.runCommand(cmd, delimiter=self.command_end, timeout=20)

    def read_sn(self):
        cmd = "sn_read"
        ret = self.runCommand(cmd, timeout=20)
        if ret[0]:
            return True, {cmd: ret[1][-2].strip()}
        return ret

    def board_id(self):
        cmd = "board_id"
        ret = self.runCommand(cmd, timeout=20)
        if ret[0]:
            return True, {cmd: ret[1][-2].strip()}
        return ret

    def fw_version(self):
        cmd = "fw_version"
        ret = self.runCommand(cmd, timeout=20)
        if ret[0]:
            return True, {cmd: ret[1][-2].strip()}
        return ret

    def soc_0_0(self):
        cmd = "soc_0_0"
        ret = self.runCommand(cmd, timeout=20)
        if ret[0]:
            return True, {cmd: ret[1][-2].strip()}
        return ret
    
    def enable_dpa(self):
        cmd = "enable_dpa 1"
        ret = self.runCommand(cmd, timeout=20)
        if ret[0]:
            return True, {cmd: ret[1][-2].strip()}
        return ret
    
    def vsync_start(self):
        cmd = "vsync start 90 1"
        ret = self.runCommand(cmd, timeout=20)
        if ret[0]:
            return True, {cmd: ret[1][-2].strip()}
        return ret
    
    def vsync_stop(self):
        cmd = "vsync stop"
        ret = self.runCommand(cmd, timeout=20)
        if ret[0]:
            return True, {cmd: ret[1][-2].strip()}
        return ret
    
    def load_image(self, side, image):
        #side = "left" or "right"
        #image = path to image file
        cmd = f"amx_write_image_dcb {side} {image}"
        ret = self.runCommand(cmd, timeout=20)
        if ret[0]:
            return True, {cmd: ret[1][-2].strip()}
        return ret
    
    def illuminate_panel(self, side, red=False, green=False, blue=False, build="PPOC"):
        #side = "left" or "right" or "both"
        #red = True/False
        #green = True/False
        #blue = True/False
        #build = "PPOC" or "POC1"

        side_arr = []
        if side.lower() == "both":
            side_arr.append("left")
            side_arr.append("right")
        else:
            side_arr.append(side.lower())

        red_tf = "1" if red else "0" #red is build agnostic
        red_register = "0x400"

        if build.lower() == "ppoc":
            green_tf = "0" if green else "3"
            blue_tf = "0" if blue else "3"
            green_register = "0x120"
            blue_register = "0x120"

        else:
            green_tf = "1" if green else "0"
            blue_tf = "1" if blue else "0"
            green_register = "0x400"
            blue_register = "0x400"

        #toggle red first
        for sides in side_arr:
            cmd = f"amx_write_tabasco_reg {sides} r {red_register} {red_tf}"
            ret = self.runCommand(cmd, timeout=20)

        #toggle green second
        for sides in side_arr:
            cmd = f"amx_write_tabasco_reg {sides} g {green_register} {green_tf}"
            ret = self.runCommand(cmd, timeout=20)

        #toggle blue third
        for sides in side_arr:
            cmd = f"amx_write_tabasco_reg {sides} b {blue_register} {blue_tf}"
            ret = self.runCommand(cmd, timeout=20)
            
        return ret


camera = Command_Camera()
# dut_server = dut_camera()
# av_cam_server = av_cam_server()
# display_tool = display()

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

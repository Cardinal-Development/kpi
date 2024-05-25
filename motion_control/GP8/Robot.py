import socket
import time
import threading
import string
import json
import logging
import time

logger = logging.getLogger(__name__)


class GP8Robot:
    def __init__(self, robot_ip, robot_port, timeout):
        self._robot_handle_client = None
        self._robot_ip = robot_ip
        self._robot_port = robot_port
        self._robot_timeout = timeout

        self.io_read_sheet = {'start button signal': 20010,
                              'pause button signal': 20011,
                              'reset button signal': 20013,
                              'emergency signal': 20040,
                              'optical grating signal': 20041,
                              'gate magnetism signal': 20042,
                              'carrier button signal': 20043,
                              'door positive limit signal': 20044,
                              'door negative limit signal': 20046,
                              'pneumatic signal': 20047,
                              'fixture move signal1': 20050,
                              'fixture original signal1': 20051,
                              'fixture move signal2': 20052,
                              'fixture original signal2': 20053,
                              'fixture move signal3': 20054,
                              'fixture original signal3': 20055,
                              'reset safety relay signal': 30017,
                              'start button light signal': 30040,
                              'stop button light signal': 30041,
                              'reset button light signal': 30042,
                              'fixture button light signal': 30043,
                              'green light signal': 30044,
                              'red light signal': 30045,
                              'yellow light signal': 30046,
                              'buzzer signal': 30047,
                              'fixture move signal': 30050,
                              'floodlight signal': 30051,
                              'fixture original signal': 30052,
                              'motor negative move signal': 30054,
                              'motor high speed signal': 30055,
                              'motor positive move signal': 30056,
                              'motor low speed signal': 30057,
                              'unload position': 50080,
                              'a job is running': 50070,
                              'home position': 50081,
                              'e_stop': 80025,
                              'gate': 80023}

        self.io_write_sheet = {'start button light': 27010,
                               'stop button light': 27011,
                               'reset button light': 27012,
                               'carrier button light': 27013,
                               'green light': 27014,
                               'red light': 27015,
                               'yellow light': 27016,
                               'buzzer': 27017,
                               'fixture move': 27020,
                               'dut ng': 37021,
                               'reset': 27040,
                               'testing': 27060,
                               }

    def connect(self, cyg_timeout=5):
        print("Attempting to connect to the robot in the connect method- Big Mike")
        self._robot_timeout = cyg_timeout
        self._robot_handle_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._robot_handle_client.connect((self._robot_ip, self._robot_port))
        print("Checking if the client actually connected MODASUCER!!! ")
        print(self._robot_handle_client)

    def close(self):
        self._robot_handle_client.close()
        self._robot_handle_client = None

    def send_msg(self, msg):
        print('Im in the modasucking sending message')
        try:
            self._robot_handle_client.send(msg.encode('utf-8'))
            try:
                print('Robot_log:send to robot {0}:{1}\n{2}' \
                      .format(self._robot_ip, self._robot_port, msg))
            except Exception as identifier:
                pass
        except Exception as identifier:
            print('Error: {}'.format(identifier))
            self._robot_handle_client.close()
            self._robot_handle_client = None

    def recv_msg(self):
        try:
            self._robot_handle_client.settimeout(self._robot_timeout)
            recv_data = self._robot_handle_client.recv(1024)
            msg = recv_data.decode('utf-8')
            try:
                print('Robot_log:Receive from robot {0}:{1}\n{2}' \
                      .format(self._robot_ip, self._robot_port, msg))
            except Exception as identifier:
                pass
            if msg == '':
                self._robot_handle_client.close()
                raise Exception('no data')
            return msg
        except Exception as identifier:
            print('Error: {}'.format(identifier))
            return ''
        finally:
            self._robot_handle_client.settimeout(None)

    def open_light(self, para):
        msg = {}
        if para['light_type'] == 'illuminator':
            para['channel1'] = para['intensity']
        elif para['light_type'] == 'et_target':
            para['channel2'] = para['intensity']
        elif para['light_type'] == 'slam_target':
            para['channel1'] = para['intensity']
            para['channel2'] = para['intensity']
            para['channel3'] = para['intensity']
        msg = para
        msg['cmd'] = 'open_light'
        self.send_msg(json.dumps(msg))
        recv_data = ''
        recv_data = self.recv_msg()
        if 'open_light' in recv_data and 'Pass' in recv_data:
            return True
        else:
            return False

    def read_temperature(self):
        msg = {}
        msg['cmd'] = 'cmd_temperature'
        self.send_msg(json.dumps(msg))
        recv_data = ''
        recv_data = self.recv_msg()  # recv_data sample:   read_io:PASS,10000,1
        if 'read_temperature' in recv_data and 'Pass' in recv_data:
            ret_value = recv_data.split('_temperature:Pass,')[1].split('\r\n')[0]
            return True, ret_value
        else:
            return False, -1

    def door_open(self):
        msg = {}
        msg['cmd'] = 'door_open'
        self.send_msg(json.dumps(msg))
        recv_data = ''
        recv_data = self.recv_msg()
        if 'door_open' in recv_data and 'Pass' in recv_data:
            return True
        else:
            return False

    def door_open_finish(self):
        msg = {}
        msg['cmd'] = 'door_open_finish'
        self.send_msg(json.dumps(msg))
        recv_data = ''
        recv_data = self.recv_msg()
        if 'door_open_finish' in recv_data and 'Pass' in recv_data:
            return True
        else:
            return False

    def open_door(self, para):
        ret = self.door_open_finish()
        if ret == True:
            return True
        ret = self.door_open()
        if ret != True:
            print('door_open failed')
            return False
        deadtime = para['timeout']
        starttime = time.time()
        while True:
            if time.time() - starttime > deadtime:
                ret = False
                break
            ret = self.door_open_finish()
            if ret == True:
                break
            time.sleep(1)
        return ret

    def door_close(self):
        msg = {}
        msg['cmd'] = 'door_close'
        self.send_msg(json.dumps(msg))
        recv_data = ''
        recv_data = self.recv_msg()
        if 'door_close:Pass' in recv_data and 'Pass' in recv_data:
            return True
        else:
            return False

    def door_close_finish(self):
        msg = {}
        msg['cmd'] = 'door_close_finish'
        self.send_msg(json.dumps(msg))
        recv_data = ''
        recv_data = self.recv_msg()
        if 'door_close_finish' in recv_data and 'Pass' in recv_data:
            return True
        else:
            return False

    def close_door(self, para):
        ret = self.door_close_finish()
        if ret == True:
            return True
        ret = self.door_close()
        if ret != True:
            print('door_close failed')
            return False
        deadtime = para['timeout']
        starttime = time.time()
        while True:
            if time.time() - starttime > deadtime:
                ret = False
                break
            ret = self.door_close_finish()
            if ret == True:
                break
            time.sleep(1)
        return ret

    def gripper_open(self):
        msg = {}
        msg['cmd'] = 'gripper_open'
        self.send_msg(json.dumps(msg))
        recv_data = ''
        recv_data = self.recv_msg()
        if 'gripper_open' in recv_data and 'Pass' in recv_data:
            return True
        else:
            return False

    def gripper_open_finish(self):
        msg = {}
        msg['cmd'] = 'gripper_open_finish'
        self.send_msg(json.dumps(msg))
        recv_data = ''
        recv_data = self.recv_msg()
        if 'gripper_open_finish' in recv_data and 'Pass' in recv_data:
            return True
        else:
            return False

    def open_gripper(self):
        if self.gripper_open_finish():
            return True
        ret = self.gripper_open()
        if ret != True:
            print('gripper_open failed')
            return False
        deadtime = 200
        starttime = time.time()
        while True:
            if time.time() - starttime > deadtime:
                ret = False
                break
            ret = self.gripper_open_finish()
            if ret == True:
                break
            time.sleep(1)
        return ret

    def gripper_close(self):
        msg = {}
        msg['cmd'] = 'gripper_close'
        self.send_msg(json.dumps(msg))
        recv_data = ''
        recv_data = self.recv_msg()
        if 'gripper_close' in recv_data and 'Pass' in recv_data:
            return True
        else:
            return False

    def gripper_close_finish(self):
        msg = {}
        msg['cmd'] = 'gripper_close_finish'
        self.send_msg(json.dumps(msg))
        recv_data = ''
        recv_data = self.recv_msg()
        if 'gripper_close_finish' in recv_data and 'Pass' in recv_data:
            return True
        else:
            return False

    def close_gripper(self):
        if self.gripper_close_finish():
            return True
        ret = self.gripper_close()
        if ret != True:
            print('close gripper failed')
            return False
        deadtime = 200
        starttime = time.time()
        while True:
            if time.time() - starttime > deadtime:
                ret = False
                break
            ret = self.gripper_close_finish()
            if ret == True:
                break
            time.sleep(1)
        return ret

    def isJobRunning(self):
        msg = {}
        msg['address'] = self.io_read_sheet['a job is running']
        # print('please check position para!')
        ret = self.io_read(msg)
        res = ret[1].split()[0]
        if int(res) == 1:
            return True
        else:
            return False

    def check_position(self, para='HOME'):
        msg = {}
        if para == 'HOME':
            msg['address'] = self.io_read_sheet['home position']
        elif para == 'LOAD':
            msg['address'] = self.io_read_sheet['unload position']
        else:
            print('please check position para!')
        ret = self.io_read(msg)
        res = ret[1].split()[0]
        if int(res) == 1:
            return True
        else:
            return False
        # self.send_msg('get_robot_position')
        # recv_data = ''
        # recv_data = self.recv_msg()
        # json_data = json.load(recv_data)
        # pos_data = {}
        # if json_data['get_robot_position'] == 'Pass':
        #     pos_data['xp'] = json_data['xp']
        #     pos_data['yp'] = json_data['yp']
        #     pos_data['zp'] = json_data['zp']
        #     pos_data['xr'] = json_data['xr']
        #     pos_data['yr'] = json_data['yr']
        #     pos_data['zr'] = json_data['zr']
        #     return True,pos_data
        # else:
        #     return False

    def reset_safety(self):
        # Check e-stop
        msg = {}
        msg['address'] = self.io_read_sheet['e_stop']
        ret = self.io_read(msg)
        if ret[1].split()[0] != '1':
            logger.error('E-Stop is broken\n====================\n\n E-Stop is broken\n\n====================\n')
            return False
        # Check gate
        msg['address'] = self.io_read_sheet['gate']
        ret = self.io_read(msg)
        if ret[1].split()[0] != '1':
            # Reset light curtain alert
            msg = {}
            msg['address'] = self.io_write_sheet['reset']
            msg['value'] = 1
            ret = self.io_write(msg)
            if ret != True:
                return False
            time.sleep(1)
            msg['value'] = 0
            ret = self.io_write(msg)
            if ret != True:
                return False
            time.sleep(1)
            msg['address'] = self.io_read_sheet['gate']
            ret = self.io_read(msg)
            # Check gate again
            if ret[1].split()[0] != '1':
                logger.error('Gate is broken\n====================\n\n Gate is broken\n\n====================\n')
                return False
        return True

    def testing_robot(self, state: bool):
        # Set the stack light to green
        msg = {}
        msg['address'] = self.io_write_sheet['testing']
        if state == True:
            msg['value'] = 1
            ret = self.io_write(msg)
            time.sleep(0.5)
            if ret != True:
                return False
            return True
        else:
            msg['value'] = 0
            ret = self.io_write(msg)
            time.sleep(0.5)
            if ret != True:
                return False
            return True

    def io_read(self, para):
        msg = {}
        msg = para
        msg['cmd'] = 'io_read'
        self.send_msg(json.dumps(msg))
        recv_data = ''
        recv_data = self.recv_msg()  # recv_data sample:   read_io:PASS,10000,1
        if 'io_read' in recv_data and 'Pass' in recv_data:
            ret_value = recv_data.split(',')
            return True, ret_value[1]
        else:
            return False, -1

    def io_write(self, para):
        msg = {}
        msg = para
        msg['cmd'] = 'io_write'
        self.send_msg(json.dumps(msg))
        recv_data = ''
        recv_data = self.recv_msg()
        if 'io_write' in recv_data and 'Pass' in recv_data:
            return True
        else:
            # print('write_io {}:{} failed'.format(para['address'],para['value']))
            return False

    def call_job(self, para):
        ret = self.robot_call_job(para['job_name'])
        if ret != True:
            print('robot_call_job failed!')
            return False
        ret = self.robot_servo_OnOff(True)
        if ret != True:
            print('robot servo on failed')
            return False
        ret = self.robot_start()
        if ret != True:
            print('robot start failed')
            return False
        deadtime = para['deadtime']
        starttime = time.time()
        while True:
            if time.time() - starttime > deadtime:
                ret = False
                break
            ret = self.robot_job_finish()
            if ret == True:
                break
        if ret != True:
            print("robot can't finish job in deadtime")
        ret = self.robot_servo_OnOff(False)
        if ret != True:
            print('robot servo off failed')
            return False
        return ret

    def robot_call_job(self, para):
        if self.close_gripper() != True:
            return False
        msg = {}
        msg['cmd'] = 'robot_call_job'
        msg['job_name'] = para
        self.send_msg(json.dumps(msg))
        recv_data = ''
        recv_data = self.recv_msg()
        if 'run_job' in recv_data and 'True' in recv_data:
            return True
        else:
            print(recv_data)
            return False

    def robot_servo_OnOff(self, status: bool):
        msg = {}
        if status == True:
            msg['cmd'] = 'servoON'
            self.send_msg(json.dumps(msg))
            recv_data = ''
            recv_data = self.recv_msg()
            if 'servoON' in recv_data and 'Pass' in recv_data:
                return True
            else:
                return False
        elif status == False:
            msg['cmd'] = 'servoOFF'
            self.send_msg(json.dumps(msg))
            recv_data = ''
            recv_data = self.recv_msg()
            if 'servoOFF' in recv_data and 'Pass' in recv_data:
                return True
            else:
                return False

    def robot_start(self):
        msg = {}
        msg['cmd'] = 'robotStart'
        self.send_msg(json.dumps(msg))
        recv_data = ''
        recv_data = self.recv_msg()
        if 'robotStart' in recv_data and 'Pass' in recv_data:
            return True
        else:
            return False

    def robot_hold(self):
        msg = {}
        msg['cmd'] = 'robotHold'
        self.send_msg(json.dumps(msg))
        recv_data = ''
        recv_data = self.recv_msg()
        if 'robotHold' in recv_data and 'Pass' in recv_data:
            return True
        else:
            return False

    def robot_job_finish(self):
        msg = {}
        msg['cmd'] = 'robot_job_finish'
        self.send_msg(json.dumps(msg))
        recv_data = ''
        recv_data = self.recv_msg()
        if 'robot_job_finish' in recv_data and 'Pass' in recv_data:
            return True
        else:
            print('waiting for job done signal from the robot')
            return False

    def robot_reset_position(self):
        if self.check_position('HOME'):
            self.close_gripper()
            ret = self.robot_servo_OnOff(True)
            starttime = time.time()
            self.robot_call_job('HOME_TO_LOAD')
            while True:
                if time.time() - starttime > 200:
                    self.robot_hold()
                    self.robot_servo_OnOff(False)
                ret = self.robot_job_finish()
                if ret == True:
                    break
                time.sleep(0.5)
            self.robot_servo_OnOff(False)


if __name__ == '__main__':
    robot = GP8Robot('127.0.0.10', 5002, 500)
    robot.connect()
    para = {}
    robot.close()

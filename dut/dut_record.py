# implement a method to dump the properties of the class into a json file.


import json
import os


class run_properties:
    def __init__(self):
        self.sn = "n/a"
        self.pre_soc_0_0 = "n/a"
        self.pre_soc_0_1 = "n/a"
        self.pre_soc_1_0 = "n/a"
        self.pre_soc_1_1 = "n/a"
        self.post_soc_0_0 = "n/a"
        self.post_soc_0_1 = "n/a"
        self.post_soc_1_0 = "n/a"
        self.post_soc_1_1 = "n/a"
        self.pre_temp_LT = "n/a"
        self.pre_temp_L = "n/a"
        self.pre_temp_CTR = "n/a"
        self.pre_temp_R = "n/a"
        self.pre_temp_RT = "n/a"
        self.post_temp_LT = "n/a"
        self.post_temp_L = "n/a"
        self.post_temp_CTR = "n/a"
        self.post_temp_R = "n/a"
        self.post_temp_RT = "n/a"
        self.light_setting = "n/a"
        self.pre_station_temp = "n/a"
        self.post_station_temp = "n/a"
        self.dut_firmware_version = "n/a"
        self.xavier_version = "n/a"
        self.delphi_board_id = "n/a"
        self.build = "n/a"
        self.station = "et-robot"

    def json_dump(self, file_path):
        data = {"sn": self.sn,
                "pre_soc_0_0": self.pre_soc_0_0,
                "pre_soc_0_1": self.pre_soc_0_1,
                "pre_soc_1_0": self.pre_soc_1_0,
                "pre_soc_1_1": self.pre_soc_1_1,
                "post_soc_0_0": self.post_soc_0_0,
                "post_soc_0_1": self.post_soc_0_1,
                "post_soc_1_0": self.post_soc_1_0,
                "post_soc_1_1": self.post_soc_1_1,
                "pre_temp_LT": self.pre_temp_LT,
                "pre_temp_L": self.pre_temp_L,
                "pre_temp_CTR": self.pre_temp_CTR,
                "pre_temp_R": self.pre_temp_R,
                "pre_temp_RT": self.pre_temp_RT,
                "post_temp_LT": self.post_temp_LT,
                "post_temp_L": self.post_temp_L,
                "post_temp_CTR": self.post_temp_CTR,
                "post_temp_R": self.post_temp_R,
                "post_temp_RT": self.post_temp_RT,
                "light_setting": self.light_setting,
                "pre_station_temp": self.pre_station_temp,
                "post_station_temp": self.post_station_temp,
                "dut_firmware_version": self.dut_firmware_version,
                "xavier_version": self.xavier_version,
                "delphi_board_id": self.delphi_board_id,
                "build": self.build,
                "station": self.station
                }
        # file_path = os.path.join(folder_path, "output.json")
        with open(file_path, "w") as f:
            json.dump(data, f)


"""
dut_properties = run_properties()
dut_properties.pre_soc_0_0 = 15

dut_properties.json_dump()
"""

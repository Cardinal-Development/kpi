import logging
from kpi.motion_control.Sever import Controller

logger = logging.getLogger(__name__)


class light:
    def __init__(self):
        self.sever = Controller

    def light_control(self, para):
        command = f"light_control({para})"
        logger.info(f"light_control({para})")
        return self.sever.send(command)


light_controller = light()

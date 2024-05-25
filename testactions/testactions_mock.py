# Copyright 2004-present Facebook. All Rights Reserved.

import logging
import time
from random import random


from arvr.projects.manufacturing.cardinal.factory.parametric_results import (
    ParametricResult,
)
from arvr.projects.manufacturing.cardinal.testactions.prompt import Prompt
from arvr.projects.manufacturing.cardinal.testactions.results import (
    ExceptionFail,
    Fail,
    Pass,
)
from arvr.projects.manufacturing.cardinal.testactions.testaction import (
    Context,
    TestAction,
)

logger = logging.getLogger(__name__)


class TAAddParametricResult(TestAction):
    def __init__(self, action_data):
        super().__init__(action_data)
        self.value = action_data.get("value")

    def run(self, context, nesting_level):
        dtr = context.device_test_record
        dtr.add_parametric_result(
            ParametricResult("parameter1", self.value, 0, 100, test_action=self.name)
        )
        return Pass(self, nesting_level)


class TAAddParametricResultInsideLoop(TestAction):
    def __init__(self, action_data):
        super().__init__(action_data)
        self.value = action_data.get("value")

    def run(self, context, nesting_level):
        dtr = context.device_test_record
        # self._result_name() is used here to generate unique
        # parameter names when this TestAction is used inside
        # a loop
        dtr.add_parametric_result(
            ParametricResult(
                self._result_name(context, "parameter1"),
                self.value,
                0,
                100,
                test_action=self.name,
            )
        )
        return Pass(self, nesting_level)


class TAPassAddRandomParameters(TestAction):
    def __init__(self, action_data):
        super().__init__(action_data)
        self.value = action_data.get("parameters", 6)
        #print(action_data)
    def run(self, context, nesting_level):
        logger.info("test run!!!!!")
        dtr = context.device_test_record
        for i in range(self.value):
            dtr.add_parametric_result(
                ParametricResult(
                    f"parameter{i}", random() * 100, 0, 100, test_action=self.name
                )
            )
        return Pass(self, nesting_level)


class TAPass(TestAction):
    def run(self, context, nesting_level):
        return Pass(self, nesting_level)


class TAFail(TestAction):
    def run(self, context, nesting_level):
        return Fail(self, nesting_level)


class TAExceptionFail(TestAction):
    def run(self, context, nesting_level):
        return ExceptionFail(self, nesting_level, Exception())


class TAAddSerialNumber(TestAction):
    def __init__(self, action_data):
        super().__init__(action_data)
        self.value = action_data.get("value")

    def run(self, context, nesting_level):
        context.device_test_record.serial_number = self.value
        return Pass(self, nesting_level)


class WaitInput(TestAction):
    def run(self, context, nesting_level):
        response = None
        while response is None:
            response = self.execute_prompt(
                context, Prompt("Press OK to start testing", 30)
            )
        return Pass(self, nesting_level)


class Delay(TestAction):
    def __init__(self, action_data):
        super().__init__(action_data)
        self.seconds = float(action_data.get("seconds", 1))

    def run(self, context, nesting_level):
        time.sleep(self.seconds)
        return Pass(self, nesting_level)

class Delay02(TestAction):
    def __init__(self, action_data):
        super().__init__(action_data)
        self.seconds = float(action_data.get("seconds", 1))

    def run(self, context, nesting_level):
        time.sleep(self.seconds)
        return Pass(self, nesting_level)


class LogSectionNumber(TestAction):
    def __init__(self, action_data):
        super().__init__(action_data)

    def run(self, context, nesting_level):
        logger.info(f"Section number: {context.section}")
        return Pass(self, nesting_level)

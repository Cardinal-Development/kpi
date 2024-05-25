import logging
from random import randint
from time import sleep
import time
from typing import Mapping

from arvr.projects.manufacturing.cardinal.factory.device_test_record import (
    DeviceTestRecord,
)
from arvr.projects.manufacturing.cardinal.factory.parametric_results import (
    ParametricResult,
)
from arvr.projects.manufacturing.cardinal.testactions.prompt import (
    Prompt,
    PromptResponse,
)
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


class TestAction1(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.param1 = action_data.get("param1", 1)
        self.param2 = action_data.get("param2", 2)
        self.param3 = action_data.get("param3", 3)

    def run(self, context: Context, nesting_level: int):
        dtr: DeviceTestRecord = context.device_test_record
        par1_values = context.parameter_definitions["TestAction1"]["par1"]
        par2_values = context.parameter_definitions["TestAction1"]["par2"]
        par3_values = context.parameter_definitions["TestAction1"]["par3"]
        dtr.add_parametric_result(
            ParametricResult(
                name="par1",
                test_action="TestAction1",
                value=self.param1,
                lower_limit=par1_values["lower_limit"],
                upper_limit=par1_values["upper_limit"],
                code=par1_values["code"],
                description=par1_values["description"],
                unit=par1_values["unit"],
            )
        )
        dtr.add_parametric_result(
            ParametricResult(
                name="par2",
                test_action="TestAction1",
                value=self.param2,
                lower_limit=par2_values["lower_limit"],
                upper_limit=par2_values["upper_limit"],
                code=par2_values["code"],
                description=par2_values["description"],
                unit=par2_values["unit"],
            )
        )
        dtr.add_parametric_result(
            ParametricResult(
                name="par3",
                test_action="TestAction1",
                value=self.param3,
                lower_limit=par3_values["lower_limit"],
                upper_limit=par3_values["upper_limit"],
                code=par3_values["code"],
                description=par3_values["description"],
                unit=par3_values["unit"],
            )
        )
        try:
            prompt = Prompt(message="Press button 2", timeout=15)
            response = self.execute_prompt(context, prompt)
            print('just here')
            if response.result == PromptResponse.PromptResult.OK:
                logger.info("I got OK!!!")
                return Pass(self, nesting_level)
            elif response.result == PromptResponse.PromptResult.CANCEL:
                logger.info("I got Cancel")
                return Fail(self, nesting_level)
            else:
                logger.info("I got Timeout")
                return Fail(self, nesting_level)
        except Exception as ex:
            logger.error(f" Error=[{ex}]")
            return ExceptionFail(self, nesting_level, ex)


class TestAction2(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)
        self.param4 = action_data.get("param4", 5)
        self.param5 = action_data.get("param5", 10)
        self.param6 = action_data.get("param6", 50)

    def run(self, context: Context, nesting_level: int):
        dtr: DeviceTestRecord = context.device_test_record
        par4_values = context.parameter_definitions["TestAction2"]["par4"]
        par5_values = context.parameter_definitions["TestAction2"]["par5"]
        par6_values = context.parameter_definitions["TestAction2"]["par6"]

        try:
            dtr.add_parametric_result(
                ParametricResult(
                    name="par4",
                    test_action="TestAction2",
                    value=100 / self.param4,
                    lower_limit=par4_values["lower_limit"],
                    upper_limit=par4_values["upper_limit"],
                    code=par4_values["code"],
                    description=par4_values["description"],
                    unit=par4_values["unit"],
                )
            )
            dtr.add_parametric_result(
                ParametricResult(
                    name="par5",
                    test_action="TestAction2",
                    value=100 / self.param5,
                    lower_limit=par5_values["lower_limit"],
                    upper_limit=par5_values["upper_limit"],
                    code=par5_values["code"],
                    description=par5_values["description"],
                    unit=par5_values["unit"],
                )
            )
            dtr.add_parametric_result(
                ParametricResult(
                    name="par6",
                    test_action="TestAction2",
                    value=100 / self.param6,
                    lower_limit=par6_values["lower_limit"],
                    upper_limit=par6_values["upper_limit"],
                    code=par6_values["code"],
                    description=par6_values["description"],
                    unit=par6_values["unit"],
                )
            )

        except ZeroDivisionError as zero:
            logger.error(f"Incorrect Division! Error=[{zero}]")
            return ExceptionFail(self, nesting_level, zero)
        return Pass(self, nesting_level)

class TestActionPassDelay(TestAction):
    def __init__(self, action_data):
        super().__init__(action_data)
        self.seconds = float(action_data.get("seconds", 2))
        self.action =action_data

    def run(self, context, nesting_level):
    
        time.sleep(self.seconds)
        logger.info(self.action)
        print (context)
        print(self.action)
        return Pass(self, nesting_level)


class TestActionPass(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)

    def run(self, context: Context, nesting_level: int):
        return Pass(self, nesting_level)


class TestActionFail(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)

    def run(self, context: Context, nesting_level: int):
        return Fail(self, nesting_level)


class TestActionExceptionFail(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)

    def run(self, context: Context, nesting_level: int):
        return ExceptionFail(self, nesting_level, RuntimeError())


class TestActionPromptInput(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)

    def run(self, context: Context, nesting_level: int):
        prompt = Prompt(message="Enter some text", timeout=15, enable_text_input=True)
        response = self.execute_prompt(context, prompt)
        if response.result != PromptResponse.PromptResult.OK:
            logger.info("I did not get OK got %s", response.result)
            return Fail(self, nesting_level)

        prompt = Prompt(message=f"You entered {response.text_input}", timeout=15)
        response = self.execute_prompt(context, prompt)
        if response.result != PromptResponse.PromptResult.OK:
            logger.info("I did not get OK got %s", response.result)
            return Fail(self, nesting_level)

        prompt = Prompt(message="Enter more text", timeout=15, enable_text_input=True)
        response = self.execute_prompt(context, prompt)
        if response.result != PromptResponse.PromptResult.OK:
            logger.info("I did not get OK got %s", response.result)
            return Fail(self, nesting_level)

        prompt = Prompt(message=f"You entered {response.text_input}", timeout=15)
        response = self.execute_prompt(context, prompt)
        if response.result != PromptResponse.PromptResult.OK:
            logger.info("I did not get OK got %s", response.result)
            return Fail(self, nesting_level)

        return Pass(self, nesting_level)


class TestActionRandom(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)

    def run(self, context: Context, nesting_level: int):
        context.serial_number = f"SN{randint(100000,999999)}"
        sleep(randint(1, 5))
        return Pass(self, nesting_level) if randint(0, 1) else Fail(self, nesting_level)


class TestActionLoopWithParamVal(TestAction):
    def __init__(self, action_data: Mapping):
        super().__init__(action_data)

    def run(self, context: Context, nesting_level: int):
        dtr: DeviceTestRecord = context.device_test_record
        param1 = randint(1, 100)

        dtr.add_parametric_result(
            ParametricResult(
                self._result_name(context, "par1"),
                param1,
                0,
                100,
                test_action=self.name,
            )
        )
        return Pass(self, nesting_level)

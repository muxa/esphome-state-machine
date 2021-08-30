import urllib.parse
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome import automation
from esphome.components import text_sensor
from esphome.components import state_machine

from esphome.const import (
    CONF_ID,
    CONF_NAME,
    CONF_TRIGGER_ID,
    CONF_FROM,
    CONF_TO,
)

AUTO_LOAD = ["text_sensor"]
DEPENDENCIES = ["state_machine"]

StateMachineTextSensor = cg.global_ns.class_(
    "StateMachineTextSensor", text_sensor.TextSensor, cg.Component
)

CONFIG_SCHEMA = text_sensor.TEXT_SENSOR_SCHEMA.extend(
    {
        cv.GenerateID(): cv.declare_id(StateMachineTextSensor),
    }
).extend(state_machine.consumer_schema())

async def to_code(config):   
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await text_sensor.register_text_sensor(var, config)
    await state_machine.register_state_machine_consumer(var, config)

    cg.add(var.dump_config())
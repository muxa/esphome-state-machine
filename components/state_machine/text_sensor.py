import logging
import urllib.parse
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome import automation
from esphome.components import text_sensor

from esphome.const import (
    CONF_ID,
    CONF_NAME,
    CONF_TRIGGER_ID,
    CONF_FROM,
    CONF_TO,
)

log = logging.getLogger("state_machine")

AUTO_LOAD = ["text_sensor"]

StateTransition = cg.global_ns.struct("StateTransition")

StateMachine = cg.global_ns.class_("StateMachine")

StateMachineTextSensor = cg.global_ns.class_(
    "StateMachineTextSensor", text_sensor.TextSensor, cg.Component
)

StateMachineOnEnterTrigger = cg.global_ns.class_(
    "StateMachineOnEnterTrigger", automation.Trigger.template()
)

StateMachineOnLeaveTrigger = cg.global_ns.class_(
    "StateMachineOnLeaveTrigger", automation.Trigger.template()
)

StateMachineInputActionTrigger = cg.global_ns.class_(
    "StateMachineInputActionTrigger", automation.Trigger.template()
)

StateMachineTransitionActionTrigger = cg.global_ns.class_(
    "StateMachineTransitionActionTrigger", automation.Trigger.template()
)

StateMachineTransitionAction = cg.global_ns.class_("StateMachineTransitionAction", automation.Action)

StateMachineTransitionCondition = cg.global_ns.class_("StateMachineTransitionCondition", automation.Condition)

CONF_INITIAL_STATE = 'initial_state'
CONF_STATES_KEY = 'states'
CONF_INPUTS_KEY = 'inputs'
CONF_TRANSITIONS_KEY = 'transitions'

CONF_STATE_ON_ENTER_KEY = 'on_enter'
CONF_STATE_ON_LEAVE_KEY = 'on_leave'
CONF_INPUT_TRANSITIONS_KEY = 'transitions'
CONF_INPUT_TRANSITIONS_ACTION_KEY = 'action'
CONF_INPUT_ACTION_KEY = 'action'

CONF_TRANSITION_FROM_KEY = 'from'
CONF_TRANSITION_INPUT_KEY = 'input'
CONF_TRANSITION_TO_KEY = 'to'


def validate_transition(value):
    if isinstance(value, dict):
        return cv.Schema(
            {
                cv.Required(CONF_FROM): cv.string_strict,
                cv.Required(CONF_TO): cv.string_strict,
                cv.Optional(CONF_INPUT_TRANSITIONS_ACTION_KEY): automation.validate_automation(
                    {
                        cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(StateMachineTransitionActionTrigger),
                    }
                )
            }
        )(value)
    value = cv.string(value)
    if "->" not in value:
        raise cv.Invalid("Transition mapping must contain '->'")
    a, b = value.split("->", 1)
    a, b = a.strip(), b.strip()
    return validate_transition({CONF_FROM: a, CONF_TO: b})

def output_graph(config):    
    graph_data = f"digraph \"{config[CONF_NAME]}\" {{\n"
    graph_data = graph_data + "  node [shape=ellipse];\n"
    for input in config[CONF_INPUTS_KEY]:
        if CONF_INPUT_TRANSITIONS_KEY in input:
            for transition in input[CONF_INPUT_TRANSITIONS_KEY]:
                graph_data = graph_data + f"  {transition[CONF_FROM]} -> {transition[CONF_TO]} [label={input[CONF_NAME]}];\n"

    graph_data = graph_data + "}"

    print(f"State Machine Diagram (for {config[CONF_NAME]}):")
    print(f"https://quickchart.io/graphviz?graph={urllib.parse.quote(graph_data)}")
    print()
    print(graph_data)
    print()

    return config

CONFIG_SCHEMA = cv.All(
    text_sensor.TEXT_SENSOR_SCHEMA.extend(
        {
            cv.GenerateID(): cv.declare_id(StateMachineTextSensor),
            cv.Required(CONF_STATES_KEY): cv.All(
                cv.ensure_list(cv.maybe_simple_value(
                    {
                        cv.Required(CONF_NAME): cv.string_strict,
                        cv.Optional(CONF_STATE_ON_ENTER_KEY): automation.validate_automation(
                            {
                                cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(StateMachineOnEnterTrigger),
                            }
                        ),
                        cv.Optional(CONF_STATE_ON_LEAVE_KEY): automation.validate_automation(
                            {
                                cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(StateMachineOnLeaveTrigger),
                            }
                        ),
                    },
                    key=CONF_NAME
                )), cv.Length(min=1)
            ),
            cv.Required(CONF_INPUTS_KEY): cv.All(
                cv.ensure_list(cv.maybe_simple_value(
                    {
                        cv.Required(CONF_NAME): cv.string_strict,
                        cv.Optional(CONF_INPUT_ACTION_KEY): automation.validate_automation(
                            {
                                cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(StateMachineInputActionTrigger),
                            }
                        ),
                        cv.Optional(CONF_INPUT_TRANSITIONS_KEY): cv.All(
                            cv.ensure_list(validate_transition), cv.Length(min=1)
                        ),
                    },
                    key=CONF_NAME
                )), cv.Length(min=1)
            ),
            cv.Optional(CONF_INITIAL_STATE): cv.string_strict,
        }
    ),
    output_graph
)

async def to_code(config):

    states = []
    inputs = []
    transitions = []

    for state in config[CONF_STATES_KEY]:
        states.append(state[CONF_NAME])
    
    for input in config[CONF_INPUTS_KEY]:
        inputs.append(input[CONF_NAME])

        if CONF_INPUT_TRANSITIONS_KEY in input:
            for transition in input[CONF_INPUT_TRANSITIONS_KEY]:
                transitions.append(
                    cg.StructInitializer(
                        StateTransition,
                        ("from_state", transition[CONF_FROM]),
                        ("input", input[CONF_NAME]),
                        ("to_state", transition[CONF_TO]),
                    )
                )

    var = cg.new_Pvariable(config[CONF_ID], states, inputs, transitions, config[CONF_INITIAL_STATE])

    for state in config[CONF_STATES_KEY]:

        if CONF_STATE_ON_ENTER_KEY in state:
            for action in state.get(CONF_STATE_ON_ENTER_KEY, []):
                trigger = cg.new_Pvariable(
                    action[CONF_TRIGGER_ID], var, state[CONF_NAME]
                )
                await automation.build_automation(trigger, [], action)

        if CONF_STATE_ON_LEAVE_KEY in state:
            for action in state.get(CONF_STATE_ON_LEAVE_KEY, []):
                trigger = cg.new_Pvariable(
                    action[CONF_TRIGGER_ID], var, state[CONF_NAME]
                )
                await automation.build_automation(trigger, [], action)

    for input in config[CONF_INPUTS_KEY]:
        if CONF_INPUT_TRANSITIONS_KEY in input:
            for transition in input[CONF_INPUT_TRANSITIONS_KEY]:
                if CONF_INPUT_TRANSITIONS_ACTION_KEY in transition:
                    for action in transition.get(CONF_INPUT_TRANSITIONS_ACTION_KEY, []):
                        trigger = cg.new_Pvariable(
                            action[CONF_TRIGGER_ID], 
                            var, 
                            cg.StructInitializer(
                                StateTransition,
                                ("from_state", transition[CONF_FROM]),
                                ("input", input[CONF_NAME]),
                                ("to_state", transition[CONF_TO]),
                            )
                        )
                        await automation.build_automation(trigger, [], action)

        if CONF_INPUT_ACTION_KEY in input:
            for action in input.get(CONF_INPUT_ACTION_KEY, []):
                trigger = cg.new_Pvariable(
                    action[CONF_TRIGGER_ID], var, input[CONF_NAME]
                )
                await automation.build_automation(trigger, [], action)
   

    await cg.register_component(var, config)
    await text_sensor.register_text_sensor(var, config)

    cg.add(var.dump_config())

@automation.register_action(
    "state_machine.transition",
    StateMachineTransitionAction,
    cv.maybe_simple_value(
        {
            cv.GenerateID(): cv.use_id(StateMachineTextSensor),
            cv.Required(CONF_TRANSITION_INPUT_KEY): cv.string_strict,
        },
        key=CONF_TRANSITION_INPUT_KEY
    ),
)
def state_machine_transition_to_code(config, action_id, template_arg, args):
    var = cg.new_Pvariable(action_id, template_arg, config[CONF_TRANSITION_INPUT_KEY])
    yield cg.register_parented(var, config[CONF_ID])
    yield var

@automation.register_condition(
    "state_machine.transition",
    StateMachineTransitionCondition,
    cv.Schema(
        {
            cv.GenerateID(): cv.use_id(StateMachineTextSensor),
            cv.Optional(CONF_TRANSITION_FROM_KEY): cv.templatable(cv.string_strict),
            cv.Optional(CONF_TRANSITION_INPUT_KEY): cv.templatable(cv.string_strict),
            cv.Optional(CONF_TRANSITION_TO_KEY): cv.templatable(cv.string_strict),
        }
    ),
)
async def state_machine_transition_condition_to_code(config, condition_id, template_arg, args):
    paren = await cg.get_variable(config[CONF_ID])    
    var = cg.new_Pvariable(condition_id, template_arg, paren)
    if CONF_TRANSITION_FROM_KEY in config:
        cg.add(var.set_from_state(await cg.templatable(config[CONF_TRANSITION_FROM_KEY], args, cg.std_string)))
    if CONF_TRANSITION_INPUT_KEY in config:
        cg.add(var.set_input(await cg.templatable(config[CONF_TRANSITION_INPUT_KEY], args, cg.std_string)))
    if CONF_TRANSITION_TO_KEY in config:
        cg.add(var.set_to_state(await cg.templatable(config[CONF_TRANSITION_TO_KEY], args, cg.std_string)))
    return var

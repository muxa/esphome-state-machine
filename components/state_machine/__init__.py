import logging
import os
import urllib.parse
import textwrap
import esphome.codegen as cg
import esphome.config_validation as cv
from esphome import automation
from esphome.automation import validate_condition, build_condition

from esphome.const import (
    CONF_ID,
    CONF_NAME,
    CONF_TRIGGER_ID,
    CONF_FROM,
    CONF_TO,
    CONF_STATE,
    CONF_VALUE,
    CONF_CONDITION
)

_LOGGER = logging.getLogger(__name__)

state_machine_ns = cg.esphome_ns.namespace("state_machine")

StateTransition = state_machine_ns.struct("StateTransition")

StateMachine = state_machine_ns.class_("StateMachine")

StateMachineComponent = state_machine_ns.class_(
    "StateMachineComponent", cg.Component
)

StateMachineOnSetTrigger = state_machine_ns.class_(
    "StateMachineOnSetTrigger", automation.Trigger.template()
)

StateMachineOnEnterTrigger = state_machine_ns.class_(
    "StateMachineOnEnterTrigger", automation.Trigger.template()
)

StateMachineOnLeaveTrigger = state_machine_ns.class_(
    "StateMachineOnLeaveTrigger", automation.Trigger.template()
)

StateMachineOnInputTrigger = state_machine_ns.class_(
    "StateMachineOnInputTrigger", automation.Trigger.template()
)

StateMachineBeforeTransitionTrigger = state_machine_ns.class_(
    "StateMachineBeforeTransitionTrigger", automation.Trigger.template()
)

StateMachineOnTransitionTrigger = state_machine_ns.class_(
    "StateMachineOnTransitionTrigger", automation.Trigger.template()
)

StateMachineAfterTransitionTrigger = state_machine_ns.class_(
    "StateMachineAfterTransitionTrigger", automation.Trigger.template()
)

StateMachineSetAction = state_machine_ns.class_("StateMachineSetAction", automation.Action)

StateMachineTransitionAction = state_machine_ns.class_("StateMachineTransitionAction", automation.Action)

StateMachineStateCondition = state_machine_ns.class_("StateMachineStateCondition", automation.Condition)
StateMachineTransitionCondition = state_machine_ns.class_("StateMachineTransitionCondition", automation.Condition)

CONF_DIAGRAM = 'diagram'
CONF_INITIAL_STATE = 'initial_state'
CONF_STATES_KEY = 'states'
CONF_INPUTS_KEY = 'inputs'
CONF_TRANSITIONS_KEY = 'transitions'

CONF_STATE_ON_SET_KEY = 'on_set'
CONF_STATE_ON_ENTER_KEY = 'on_enter'
CONF_STATE_ON_LEAVE_KEY = 'on_leave'
CONF_INPUT_TRANSITIONS_KEY = 'transitions'
CONF_BEFORE_TRANSITION_KEY = 'before_transition'
CONF_ON_TRANSITION_KEY = 'on_transition'
CONF_AFTER_TRANSITION_KEY = 'after_transition'
CONF_ON_INPUT_KEY = 'on_input'

# deprecated
CONF_INPUT_TRANSITIONS_ACTION_KEY = 'action'
CONF_INPUT_ACTION_KEY = 'action'

CONF_TRANSITION_FROM_KEY = 'from'
CONF_TRANSITION_INPUT_KEY = 'input'
CONF_TRANSITION_TO_KEY = 'to'

CONF_STATE_MACHINE_ID = 'state_machine_id'

memorizer = dict()
async def build_condition_(config):
    if config['type_id'] not in memorizer:
        memorizer[config['type_id']] = await build_condition(config, cg.TemplateArguments(), [])
    return memorizer[config['type_id']]

def validate_transition(value):
    if isinstance(value, dict):
        return cv.Schema(
            {
                cv.Required(CONF_FROM): cv.string_strict,
                cv.Required(CONF_TO): cv.string_strict,
                cv.Optional(CONF_CONDITION): validate_condition,
                cv.Optional(CONF_BEFORE_TRANSITION_KEY): automation.validate_automation(
                    {
                        cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(StateMachineBeforeTransitionTrigger),
                    }
                ),
                cv.Optional(CONF_ON_TRANSITION_KEY): automation.validate_automation(
                    {
                        cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(StateMachineOnTransitionTrigger),
                    }
                ),
                cv.Optional(CONF_AFTER_TRANSITION_KEY): automation.validate_automation(
                    {
                        cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(StateMachineAfterTransitionTrigger),
                    }
                ),
                cv.Optional(CONF_INPUT_TRANSITIONS_ACTION_KEY): cv.invalid("`action` is deprecated. Please use one of `before_transition`, `on_transition` or `after_transition` instead"),
            }
        )(value)
    value = cv.string(value)
    if "->" not in value:
        raise cv.Invalid("Transition mapping must contain '->'")
    a, b = value.split("->", 1)
    a, b = a.strip(), b.strip()
    return validate_transition({CONF_FROM: a, CONF_TO: b})


def format_lambda(s):
    s=s.strip()
    if s.startswith('return'):
        s = s[len('return'):]

    if s.endswith(";"):
        s = s[:-1]

    return s.strip()


def format_condition_argument(ca):
    if 'id' in ca:
        ca = ca['id']
        if hasattr(ca, 'id'):
            return ca.id
    return ''

def format_condition(c):
    try:
        v = ''
        long = ''

        if 'lambda' in c:
            v = format_lambda(c['lambda'].value)
        else:
            c2 = c.copy()
            for i in c:
                if i in ['type_id', 'type', 'ID', 'manual']:
                    c2.pop(i)
            
            conditionname = None

            for i in c2:
                if "." in i:
                    conditionname = i
                    break

            if not conditionname:
                for i in c2:
                    conditionname = i
                    break
            
            arg = format_condition_argument(c2[conditionname])
            long = conditionname + " " + arg

            conditionname = conditionname.split('.')




            # If we have something like binary_sensor.is_on, the part before the dot
            # needs to go to keep things short.
            # But if it is something short already we can keep it.
            if len(conditionname)==1:
                conditionname = conditionname[0]
            else:
                suffix = conditionname[-1]
                p = '.'.join(conditionname[:-1])

                if len(p) < 7:
                    conditionname = p + "." + suffix
                else:
                    conditionname = suffix

            v = conditionname + " " + arg
     
        v = v.strip()
            
        return (v, long or v)
    except Exception as e:
        _LOGGER.exception(f"Mermaid chart error:{e}")
        return('','')


def output_graph(config):
    if not CONF_DIAGRAM in config:
        return config

    if config[CONF_DIAGRAM] == "mermaid":
        output_mermaid_graph(config)
    else:
        output_dot_graph(config)

    return config


MAX_CONDITION_LENGTH_IN_DIAGRAM = 22
def output_mermaid_graph(config):
    graph_data = f"stateDiagram-v2{os.linesep}"
    graph_data = graph_data + f"  direction LR{os.linesep}"
    initial_state = config[CONF_INITIAL_STATE] if CONF_INITIAL_STATE in config else config[CONF_STATES_KEY][0][CONF_NAME]
    graph_data = graph_data + f"  [*] --> {initial_state}{os.linesep}"
    footnotes = []

    for input in config[CONF_INPUTS_KEY]:
        if CONF_INPUT_TRANSITIONS_KEY in input:
            for transition in input[CONF_INPUT_TRANSITIONS_KEY]:
                if CONF_CONDITION in transition and transition[CONF_CONDITION]:
                    cond, longcond = format_condition(transition[CONF_CONDITION])

                    if len(cond) > MAX_CONDITION_LENGTH_IN_DIAGRAM:
                        footnotes.append(f'[{len(footnotes)+1}] {longcond}')

                    cond2 = textwrap.shorten(cond, MAX_CONDITION_LENGTH_IN_DIAGRAM, placeholder=f"[{len(footnotes)}]")
                    cond2 = f"(? {cond2})"
                    graph_data = graph_data + f"  {transition[CONF_FROM]} --> {transition[CONF_TO]}: {input[CONF_NAME]}{cond2}{os.linesep}"
                else:
                    graph_data = graph_data + f"  {transition[CONF_FROM]} --> {transition[CONF_TO]}: {input[CONF_NAME]}{os.linesep}"


    if footnotes:
        graph_data = graph_data + f"note: legend{os.linesep}"

    for i in footnotes:
        graph_data = graph_data + f"note: {i}{os.linesep}"


    graph_url = "" # f"https://quickchart.io/graphviz?format=svg&graph={urllib.parse.quote(graph_data)}"

    if CONF_NAME in config:
        _LOGGER.info(f"State Machine Diagram (for {config[CONF_NAME]}):{os.linesep}{graph_url}{os.linesep}")
    else:
        _LOGGER.info(f"State Machine Diagram:{os.linesep}{graph_url}{os.linesep}")

    _LOGGER.info(f"Mermaid chart:{os.linesep}{graph_data}")

def output_dot_graph(config):
    graph_data = f"digraph \"{config[CONF_NAME] if CONF_NAME in config else 'State Machine'}\" {{\n"
    graph_data = graph_data + "  node [shape=ellipse];\n"
    for input in config[CONF_INPUTS_KEY]:
        if CONF_INPUT_TRANSITIONS_KEY in input:
            for transition in input[CONF_INPUT_TRANSITIONS_KEY]:
                graph_data = graph_data + f"  {transition[CONF_FROM]} -> {transition[CONF_TO]} [label={input[CONF_NAME]}];\n"

    graph_data = graph_data + "}"
    graph_url = f"https://quickchart.io/graphviz?format=svg&graph={urllib.parse.quote(graph_data)}"

    if CONF_NAME in config:
        _LOGGER.info(f"State Machine Diagram (for {config[CONF_NAME]}):{os.linesep}{graph_url}{os.linesep}")
    else:
        _LOGGER.info(f"State Machine Diagram:{os.linesep}{graph_url}{os.linesep}")

    _LOGGER.info(f"DOT language graph:{os.linesep}{graph_data}")

def validate_transitions(config):  
    states = set(map(lambda x: x[CONF_NAME], config[CONF_STATES_KEY]))

    for input in config[CONF_INPUTS_KEY]:

        if CONF_INPUT_TRANSITIONS_KEY in input:
            for transition in input[CONF_INPUT_TRANSITIONS_KEY]:
                if transition[CONF_FROM] not in states:
                    raise cv.Invalid(f"Undefined `from` state \"{transition[CONF_FROM]}\" used in transition for input \"{input[CONF_NAME]}\"")
                if transition[CONF_TO] not in states:
                    raise cv.Invalid(f"Undefined `to` state \"{transition[CONF_TO]}\" used in transition for input \"{input[CONF_NAME]}\"")

    return config

def unique_names(items): 
    names = list(map(lambda x: x[CONF_NAME], items));
    if len(names) != len(set(names)):
        raise cv.Invalid("Items must have unique names")
    return items

MULTI_CONF = True

CONFIG_SCHEMA = cv.All(
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(StateMachineComponent),
            cv.Optional(CONF_NAME): cv.string,
            cv.Required(CONF_STATES_KEY): cv.All(
                cv.ensure_list(cv.maybe_simple_value(
                    {
                        cv.Required(CONF_NAME): cv.string_strict,
                        cv.Optional(CONF_STATE_ON_SET_KEY): automation.validate_automation(
                            {
                                cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(StateMachineOnSetTrigger),
                            }
                        ),
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
                )), cv.Length(min=1), unique_names
            ),
            cv.Required(CONF_INPUTS_KEY): cv.All(
                cv.ensure_list(cv.maybe_simple_value(
                    {
                        cv.Required(CONF_NAME): cv.string_strict,
                        cv.Optional(CONF_ON_INPUT_KEY): automation.validate_automation(
                            {
                                cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(StateMachineOnInputTrigger),
                            }
                        ),
                        cv.Optional(CONF_INPUT_ACTION_KEY): cv.invalid("`action` is deprecated. Please use `on_input` instead"),
                        cv.Optional(CONF_INPUT_TRANSITIONS_KEY): cv.All(
                            cv.ensure_list(validate_transition), cv.Length(min=1)
                        ),
                    },
                    key=CONF_NAME
                )), cv.Length(min=1), unique_names
            ),
            cv.Optional(CONF_INITIAL_STATE): cv.string_strict,
            cv.Optional(CONF_DIAGRAM): cv.one_of("mermaid", "dot")
        }
    ).extend(cv.COMPONENT_SCHEMA),
    validate_transitions,
    output_graph
)

STATE_MACHINE_CONSUMER_SCHEMA = cv.Schema(
    {
        cv.Required(CONF_ID): cv.use_id(StateMachineComponent)
    }
)
def state_machine_consumer_schema():
    return cv.Schema({
        cv.GenerateID(CONF_STATE_MACHINE_ID): cv.use_id(StateMachineComponent)
    })

async def register_state_machine_consumer(var, config):
    parent = await cg.get_variable(config[CONF_STATE_MACHINE_ID])
    cg.add(var.set_state_machine(parent))

async def to_code(config):

    cg.add_global(state_machine_ns.using)

    initial_state = config[CONF_INITIAL_STATE] if CONF_INITIAL_STATE in config else config[CONF_STATES_KEY][0][CONF_NAME]

    var = cg.new_Pvariable(config[CONF_ID], initial_state)

    if CONF_NAME in config:
        cg.add(var.set_name(config[CONF_NAME]))   

    for state in config[CONF_STATES_KEY]:
        cg.add(var.add_state(state[CONF_NAME]))
    
    for input in config[CONF_INPUTS_KEY]:
        cg.add(var.add_input(input[CONF_NAME]))

        if CONF_INPUT_TRANSITIONS_KEY in input:
            for transition in input[CONF_INPUT_TRANSITIONS_KEY]:
                cg.add(
                    var.add_transition(
                        cg.StructInitializer(
                            StateTransition,
                            ("from_state", transition[CONF_FROM]),
                            ("input", input[CONF_NAME]),
                            ("to_state", transition[CONF_TO]),
                            ("condition", await build_condition_(transition[CONF_CONDITION]) if CONF_CONDITION in transition else cg.nullptr)
                        )
                    )
                ) 

    # setup on_set automations
    for state in config[CONF_STATES_KEY]:

        if CONF_STATE_ON_SET_KEY in state:
            for action in state.get(CONF_STATE_ON_SET_KEY, []):
                trigger = cg.new_Pvariable(
                    action[CONF_TRIGGER_ID], var, state[CONF_NAME]
                )
                await automation.build_automation(trigger, [], action)

    # setup transition/input automations (they should run first)
    for input in config[CONF_INPUTS_KEY]:

        # 1. on_input automations
        if CONF_ON_INPUT_KEY in input:
            for action in input.get(CONF_ON_INPUT_KEY, []):
                trigger = cg.new_Pvariable(
                    action[CONF_TRIGGER_ID], var, input[CONF_NAME]
                )
                await automation.build_automation(trigger, [], action)

        # 2. before_transition automations
        if CONF_INPUT_TRANSITIONS_KEY in input:
            for transition in input[CONF_INPUT_TRANSITIONS_KEY]:
                if CONF_BEFORE_TRANSITION_KEY in transition:
                    for action in transition.get(CONF_BEFORE_TRANSITION_KEY, []):
                        trigger = cg.new_Pvariable(
                            action[CONF_TRIGGER_ID], 
                            var, 
                            cg.StructInitializer(
                                StateTransition,
                                ("from_state", transition[CONF_FROM]),
                                ("input", input[CONF_NAME]),
                                ("to_state", transition[CONF_TO]),
                                ("condition", await build_condition_(transition[CONF_CONDITION]) if CONF_CONDITION in transition else cg.nullptr)
                            )
                        )
                        await automation.build_automation(trigger, [], action)

    # 3. on_leave automations
    for state in config[CONF_STATES_KEY]:

        if CONF_STATE_ON_LEAVE_KEY in state:
            for action in state.get(CONF_STATE_ON_LEAVE_KEY, []):
                trigger = cg.new_Pvariable(
                    action[CONF_TRIGGER_ID], var, state[CONF_NAME]
                )
                await automation.build_automation(trigger, [], action)

    # 4. on_transition automations
    for input in config[CONF_INPUTS_KEY]:
        if CONF_INPUT_TRANSITIONS_KEY in input:
            for transition in input[CONF_INPUT_TRANSITIONS_KEY]:
                if CONF_ON_TRANSITION_KEY in transition:
                    for action in transition.get(CONF_ON_TRANSITION_KEY, []):
                        trigger = cg.new_Pvariable(
                            action[CONF_TRIGGER_ID], 
                            var, 
                            cg.StructInitializer(
                                StateTransition,
                                ("from_state", transition[CONF_FROM]),
                                ("input", input[CONF_NAME]),
                                ("to_state", transition[CONF_TO]),
                                ("condition", await build_condition_(transition[CONF_CONDITION]) if CONF_CONDITION in transition else cg.nullptr)
                            )
                        )
                        await automation.build_automation(trigger, [], action)

    # 5. on_enter automations
    for state in config[CONF_STATES_KEY]:

        if CONF_STATE_ON_ENTER_KEY in state:
            for action in state.get(CONF_STATE_ON_ENTER_KEY, []):
                trigger = cg.new_Pvariable(
                    action[CONF_TRIGGER_ID], var, state[CONF_NAME]
                )
                await automation.build_automation(trigger, [], action)  

    # 6. after_transition automations
    for input in config[CONF_INPUTS_KEY]:
        if CONF_INPUT_TRANSITIONS_KEY in input:
            for transition in input[CONF_INPUT_TRANSITIONS_KEY]:
                if CONF_AFTER_TRANSITION_KEY in transition:
                    for action in transition.get(CONF_AFTER_TRANSITION_KEY, []):
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

    await cg.register_component(var, config)

@automation.register_action(
    "state_machine.set",
    StateMachineSetAction,
    cv.maybe_simple_value(
        {
            cv.GenerateID(): cv.use_id(StateMachineComponent),
            cv.Required(CONF_STATE): cv.string_strict,
        },
        key=CONF_STATE
    ),
)
def state_machine_set_to_code(config, action_id, template_arg, args):
    var = cg.new_Pvariable(action_id, template_arg, config[CONF_STATE])
    yield cg.register_parented(var, config[CONF_ID])
    yield var

@automation.register_action(
    "state_machine.transition",
    StateMachineTransitionAction,
    cv.maybe_simple_value(
        {
            cv.GenerateID(): cv.use_id(StateMachineComponent),
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
    "state_machine.state",
    StateMachineStateCondition,
    cv.maybe_simple_value(
        {
            cv.GenerateID(): cv.use_id(StateMachineComponent),
            cv.Required(CONF_VALUE): cv.templatable(cv.string_strict)
        },
        key=CONF_VALUE
    ),
)
async def state_machine_state_condition_to_code(config, condition_id, template_arg, args):
    paren = await cg.get_variable(config[CONF_ID])    
    var = cg.new_Pvariable(condition_id, template_arg, paren)
    cg.add(var.set_value(await cg.templatable(config[CONF_VALUE], args, cg.std_string)))
    return var


@automation.register_condition(
    "state_machine.transition",
    StateMachineTransitionCondition,
    cv.Schema(
        {
            cv.GenerateID(): cv.use_id(StateMachineComponent),
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

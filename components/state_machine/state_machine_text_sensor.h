#pragma once

#include "esphome/core/component.h"
#include "esphome/components/text_sensor/text_sensor.h"
#include "state_machine.h"
namespace esphome
{

  class StateMachineTextSensor : public text_sensor::TextSensor, public Component
  {
  public:
    StateMachineTextSensor(
        std::vector<std::string> states,
        std::vector<std::string> inputs,
        std::vector<StateTransition> transitions,
        std::string initial_state)
    {
      state_machine_ = new StateMachine(states, inputs, transitions, initial_state);
      last_transition = {};
    }

    float get_setup_priority() const override { return setup_priority::HARDWARE; }

    void setup() override;

    void dump_config() override;

    optional<StateTransition> last_transition;

    bool transition(std::string input);

    void add_on_transition_callback(std::function<void(StateTransition)> &&callback) { this->transition_callback_.add(std::move(callback)); }

  protected:
    CallbackManager<void(StateTransition)> transition_callback_{};

    StateMachine *state_machine_;
  };

} // namespace esphome
#include "esphome/core/log.h"
#include "state_machine.h"

namespace esphome
{

  static const char *const TAG = "state_machine";
  static const char *const ESPSM_VERSION = "0.0.0";

  StateMachine::StateMachine(
      std::vector<std::string> states,
      std::vector<std::string> inputs,
      std::vector<StateTransition> transitions,
      std::string initial_state)
  {
    this->states_ = states;
    this->inputs_ = inputs;
    this->transitions_ = transitions;
    this->current_state_ = initial_state;
    this->last_transition_ = {};

    ESP_LOGI(TAG, "State Machine version %s", ESPSM_VERSION);

    ESP_LOGD(TAG, "State machine ready. Current state: %s", this->current_state_.c_str());

    ESP_LOGD(TAG, "States: %d", this->states_.size());
    for (auto &state : this->states_)
    {
      ESP_LOGD(TAG, "  %s", state.c_str());
    }

    ESP_LOGD(TAG, "Inputs: %d", this->inputs_.size());
    for (auto &input : this->inputs_)
    {
      ESP_LOGD(TAG, "  %s", input.c_str());
    }

    ESP_LOGD(TAG, "Transitions: %d", this->transitions_.size());
    for (StateTransition &transition : this->transitions_)
    {
      ESP_LOGD(TAG, "  %s - %s -> %s", transition.from_state.c_str(), transition.input.c_str(), transition.to_state.c_str());
    }
  }

  optional<StateTransition> StateMachine::get_transition(std::string input)
  {
    if (std::find(this->inputs_.begin(), this->inputs_.end(), input) == this->inputs_.end())
    {
      ESP_LOGE(TAG, "Invalid input value: %s", input.c_str());
      return {};
    }

    for (StateTransition &transition : this->transitions_)
    {
      if (transition.from_state == this->current_state_ && transition.input == input)
        return transition;
    }

    return {};
  }

  optional<StateTransition> StateMachine::transition(std::string input)
  {
    optional<StateTransition> transition = get_transition(input);
    if (transition)
    {
      ESP_LOGD(TAG, "%s: transitioned from %s to %s", input.c_str(), transition.value().from_state.c_str(), transition.value().to_state.c_str());
      this->last_transition_ = transition;
      this->current_state_ = transition.value().to_state;      
    }
    else
    {
      ESP_LOGW(TAG, "%s: invalid input %s", input.c_str(), this->current_state_.c_str());
    }
    return transition;
  }

} // namespace esphome
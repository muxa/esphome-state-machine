#include "state_machine.h"
#include "esphome/core/log.h"

namespace esphome
{
  namespace state_machine
  {

    static const char *const TAG = "state_machine";

    StateMachineComponent::StateMachineComponent(
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
    }

    const std::string &StateMachineComponent::get_name() const { return this->name_; }
    void StateMachineComponent::set_name(const std::string &name)
    {
      this->name_ = name;
    }

    void StateMachineComponent::setup()
    {
      auto initial_state = this->current_state_;
      this->current_state_ = {};
      this->set(initial_state);
    }

    void StateMachineComponent::dump_config()
    {
      ESP_LOGCONFIG(TAG, "State Machine '%s'", this->name_.c_str());

      ESP_LOGCONFIG(TAG, "Current State: %s", this->current_state_.c_str());

      ESP_LOGCONFIG(TAG, "States: %d", this->states_.size());
      for (auto &state : this->states_)
      {
        ESP_LOGCONFIG(TAG, "  %s", state.c_str());
      }

      ESP_LOGCONFIG(TAG, "Inputs: %d", this->inputs_.size());
      for (auto &input : this->inputs_)
      {
        ESP_LOGCONFIG(TAG, "  %s", input.c_str());
      }

      ESP_LOGCONFIG(TAG, "Transitions: %d", this->transitions_.size());
      for (StateTransition &transition : this->transitions_)
      {
        ESP_LOGCONFIG(TAG, "  %s: %s -> %s", transition.input.c_str(), transition.from_state.c_str(), transition.to_state.c_str());
      }
    }

    optional<StateTransition> StateMachineComponent::get_transition(std::string input)
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

    void StateMachineComponent::set(std::string state)
    {
      if (std::find(this->states_.begin(), this->states_.end(), state) == this->states_.end())
      {
        ESP_LOGE(TAG, "Invalid state: %s", state.c_str());
        return;
      }

      if (state != this->current_state_)
      {
        ESP_LOGD(TAG, "State set to %s", state.c_str());
        this->current_state_ = state;
        this->set_callback_.call(state);
      }
    }

    optional<StateTransition> StateMachineComponent::transition(std::string input)
    {
      optional<StateTransition> transition = this->get_transition(input);
      if (transition)
      {
        this->before_transition_callback_.call(transition.value());
        ESP_LOGD(TAG, "%s: transitioned from %s to %s", input.c_str(), transition.value().from_state.c_str(), transition.value().to_state.c_str());
        this->last_transition_ = transition;
        this->current_state_ = transition.value().to_state;
        this->after_transition_callback_.call(transition.value());
      }
      else
      {
        ESP_LOGW(TAG, "%s: no transition from %s", input.c_str(), this->current_state_.c_str());
      }
      return transition;
    }

  } // namespace state_machine
} // namespace esphome
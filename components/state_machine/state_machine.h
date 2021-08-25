#pragma once

#include <string>
#include "esphome/core/optional.h"

namespace esphome
{

  struct StateTransition
  {
    std::string from_state;
    std::string input;
    std::string to_state;
  };

  class StateMachine
  {
  public:
    StateMachine(
        std::vector<std::string> states,
        std::vector<std::string> inputs,
        std::vector<StateTransition> transitions,
        std::string initial_state);

    std::string current_state() { return this->current_state_; }
    optional<StateTransition> last_transition() { return this->last_transition_; }

    optional<StateTransition> transition(std::string input);

  private:
    std::vector<std::string> states_;
    std::vector<std::string> inputs_;
    std::vector<StateTransition> transitions_;
    std::string current_state_;
    optional<StateTransition> last_transition_;

    optional<StateTransition> get_transition(std::string input);
  };

} // namespace esphome
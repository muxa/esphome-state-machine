#pragma once

#include "esphome/core/component.h"
#include "esphome/core/helpers.h"
namespace esphome
{
  namespace state_machine
  {

    struct StateTransition
    {
      std::string from_state;
      std::string input;
      std::string to_state;
    };

    class StateMachineComponent : public Component
    {
    public:
      StateMachineComponent(
          std::vector<std::string> states,
          std::vector<std::string> inputs,
          std::vector<StateTransition> transitions,
          std::string initial_state);

      const std::string &get_name() const;
      void set_name(const std::string &name);

      void setup() override;
      void dump_config() override;

      std::string current_state() { return this->current_state_; }
      optional<StateTransition> last_transition() { return this->last_transition_; }

      void set(std::string state);
      optional<StateTransition> transition(std::string input);

      void add_on_set_callback(std::function<void(std::string)> &&callback) { this->set_callback_.add(std::move(callback)); }
      void add_on_transition_callback(std::function<void(StateTransition)> &&callback) { this->transition_callback_.add(std::move(callback)); }

    protected:
      std::string name_;

      std::vector<std::string> states_;
      std::vector<std::string> inputs_;
      std::vector<StateTransition> transitions_;
      std::string current_state_;
      optional<StateTransition> last_transition_;

      optional<StateTransition> get_transition(std::string input);

      CallbackManager<void(std::string)> set_callback_{};
      CallbackManager<void(StateTransition)> transition_callback_{};
    };

  } // namespace state_machine
} // namespace esphome
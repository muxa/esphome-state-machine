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
      StateMachineComponent(const std::string &initial_state);

      const std::string &get_name() const;
      void set_name(const std::string &name);

      void setup() override;
      void dump_config() override;

      std::string current_state() { return this->current_state_; }
      optional<StateTransition> last_transition() { return this->last_transition_; }

      void set(const std::string &state);
      optional<StateTransition> transition(const std::string &input);

      void add_on_set_callback(std::function<void(const std::string&)> &&callback) { this->set_callback_.add(std::move(callback)); }
      void add_before_transition_callback(std::function<void(const StateTransition&)> &&callback) { this->before_transition_callback_.add(std::move(callback)); }
      void add_after_transition_callback(std::function<void(const StateTransition&)> &&callback) { this->after_transition_callback_.add(std::move(callback)); }

      void add_state(const std::string &state) {
        this->states_.push_back(state);
      }

      void add_input(const std::string &input) {
        this->inputs_.push_back(input);
      }

      void add_transition(const StateTransition &transition) {
        this->transitions_.push_back(transition);
      }

    protected:
      std::string name_;

      std::vector<std::string> states_;
      std::vector<std::string> inputs_;
      std::vector<StateTransition> transitions_;
      std::string current_state_;
      optional<StateTransition> last_transition_;

      optional<StateTransition> get_transition(const std::string &input);

      CallbackManager<void(std::string)> set_callback_{};
      CallbackManager<void(StateTransition)> before_transition_callback_{};
      CallbackManager<void(StateTransition)> after_transition_callback_{};
    };

  } // namespace state_machine
} // namespace esphome
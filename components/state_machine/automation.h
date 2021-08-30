#pragma once

#include "esphome/core/component.h"
#include "esphome/core/automation.h"
#include "state_machine.h"

namespace esphome
{
  namespace state_machine
  {

    class StateMachineOnEnterTrigger : public Trigger<>
    {
    public:
      StateMachineOnEnterTrigger(StateMachineComponent *state_machine, std::string state)
      {
        state_machine->add_on_transition_callback(
            [this, state](StateTransition transition)
            {
              this->stop_action(); // stop any previous running actions
              if (transition.to_state == state)
              {
                this->trigger();
              }
            });
      }
    };

    class StateMachineOnLeaveTrigger : public Trigger<>
    {
    public:
      StateMachineOnLeaveTrigger(StateMachineComponent *state_machine, std::string state)
      {
        state_machine->add_on_transition_callback(
            [this, state](StateTransition transition)
            {
              this->stop_action(); // stop any previous running actions
              if (transition.from_state == state)
              {
                this->trigger();
              }
            });
      }
    };

    class StateMachineTransitionActionTrigger : public Trigger<>
    {
    public:
      StateMachineTransitionActionTrigger(StateMachineComponent *state_machine, StateTransition for_transition)
      {
        state_machine->add_on_transition_callback(
            [this, for_transition](StateTransition transition)
            {
              this->stop_action(); // stop any previous running actions
              if (transition.from_state == for_transition.from_state && transition.input == for_transition.input && transition.to_state == for_transition.to_state)
              {
                this->trigger();
              }
            });
      }
    };

    class StateMachineInputActionTrigger : public Trigger<>
    {
    public:
      StateMachineInputActionTrigger(StateMachineComponent *state_machine, std::string input)
      {
        state_machine->add_on_transition_callback(
            [this, input](StateTransition transition)
            {
              this->stop_action(); // stop any previous running actions
              if (transition.input == input)
              {
                this->trigger();
              }
            });
      }
    };

    template <typename... Ts>
    class StateMachineTransitionAction : public Action<Ts...>, public Parented<StateMachineComponent>
    {
    public:
      StateMachineTransitionAction(std::string input)
      {
        this->input_ = input;
      }

      void play(Ts... x) override { this->parent_->transition(this->input_); }

    protected:
      std::string input_;
    };

    template <typename... Ts>
    class StateMachineTransitionCondition : public Condition<Ts...>
    {
    public:
      explicit StateMachineTransitionCondition(StateMachineComponent *parent) : parent_(parent) {}

      TEMPLATABLE_VALUE(std::string, from_state)
      TEMPLATABLE_VALUE(std::string, input)
      TEMPLATABLE_VALUE(std::string, to_state)

      bool check(Ts... x) override
      {
        if (!this->parent_->last_transition().has_value())
          return false;
        StateTransition transition = this->parent_->last_transition().value();
        if (this->from_state_.has_value() && this->from_state_.value(x...) != transition.from_state)
          return false;
        if (this->input_.has_value() && this->input_.value(x...) != transition.input)
          return false;
        if (this->to_state_.has_value() && this->to_state_.value(x...) != transition.to_state)
          return false;
        return true;
      }

    protected:
      StateMachineComponent *parent_;
    };

  } // namespace state_machine
} // namespace esphome
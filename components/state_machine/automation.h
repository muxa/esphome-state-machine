#pragma once

#include "esphome/core/component.h"
#include "esphome/core/automation.h"
#include "state_machine.h"

namespace esphome
{
  namespace state_machine
  {

    class StateMachineOnSetTrigger : public Trigger<>
    {
    public:
      StateMachineOnSetTrigger(StateMachineComponent *state_machine, const std::string &state)
      {
        state_machine->add_on_set_callback(
            [this, state](const std::string &new_state)
            {
              if (new_state == state)
              {
                this->stop_action(); // stop any previous running actions
                this->trigger();
              }
            });
      }
    };

    class StateMachineOnInputTrigger : public Trigger<>
    {
    public:
      StateMachineOnInputTrigger(StateMachineComponent *state_machine, const std::string &input)
      {
        state_machine->add_before_transition_callback(
            [this, input](const StateTransition &transition)
            {
              this->stop_action(); // stop any previous running actions
              if (transition.input == input)
              {
                this->trigger();
              }
            });
      }
    };
    class StateMachineBeforeTransitionTrigger : public Trigger<>
    {
    public:
      StateMachineBeforeTransitionTrigger(StateMachineComponent *state_machine, const StateTransition &for_transition)
      {
        state_machine->add_before_transition_callback(
            [this, for_transition](const StateTransition &transition)
            {
              this->stop_action(); // stop any previous running actions
              if (transition.from_state == for_transition.from_state && transition.input == for_transition.input && transition.to_state == for_transition.to_state)
              {
                this->trigger();
              }
            });
      }
    };

    class StateMachineOnLeaveTrigger : public Trigger<>
    {
    public:
      StateMachineOnLeaveTrigger(StateMachineComponent *state_machine, const std::string &state)
      {
        state_machine->add_before_transition_callback(
            [this, state](const StateTransition &transition)
            {
              this->stop_action(); // stop any previous running actions
              if (transition.from_state == state)
              {
                this->trigger();
              }
            });
      }
    };
    class StateMachineOnTransitionTrigger : public Trigger<>
    {
    public:
      StateMachineOnTransitionTrigger(StateMachineComponent *state_machine, const StateTransition &for_transition)
      {
        state_machine->add_before_transition_callback(
            [this, for_transition](const StateTransition &transition)
            {
              this->stop_action(); // stop any previous running actions
              if (transition.from_state == for_transition.from_state && transition.input == for_transition.input && transition.to_state == for_transition.to_state)
              {
                this->trigger();
              }
            });
      }
    };

    class StateMachineOnEnterTrigger : public Trigger<>
    {
    public:
      StateMachineOnEnterTrigger(StateMachineComponent *state_machine, const std::string &state)
      {
        state_machine->add_after_transition_callback(
            [this, state](const StateTransition &transition)
            {
              this->stop_action(); // stop any previous running actions
              if (transition.to_state == state)
              {
                this->trigger();
              }
            });
      }
    };
    class StateMachineAfterTransitionTrigger : public Trigger<>
    {
    public:
      StateMachineAfterTransitionTrigger(StateMachineComponent *state_machine, const StateTransition &for_transition)
      {
        state_machine->add_after_transition_callback(
            [this, for_transition](const StateTransition &transition)
            {
              this->stop_action(); // stop any previous running actions
              if (transition.from_state == for_transition.from_state && transition.input == for_transition.input && transition.to_state == for_transition.to_state)
              {
                this->trigger();
              }
            });
      }
    };

    template <typename... Ts>
    class StateMachineSetAction : public Action<Ts...>, public Parented<StateMachineComponent>
    {
    public:
      StateMachineSetAction(std::string state)
      {
        this->state_ = state;
      }

      void play(const Ts &... x) override { this->parent_->set(this->state_); }

    protected:
      std::string state_;
    };

    template <typename... Ts>
    class StateMachineTransitionAction : public Action<Ts...>, public Parented<StateMachineComponent>
    {
    public:
      StateMachineTransitionAction(std::string input)
      {
        this->input_ = input;
      }

      void play(const Ts &... x) override { this->parent_->transition(this->input_); }

    protected:
      std::string input_;
    };

    template <typename... Ts>
    class StateMachineStateCondition : public Condition<Ts...>
    {
    public:
      explicit StateMachineStateCondition(StateMachineComponent *parent) : parent_(parent) {}

      TEMPLATABLE_VALUE(std::string, value)

      bool check(const Ts &... x) override
      {
        return this->value_.value(x...) == this->parent_->current_state();
      }

    protected:
      StateMachineComponent *parent_;
    };

    template <typename... Ts>
    class StateMachineTransitionCondition : public Condition<Ts...>
    {
    public:
      explicit StateMachineTransitionCondition(StateMachineComponent *parent) : parent_(parent) {}

      TEMPLATABLE_VALUE(std::string, from_state)
      TEMPLATABLE_VALUE(std::string, input)
      TEMPLATABLE_VALUE(std::string, to_state)

      bool check(const Ts &... x) override
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
#pragma once

#include "esphome/core/component.h"
#include "esphome/core/automation.h"
#include "state_machine_text_sensor.h"

namespace esphome
{

  class StateMachineOnEnterTrigger : public Trigger<>
  {
  public:
    StateMachineOnEnterTrigger(StateMachineTextSensor *text_sensor, std::string state)
    {
      text_sensor->add_on_transition_callback(
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
    StateMachineOnLeaveTrigger(StateMachineTextSensor *text_sensor, std::string state)
    {
      text_sensor->add_on_transition_callback(
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

  class StateMachineInputActionTrigger : public Trigger<>
  {
  public:
    StateMachineInputActionTrigger(StateMachineTextSensor *text_sensor, std::string input)
    {
      text_sensor->add_on_transition_callback(
          [this, input](StateTransition transition)
          {
            if (transition.input == input)
            {
              this->trigger();
            }
          });
    }
  };

  template <typename... Ts>
  class StateMachineTransitionAction : public Action<Ts...>, public Parented<StateMachineTextSensor>
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
    explicit StateMachineTransitionCondition(StateMachineTextSensor *parent) : parent_(parent) {}

    TEMPLATABLE_VALUE(std::string, from_state)
    TEMPLATABLE_VALUE(std::string, input)
    TEMPLATABLE_VALUE(std::string, to_state)

    bool check(Ts... x) override
    {
      if (!this->parent_->last_transition.has_value())
        return false;
      StateTransition transition = this->parent_->last_transition.value();
      if (this->from_state_.has_value() && this->from_state_.value(x...) != transition.from_state)
        return false;
      if (this->input_.has_value() && this->input_.value(x...) != transition.input)
        return false;
      if (this->to_state_.has_value() && this->to_state_.value(x...) != transition.to_state)
        return false;
      return true;
    }

  protected:
    StateMachineTextSensor *parent_;
  };

} // namespace esphome
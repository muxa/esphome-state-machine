#include "state_machine_text_sensor.h"
#include "esphome/core/log.h"

namespace esphome
{

  static const char *const TAG = "state_machine.text_sensor";

  void StateMachineTextSensor::setup()
  {
    this->publish_state(this->state_machine_->current_state());
  }

  void StateMachineTextSensor::dump_config()
  {
    LOG_TEXT_SENSOR("", "State Machine Text Sensor", this);
    this->state_machine_->dump_config();
  }

  bool StateMachineTextSensor::transition(std::string input)
  {
    auto transition = this->state_machine_->transition(input);
    if (transition)
    {
      this->last_transition = transition;
      this->publish_state(transition.value().to_state);
      this->transition_callback_.call(transition.value());
      return true;
    }

    return false;
  }

} // namespace esphome
#include "state_machine_text_sensor.h"
#include "esphome/core/log.h"

namespace esphome
{
  namespace state_machine
  {
    static const char *const TAG = "state_machine.text_sensor";

    void StateMachineTextSensor::set_state_machine(StateMachineComponent *state_machine)
    {
      this->state_machine_ = state_machine;
      this->state_machine_->add_on_transition_callback(
            [this](StateTransition transition)
            {
              this->update();
            });
    }

    void StateMachineTextSensor::setup()
    {
      this->publish_state(this->state_machine_->current_state());
    }

    void StateMachineTextSensor::update()
    {
      this->publish_state(this->state_machine_->current_state());
    }

    float StateMachineTextSensor::get_setup_priority() const
    {
      return setup_priority::HARDWARE;
    }

    void StateMachineTextSensor::dump_config()
    {
      LOG_TEXT_SENSOR("", "State Machine Text Sensor", this);
      ESP_LOGCONFIG(TAG, "State Machine: %s", this->state_machine_->get_name().c_str());
    }

  } // namespace state_machine
} // namespace esphome
#pragma once

#include "esphome/core/component.h"
#include "esphome/components/text_sensor/text_sensor.h"
#include "../state_machine.h"

namespace esphome
{
  namespace state_machine
  {
    class StateMachineTextSensor : public text_sensor::TextSensor, public Component
    {
    public:

      void set_state_machine(StateMachineComponent *state_machine);

      void setup() override;

      void update();

      float get_setup_priority() const override;

      void dump_config() override;

    protected:
      StateMachineComponent *state_machine_;
    };

  } // namespace state_machine
} // namespace esphome
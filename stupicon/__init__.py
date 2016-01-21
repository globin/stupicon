import time
import logging
import pygame
import pygame.midi
import smbus

from .config_read import Config
from .io_extension import IoPi

log_format = '%(levelname)s | %(asctime)-15s | %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)


# import RPIO

# numbering starts at 2, 2 & 3 are used for I2C
# GPIO_PINS = list(range(4, 27))

BUS_ADDRESSES = list(range(0x20, 0x28))

class Stupicon:
    read_status = {}

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.config = Config.from_file('./test.toml')

        pygame.midi.init()
        self.player = pygame.midi.Output(2)
        self.player.set_instrument(48, 1)
        self.midi_capture = pygame.midi.Input(1)

        self.setup_gpio()

        while True:
            self.read_pins()
            self.read_midi()
            time.sleep(.01)

    def setup_gpio(self):
        bus = smbus.SMBus(1)
        self.io_chips = [IoPi(bus, i) for i in BUS_ADDRESSES]
        for chip_num, chip in enumerate(self.io_chips):
            chip.mirror_interrupts(0)
            chip.set_interrupt_type(0, 0)
            chip.set_interrupt_type(1, 0)
            for (pin, type) in self.config.pins[chip_num].items():
                chip.set_pin_direction(pin, type)
                if type == Config.IN:
                    chip.set_pin_direction(pin, type)
                    chip.set_pin_pullup(pin, 1)
                    chip.set_interrupt_on_pin(pin, 1)
                    chip.invert_pin(pin, 1)
                    self.read_status[(chip_num, pin)] = 0
                elif type == Config.OUT:
                    chip.write_pin(pin, 1)

        # RPIO.setmode(RPIO.BCM)

        # [self.setup_input_pin(pin) for pin in GPIO_PINS]
        # [self.set_interrupt(pin) for pin in GPIO_PINS]

    def read_pins(self):
        for chip_num, chip in enumerate(self.io_chips):
            for (pin, type) in self.config.pins[chip_num].items():
                if type == Config.IN:
                    val = chip.read_pin(pin)
                    if self.read_status.get((chip_num, pin)) is not val:
                        self.read_status[(chip_num, pin)] = val
                        self.logger.info('pin changed {} {}: {}'.format(chip_num, pin, val))
                        self.gpio_changed(chip_num, pin, val)

    def gpio_changed(self, chip_num, pin, val):
        self.play(chip_num * 16 + pin, val)

    # def setup_input_pin(self, pin):
    #     self.logger.info('setup pin: {}'.format(pin))
    #     RPIO.setup(pin, RPIO.IN, pull_up_down=RPIO.PUD_DOWN)

    # def set_interrupt(self, pin):
    #     self.logger.info('setup interrupt: {}'.format(pin))
    #     RPIO.add_interrupt_callback(pin, self.gpio_callback,
    #             debounce_timeout_ms=50)

    def play(self, note, state):
        self.logger.info('playing: {} {}'.format(
            note,
            'on' if state else 'off'
        ))
        if state:
            self.player.note_on(note, 127, 1)
        else:
            self.player.note_off(note, 127, 1)

    def read_midi(self):
        if self.midi_capture.poll():
            for [[event, note, _, _], time] in self.midi_capture.read(64):
                chip = self.io_chips[note // 16]
                pin = note % 16 + 1
                if 0x80 <= event < 0x90: # NOTE OFF
                    chip.write_pin(pin, 0)
                elif 0x90 <= event < 0xA0: # NOTE ON
                    chip.write_pin(pin, 1)
                self.logger.info('midi event {:#x}'.format(event))

def main():
    try:
        Stupicon()
    except KeyboardInterrupt:
        # RPIO.cleanup()
        pygame.midi.quit()

import time
import logging

import click
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
    pin_state = {}

    def __init__(self, config_file):
        self.logger = logging.getLogger(__name__)

        self.config = Config.from_file(config_file)

        pygame.midi.init()
        self.player = pygame.midi.Output(2)
        self.player.set_instrument(48, 1)
        self.midi_capture = pygame.midi.Input(3)

        self.setup_gpio()

        while True:
            self.read_pins()
            self.read_midi()
            time.sleep(.01)

    def setup_gpio(self):
        bus = smbus.SMBus(1)
        self.io_chips = [IoPi(bus, i) for i in BUS_ADDRESSES]
        for chip_num, chip in enumerate(self.io_chips):
            self.logger.info('set up chip {}'.format(chip_num))
            chip.mirror_interrupts(0)
            chip.set_interrupt_type(0, 0)
            chip.set_interrupt_type(1, 0)
            for (pin, config) in self.config.pins[chip_num].items():
                type = config['type']
                if type in [Config.IN, Config.VIA]:
                    self.logger.info('setup pin {:#x}: IN'.format(pin, type))
                    chip.set_pin_direction(pin, Config.IN)
                    chip.set_pin_pullup(pin, 1)
                    chip.set_interrupt_on_pin(pin, 1)
                    chip.invert_pin(pin, 1)
                elif type in [Config.OUT, Config.STATE]:
                    self.logger.info('setup pin {:#x}: OUT'.format(pin))
                    chip.set_pin_direction(pin, Config.OUT)
                    chip.write_pin(pin, 0)

                self.pin_state[(chip_num, pin)] = 0


        # RPIO.setmode(RPIO.BCM)

        # [self.setup_input_pin(pin) for pin in GPIO_PINS]
        # [self.set_interrupt(pin) for pin in GPIO_PINS]

    # def setup_input_pin(self, pin):
    #     self.logger.info('setup pin: {}'.format(pin))
    #     RPIO.setup(pin, RPIO.IN, pull_up_down=RPIO.PUD_DOWN)

    # def set_interrupt(self, pin):
    #     self.logger.info('setup interrupt: {}'.format(pin))
    #     RPIO.add_interrupt_callback(pin, self.gpio_callback,
    #             debounce_timeout_ms=50)

    def read_pins(self):
        for chip_num, chip in enumerate(self.io_chips):
            for (pin, pin_config) in self.config.pins[chip_num].items():
                type = pin_config['type']
                if type in [Config.IN, Config.VIA]:
                    val = chip.read_pin(pin)
                    if self.pin_state.get((chip_num, pin)) is not val:
                        self.pin_state[(chip_num, pin)] = val
                        self.gpio_changed(chip_num, pin, val, pin_config)

    def gpio_changed(self, chip_num, pin, val, pin_config):
        self.logger.info('pin in  {}-{:#x}: {}'.format(chip_num, pin, val, pin_config))
        if pin_config['type'] == Config.IN:
            self.play(chip_num * 16 + pin, val)
        elif pin_config['type'] == Config.VIA:
            for to_chip_num, to_pin in pin_config['to']:
                self.change_pin(to_chip_num, to_pin, val)

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
                chip_num = note // 16
                pin = note % 16 + 1
                if 0x80 <= event < 0x90: # NOTE OFF
                    self.change_pin(chip_num, pin, 0)
                elif 0x90 <= event < 0xA0: # NOTE ON
                    self.change_pin(chip_num, pin, 1)
                self.logger.info('midi event {:#x}'.format(event))

    def change_pin(self, chip_num, pin, value):
        pin_config = self.config.pins[chip_num][pin]
        if pin_config['type'] == Config.OUT:
            self.io_chips[chip_num].write_pin(pin, value)
            self.logger.info('pin {}-{:#x}: {}'.format(chip_num, pin, value))
        elif pin_config['type'] == Config.STATE and value == 1:
            pin_val = self.pin_state[(chip_num, pin)] = (self.pin_state[(chip_num, pin)] + 1) % 2
            self.io_chips[chip_num].write_pin(pin, pin_val)
            self.logger.info('pin out {}-{:#x}: {}'.format(chip_num, pin, pin_val))


@click.command()
@click.option('--config', '-c', help='config TOML file to specify IO functionality',
        required=True, type=click.Path(exists=True, dir_okay=False))
def main(config):
    try:
        Stupicon(config)
    except KeyboardInterrupt:
        # RPIO.cleanup()
        pygame.midi.quit()

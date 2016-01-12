import time
import logging
import pygame
import pygame.midi

log_format = '%(levelname)s | %(asctime)-15s | %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)


import RPIO
GPIO_PINS = list(range(2, 26))

class Stupicon:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        pygame.midi.init()
        self.player = pygame.midi.Output(2)
        self.player.set_instrument(48, 1)

        self.setup_gpio()
        # RPIO.setup(12, RPIO.OUT)
        # RPIO.output(12, True)
        # time.sleep(1)
        # RPIO.output(12, False)
        RPIO.wait_for_interrupts()

    def setup_gpio(self):
        RPIO.setmode(RPIO.BCM)
        [self.setup_input_pin(pin) for pin in GPIO_PINS]
        [self.set_interrupt(pin) for pin in GPIO_PINS]

    def gpio_callback(self, gpio_id, val):
        self.logger.info('callback {} {}'.format(gpio_id, val))
        self.play(gpio_id, not val)

    def setup_input_pin(self, pin):
        self.logger.info('setup pin: {}'.format(pin))
        RPIO.setup(pin, RPIO.IN, pull_up_down=RPIO.PUD_DOWN)

    def set_interrupt(self, pin):
        self.logger.info('setup interrupt: {}'.format(pin))
        RPIO.add_interrupt_callback(pin, self.gpio_callback,
                debounce_timeout_ms=50)

    def play(self, note, state):
        self.logger.info('playing: {} {}'.format(
            note,
            'on' if state else 'off'
        ))
        if state:
            self.player.note_on(note, 127, 1)
        else:
            self.player.note_off(note, 127, 1)

def main():
    try:
        Stupicon()
    except KeyboardInterrupt:
        RPIO.cleanup()
        pygame.midi.quit()

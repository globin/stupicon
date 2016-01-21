import itertools
import toml

class Config:
    OUT = 0
    IN = 1
    STATE = 2
    VIA = 3

    pins = {}

    @classmethod
    def from_file(cls, filename):
        with open(filename) as file:
            return cls(toml.loads(file.read()))

    def __init__(self, config):
        for chip in config['pins'].keys():
            self.parse_pins(int(chip) - 1, config['pins'][chip])

    def parse_pins(self, chip_num, chip_config):
        self.pins[chip_num] = {}
        for i in chip_config['A'].keys():
            self.pins[chip_num][int(i) + 1] = self.parse(chip_config['A'][i])
        for i in chip_config['B'].keys():
            self.pins[chip_num][int(i) + 9] = self.parse(chip_config['B'][i])
        print(chip_num, self.pins[chip_num])

    def parse(self, value):
        if value == 'IN':
            return { 'type': self.IN }
        elif value == 'OUT':
            return { 'type': self.OUT }
        elif value == 'STATE':
            return { 'type': self.STATE }
        elif value.startswith('VIA'):
            to = map(self.parse_pin_id, value.split(' ')[1:])
            return { 'type': self.VIA, 'to': list(to) }

    def parse_pin_id(self, pin_id):
        chip_num, port_name, pin = pin_id.split('.')
        port = 0 if port_name == 'A' else 1
        return (int(chip_num) - 1, port * 8 + int(pin) + 1)

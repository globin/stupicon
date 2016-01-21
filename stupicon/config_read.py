import itertools
import toml

class Config:
    IN = 1
    OUT = 0

    pins = []

    @classmethod
    def from_file(cls, filename):
        with open(filename) as file:
            return cls(toml.loads(file.read()))

    def __init__(self, config):
        self.toml_input = config
        self.pins = list(map(self.parse_pins, sorted(config['pins'].keys())))

    def parse_pins(self, chip_num):
        chip_config = self.toml_input['pins'][chip_num]
        pin_config_A = ((int(i) + 1, self.to_const(chip_config['A'][i])) for i in chip_config['A'].keys())
        pin_config_B = ((int(i) + 9, self.to_const(chip_config['B'][i])) for i in chip_config['B'].keys())
        return dict(itertools.chain(pin_config_A, pin_config_B))

    def to_const(self, value):
        if value == 'IN':
            return self.IN
        if value == 'OUT':
            return self.OUT

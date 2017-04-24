from enum import Enum
import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(name='gpu')

class GPU:
    """
    GPU for the gameboy
    NOTE: referenced https://github.com/zeta0134/luagb

    Attributes
    ----------
    clock : int
        keeps track of cpu cycles updates accordingly
    screen : bytearray
        gameboy LCD screen arranged in an array
        160x144
        index = col + (row * 160)

    """
    def __init__(self, memory):
        self.clock = 456
        self.gb_screen = bytearray(23040)
        self.white_screen = bytearray(23040)
        self.mem = memory
        self.modes = Enum('Mode', 'HB VB OR LCD')
        print(self.modes.HB)
        self.mode = self.modes.OR
        print(self.mode)
        self.dispatch_mode = {
            self.modes.HB: self.h_blank,
            self.modes.VB: self.v_blank,
            self.modes.OR: self.o_ram,
            self.modes.LCD: self.lcd_trans
        }

    def update_graphics(self, cycles):
        if self.lcd_enabled():
            self.dispatch_mode[self.mode]()
        else:
            pass
            # TODO ????

    def h_blank(self):
        pass

    def v_blank(self):
        pass

    def o_ram(self):
        pass

    def lcd_trans(self):
        pass


    def lcd_enabled(self):
        """
        Returns True if bit 7 of LCD control register is set
        LCD control register is 0xff40 in memory

        Returns
        -------
        bool
        """
        return True if self.mem.read(0xff40) & 0x80 == 0x80 else False

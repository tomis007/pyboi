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
        self.clock = 0
        self.mode_clock = 0
        self.gb_screen = bytearray(23040)
        self.white_screen = bytearray(23040)
        self.mem = memory
        self.modes = Enum('Mode', 'HB VB OR LCD')
        self.mode = self.modes.OR
        self.dispatch_mode = {
            self.modes.HB: self.h_blank,
            self.modes.VB: self.v_blank,
            self.modes.OR: self.o_ram,
            self.modes.LCD: self.lcd_trans
        }
        self.scanline = 0

    def update_graphics(self, cycles):
        """
        Updates the graphics display according to number of cycles
        elapsed from cpu

        Arguments
        ---------
        int cycles
            number of cycles since last call
        """
        if self.lcd_enabled():
            self.dispatch_mode[self.mode](cycles)
        else:
            # TODO CORRECT??
            #self.set_mode(self.modes.VB, 0)
            pass

    def h_blank(self, cycles):
        """
        Mode 0 of screen drawing process.
        CPU can access both RAM/OAM.
        """
        self.mode_clock += cycles
        if self.mode_clock >= 204:
            if self.scanline < 144:
                self.set_mode(self.modes.OR, self.mode_clock % 204)
            else:
                self.set_mode(self.modes.VB, self.mode_clock % 204)

    def v_blank(self, cycles):
        """
        Mode 1 of drawing process, Vertical Blank.
        Between scanlines 144 - 153, CPU can access both
        RAM and OAM.
        """
        self.mode_clock += cycles
        if self.mode_clock >= 456:
            if self.scanline >= 152:
                self.set_mode(self.modes.HB, self.mode_clock % 456)
                self.scanline = 0
            else:
                self.scanline += 1
                self.set_mode(self.modes.VB, self.mode_clock % 456)
            

    #TODO block OAM memory access
    def o_ram(self, cycles):
        """
        Mode 2 of the screen draw process, reading from OAM memory.
        CPU cannot access OAM memory during.
        """
        self.mode_clock += cycles
        if self.mode_clock >= 80:
            self.set_mode(self.modes.LCD, self.mode_clock % 80)
        
    #TODO block OAM/VRAM access
    def lcd_trans(self, cycles):
        """
        Mode 3 of the screen drawing process, reading from OAM/VRAM.
        After this mode is complete the current scanline is drawn
        """
        self.mode_clock += cycles
        if self.mode_clock >= 174:
            self.set_mode(self.modes.HB, self.mode_clock % 204)
            self.draw_scanline(self.scanline)
            self.scanline += 1

    
    def set_mode(self, mode, cycles):
        """
        Sets the mode. Changes ff41 register in memory, resets clock
        timings.

        Parameters
        ----------
        mode 
            to set to
        cycles
            to set the next clock clycles to
        """
        self.mode_clock = cycles
        self.mode = mode

        #change registers in mem
        flag = self.mem.read(0xff41)
        next_mode = 0
        if mode == self.modes.HB:
            next_mode = 0x0
        elif mode == self.modes.VB:
            next_mode = 0x1
        elif mode == self.modes.OR:
            next_mode = 0x2
        else: # mode == self.modes.LCD
            next_mode = 0x3
        flag &= 0xfc
        flag |= next_mode
        self.mem.write(flag, 0xff41)

       
    def draw_scanline(self, scanline):
        #print("drawing background " + str(scanline))
        self.draw_background(scanline)
        self.mem.write(self.scanline, 0xff44)


    def draw_background(self, scanline):
        """
        Draws the background for the current scanline

        Parameters
        ----------
        scanline
            to draw background on
        """
        # background display register
        if not self.is_set(0xff40, 0):
            #print("background not turned on :(")
            return #bg turned off
        else:
            print("DRAWING BACKGROUND!!!!!!!")


        


    def is_set(self, address, bit):
        """
        Checks address in mem and tests if bit is set.
        LSB - Bit 0
        MSB - Bit 7

        ...
        Parameters
        ----------
        address 
            address in memory to check
        bit
            bit at address to check

        Returns
        -------
        True if bit set
        False if not set
        """
        data = self.mem.read(address)
        return True if (data >> bit) & 0x1 == 0x1 else False


    def lcd_enabled(self):
        """
        Returns True if bit 7 of LCD control register is set
        LCD control register is 0xff40 in memory

        Returns
        -------
        bool
        """
        return True if (self.mem.read(0xff40) & 0x80) == 0x80 else False

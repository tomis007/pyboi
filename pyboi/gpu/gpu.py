from enum import Enum
import pdb
from ctypes import c_int8
import drawille
import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(name='gpu')

class GPU:
    """
    GPU for the gameboy
    thanks to: https://github.com/zeta0134/luagb

    Attributes
    ----------
    clock : int
        keeps track of cpu cycles updates accordingly
    screen : bytearray
        gameboy LCD screen arranged in an array
        160x144
        index = col + (row * 160)

    """
    #TODO: The scanline incrementing is confusing...
    def __init__(self, memory):
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
        self.lcd_prev_enabled = True

        #set up initial state
        self.mem.set_scanline(0)
        self.set_mode(self.modes.OR, 0)

    def update_graphics(self, cycles):
        """
        Updates the graphics display according to number of cycles
        elapsed from cpu

        Arguments
        ---------
        int cycles
            number of cycles since last call
        """
        if self.lcd_enabled() and self.lcd_prev_enabled:
            self.dispatch_mode[self.mode](cycles)
        elif self.lcd_enabled() and not self.lcd_prev_enabled:
            # enabled LCD start in HBlank
            self.set_mode(self.modes.HB, 0)
            self.dispatch_mode[self.mode](cycles)
            self.lcd_prev_enabled = True
        else:
            # LCD is in VBlank when disabled
            if self.mode != self.modes.VB:
                self.mem.set_scanline(0)
                self.set_mode(self.modes.VB, 0)
            self.lcd_prev_enabled = False

    def h_blank(self, cycles):
        """
        Mode 0 of screen drawing process.
        CPU can access both RAM/OAM.
        """
        self.mode_clock += cycles
        if self.mode_clock >= 204:
            self.mem.inc_scanline()
            # check for LYC compare
            if self.mem.read(0xff45) == self.mem.get_scanline():
                self.mem.set_lcd_coincidence(1)
                # check for interrupt enable
                if self.mem.read(0xff41) & 0x40 != 0:
                    self.mem.request_interrupt(1)
            else:
                self.mem.set_lcd_coincidence(0)


            if self.mem.get_scanline() < 144:
                # back to mode 2
                self.set_mode(self.modes.OR, self.mode_clock % 204)
            else:
                # time for Vertical Blank, signal request
                self.mem.request_interrupt(0)
                self.set_mode(self.modes.VB, self.mode_clock % 204)


    #TODO memory access
    def v_blank(self, cycles):
        """
        Mode 1 of drawing process, Vertical Blank.
        Between scanlines 144 - 153, CPU can access both
        RAM and OAM.
        """
        self.mode_clock += cycles
        #if turning the screen back on
        if self.mode_clock >= 456 or (self.mem.get_scanline() == 153 and self.mode_clock >= 64):
            self.mem.inc_scanline()
            if self.mem.get_scanline() > 153:
                # Go to OR mode on line 0
                self.mem.set_scanline(0)
                self.set_mode(self.modes.OR, 0)
            else:
                self.set_mode(self.modes.VB, self.mode_clock % 456) 

    #TODO block OAM memory access
    def o_ram(self, cycles):
        """
        Mode 2 of the screen draw process, reading from OAM memory.
        CPU cannot access OAM memory during.
        """
        self.mode_clock += cycles
        # 80 cycles for OAM mode 
        if self.mode_clock >= 80:
            self.set_mode(self.modes.LCD, self.mode_clock % 80)
        
    #TODO block OAM/VRAM access
    def lcd_trans(self, cycles):
        """
        Mode 3 of the screen drawing process, LCD controller is reading
        from OAM/VRAM. After this mode is complete the current 
        scanline is drawn.
        """
        self.mode_clock += cycles
        if self.mode_clock >= 174:
            # enter H-Blank mode and draw line
            self.draw_scanline(self.mem.get_scanline())
            self.set_mode(self.modes.HB, self.mode_clock % 204)


    
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
        req_interrupt = False

        #change registers in mem
        flag = self.mem.read(0xff41)
        flag &= 0xfc
        if mode == self.modes.HB:
            flag |= 0x0
            if flag & 0x8 != 0:
                req_interrupt = True 
        elif mode == self.modes.VB:
            flag |= 0x1
            if flag & 0x10 != 0:
                req_interrupt = True
        elif mode == self.modes.OR:
            flag |= 0x2
            if flag & 0x20 != 0:
                req_interrupt = True
        else: # mode == self.modes.LCD
            flag |= 0x3
        self.mem.lcd_stat_write(flag)

        # check to see if request interrupt
        if req_interrupt:
            self.mem.request_interrupt(1)


       
    def draw_scanline(self, scanline):
        """
        Draws the scanline specified based on the current
        contents of memory

        ...
        Parameters
        ----------
        scanline : int
            scanline to draw (0-143)
        """
        self.draw_background(scanline)


    def draw_background(self, scanline):
        """
        Draws the background for the current scanline

        Parameters
        ----------
        scanline
            to draw background on
        """
        # background display register
        lcd_control = self.mem.read(0xff40)
        if not self.bit_set(lcd_control, 0):
            return #bg turned off

        scY = self.mem.read(0xff42)
        scX = self.mem.read(0xff43)
        tile_select = 0x8000 if self.bit_set(lcd_control, 4) else 0x9000
        tile_map = 0x9c00 if self.bit_set(lcd_control, 3) else 0x9800

        y_offset = (((scY + scanline) // 8) % 32) * 32
        tile_line = (scY + scanline) % 8
        for x_tile in range(20):
            x_offset = (x_tile + (scX // 8)) % 32
            tile_index = self.mem.read(tile_map + y_offset + x_offset)
            if tile_select == 0x9000:
                tile_index = c_int8(tile_index).value
            address = tile_select + (16 * tile_index)
            x_shift = scX % 8
            if x_tile == 0 and x_shift != 0:
                self.draw_bg_tile(address, tile_line, 
                                  0, scanline, x_shift, 7)
            elif x_tile == 20 and x_shift != 0:
                self.draw_bg_tile(address, tile_line, 
                                  160 - x_shift, scanline, 0, x_shift - 1)
            else:
                self.draw_bg_tile(address, tile_line, 
                                 (x_tile * 8) - x_shift, scanline, 0, 7)

    def draw_bg_tile(self, address, line, x, y, pix_start, pix_end):
        """
        Draws a background tile into the display buffer.

        ...
        Parameters
        ----------
        address : int
            address in memory of tile data 
        line : int
            line of the tile to draw (0-7)
        x : int
            x position on the GB screen
        y : int
            y position on the GB screen
        pix_start : int
            first pixel in the block to draw
        pix_end : int
            last pixel in the block to draw
        """
        #if address != 0x8000:
            #print('drawing tile: ' + hex(address) + '  line: ' + str(line))
            #pdb.set_trace()
        block_one = self.mem.read(address + (2 * line))
        block_two = self.mem.read(address + (2 * line) + 1)
        
        #TODO check if loops correctly
        for pixel in range(pix_start, pix_end + 1):
            color = self.get_color(block_one, block_two, pixel)
            x_pix = (x + pixel - pix_start) % 160
            self.draw_to_buffer(x_pix, y, color)




    def dump_tile(self, address):
        c = drawille.Canvas()
        line1 = []
        line2 = []
        for x in range(8):
            line1.append(self.mem.read(address + (2 * x)))
            line2.append(self.mem.read(address + (2 * x) + 1))
        print('Tile Data @' + hex(address))
        c.set(0,0)
        c.set(10,10)
        for i,line in enumerate(line1):
            for pixel in range(8):
                if self.get_color(line, line2[i], pixel) != 0:
                    c.set(1 + pixel,1 + i)
        print(c.frame())        

        ##for index, data in enumerate(zip(line1, line2)):
        #    print(bin(data[0]))
        #    if data[1] != 0:
        #        print(bin(data[1]))
        #pdb.set_trace()

    def dump_tile_to_screen(self, address, x_start):
        line1 = []
        line2 = []
        for x in range(8):
            line1.append(self.mem.read(address + (2 * x)))
            line2.append(self.mem.read(address + (2 * x) + 1))
        for i,line in enumerate(line1):
            for pixel in range(8):
                if self.get_color(line, line2[i], pixel) != 0:
                    self.draw_to_buffer(x_start + i, pixel, 1)
        c = drawille.Canvas()
        c.clear()
        c.set(0,0)
        c.set(160,144)
        for row in range(144):
            for col in range(160):
                if self.gb_screen[(row * 160) + col] != 0:
                    c.set(col, row)
        print(c.frame())



    def draw_to_buffer(self, col, row, color):
        """
        Places color at position col,row in the screen buffer.
        color is a byte value
        """
        self.gb_screen[col + (row * 160)] = color

    def get_color(self, block_one, block_two, pixel):
        """
        Return the color of the pixel to draw.
        For GB MODE
        0-3
        """
        pix = 7 - pixel
        color_num = 1 if self.bit_set(block_two, pix) else 0
        color_num = (color_num << 1) | (1 if self.bit_set(block_one, pix) else 0)
        palette = self.mem.read(0xff47)
        color = (palette >> (color_num * 2)) & 0x3

        return color

        
    def bit_set(self, data, bit):
        """
        Checks if bit bit is set in data.
        Same as is_set without reading
        from memory
        """
        return True if (data >> bit) & 0x1 == 0x1 else False

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

    def get_frame_buffer(self):
        """ Returns the current gb screen buffer. """
        return self.gb_screen

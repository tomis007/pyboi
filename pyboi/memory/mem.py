import os.path
import logging
from .membanks import MemBanks
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(name='memory')

class Memory:
    """
    Represents the memory of the GB.

    ...
    Attributes
    ----------
    membanks : MemBank()
        represents the following areas of memory
        0x0000 - 0x7fff : ROMBANKS
        0x8000 - 0xdfff : RAM + RAM banks
    oam : bytearray
        sprite attribute table
        0xfe00 - 0xfe9f
    regio : bytearray
        0xff00 - 0xff7f
        I/O ports + Registers
    hram : bytearray
        0xff80 - 0xfffe 
        high ram
    bios_mode : bool
        if true, when accessing memory below 0x100, 
        reads from bios. defaults to False

    """
    def __init__(self):
        self.membanks = None
        self.oam = bytearray(0xa0)
        self.regio = bytearray(0x80)
        self.hram = bytearray(0x80)
        self.bios_mode = False #default
        self.interrupt_enable = 0
        #requires bios.gb in directory
        if not os.path.isfile('./roms/bios.gb'):
            log.critical('no bios file')
            exit()
        with open('./roms/bios.gb', 'rb') as f:
            self.bios = bytearray(f.read())

    def load_rom(self, rom):
        """
        Load a rom from file into memory.

        ...
        Parameters
        ----------
        rom : string
            path to rom to load

        Returns
        -------
        boolean
            False on failure, or True on success
        NOTE: Logs an appropriate error on Failure

        """
        # cleaner to not use exception handling
        if not os.path.isfile(rom):
            log.critical('rom file can not be opened')
            quit()
        with open(rom, 'rb') as f:
            # this puts entire rom in RAM, but
            # roms are quite small
            self.membanks = MemBanks(bytearray(f.read()))
            log.info('LOADING: ' + rom)
        return True

    def read_bios(self, address):
        """
        Read a byte from the bios in memory.
        
        ...
        Parameters
        ----------
        address : int
            to read, must be less than 0x100
        Returns
        -------
        int
            value of memory at address
        """
        if address < 0:
            #log.critical('reading from negative address in bios')
            return 0
        elif address <= 0x100:
            return self.bios[address]
        else:
            #log.critical('reading from out of bounds address in bios')
            return 0


    def read(self, address):
        """
        Read a byte from memory

        ...
        Parameters
        ----------
        address : integer
            to read
        
        Returns
        -------
        int
            value of memory at address
        """
        if address < 0:
            log.error('negative address read!')
        elif self.bios_mode and address <= 0x100:
            return self.read_bios(address)
        elif address < 0xe000:
            return self.membanks.read(address)
        elif address < 0xfe00:
            return self.membanks.read(address - 0x1e00) #echo ram
        elif address < 0xfea0:
            return self.oam[address - 0xfe00]
        elif address < 0xff00:
            log.error('reading from invalid address')
            log.error(hex(address))
        elif address == 0xff00:
            return self.get_input_state()
        elif address < 0xff80:
            return self.regio[address - 0xff00]
        elif address < 0xffff:
            return self.hram[address - 0xff80]
        elif address == 0xffff:
            return self.interrupt_enable

    def read_word(self, address):
        """
        Reads two bytes (a word) from memory.

        ...
        Parameters
        ----------
        address : int
            to read from

        Returns
        -------
        int 
            value of memory at address (two bytes)
        """
        return (self.read(address + 1) << 8) | self.read(address)

    def write(self, byte, address):
        """
        Write a byte to memory.

        ...
        Parameters
        ----------
        byte : int
            byte to write
        address : int
            address to write to

        """
        # for test roms
        if address == 0xff01:
            print(chr(byte), end='', flush=True)
        if address < 0:
            log.error('writing to negative address!')
        elif address < 0xe000:
            self.membanks.write(byte, address)
        elif address < 0xfe00:
            self.membanks.write(byte, address - 0x1e00) #echo ram
        elif address < 0xfea0:
            self.oam[address - 0xfe00] = byte & 0xff
        elif address < 0xff00:
            # not usable
            return
        elif address < 0xff80:
            self.reg_write(byte, address)
        elif address < 0xffff:
            self.hram[address - 0xff80] = byte & 0xff
        elif address == 0xffff:
            self.interrupt_enable = byte & 0xff


    # TODO
    def reg_write(self, byte, address):
        """
        Write a byte to IO Ports and handle register resets

        ...
        Parameters
        ----------
        byte : int
            byte to write
        address : int
            address to write to

        """
        if address == 0xff00:
            #IO PORTS TODO INPUT
            self.regio[0] |= (byte & 0xf0)
        elif address == 0xff04:
            # divider, reset on write
            self.regio[0x4] = 0
        elif address == 0xff41:
            #LCD STAT
            byte &= 0xf8
            self.regio[0x41] &= 0x7
            self.regio[0x41] |= byte
            self.regio[0x41] |= 0x80
        elif address == 0xff44:
            self.regio[0x44] = 0
        elif address == 0xff46:
            dma_addr = byte * 0x100
            for i in range(0xa0):
                self.oam[i] = self.read(dma_addr + i)
        else:
            self.regio[address - 0xff00] = byte & 0xff

    def lcd_stat_write(self, byte):
        """
        Writes the mode to the LCD status register.
        """
        self.regio[0x41] &= 0xfc
        self.regio[0x41] |= (byte & 0x3)


    def set_bios_mode(self, val):
        """
        Sets read_bios flag in memory to val, if true
        when memory accessed below 0x100 reads from
        bios not cartridge.

        Parameters
        ----------
        val : bool
        
        """
        self.bios_mode = val

    def request_interrupt(self, int_id):
        """
        Requests interrupt int_id.
        0 - VBlank
        1 - LCD STAT
        2 - Timer
        3 - Serial
        4 - JoyPad
        """
        ir = self.regio[0xf]
        ir |= 1 << int_id
        self.regio[0xf] = ir

    def set_lcd_coincidence(self, bit):
        """
        Sets the STAT register coincidence bit to bit
        """
        bit &= 1
        self.regio[0x41] &= ~0x4 & 0xff
        self.regio[0x41] |= bit

    def inc_scanline(self):
        """ Increment scanline register @ 0xff44"""
        self.regio[0x44] += 1

    def set_scanline(self, val):
        """ Set scanline register @ 0xff44 to val """
        self.regio[0x44] = val

    def get_scanline(self):
        return self.regio[0x44]

    #TODO
    def get_input_state(self):
        return self.regio[0] | 0xf

    def inc_div(self):
        """
        Increments the div timer by 1.
        """
        self.regio[0x4] = (1 + self.regio[0x4]) & 0xff

    def inc_tima(self):
        """
        Increments the tima register, requests an interrupt if needed.
        """
        new_val = self.regio[0x5] + 1
        self.regio[0x5] = new_val & 0xff
        if new_val > 0xff:
            # overflow
            self.regio[0x5] = self.regio[0x6]
            self.request_interrupt(2)



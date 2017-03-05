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
    ioports : bytearray
        0xff00 - 0xff7f
        I/O ports
    hram : bytearray
        0xff80 - 0xfffe 
        high ram

    """
    def __init__(self):
        self.membanks = None
        self.oam = bytearray(0xa0)
        self.ioports = bytearray(0x80)
        self.hram = bytearray(0x80)

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
            return False
        with open(rom, 'rb') as f:
            # this puts entire rom in RAM, but
            # roms are quite small
            self.membanks = MemBanks(bytearray(f.read()))
            print('LOADING!')
            log.debug('loaded membank')
        return True

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
        elif address < 0xe000:
            return self.membanks.read(address)
        elif address < 0xfe00:
            return self.membanks.read(address - 0x1e00) #echo ram
        elif address < 0xfea0:
            return self.oam[address - 0xfe00]
        elif address < ff00:
            log.error('reading from invalid address')
        elif address < 0xff80:
            return self.ioports[address - 0xff80]
        elif address < 0xffff:
            return self.hram[address - 0xff80]

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
        return (self.read(address) << 8) | self.read(address + 1)

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
        if address < 0:
            log.error('writing to negative address!')
        elif address < 0xe000:
            self.membanks.write(byte, address)
        elif address < 0xfe00:
            self.membanks.write(byte, address - 0x1e00) #echo ram
        elif address < 0xfea0:
            self.oam[address - 0xfe00] = byte & 0xff
        elif address < ff00:
            log.error('writing to invalid address')
        elif address < 0xff80:
            self._iowrite(byte, address)
        elif address < 0xffff:
            self.hram[address - 0xff80] = byte & 0xff

    # TODO
    def _iowrite(self, byte, address):
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
        pass



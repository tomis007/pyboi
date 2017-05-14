from .rambank import RAMBank
import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(name='mbc1')

class MBC1:
    """
    Memory Bank Controller 1
    Memory from 0x0-0x7fff is both read from and writen
    to for control of MBC Registers

    ...
    Attributes
    ----------
    rom : bytearray 
        the ROM of the entire cartridge
    cur_rom : int
        the current rom Bank selected
    cur_ram : int
        the current ram Bank selected
    """
    def __init__(self, cartridge):
        """
        Initialize MBC1.

        ...
        Parameters
        ----------
        cartridge : bytearray
            the ROM to initialize from
        """
        self.rom = cartridge
        self.ram = RAMBank(cartridge[0x149])
        self.cur_rom = 1
        self.cur_ram = 0

    def read_byte(self, address):
        """
        Read a byte from mbc1.

        ...
        Parameters
        ----------
        address : int
            to read

        """
        if address < 0x4000:
            return self.rom[address]
        elif address < 0x8000:
            address -= 0x4000
            return self.rom[address + (self.cur_rom * 0x4000)]
        elif address < 0xfdff:
            return self.ram.read_byte(address)
        else:
            log.critical('INVALID READ AT: ' + hex(address))
            return 1

    def write_byte(self, byte, address):
        """
        Write a byte to MBC1. This controls/updates registers.

        RAM ENABLE: 0x0 - 0x1fff 
        ROM BANK #: 0x2000 - 0x3ffff
        RAM BANK # or upper bits of ROM BANK: 0x4000 - 0x5fff
        ROM/RAM Select: 0x6000 - 0x7fff

        ...
        Parameters
        ----------
        byte : int
            to write
        address : int
            to write to
        """
        if address < 0x8000:
            #TODO
            log.critical('ROM BANKING NOT IMPLEMENTED')
        elif address < 0xfdff:
            self.ram.write_byte(byte, address)
        else:
            log.critical('INVALID WRITE TO: ' + hex(address))

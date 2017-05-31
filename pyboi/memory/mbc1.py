from .rambank import RAMBank
import logging
from enum import Enum
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
        self.modes = Enum('BankMode', 'ROM RAM')
        self.mode = self.modes.ROM


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
        elif address < 0xe000:
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
            if address < 0x2000:
                #enable/disable ram register
                if byte & 0xa == 0xa:
                    self.ram.set_ext_ram_enable(True)
                else:
                    self.ram.set_ext_ram_enable(False)
            elif address < 0x4000:
                #rom bank number, lower 5 bits
                self.cur_rom &= 0xe0
                if byte == 0:
                    byte |= 0x1 #MBC 1 translates 0 -> 1
                self.cur_rom |=  byte & 0x1f
            elif address < 0x6000:
                # ram bank num or upper bits of rom bank #
                if self.mode == self.modes.RAM:
                    self.ram.set_bank_num(byte & 0x3)
                else:
                    self.cur_rom &= 0x1f
                    self.cur_rom |= (byte & 0x3) << 5
            else: # address < 0x8000
                #rom/ram mode select
                if byte == 0x0:
                    self.mode = self.modes.ROM
                elif byte == 0x1:
                    self.mode = self.modes.RAM
        elif address < 0xe000:
            self.ram.write_byte(byte, address)
        else:
            log.critical('INVALID WRITE TO: ' + hex(address))

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, PickleType
from ..base import Base
from ctypes import c_int8
from enum import Enum
import pickle
import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(name='z80')

class CpuState(Base):
    """
    SQLAlchemy base class to save cpustate.

    ...

    Attributes
    ----------
    id : int
        primary key for database
    savename : string
        game save name
    gbregisters : pickle
        pickled list of the cpu registers A-F
    stack_ptr : int
        the stack pointer
    program_ctr : int
        the program counter

    """
    __tablename__ = 'cpuState'

    id = Column(Integer, primary_key=True)
    savename = Column(String)
    gbregisters = Column(PickleType)
    stack_ptr = Column(Integer)
    program_ctr = Column(Integer)

    def __repr__(self):
        return "<CPU_STATE(savename=%r>" % self.savename


class Z80():
    """
    An implementation of the gameboy's ~z80 (similar) cpu.

    ...
    Attributes
    ----------
    reg : list of ints
        registers A-F in the z80 cpu
    pc : int
        program counter
    sp : int
        stack pointer
    mem : Memory
        memory object for this processor's memory
    opcodes : Dictionary
        function dictionary for dispatching the opcodes

    """

    def __init__(self, mem):
        """
        __init__ function

        ...
        Refer to Z80 class documentation for attribute info.

        """

        self.count = 0

        self.reg = [0 for _ in range(8)]
        # register index constants
        self.A = 0
        self.B = 1
        self.C = 2
        self.D = 3
        self.E = 4
        self.F = 5
        self.H = 6
        self.L = 7
        # register enums
        self.reg_pairs = Enum('RegPairs', 'HL BC DE AF')
        self.load_vals = Enum('ImmediateByte', 'N NN SP')
        self.HL = self.reg_pairs.HL
        self.BC = self.reg_pairs.BC
        self.DE = self.reg_pairs.DE
        self.AF = self.reg_pairs.AF
        self.N = self.load_vals.N
        self.NN = self.load_vals.NN
        self.SP = self.load_vals.SP
        self.flags = Enum('Flags', 'Z N H C')
        #pc/sp
        self.pc = 0#0x100
        self.sp = 0#0xfffe
        self.mem = mem
        self.opcodes = {
            0xcb: lambda: self.extended_opcode(),
            0xf3: lambda: self.disable_interrupts(),
            0x00: lambda: self.NOP(),
            0x06: lambda: self.ld_byte_n(self.B),
            0x0e: lambda: self.ld_byte_n(self.C),
            0x16: lambda: self.ld_byte_n(self.D),
            0x1e: lambda: self.ld_byte_n(self.E),
            0x26: lambda: self.ld_byte_n(self.H),
            0x2e: lambda: self.ld_byte_n(self.L),
            0x7f: lambda: self.ld_r1_r2(self.A, self.A),
            0x78: lambda: self.ld_r1_r2(self.A, self.B),
            0x79: lambda: self.ld_r1_r2(self.A, self.C),
            0x7a: lambda: self.ld_r1_r2(self.A, self.D),
            0x7b: lambda: self.ld_r1_r2(self.A, self.E),
            0x7c: lambda: self.ld_r1_r2(self.A, self.H),
            0x7d: lambda: self.ld_r1_r2(self.A, self.L),
            0x7e: lambda: self.ld_r1_r2(self.A, self.HL),
            0x40: lambda: self.ld_r1_r2(self.B, self.B),
            0x41: lambda: self.ld_r1_r2(self.B, self.C),
            0x42: lambda: self.ld_r1_r2(self.B, self.D),
            0x43: lambda: self.ld_r1_r2(self.B, self.E),
            0x44: lambda: self.ld_r1_r2(self.B, self.H),
            0x45: lambda: self.ld_r1_r2(self.B, self.L),
            0x46: lambda: self.ld_r1_r2(self.B, self.HL),
            0x48: lambda: self.ld_r1_r2(self.C, self.B),
            0x49: lambda: self.ld_r1_r2(self.C, self.C),
            0x4a: lambda: self.ld_r1_r2(self.C, self.D),
            0x4b: lambda: self.ld_r1_r2(self.C, self.E),
            0x4c: lambda: self.ld_r1_r2(self.C, self.H),
            0x4d: lambda: self.ld_r1_r2(self.C, self.L),
            0x4e: lambda: self.ld_r1_r2(self.C, self.HL),
            0x50: lambda: self.ld_r1_r2(self.D, self.B),
            0x51: lambda: self.ld_r1_r2(self.D, self.C),
            0x52: lambda: self.ld_r1_r2(self.D, self.D),
            0x53: lambda: self.ld_r1_r2(self.D, self.E),
            0x54: lambda: self.ld_r1_r2(self.D, self.H),
            0x55: lambda: self.ld_r1_r2(self.D, self.L),
            0x56: lambda: self.ld_r1_r2(self.D, self.HL),
            0x58: lambda: self.ld_r1_r2(self.E, self.B),
            0x59: lambda: self.ld_r1_r2(self.E, self.C),
            0x5a: lambda: self.ld_r1_r2(self.E, self.D),
            0x5b: lambda: self.ld_r1_r2(self.E, self.E),
            0x5c: lambda: self.ld_r1_r2(self.E, self.H),
            0x5d: lambda: self.ld_r1_r2(self.E, self.L),
            0x5e: lambda: self.ld_r1_r2(self.E, self.HL),
            0x60: lambda: self.ld_r1_r2(self.H, self.B),
            0x61: lambda: self.ld_r1_r2(self.H, self.C),
            0x62: lambda: self.ld_r1_r2(self.H, self.D),
            0x63: lambda: self.ld_r1_r2(self.H, self.E),
            0x64: lambda: self.ld_r1_r2(self.H, self.H),
            0x65: lambda: self.ld_r1_r2(self.H, self.L),
            0x66: lambda: self.ld_r1_r2(self.H, self.HL),
            0x68: lambda: self.ld_r1_r2(self.L, self.B),
            0x69: lambda: self.ld_r1_r2(self.L, self.C),
            0x6a: lambda: self.ld_r1_r2(self.L, self.D),
            0x6b: lambda: self.ld_r1_r2(self.L, self.E),
            0x6c: lambda: self.ld_r1_r2(self.L, self.H),
            0x6d: lambda: self.ld_r1_r2(self.L, self.L),
            0x6e: lambda: self.ld_r1_r2(self.L, self.HL),
            0x70: lambda: self.ld_r1_r2(self.HL, self.B),
            0x71: lambda: self.ld_r1_r2(self.HL, self.C),
            0x72: lambda: self.ld_r1_r2(self.HL, self.D),
            0x73: lambda: self.ld_r1_r2(self.HL, self.E),
            0x74: lambda: self.ld_r1_r2(self.HL, self.H),
            0x75: lambda: self.ld_r1_r2(self.HL, self.L),  
            0x36: lambda: self.ld_r1_r2(self.HL, self.N),
            0x0a: lambda: self.load_a(self.BC),
            0x1a: lambda: self.load_a(self.DE),
            0xfa: lambda: self.load_a(self.NN),
            0x3e: lambda: self.load_a(self.N),
            0x7f: lambda: self.write_a(self.A),
            0x47: lambda: self.write_a(self.B),
            0x4f: lambda: self.write_a(self.C),
            0x57: lambda: self.write_a(self.D),
            0x5f: lambda: self.write_a(self.E),
            0x67: lambda: self.write_a(self.H),
            0x6f: lambda: self.write_a(self.L),
            0x02: lambda: self.write_a(self.BC),
            0x12: lambda: self.write_a(self.DE),
            0x77: lambda: self.write_a(self.HL),
            0xea: lambda: self.write_a(self.NN),
            0xf2: lambda: self.load_a_c(store=False),
            0xe2: lambda: self.load_a_c(store=True),
            0x3a: lambda: self.load_a_hl(dec=True, load=True),
            0x32: lambda: self.load_a_hl(dec=True, load=False),
            0x2a: lambda: self.load_a_hl(dec=False, load=True),
            0x22: lambda: self.load_a_hl(dec=False, load=False),
            0xe0: lambda: self.a_n(True),
            0xf0: lambda: self.a_n(False),
            0x01: lambda: self.ld_nn(self.BC, set_sp=False),
            0x11: lambda: self.ld_nn(self.DE, set_sp=False),
            0x21: lambda: self.ld_nn(self.HL, set_sp=False),
            0x31: lambda: self.ld_nn(self.sp, set_sp=True),
            0xf9: lambda: self.ld_sp_hl(),
            0xf8: lambda: self.ldhl_sp(),
            0x08: lambda: self.ld_nn_sp(),
            0xf5: lambda: self.push_nn(self.A, self.F),
            0xc5: lambda: self.push_nn(self.B, self.C),
            0xd5: lambda: self.push_nn(self.D, self.E),
            0xe5: lambda: self.push_nn(self.H, self.L),
            0xf1: lambda: self.pop_nn(self.A, self.F),
            0xc1: lambda: self.pop_nn(self.B, self.C),
            0xd1: lambda: self.pop_nn(self.D, self.E),
            0xe1: lambda: self.pop_nn(self.H, self.L),
            0x87: lambda: self.add_a_n(self.A, add_carry=False),
            0x80: lambda: self.add_a_n(self.B, add_carry=False),
            0x81: lambda: self.add_a_n(self.C, add_carry=False),
            0x82: lambda: self.add_a_n(self.D, add_carry=False),
            0x83: lambda: self.add_a_n(self.E, add_carry=False),
            0x84: lambda: self.add_a_n(self.H, add_carry=False),
            0x85: lambda: self.add_a_n(self.L, add_carry=False),
            0x86: lambda: self.add_a_n(self.HL, add_carry=False),
            0xc6: lambda: self.add_a_n(self.N, add_carry=False),
            0x8f: lambda: self.add_a_n(self.A, add_carry=True),
            0x88: lambda: self.add_a_n(self.B, add_carry=True),
            0x89: lambda: self.add_a_n(self.C, add_carry=True),
            0x8a: lambda: self.add_a_n(self.D, add_carry=True),
            0x8b: lambda: self.add_a_n(self.E, add_carry=True),
            0x8c: lambda: self.add_a_n(self.H, add_carry=True),
            0x8d: lambda: self.add_a_n(self.L, add_carry=True),
            0x8e: lambda: self.add_a_n(self.HL, add_carry=True),
            0xce: lambda: self.add_a_n(self.N, add_carry=True),
            0x97: lambda: self.sub_a_n(self.A, sub_carry=False),
            0x90: lambda: self.sub_a_n(self.B, sub_carry=False),
            0x91: lambda: self.sub_a_n(self.C, sub_carry=False),
            0x92: lambda: self.sub_a_n(self.D, sub_carry=False),
            0x93: lambda: self.sub_a_n(self.E, sub_carry=False),
            0x94: lambda: self.sub_a_n(self.H, sub_carry=False),
            0x95: lambda: self.sub_a_n(self.L, sub_carry=False),
            0x96: lambda: self.sub_a_n(self.HL, sub_carry=False),
            0xd6: lambda: self.sub_a_n(self.N, sub_carry=False),
            0x9f: lambda: self.sub_a_n(self.A, sub_carry=True),
            0x98: lambda: self.sub_a_n(self.B, sub_carry=True),
            0x99: lambda: self.sub_a_n(self.C, sub_carry=True),
            0x9a: lambda: self.sub_a_n(self.D, sub_carry=True),
            0x9b: lambda: self.sub_a_n(self.E, sub_carry=True),
            0x9c: lambda: self.sub_a_n(self.H, sub_carry=True),
            0x9d: lambda: self.sub_a_n(self.L, sub_carry=True),
            0x9e: lambda: self.sub_a_n(self.HL, sub_carry=True),
            0xa7: lambda: self.and_n(self.A),
            0xa0: lambda: self.and_n(self.B),
            0xa1: lambda: self.and_n(self.c),
            0xa2: lambda: self.and_n(self.D),
            0xa3: lambda: self.and_n(self.E),
            0xa4: lambda: self.and_n(self.H),
            0xa5: lambda: self.and_n(self.L),
            0xa6: lambda: self.and_n(self.HL),
            0xe6: lambda: self.and_n(self.N),
            0xb7: lambda: self.or_n(self.A, exclusive_or=False),
            0xb0: lambda: self.or_n(self.B, exclusive_or=False),
            0xb1: lambda: self.or_n(self.C, exclusive_or=False),
            0xb2: lambda: self.or_n(self.D, exclusive_or=False),
            0xb3: lambda: self.or_n(self.E, exclusive_or=False),
            0xb4: lambda: self.or_n(self.H, exclusive_or=False),
            0xb5: lambda: self.or_n(self.L, exclusive_or=False),
            0xb6: lambda: self.or_n(self.HL, exclusive_or=False), 
            0xf6: lambda: self.or_n(self.N, exclusive_or=False),
            0xaf: lambda: self.or_n(self.A, exclusive_or=True),
            0xa8: lambda: self.or_n(self.B, exclusive_or=True),
            0xa9: lambda: self.or_n(self.C, exclusive_or=True),
            0xaa: lambda: self.or_n(self.D, exclusive_or=True),
            0xab: lambda: self.or_n(self.E, exclusive_or=True),
            0xac: lambda: self.or_n(self.H, exclusive_or=True),
            0xad: lambda: self.or_n(self.L, exclusive_or=True),
            0xae: lambda: self.or_n(self.HL, exclusive_or=True),
            0xee: lambda: self.or_n(self.N, exclusive_or=True),
            0xbf: lambda: self.cp_n(self.A),
            0xb8: lambda: self.cp_n(self.B),
            0xb9: lambda: self.cp_n(self.C),
            0xba: lambda: self.cp_n(self.D),
            0xbb: lambda: self.cp_n(self.E),
            0xbc: lambda: self.cp_n(self.F),
            0xbd: lambda: self.cp_n(self.L),
            0xbe: lambda: self.cp_n(self.HL),
            0xfe: lambda: self.cp_n(self.N),
            0x3c: lambda: self.inc_n(self.A),
            0x04: lambda: self.inc_n(self.B),
            0x0c: lambda: self.inc_n(self.C),
            0x14: lambda: self.inc_n(self.D),
            0x1c: lambda: self.inc_n(self.E),
            0x24: lambda: self.inc_n(self.H),
            0x2c: lambda: self.inc_n(self.L),
            0x34: lambda: self.inc_n(self.HL),
            0x3d: lambda: self.dec_n(self.A),
            0x05: lambda: self.dec_n(self.B),
            0x0d: lambda: self.dec_n(self.C),
            0x15: lambda: self.dec_n(self.D),
            0x1d: lambda: self.dec_n(self.E),
            0x25: lambda: self.dec_n(self.H),
            0x2d: lambda: self.dec_n(self.L),
            0x35: lambda: self.dec_n(self.HL),
            0x09: lambda: self.add_hl(self.B, self.C, add_sp=False),
            0x19: lambda: self.add_hl(self.D, self.E, add_sp=False),
            0x29: lambda: self.add_hl(self.H, self.L, add_sp=False),
            0x39: lambda: self.add_hl(self.B, self.C, add_sp=True),
            0xe8: lambda: self.add_sp_n(),
            0x03: lambda: self.inc_nn(self.B, self.C, inc_sp=False),
            0x13: lambda: self.inc_nn(self.D, self.E, inc_sp=False),
            0x23: lambda: self.inc_nn(self.H, self.L, inc_sp=False),
            0x33: lambda: self.inc_nn(self.B, self.C, inc_sp=True),
            0x0b: lambda: self.dec_nn(self.B, self.C, dec_sp=False),
            0x1b: lambda: self.dec_nn(self.D, self.E, dec_sp=False),
            0x2b: lambda: self.dec_nn(self.H, self.L, dec_sp=False),
            0x3b: lambda: self.dec_nn(self.B, self.C, dec_sp=True),
            0xc3: lambda: self.jump_nn(),
            0xc2: lambda: self.jump_cc(False, self.flags.Z, immmediate_jump=False),
            0xca: lambda: self.jump_cc(True, self.flags.Z, immmediate_jump=False),
            0xd2: lambda: self.jump_cc(False, self.flags.C, immmediate_jump=False),
            0xda: lambda: self.jump_cc(True, self.flags.C, immmediate_jump=False),
            0xe9: lambda: self.jump_hl(),
            0x18: lambda: self.jump_n(),
            0x20: lambda: self.jump_cc(False, self.flags.Z, immmediate_jump=True),
            0x28: lambda: self.jump_cc(True, self.flags.Z, immmediate_jump=True),
            0x30: lambda: self.jump_cc(False, self.flags.C, immmediate_jump=True),
            0x38: lambda: self.jump_cc(True, self.flags.C, immmediate_jump=True),
            0x27: lambda: self.dec_adjust(),
            0x2f: lambda: self.complement_a(),
            0x3f: lambda: self.complement_cf(),
            0x37: lambda: self.set_cf(),
            0x07: lambda: self.rotate_l_a_c(),
            0x17: lambda: self.rotate_l_a(),
            0x0f: lambda: self.rotate_r_a_c(),
            0x1f: lambda: self.rotate_r_a(),
            0xcd: lambda: self.call(),
            0xc4: lambda: self.call_cc(self.flags.Z, False),
            0xcc: lambda: self.call_cc(self.flags.Z, True),
            0xd4: lambda: self.call_cc(self.flags.C, False),
            0xdc: lambda: self.call_cc(self.flags.C, True),
            0xc9: lambda: self.ret(),
            0xc0: lambda: self.ret_cc(self.flags.N, False),
            0xc8: lambda: self.ret_cc(self.flags.N, True),
            0xd0: lambda: self.ret_cc(self.flags.C, False),
            0xd8: lambda: self.ret_cc(self.flags.C, True),
            0x10: lambda: self.stop()
        }
        self.ext_opcodes = {
            0x3f: lambda: self.srl_n(self.A, False),
            0x38: lambda: self.srl_n(self.B, False),
            0x39: lambda: self.srl_n(self.C, False),
            0x3a: lambda: self.srl_n(self.D, False),
            0x3b: lambda: self.srl_n(self.E, False),
            0x3c: lambda: self.srl_n(self.H, False),
            0x3d: lambda: self.srl_n(self.L, False),
            0x3e: lambda: self.srl_n(self.HL, False),
            0x2f: lambda: self.srl_n(self.A, True),
            0x28: lambda: self.srl_n(self.B, True),
            0x29: lambda: self.srl_n(self.C, True),
            0x2a: lambda: self.srl_n(self.D, True),
            0x2b: lambda: self.srl_n(self.E, True),
            0x2c: lambda: self.srl_n(self.H, True),
            0x2d: lambda: self.srl_n(self.L, True),
            0x2e: lambda: self.srl_n(self.HL, True),
            0x1f: lambda: self.rr_n(self.A),
            0x18: lambda: self.rr_n(self.B),
            0x19: lambda: self.rr_n(self.C),
            0x1a: lambda: self.rr_n(self.D),
            0x1b: lambda: self.rr_n(self.E),
            0x1c: lambda: self.rr_n(self.H),
            0x1d: lambda: self.rr_n(self.L),
            0x1e: lambda: self.rr_n(self.HL),
            0x37: lambda: self.swap(self.A),
            0x30: lambda: self.swap(self.B),
            0x31: lambda: self.swap(self.C),
            0x32: lambda: self.swap(self.D),
            0x33: lambda: self.swap(self.E),
            0x34: lambda: self.swap(self.H),
            0x35: lambda: self.swap(self.L),
            0x36: lambda: self.swap(self.HL),

            0x27: lambda: self.sla_n(self.A),   
            0x20: lambda: self.sla_n(self.B),
            0x21: lambda: self.sla_n(self.C),
            0x22: lambda: self.sla_n(self.D),
            0x23: lambda: self.sla_n(self.E),
            0x24: lambda: self.sla_n(self.H),
            0x25: lambda: self.sla_n(self.L),
            0x26: lambda: self.sla_n(self.HL),
            
            0x07: lambda: self.rotate_n_lc(self.A), 
            0x00: lambda: self.rotate_n_lc(self.B),
            0x01: lambda: self.rotate_n_lc(self.C),
            0x02: lambda: self.rotate_n_lc(self.D),
            0x03: lambda: self.rotate_n_lc(self.E),
            0x04: lambda: self.rotate_n_lc(self.H),
            0x05: lambda: self.rotate_n_lc(self.L),
            0x06: lambda: self.rotate_n_lc(self.HL),




            0x17: lambda: self.rotate_l_n(self.A),
            0x10: lambda: self.rotate_l_n(self.B), 
            0x11: lambda: self.rotate_l_n(self.C), 
            0x12: lambda: self.rotate_l_n(self.D), 
            0x13: lambda: self.rotate_l_n(self.E), 
            0x14: lambda: self.rotate_l_n(self.H), 
            0x15: lambda: self.rotate_l_n(self.L), 
            0x16: lambda: self.rotate_l_n(self.HL),

            0x0f: lambda: self.rrc_n(self.A),
            0x08: lambda: self.rrc_n(self.B), 
            0x09: lambda: self.rrc_n(self.C), 
            0x0a: lambda: self.rrc_n(self.D), 
            0x0b: lambda: self.rrc_n(self.E), 
            0x0c: lambda: self.rrc_n(self.H), 
            0x0d: lambda: self.rrc_n(self.L), 
            0x0e: lambda: self.rrc_n(self.HL),



            0x47: lambda: self.bit_br(0, self.A),
            0x40: lambda: self.bit_br(0, self.B),
            0x41: lambda: self.bit_br(0, self.C),
            0x42: lambda: self.bit_br(0, self.D),
            0x43: lambda: self.bit_br(0, self.E),
            0x44: lambda: self.bit_br(0, self.H),
            0x45: lambda: self.bit_br(0, self.L),
            0x46: lambda: self.bit_br(0, self.HL),
            0x4f: lambda: self.bit_br(1, self.A),
            0x48: lambda: self.bit_br(1, self.B),
            0x49: lambda: self.bit_br(1, self.C),
            0x4a: lambda: self.bit_br(1, self.D),
            0x4b: lambda: self.bit_br(1, self.E),
            0x4c: lambda: self.bit_br(1, self.H),
            0x4d: lambda: self.bit_br(1, self.L),
            0x4e: lambda: self.bit_br(1, self.HL),
            0x57: lambda: self.bit_br(2, self.A),
            0x50: lambda: self.bit_br(2, self.B),
            0x51: lambda: self.bit_br(2, self.C),
            0x52: lambda: self.bit_br(2, self.D),
            0x53: lambda: self.bit_br(2, self.E),
            0x54: lambda: self.bit_br(2, self.H),
            0x55: lambda: self.bit_br(2, self.L),
            0x56: lambda: self.bit_br(2, self.HL),
            0x5f: lambda: self.bit_br(3, self.A),
            0x58: lambda: self.bit_br(3, self.B),
            0x59: lambda: self.bit_br(3, self.C),
            0x5a: lambda: self.bit_br(3, self.D),
            0x5b: lambda: self.bit_br(3, self.E),
            0x5c: lambda: self.bit_br(3, self.H),
            0x5d: lambda: self.bit_br(3, self.L),
            0x5e: lambda: self.bit_br(3, self.HL),

            0x67: lambda: self.bit_br(4, self.A),
            0x60: lambda: self.bit_br(4, self.B),
            0x61: lambda: self.bit_br(4, self.C),
            0x62: lambda: self.bit_br(4, self.D),
            0x63: lambda: self.bit_br(4, self.E),
            0x64: lambda: self.bit_br(4, self.H),
            0x65: lambda: self.bit_br(4, self.L),
            0x66: lambda: self.bit_br(4, self.HL),
            0x6f: lambda: self.bit_br(5, self.A),
            0x68: lambda: self.bit_br(5, self.B),
            0x69: lambda: self.bit_br(5, self.C),
            0x6a: lambda: self.bit_br(5, self.D),
            0x6b: lambda: self.bit_br(5, self.E),
            0x6c: lambda: self.bit_br(5, self.H),
            0x6d: lambda: self.bit_br(5, self.L),
            0x6e: lambda: self.bit_br(5, self.HL),
            0x77: lambda: self.bit_br(6, self.A),
            0x70: lambda: self.bit_br(6, self.B),
            0x71: lambda: self.bit_br(6, self.C),
            0x72: lambda: self.bit_br(6, self.D),
            0x73: lambda: self.bit_br(6, self.E),
            0x74: lambda: self.bit_br(6, self.H),
            0x75: lambda: self.bit_br(6, self.L),
            0x76: lambda: self.bit_br(6, self.HL),
            0x7f: lambda: self.bit_br(7, self.A),
            0x78: lambda: self.bit_br(7, self.B),
            0x79: lambda: self.bit_br(7, self.C),
            0x7a: lambda: self.bit_br(7, self.D),
            0x7b: lambda: self.bit_br(7, self.E),
            0x7c: lambda: self.bit_br(7, self.H),
            0x7d: lambda: self.bit_br(7, self.L),
            0x7e: lambda: self.bit_br(7, self.HL),

            0xc7: lambda: self.set_b_r(self.A, 0, 1),
            0xc0: lambda: self.set_b_r(self.B, 0, 1),
            0xc1: lambda: self.set_b_r(self.C, 0, 1),
            0xc2: lambda: self.set_b_r(self.D, 0, 1),
            0xc3: lambda: self.set_b_r(self.E, 0, 1),
            0xc4: lambda: self.set_b_r(self.H, 0, 1),
            0xc5: lambda: self.set_b_r(self.L, 0, 1),
            0xc6: lambda: self.set_b_r(self.HL, 0, 1),
            0xcf: lambda: self.set_b_r(self.A, 1, 1),
            0xc8: lambda: self.set_b_r(self.B, 1, 1),
            0xc9: lambda: self.set_b_r(self.C, 1, 1),
            0xca: lambda: self.set_b_r(self.D, 1, 1),
            0xcb: lambda: self.set_b_r(self.E, 1, 1),
            0xcc: lambda: self.set_b_r(self.H, 1, 1),
            0xcd: lambda: self.set_b_r(self.L, 1, 1),
            0xce: lambda: self.set_b_r(self.HL, 1, 1),
            0xd7: lambda: self.set_b_r(self.A, 2, 1),
            0xd0: lambda: self.set_b_r(self.B, 2, 1),
            0xd1: lambda: self.set_b_r(self.C, 2, 1),
            0xd2: lambda: self.set_b_r(self.D, 2, 1),
            0xd3: lambda: self.set_b_r(self.E, 2, 1),
            0xd4: lambda: self.set_b_r(self.H, 2, 1),
            0xd5: lambda: self.set_b_r(self.L, 2, 1),
            0xd6: lambda: self.set_b_r(self.HL, 2, 1),
            0xdf: lambda: self.set_b_r(self.A, 3, 1),
            0xd8: lambda: self.set_b_r(self.B, 3, 1),
            0xd9: lambda: self.set_b_r(self.C, 3, 1),
            0xda: lambda: self.set_b_r(self.D, 3, 1),
            0xdb: lambda: self.set_b_r(self.E, 3, 1),
            0xdc: lambda: self.set_b_r(self.H, 3, 1),
            0xdd: lambda: self.set_b_r(self.L, 3, 1),
            0xde: lambda: self.set_b_r(self.HL, 3, 1),
            0xe7: lambda: self.set_b_r(self.A, 4, 1),
            0xe0: lambda: self.set_b_r(self.B, 4, 1),
            0xe1: lambda: self.set_b_r(self.C, 4, 1),
            0xe2: lambda: self.set_b_r(self.D, 4, 1),
            0xe3: lambda: self.set_b_r(self.E, 4, 1),
            0xe4: lambda: self.set_b_r(self.H, 4, 1),
            0xe5: lambda: self.set_b_r(self.L, 4, 1),
            0xe6: lambda: self.set_b_r(self.HL, 4, 1),
            0xef: lambda: self.set_b_r(self.A, 5, 1),
            0xe8: lambda: self.set_b_r(self.B, 5, 1),
            0xe9: lambda: self.set_b_r(self.C, 5, 1),
            0xea: lambda: self.set_b_r(self.D, 5, 1),
            0xeb: lambda: self.set_b_r(self.E, 5, 1),
            0xec: lambda: self.set_b_r(self.H, 5, 1),
            0xed: lambda: self.set_b_r(self.L, 5, 1),
            0xee: lambda: self.set_b_r(self.HL, 5, 1),
            0xf7: lambda: self.set_b_r(self.A, 6, 1),
            0xf0: lambda: self.set_b_r(self.B, 6, 1),
            0xf1: lambda: self.set_b_r(self.C, 6, 1),
            0xf2: lambda: self.set_b_r(self.D, 6, 1),
            0xf3: lambda: self.set_b_r(self.E, 6, 1),
            0xf4: lambda: self.set_b_r(self.H, 6, 1),
            0xf5: lambda: self.set_b_r(self.L, 6, 1),
            0xf6: lambda: self.set_b_r(self.HL, 6, 1),
            0xff: lambda: self.set_b_r(self.A, 7, 1),
            0xf8: lambda: self.set_b_r(self.B, 7, 1),
            0xf9: lambda: self.set_b_r(self.C, 7, 1),
            0xfa: lambda: self.set_b_r(self.D, 7, 1),
            0xfb: lambda: self.set_b_r(self.E, 7, 1),
            0xfc: lambda: self.set_b_r(self.H, 7, 1),
            0xfd: lambda: self.set_b_r(self.L, 7, 1),
            0xfe: lambda: self.set_b_r(self.HL, 7, 1),
            0x87: lambda: self.set_b_r(self.A, 0, 0),
            0x80: lambda: self.set_b_r(self.B, 0, 0),
            0x81: lambda: self.set_b_r(self.C, 0, 0),
            0x82: lambda: self.set_b_r(self.D, 0, 0),
            0x83: lambda: self.set_b_r(self.E, 0, 0),
            0x84: lambda: self.set_b_r(self.H, 0, 0),
            0x85: lambda: self.set_b_r(self.L, 0, 0),
            0x86: lambda: self.set_b_r(self.HL, 0, 0),
            0x8f: lambda: self.set_b_r(self.A, 1, 0),
            0x88: lambda: self.set_b_r(self.B, 1, 0),
            0x89: lambda: self.set_b_r(self.C, 1, 0),
            0x8a: lambda: self.set_b_r(self.D, 1, 0),
            0x8b: lambda: self.set_b_r(self.E, 1, 0),
            0x8c: lambda: self.set_b_r(self.H, 1, 0),
            0x8d: lambda: self.set_b_r(self.L, 1, 0),
            0x8e: lambda: self.set_b_r(self.HL, 1, 0),
            0x97: lambda: self.set_b_r(self.A, 2, 0),
            0x90: lambda: self.set_b_r(self.B, 2, 0),
            0x91: lambda: self.set_b_r(self.C, 2, 0),
            0x92: lambda: self.set_b_r(self.D, 2, 0),
            0x93: lambda: self.set_b_r(self.E, 2, 0),
            0x94: lambda: self.set_b_r(self.H, 2, 0),
            0x95: lambda: self.set_b_r(self.L, 2, 0),
            0x96: lambda: self.set_b_r(self.HL, 2, 0),
            0x9f: lambda: self.set_b_r(self.A, 3, 0),
            0x98: lambda: self.set_b_r(self.B, 3, 0),
            0x99: lambda: self.set_b_r(self.C, 3, 0),
            0x9a: lambda: self.set_b_r(self.D, 3, 0),
            0x9b: lambda: self.set_b_r(self.E, 3, 0),
            0x9c: lambda: self.set_b_r(self.H, 3, 0),
            0x9d: lambda: self.set_b_r(self.L, 3, 0),
            0x9e: lambda: self.set_b_r(self.HL, 3, 0),
            0xa7: lambda: self.set_b_r(self.A, 4, 0),
            0xa0: lambda: self.set_b_r(self.B, 4, 0),
            0xa1: lambda: self.set_b_r(self.C, 4, 0),
            0xa2: lambda: self.set_b_r(self.D, 4, 0),
            0xa3: lambda: self.set_b_r(self.E, 4, 0),
            0xa4: lambda: self.set_b_r(self.H, 4, 0),
            0xa5: lambda: self.set_b_r(self.L, 4, 0),
            0xa6: lambda: self.set_b_r(self.HL, 4, 0),
            0xaf: lambda: self.set_b_r(self.A, 5, 0),
            0xa8: lambda: self.set_b_r(self.B, 5, 0),
            0xa9: lambda: self.set_b_r(self.C, 5, 0),
            0xaa: lambda: self.set_b_r(self.D, 5, 0),
            0xab: lambda: self.set_b_r(self.E, 5, 0),
            0xac: lambda: self.set_b_r(self.H, 5, 0),
            0xad: lambda: self.set_b_r(self.L, 5, 0),
            0xae: lambda: self.set_b_r(self.HL, 5, 0),
            0xb7: lambda: self.set_b_r(self.A, 6, 0),
            0xb0: lambda: self.set_b_r(self.B, 6, 0),
            0xb1: lambda: self.set_b_r(self.C, 6, 0),
            0xb2: lambda: self.set_b_r(self.D, 6, 0),
            0xb3: lambda: self.set_b_r(self.E, 6, 0),
            0xb4: lambda: self.set_b_r(self.H, 6, 0),
            0xb5: lambda: self.set_b_r(self.L, 6, 0),
            0xb6: lambda: self.set_b_r(self.HL, 6, 0),
            0xbf: lambda: self.set_b_r(self.A, 7, 0),
            0xb8: lambda: self.set_b_r(self.B, 7, 0),
            0xb9: lambda: self.set_b_r(self.C, 7, 0),
            0xba: lambda: self.set_b_r(self.D, 7, 0),
            0xbb: lambda: self.set_b_r(self.E, 7, 0),
            0xbc: lambda: self.set_b_r(self.H, 7, 0),
            0xbd: lambda: self.set_b_r(self.L, 7, 0),
            0xbe: lambda: self.set_b_r(self.HL, 7, 0)
        }

    def save_state(self, name, session):
        """
        Save the cpu state into the SQLAlchemy session session.

        ...
        Parameters
        ----------
        name : string
            name to associate with the save
        session : A SQLAlchemy Session object
            session to save the state in

        Returns
        -------
        Human readable error message, or None on success
        """
        pickledregisters = pickle.dumps(self.reg)
        cpu_state = CpuState(savename=name, stack_ptr=self.sp,
                             program_ctr=self.pc,
                             gbregisters=pickledregisters)
        session.add(cpu_state)
        session.commit()

    def execute_boot_opcode(self, num=1):
        """
        Executes an opcode of the booting sequence, takes
        ????? instructions to complete.
        Reads instructions with mem.read_bios() instead
        of from normal memory.

        Returns
        -------
        int
            number of clock cycles taken
        """
        if self.pc >= 0x100:
            log.info("BIOS COMPLETE!")
            self.dump_registers()
            quit()
        opcode = self.mem.read_bios(self.pc)
        self.pc += 1
        try:
            #log.info("executing: " + hex(opcode) + " @ " + hex(self.pc - 1))
            cycles = self.opcodes[opcode]()
        except KeyError:
            log.critical('INVALID OPCODE ' + hex(opcode) + ' @ ' + hex(self.pc))
            cycles = 0

        return cycles

    def execute_opcode(self, num=1):
        """
        Executes num number of opcode instructions.

        ...
        Parameters
        ----------
        num : int
            number of opcode instructions to execute

        Returns
        -------
        int
            number of clock cycles taken to execute

        """
        opcode = self.mem.read(self.pc)
        self.pc += 1
        try:
            cycles = self.opcodes[opcode]()
        except KeyError:
            log.critical('INVALID OPCODE ' + hex(opcode) + ' @ ' + hex(self.pc))
            cycles = 0
        if cycles == None:
            print(hex(opcode))
        return cycles

    def extended_opcode(self):
        """
        Extended opcodes.

        Returns
        -------
        int
            number of cycles taken
        """
        opcode = self.mem.read(self.pc)
        self.pc += 1
        try:
            cycles = self.ext_opcodes[opcode]()
        except KeyError:
            log.critical('EXTENDED INVALID OPCODE ' + hex(opcode) + ' @ ' + hex(self.pc))
            cycles = 0
        return cycles

    def NOP(self):
        """ No operation """
        return 4

    def ld_byte_n(self, reg_index):
        """
        Load a byte from memory into register.
        Byte is located at pc.

        ...
        Parameters
        ----------
        reg_index : int
            index of reg to load

        """
        self.reg[reg_index] = self.mem.read(self.pc)
        self.pc += 1
        return 8

    def ld_r1_r2(self, r1, r2):
        """
        Put value r2 into r1.

        r1,r2 = A,B,C,D,E,H,L,(HL)

        ...
        Parameters
        ----------
        r1 : int
            index of r1
        r2 : int
            index of r2
        """
        if r2 != self.HL and r1 != self.HL:
            self.reg[r1] = self.reg[r2]
            return 4
        elif r2 == self.HL:
            self.reg[r1] = self.mem.read(self.get_reg(self.H, self.L))
            return 8
        elif r2 == self.N:
            self.mem.write(self.mem.read(self.pc), self.get_reg(self.H, self.L))
            self.pc += 1
            return 12
        else:
            self.mem.write(self.reg[r2], self.get_reg(self.H, self.L))
            return 8

    def load_a(self, src):
        """
        Put value src into A.

        src = (BC/DE/nn), n
        ...
        Parameters 
        ----------
        src
            which src to load into a
        """
        if src == self.BC:
            self.reg[self.A] = self.mem.read(self.get_reg(self.B, self.C))
            return 8
        elif src == self.DE:
            self.reg[self.A] = self.mem.read(self.get_reg(self.D, self.E))
            return 8
        elif src == self.NN:
            self.reg[self.A] = self.mem.read(self.mem.read_word(self.pc))
            self.pc += 2
            return 16
        else: #self.N
            self.reg[self.A] = self.mem.read(self.pc)
            self.pc += 1
            return 8

    def write_a(self, dest):
        """
        Put value A into dest.

        ...
        Parameters
        ----------
        dest : A-L, (BC/DE/HL/nn)
            place to store A
        """
        if dest == self.BC:
            self.mem.write(self.reg[self.A], self.get_reg(self.B, self.C))
            return 8
        elif dest == self.DE:
            self.mem.write(self.reg[self.A], self.get_reg(self.D, self.E))
            return 8
        elif dest == self.HL:
            self.mem.write(self.reg[self.A], self.get_reg(self.H, self.L))
            return 8
        elif dest == self.NN:
            self.mem.write(self.reg[self.A], self.mem.read_word(self.pc))
            self.pc += 2
            return 16
        else: 
            self.reg[dest] = self.reg[self.A]
            return 4

    def load_a_c(self, store=False):
        """
        Load A, (C) - put value at 0xff00 + regC into A, or
        Put A into address 0xff00 + regC
        
        ...
        Parameters
        ----------
        store : bool
            False - Put value 0xff00 + regC into A
            True  - store A at 0xff00 + regC
        
        Returns
        -------
        int
            num of cycles
        """
        if store:
            self.mem.write(self.reg[self.A], self.reg[self.C] + 0xff00)
        else:
            self.reg[self.A] = self.mem.read(self.reg[self.C] + 0xff00)
        return 8

    def load_a_hl(self, dec, load):
        """
        Store/load A in (HL), or (HL) in A, increment/decrement HL.

        ...
        Parameters
        ----------
        dec : bool
            Decrement register HL if True, increments if False
        load : bool
            Load value at (HL) into A if true
            Store A at (HL) if false

        Returns
        -------
        int 
            num of cycles
        """
        if load:
            self.reg[self.A] = self.mem.read(self.get_reg(self.H, self.L))
        else:
            self.mem.write(self.reg[self.A], self.get_reg(self.H, self.L))
        HL_val = self.get_reg(self.H, self.L)
        HL_val += -1 if dec else 1
        self.set_reg(self.H, self.L, HL_val)
        return 8

    def a_n(self, store):
        """
        Store/load A in memory address 0xff00 + n

        Parameters
        ----------
        store : bool
            if true writes, if false loads
        Returns
        -------
        int
            num of cycles
        """
        offset = self.mem.read(self.pc)
        self.pc += 1
        if store:
            self.mem.write(self.reg[self.A], offset + 0xff00)
        else:
            self.reg[self.A] = self.mem.read(offset + 0xff00)
        return 12

    def ld_nn(self, dest, set_sp=False):
        """
        Put value nn into dest.

        Dest = BC/DE/HL/SP

        Parameters
        ----------
        dest : int
            destination register pair (defined in class constants)
            if not self.BC/DE/HL defaults to setting stack pointer
        set_sp : bool
            if True, loads value into stack pointer
            if False, doesnt

        Returns
        -------
        int 
            num of cycles
        """
        word = self.mem.read_word(self.pc)
        self.pc += 2
        if set_sp:
            self.sp = word
            return 12
        elif dest == self.BC:
            r1 = self.B
            r2 = self.C
        elif dest == self.DE:
            r1 = self.D
            r2 = self.E
        elif dest == self.HL:
            r1 = self.H
            r2 = self.L
        self.set_reg(r1, r2, word)
        return 12

    def ld_sp_hl(self):
        """
        Put HL into sp.

        Returns
        -------
        int
            number of cycles
        """
        self.sp = self.get_reg(self.H, self.L)
        return 8

    def ldhl_sp(self):
        """
        Put sp + n effective address into HL.
        n = one byte signed value
        
        Flags:
        Z/N - Reset
        H/C - Set/Reset according to operation
        """
        #interpret as signed byte
        n = c_int8(self.mem.read(self.sp)).value
        self.set_reg(self.H, self.L, self.sp + n)

        self.reset_flags()
        if (self.sp & 0xf) + (n & 0xf) > 0xf:
            self.set_flag(self.flags.H)
        if (self.sp & 0xff) + (n & 0xff) > 0xff:
            self.set_flag(self.flags.C)
        return 12

    def ld_nn_sp(self):
        """
        Put sp at address nn (two byte immediate address).
        
        Returns
        -------
        int
            number of clock cycles
        """
        address = self.mem.read_word(self.pc)
        self.pc += 2
        self.mem.write(self.sp & 0xff, address)
        self.mem.write((self.sp & 0xff00) >> 8, address + 1)
        return 20


    def push_nn(self, r1, r2):
        """
        Push register pair r1r2 onto stack.
        Decrement sp twice.

        Parameters
        ----------
        r1, r2
            register pair r1r2
        """
        self.sp -= 1
        self.mem.write(self.reg[r1], self.sp)
        self.sp -= 1
        self.mem.write(self.reg[r2], self.sp)
        return 16

    def pop_nn(self, r1, r2):
        """
        Pop two bytes off stack into register pair r1r2.
        Increment sp twice.

        Parameters
        ----------
            r1 
                reg1
            r2
                reg2
        """
        self.reg[r2] = self.mem.read(self.sp)
        if r2 == self.F:
            self.reg[r2] &= 0xf0
        self.sp += 1
        self.reg[r1] = self.mem.read(self.sp)
        self.sp += 1
        return 12


    def set_reg(self, r1, r2, word):
        """
        set register pair r1r2 to 16 bit word.

        Parameters
        ----------
        r1,r2 : ints
            indexes of r1 r2 registers to set
            r1 = H, r2 = L sets pair HL
        """
        self.reg[r1] = (word & 0xff00) >> 8
        self.reg[r2] = word & 0xff
        

    def get_reg(self, r1, r2):
        """
        Access register r1r2 - combination of r1 and r1 registers.
        For example get_reg(H,L) accesses register HL

        ...
        Returns
        -------
        int
            value of HL register
        """
        return ((self.reg[r1] << 8) | self.reg[r2]) 


    def set_flag(self, flag):
        """
        Sets Flag flag in the F register.

        Parameters
        ----------
        flag : Flag enum
            which flag to set
        """
        if flag == self.flags.Z:
            self.reg[self.F] |= 0x80
        elif flag == self.flags.H:
            self.reg[self.F] |= 0x20
        elif flag == self.flags.C:
            self.reg[self.F] |= 0x10
        elif flag == self.flags.N:
            self.reg[self.F] |= 0x40

    def reset_flag(self, flag):
        """
        Resets Flag flag in the F register.

        Parameters
        ----------
        flag : Flag enum
            which flag to reset
        """
        if flag == self.flags.Z:
            self.reg[self.F] &= 0x70
        elif flag == self.flags.H:
            self.reg[self.F] &= 0xd0
        elif flag == self.flags.C:
            self.reg[self.F] &= 0xe0
        elif flag == self.flags.N:
            self.reg[self.F] &= 0xb0

    def flag_set(self, flag):
        """
        Returns True if flag is set
        False if not

        Parameters
        ----------
        flag : Flag enum
            which flag to check

        Returns
        -------
        bool
            True if set, False if not
        """
        if flag == self.flags.Z:
            return self.reg[self.F] & 0x80 != 0
        elif flag == self.flags.H:
            return self.reg[self.F] & 0x20 != 0
        elif flag == self.flags.C:
            return self.reg[self.F] & 0x10 != 0
        elif flag == self.flags.N:
            return self.reg[self.F] & 0x40 != 0

    def add_a_n(self, src, add_carry=False):
        """
        Add n to A (and carry if add_carry is true).
        Flags: 
        Z - Set if zero
        N - Reset
        H - Set if carry from bit 3
        C - Set if carry from bit 7
        
        Parameters
        ----------
        src
            source A-L, (HL), or n

        Returns
        -------
        int 
            clock cycles taken
        """
        a_reg = self.reg[self.A]
        if src == self.N:
            val = self.mem.read(self.pc)
            self.pc += 1
        elif src == self.HL:
            val = self.mem.read(self.get_reg(self.H, self.L))
        else: #src is index of A-L
            val = self.reg[src]
        carry_bit = 1 if add_carry and self.flag_set(self.flags.C) else 0
        
        self.reg[self.A] = (a_reg + carry_bit + val) & 0xff
        self.reset_flags()
        if self.reg[self.A] == 0:
            self.set_flag(self.flags.Z)
        if (a_reg & 0xf) + (val & 0xf) + carry_bit > 0xf:
            self.set_flag(self.flags.H)
        if a_reg + val + carry_bit > 0xff:
            self.set_flag(self.flags.C)

        return 8 if src == self.N or src == self.HL else 4

    def sub_a_n(self, src, sub_carry=False):
        """
        Subtract n from A (n + carry if sub_carry is true)
        Flags:
        Z - Set if 0
        N - Set
        H - Set if no borrow from bit 4
        C - Set if no borrow

        Parameters
        ----------
        src
            source A-L, (HL), or n
        Returns
        -------
        int 
            number of cylces elapsed
        """
        a_reg = self.reg[self.A]
        if src == self.N:
            val = self.mem.read(self.pc)
            self.pc += 1
        elif src == self.HL:
            val = self.mem.read(self.get_reg(self.H, self.L))
        else: #src is index of A-L
            val = self.reg[src]
        carry_bit = 1 if sub_carry and self.flag_set(self.flags.C) else 0

        self.reg[self.A] = (a_reg - val - carry_bit) & 0xff
        self.reset_flags()
        if self.reg[self.A] == 0:
            self.set_flag(self.flags.Z)
        if (a_reg & 0xf) < (val & 0xf) + carry_bit:
            self.set_flag(self.flags.H)
        if a_reg < val + carry_bit:
            self.set_flag(self.flags.C)

        return 8 if src == self.N or src == self.HL else 4

    def and_n(self, src):
        """
        Logically AND n with A, result in A
        Flags:
        Z - Set if result is 0
        N/C - Reset
        H - Set

        Parameters
        ----------
        src
            source A-L, (HL), or n
        Returns
        -------
        int
            number of cycles elapsed
        """
        a_reg = self.reg[self.A]
        if src == self.N:
            val = self.mem.read(self.pc)
            self.pc += 1
        elif src == self.HL:
            val = self.mem.read(self.get_reg(self.H, self.L))
        else: #src is index of A-L
            val = self.reg[src]
        self.reg[self.A] = val & a_reg & 0xff

        self.reset_flags()
        if self.reg[self.A] == 0:
            self.set_flag(self.flags.Z)
        self.set_flag(self.flags.H)

        return 8 if src == self.N or src == self.HL else 4

    def or_n(self, src, exclusive_or=False):
        """
        Logically OR or XOR n with A, result in A.
        Flags:
        Z - Set if 0
        N/H/C - Reset

        Parameters
        ----------
        src
            source A-L, (HL), or n
        exclusive_or
            if True uses exclusive OR not OR
        Returns
        -------
        int 
            number of cycles elapsed
        """
        a_reg = self.reg[self.A]
        if src == self.N:
            val = self.mem.read(self.pc)
            self.pc += 1
        elif src == self.HL:
            val = self.mem.read(self.get_reg(self.H, self.L))
        else: # src is index of A-L
            val = self.reg[src]

        self.reg[self.A] = (a_reg ^ val) if exclusive_or else (a_reg | val)
        self.reg[self.A] &= 0xff
        self.reset_flags()
        if self.reg[self.A] == 0:
            self.set_flag(self.flags.Z)
        
        return 8 if val == self.HL or val == self.N else 4


    def cp_n(self, src):
        """
        Compare A with n (A - n subtraction but results arent saved).
        Flags:
        Z - Set if 0
        N - Set
        H - Set if no borrow from bit 4
        C - Set if no borrow (if A is less than n)

        Parameters
        ----------
        src
            A-L, (HL), N
        Returns
        -------
        int
            number of clock cycles
        """
        a_reg = self.reg[self.A]
        if src == self.N:
            val = self.mem.read(self.pc)
            self.pc += 1
        elif src == self.HL:
            val = self.mem.read(self.get_reg(self.H, self.L))
        else: # src is index
            val = self.reg[src]

        self.reset_flags()
        self.set_flag(self.flags.N)
        if val == a_reg:
            self.set_flag(self.flags.Z)
        if (a_reg & 0xf) < (val & 0xf):
            self.set_flag(self.flags.H)
        if a_reg < val:
            self.set_flag(self.flags.C)

        return 8 if src == self.N or src == self.HL else 4

    def inc_n(self, src):
        """
        Increment register n
        Flags:
        Z - Set if 0
        N - Reset
        H - Set if carry from bit 3
        C - Not affected

        Parameters
        ----------
        src
            A-L, (HL)
        Returns
        -------
        int
            number of cycles
        """
        if src == self.HL:
            val = self.mem.read(self.get_reg(self.H, self.L))
            old_val = val
            self.mem.write(val + 1, self.get_reg(self.H, self.L))
        else: # src is index
            old_val = self.reg[src]
            val = (self.reg[src] + 1) & 0xff
            self.reg[src] = val

        self.set_flag(self.flags.Z) if val == 0 else self.reset_flag(self.flags.Z)
        self.reset_flag(self.flags.N)
        self.set_flag(self.flags.H) if old_val & 0xf == 0xf else self.reset_flag(self.flags.H)

        return 12 if src == self.HL else 4

    def dec_n(self, src):
        """
        Decrement register n.
        Flags:
        Z - Set if 0
        N - Set
        H - Set if no borrow from bit 4
        C - Not affected

        Parameters
        ----------
        src
            A-L, (HL)
        Returns
        -------
        int
            number of cycles
        """
        if src == self.HL:
            val = self.mem.read(self.get_reg(self.H, self.L))
            self.mem.write(val - 1, self.get_reg(self.H, self.L))
        else: # src is index
            val = (self.reg[src] - 1) & 0xff
            self.reg[src] = val

        self.set_flag(self.flags.Z) if val == 0 \
                                    else self.reset_flag(self.flags.Z)
        self.set_flag(self.flags.N)
        self.set_flag(self.flags.H) if (val + 1) & 0xf0 != 0xf0 & val \
                                    else self.reset_flag(self.flags.H)

        return 12 if src == self.HL else 4

    def add_hl(self, r1, r2, add_sp=False):
        """
        Add n to HL.
        Flags:
        Z - Not affected
        N - Reset
        H - Set if carry from bit 11
        C - Set if carry from bit 15

        Parameters
        ----------
        r1, r2
            register index for HL, BC, DE
        add_sp : bool
            if true addes to sp not register pair
        Returns
        -------
        int
            cycles taken
        """
        hl = self.get_reg(self.H, self.L)
        val = self.sp if add_sp else self.get_reg(r1, r2)
        self.set_reg(self.H, self.L, (val  + hl) & 0xffff)

        self.reset_flag(self.flags.N)
        if (val & 0xfff) + (hl & 0xfff) > 0xfff:
            self.set_flag(self.flags.H)
        else:
            self.reset_flag(self.flags.H)
        if val + hl > 0xffff:
            self.set_flag(self.flags.C)
        else:
            self.reset_flag(self.flags.C)

        return 8

    def add_sp_n(self):
        """
        Adds an immediate signed byte to sp.
        Flags:
        Z, N - Reset
        H, C - Set/Reset according to operation 
        NOTE: Specifications vague if this is 8 or 
        16 bit flag addition behavior

        Returns
        -------
        int
            cycles taken
        """
        # read as a signed byte
        val = c_int8(self.mem.read(self.pc)).value
        self.pc += 1

        self.reset_flags()
        if (self.sp & 0xf) + (val & 0xf) > 0xf:
            self.set_flag(self.flags.H)
        if (self.sp & 0xff) + (val & 0xff) > 0xff:
            self.set_flag(self.flags.C)

        self.sp += val
        self.sp &= 0xffff
        return 16

    def inc_nn(self, r1, r2, inc_sp=False):
        """
        Increment register pair r1r2.

        Parameters
        ----------
        r1r2
            register pair r1r2
        inc_sp : Boolean
            if True increments SP not r1r2
        Returns
        -------
        int
            clock cycles taken
        """
        if inc_sp:
            self.sp += 1
            self.sp &= 0xffff
        else:
            val = self.get_reg(r1, r2)
            self.set_reg(r1, r2, (val + 1) & 0xffff)
        return 8

    def dec_nn(self, r1, r2, dec_sp=False):
        """
        Decrement register pair r1r2

        Parameters
        ----------
        r1r2
            register pair r1r2
        dec_sp : boolean
            if True decrements SP not r1r2
        Returns
        -------
        int
            clock cycles taken
        """
        if dec_sp:
            self.sp -= 1
            self.sp &= 0xffff
        else:
            val = self.get_reg(r1, r2)
            self.set_reg(r1, r2, (val - 1) & 0xffff)
        return 8

    def jump_nn(self):
        """
        Jump to nn.
        """
        val = self.mem.read_word(self.pc)
        self.pc = val
        return 12

    def jump_cc(self, isSet, flag, immmediate_jump=False):
        """
        Jump to address n if flag and isSet match
        
        Parameters
        ----------
        isSet : bool
            
        Returns
        -------
        int
            number of cycles
        """
        if self.flag_set(flag) == isSet:
            return self.jump_n() if immmediate_jump else self.jump_nn()

        self.pc += 1
        return 12

    def jump_hl(self):
        """
        Jump to address in HL

        Returns
        -------
        int
            cycles taken
        """
        self.pc = self.get_reg(self.H, self.L)
        return 4

    def jump_n(self):
        """
        Add n to current address and jump to it.

        Returns
        -------
        int 
            cycles taken
        """
        val = c_int8(self.mem.read(self.pc)).value
        self.pc += 1
        self.pc += val
        return 8

    def dec_adjust(self):
        """
        Decimal adjust reg A to a representation of Binary Coded Decimal.
        Flags
        Z - Set if A is zero
        N - Not affected
        H - Reset
        C - Set or reset
        referenced: https://github.com/Dooskington/gamelad

        Returns
        -------
        int
            clock cycles taken
        """
        print("dec adjusting!")
        print(self.count)
        self.count += 1
        a_reg = self.reg[self.A]
        if self.flag_set(self.flags.N):
            if self.flag_set(self.flags.H) or a_reg & 0x0f > 0x09:
                a_reg += 0x06
            if self.flag_set(self.flags.C) or a_reg > 0x9f:
                a_reg += 0x06
        else:
            if self.flag_set(self.flags.H):
                a_reg = (a_reg - 0x06) & 0xff
            if self.flag_set(self.flags.C):
                a_reg -= 0x60
        if a_reg & 0x100 == 0x100:
            self.set_flag(self.flags.C)

        a_reg &= 0xff
        self.reset_flag(self.flags.H)
        self.reset_flag(self.flags.Z)
        if a_reg == 0:
            self.set_flag(self.flags.Z)

        self.reg[self.A] = a_reg
        return 4


    def complement_a(self):
        """
        Complements register A (toggles all bits).
        Flags
        N/H - Set
        C/Z - Not affected

        Returns
        -------
        int     
            number of cycles taken
        """
        self.reg[self.A] ^= 0xff
        self.set_flag(self.flags.N)
        self.set_flag(self.flags.H)
        return 4

    def complement_cf(self):
        """
        Complements the carry flag (toggles it).
        Flags
        Z - Not affected
        H/N - Reset
        C - Toggles
        
        Returns
        -------
        int 
            cycles taken
        """
        if self.flag_set(self.flags.C):
            self.reset_flag(self.flags.C)
        else:
            self.set_flag(self.flags.C)
        self.reset_flag(self.flags.N)
        self.reset_flag(self.flags.H)
        return 4

    def set_cf(self):
        """
        Sets the carry flag.
        Flags
        Z - Not affected
        H/N - Reset
        C - Set

        Returns
        -------
        int 
            cycles taken
        """
        self.set_flag(self.flags.C)
        self.reset_flag(self.flags.H)
        self.reset_flag(self.flags.N)
        return 4

    def rotate_l_a_c(self):
        """
        Rotates A left, old bit 7 to carry flag.

        Flags
        Z - Set if 0 NOTE??? RESET??
        N/H - Reset
        C - Contains old bit 7 data

        Returns
        -------
        int 
            cycles taken
        """
        a_reg = self.reg[self.A]
        msb = (a_reg & 0x80) >> 7

        a_reg <<= 1
        a_reg |= msb

        self.reset_flags()
        if msb == 1:
            self.set_flag(self.flags.C)
        self.reg[self.A] = a_reg & 0xff
        return 4


    def rotate_n_lc(self, src):
        """
        Rotates n left, old bit 7 to carry flag.

        Flags
        Z - Set if 0
        N/H - Reset
        C - Old bit 7 data
        
        ...
        Parameters
        -----------
        src
            A-L, HL
        Returns
        -------
        int 
            cycles taken
        """
        if src == self.HL:
            data = self.mem.read(self.get_reg(self.H, self.L))
        else: 
            data = self.reg[src]
        msb = (data & 0x80) >> 7

        data <<= 1
        data |= msb

        self.reset_flags()
        if msb == 1:
            self.set_flag(self.flags.C)

        if src == self.HL:
            self.mem.write(data, self.get_reg(self.H, self.L))
            return 16
        else: 
            self.reg[src] = data & 0xff
            return 8

    def rotate_l_n(self, src):
        """
        Rotates n left through carry flag.
        src - A-HL
        Flags
        Z - set if 0
        N/H - reset
        C - old bit 7 data

        ...
        Returns
        int
            cycles taken
        """
        if src == self.HL:
            data = self.mem.read(self.get_reg(self.H, self.L))
        else: 
            data = self.reg[src]

        data = self.reg[self.A]
        data <<= 1
        if self.flag_set(self.flags.C):
            data |= 1 # set lsb to C
        self.reset_flags()
        if data & 0x100 == 0x100:
            self.set_flag(self.flags.C)

        if src == self.HL:
            self.mem.write(data, self.get_reg(self.H, self.L))
            return 16
        else: 
            self.reg[src] = data & 0xff
            return 8


    def rotate_l_a(self):
        """
        Rotate A left through carry flag.
        Flags
        Z/N/H - Reset
        C - Old bit 7 data

        Returns
        -------
        int 
            cycles taken
        """
        a_reg = self.reg[self.A]
        a_reg <<= 1
        if self.flag_set(self.flags.C):
            a_reg |= 1 # set lsb to C
        self.reset_flags()
        if a_reg & 0x100 == 0x100:
            self.set_flag(self.flags.C)

        self.reg[self.A] = a_reg & 0xff
        return 4

    def rotate_r_a_c(self):
        """
        Rotates A right, old bit 0 to carry flag.

        Flags:
        C - Old bit 0
        Z/H/N - Reset

        Returns
        -------
        int
            clock cycles taken
        """
        a_reg = self.reg[self.A]
        lsb = a_reg & 0x1

        a_reg >>= 1
        a_reg |= lsb << 7

        self.reset_flags()

        if lsb == 1:
            self.set_flag(self.flags.C)
        self.reg[self.A] = a_reg & 0xff
        return 4

    #TODO??? 0 flag set?
    def rotate_r_a(self):
        """
        Rotate A right through carry flag.

        Flags
        C - Old bit 0
        Z/H/N - Reset

        Returns
        -------
        int 
            cycles taken
        """
        a_reg = self.reg[self.A]
        lsb = a_reg & 0x1

        a_reg >>= 1
        if self.flag_set(self.flags.C):
            a_reg |= 0x80

        self.reset_flags()
        if lsb == 1:
            self.set_flag(self.flags.C)
        self.reg[self.A] = a_reg & 0xff
        return 4

    def rr_n(self, src):
        """
        Rotate n right through Carry Flag

        n = A-L, (HL)
        Flags
        Z - set if 0
        N/H - Reset
        C - Old bit 0
        
        Returns
        -------
        int 
            cycles taken
        """
        if src == self.HL:
            data = self.mem.read(self.get_reg(self.H, self.L))
        else:
            data = self.reg[src]

        lsb = data & 0x1
        carryIn = 1 if self.flag_set(self.flags.C) else 0
        data = (data >> 1) | (carryIn << 7)
        data &= 0xff

        self.reset_flags()
        if data == 0:
            self.set_flag(self.flags.Z)

        if lsb != 0:
            self.set_flag(self.flags.C)

        if src == self.HL:
            self.mem.write(data, self.get_reg(self.H, self.L))
        else:
            self.reg[src] = data

        return 16 if src == self.HL else 8

    def rrc_n(self, src):
        """
        Rotate n right. Old bit 0 to carry flag
        Flags
        Z - Set if 0
        N/H - Reset
        C - Old bit 0 data

        Returns
        int
            cycles taken
        """
        if src == self.HL:
            data = self.mem.read(self.get_reg(self.H, self.L))
        else:
            data = self.reg[src]

        lsb = data & 0x1
        data = (data >> 1) | (lsb << 7)
        data &= 0xff

        self.reset_flags()
        if data == 0:
            self.set_flag(self.flags.Z)
        if lsb == 1:
            self.set_flag(self.flags.C)

        if src == self.HL:
            self.mem.write(data, self.get_reg(self.H, self.L))
        else:
            self.reg[src] = data

        return 8 if src != self.HL else 16

        

    def stop(self):
        """
        TODO
        """
        self.pc += 1
        log.debug("IMPLEMENT STOP")
        return 0

    #TODO
    def disable_interrupts(self):
        """
        #TODO
        """
        log.debug('DISABLE INTERRUPTS TODO')
        return 0
        

    def call(self):
        """
        Push address of next instruction onto stack and then jump to address
        nn.

        Returns
        -------
        int 
            cycles taken
        """
        address = self.mem.read_word(self.pc)
        self.pc += 2
        self.push_pc()
        self.pc = address
        return 12 

    def call_cc(self, flag, isSet):
        """
        Call address n if isSet and flag match

        Returns
        -------
        int
            cycles taken
        """
        if self.flag_set(flag) == isSet:
            return 12 + self.call()
        else:
            self.pc += 2
            return 12
            
    def ret(self):
        """
        Pops two bytes from stack jumps to that address
        
        Returns
        -------
        int
            cycles taken
        """
        self.pc = self.mem.read_word(self.sp)
        self.sp += 2
        return 8 

    def ret_cc(self, flag, isSet):
        """
        Return if isSet and flag match

        Returns
        -------
        int
            cycles taken
        """
        if self.flag_set(flag) == isSet:
            return 4 + self.ret()
        else:
            return 8



    def push_pc(self):
        """
        Pushes current program counter value to the stack
        MSB first
        """
        self.sp -= 1
        self.mem.write((self.pc & 0xff00) >> 8, self.sp)
        self.sp -= 1
        self.mem.write((self.pc & 0xff), self.sp)

            
    def dump_registers(self):
        """
        Prints the current cpu registers and their values to the screen.
        """
        print("A:  ", hex(self.reg[self.A]))
        print("B:  ", hex(self.reg[self.B]))
        print("C:  ", hex(self.reg[self.C]))
        print("D:  ", hex(self.reg[self.D]))       
        print("E:  ", hex(self.reg[self.E]))
        print("F:  ", hex(self.reg[self.F]))
        print("H:  ", hex(self.reg[self.H]))
        print("L:  ", hex(self.reg[self.L]))
        print("PC: ", hex(self.pc))
        print("SP: ", hex(self.sp))

    def reset_flags(self):
        """ Resets all Flags to 0.  """
        self.reg[self.F] = 0


    def sla_n(self, src):
        """
        Shift src left into carry, LSB of n set to 0.

        Flags
        Z - Set if 0
        H/N - Reset
        C - old bit 7 data

        Parameters
        ----------
        src
            A-L, (HL)
        Returns
        -------
        int
            cycles taken
        """
        if src == self.HL:
            data = self.mem.read(self.get_reg(self.H, self.L))
        else:
            data = self.reg[src]

        msb = (data & 0x80) & 0xff
        data <<= 1
        data &= 0xff

        self.reset_flags()
        if data == 0:
            self.set_flag(self.flags.Z)
        if msb != 0:
            self.set_flag(self.flags.C)

        if src == self.HL:
            self.mem.write(data, self.get_reg(self.H, self.L))
        else:
            self.reg[src] = data

        return 8 if src != self.HL else 16
        

    def srl_n(self, src, signed):
        """
        Shift n right into Carry. MSB set to 0 if signed = True, else unchanged
        n : A-L, (HL)
        Flags:
        Z - set if 0
        N/H - Reset
        C - Old bit 0 data

        Parameters
        ----------
        src
            register to shift
        signed
            if True MSB set to 0, if false not changed

        Returns
        -------
        int
            cycles taken
        """
        if src == self.HL:
            data = self.mem.read(self.get_reg(self.H, self.L))
        else:
            data = self.reg[src]

        lsb = data & 0x1
        if signed:
            bit7 = data & 0x80
            data >>= 1 
            data |= bit7
        else:
            data >>= 1
            data &= 0x3f

        self.reset_flags()
        if data == 0:
            self.set_flag(self.flags.Z)
        if lsb == 1:
            self.set_flag(self.flags.C)
        
        if src == self.HL:
            self.mem.write(data, self.get_reg(self.H, self.L))
        else:
            self.reg[src] = data

        return 16 if src == self.HL else 8

    def swap(self, src):
        """
        Swaps the upper and lower nibbles of n.

        n = A-L/(HL)

        Flags
        Z - Set if 0
        N/H/C - Reset

        Parameters
        ----------
        src
            to swap A-L/(HL)

        Returns
        -------
        int
            clock cycles
        """
        if src == self.HL:
            data = self.mem.read(self.get_reg(self.H, self.L))
        else:
            data = self.reg[src]
        
        lower_nibble = data & 0xf
        data = ((data & 0xf0) >> 4) | (lower_nibble << 4)

        self.reset_flags()
        if data == 0x0:
            self.set_flag(self.flags.Z)

        if src == self.HL:
            self.mem.write(data, self.get_reg(self.H, self.L))
        else:
            self.reg[src] = data

        return 16 if src == self.HL else 8


    def bit_br(self, bit, reg):
        """
        Tests bit b in register r.
    
        Flags:
        Z - Set if 0
        N - reset
        H - set
        C - not affected
    
        Returns
        -------
        int 
            number of cycles
        """
        if reg == self.HL:
            data = self.mem.read(self.get_reg(self.H, self.L))
        else:
            data = self.reg[reg]

        self.reset_flag(self.flags.Z)
        if not self.is_set(data, bit):
            self.set_flag(self.flags.Z)
        self.reset_flag(self.flags.N)
        self.set_flag(self.flags.H)

        return 8 if reg == self.HL else 4

    def set_b_r(self, src, bit, new_bit):
        """
        Sets bit bit in src to new_bit.
        """
        if src == self.HL:
            data = self.mem.read(self.get_reg(self.H, self.L))
        else:
            data = self.reg[src]
        data = self.set_bit(data, bit, new_bit)

        return 8 if src == self.HL else 4

    def set_bit(self, num, bit, new_bit):
        """
        Sets bit bit in num to new_bit.
        """
        if new_bit == 1:
            return num | 1 << bit
        else:
            return num & ~(1 << bit)


    def is_set(self, num, bit):
        """
        Tests if bit bit is set in num.

        Returns
        -------
        True if 1
        False if 0
        """
        return ((num >> bit) & 0x1) == 0x1
    

                

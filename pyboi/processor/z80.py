from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, PickleType
from ..base import Base
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
    An implementation of the gameboy's z80 cpu.

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
        self.reg = [0 for _ in range(8)]
        self.A = 0
        self.B = 1
        self.C = 2
        self.D = 3
        self.E = 4
        self.F = 5
        self.H = 6
        self.L = 7
        self.pc = 0x100
        self.sp = 0xfffe
        self.mem = mem
        self.opcodes= {
            0x00: self.NOP
            0x06: self.ld_byte_n(B)
            0x0e: self.ld_byte_n(C)
            0x16: self.ld_byte_n(D)
            0x1e: self.ld_byte_n(E)
            0x26: self.ld_byte_n(H)
            0x2e: self.ld_byte_n(L)
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
        try:
            log.debug('executing: %s' % hex(opcode))
            cycles = self.opcodes[opcode]()
            self.pc += 1
        except KeyError:
            log.critical('INVALID OPCODE EXECUTION ATTEMPT!')
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
        self.reg[reg_index] = self.mem.read(pc)
        pc += 1
        return 8

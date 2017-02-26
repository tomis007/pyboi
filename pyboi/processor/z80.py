from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, PickleType
from ..base import Base
import pickle


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
    registers : list of ints
        registers A-F in the z80 cpu
    pc : int
        program counter
    sp : int
        stack pointer

    """


    def __init__(self):
        """
        __init__ function

        ...
        Refer to Z80 class documentation for attribute info

        """
        self.registers = [0 for _ in range(8)]
        self.pc = 0
        self.sp = 0

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
        pickledregisters = pickle.dumps(self.registers)
        cpu_state = CpuState(savename=name, stack_ptr=self.sp,
                             program_ctr=self.pc,
                             gbregisters=pickledregisters)
        session.add(cpu_state)
        session.commit()

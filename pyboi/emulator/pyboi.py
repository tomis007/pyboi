from ..processor.z80 import Z80
from ..memory.mem import Memory
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..base import Base
import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(name='pyboi')

class Pyboi:
    def __init__(self):
        self.mem = Memory()
        self.z80 = Z80()
        self.engine = create_engine('sqlite:///saved_games.db')
        Base.metadata.create_all(self.engine)
    
    def save(self, save_name):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        self.z80.save_state(save_name, session)

    def load_rom(self, rom):
        self.mem.load_rom(rom)
        for x in range(0x104, 0x134):
            print(hex(self.mem.read(x)))


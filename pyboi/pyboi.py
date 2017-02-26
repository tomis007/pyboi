from processor import Z80
from memory import Memory
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import base
import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(name='pyboi')

class pyboi:
    def __init__(self):
        self.mem = Memory()
        self.z80 = Z80()
    
    def save(self, session):
        self.z80.save_state('game', session)

    def load_rom(self, rom):
        self.mem.load_rom(rom)

if __name__ == "__main__":
    engine = create_engine('sqlite:///saved_games.db')
    base.Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    gameboy = pyboi()
    #gameboy.save(session)
    gameboy.load_rom('tetris.gb')


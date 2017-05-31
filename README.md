#PyBoi

###ABOUT
This is an implementation of a GB/GBC emulator in python. Currently in progress.

###STATUS
STATUS: BLARGG'S CPU TESTS Passes tests: 
* 06-ld r,r 
* 08-misc instrs
* 09-op r,r
* 10-bit ops
* 04-op r,imm
* 05-op rp
* 11-op a,(hl)
* 03-op sp,hl
* 07-jr,jp,call,ret,rst
* 01-special

Failed tests:
* 02-interrupts

###SCREENSHOTS
![alt text][cpu_instr]
![alt text][tetris]
![alt text][kirby]

Installation:

```
git clone https://github.com/tomis007/pyboi.git
cd pyboi
virtualenv -p python3 gb_virtualenv
cd gb_virtualenv/bin
source activate
cd ../../
pip install -r requirements.txt
```

Then copy all your rom files/gb bois file to /roms. To run the emulator:

```
./localboi.py
```

To leave virtualenv
```
deactivate
```
[cpu_instr]: https://github.com/tomis007/pyboi/screenshots/cpu_instr.png
[tetris]: https://github.com/tomis007/pyboi/screenshots/tetris.png
[kirby]: https://github.com/tomis007/pyboi/screenshots/kirby.png



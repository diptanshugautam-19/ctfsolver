Afterglow

Your instance serves the recovered panel flash at:

  http://<your-instance-host>/panel.rom

Download it and boot it on your own bench with a stock emulator:

  curl -O http://<your-instance-host>/panel.rom
  qemu-system-i386 -drive format=raw,file=panel.rom

The board powers on, runs its self test, and drives the matrix. The tag that
lights up along the top calibration strip is a factory print and is identical
on every recovered board, so it is not your unit's tag. Bring the panel into
service to make it show its own.

Each instance serves a different board.

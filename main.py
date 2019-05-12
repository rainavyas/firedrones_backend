from simulate_drones import do_all

import threading

def loopit():
  threading.Timer(5, loopit).start()
  do_all()

loopit()

import json
import threading
from collections import defaultdict

# prevent race condition
_rlock = threading.RLock()

class JsonIOHandler():
  
  def __init__(self, filename, initial_value = None):
    self._filename = filename
    self.initial_func = lambda: initial_value

  def __enter__(self):
    _rlock.acquire()
    try:
      with open(self._filename, 'r', encoding='utf8') as jfile:
        raw_data = json.load(jfile)
        self.data = defaultdict(self.initial_func, raw_data)
    except FileNotFoundError:
      self.data = defaultdict(self.initial_func, {})
    _rlock.release()
    
    return self
  
  def __exit__(self, exc_type, exc_value, traceback):
    _rlock.acquire()
    with open(self._filename, 'w', encoding='utf8') as jfile:
      json.dump(self.data, jfile, ensure_ascii=False, indent=2)
    _rlock.release()
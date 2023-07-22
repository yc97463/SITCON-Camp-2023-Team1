import json

class JsonIOHandler():
  
  def __init__(self, filename):
    self._filename = filename

  def __enter__(self):
    try:
      with open(self._filename, 'r', encoding='utf8') as jfile:
        self.data = json.load(jfile)
    except FileNotFoundError:
      self.data = {}
    return self
  
  def __exit__(self, exc_type, exc_value, traceback):
    with open(self._filename, 'w', encoding='utf8') as jfile:
      json.dump(self.data, jfile)
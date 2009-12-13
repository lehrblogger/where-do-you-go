import math
import logging

ZOOM_MAX = 20 # NOTE that this must also be in the static wdyg.js file

def createDot(rad, max_alpha = 100):
  level = []
  for i in range(int(rad * 2)):
    level.append([0.] * int(rad * 2))
  try:
    for y in range(0, int(rad * 2)):
      for x in range(0, int(rad * 2)):
        y_adj = math.pow(y - rad, 2)
        x_adj = math.pow(x - rad, 2)
        pt_rad = math.sqrt(y_adj + x_adj)
        if pt_rad > rad:
          level[y][x] = 0.
          continue
        level[y][x] = max_alpha * ((rad - pt_rad) / rad)
  except MemoryError:
    logging.error("There was a MemoryError at rad=%d and x,y=%d, %d" % (rad, x,y))
    raise
  return level

dot = []
for i in range(1, ZOOM_MAX + 1):
  #logging.warning(i)
  dot.append(createDot(3 * i))

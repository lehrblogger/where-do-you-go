import math
import pngcanvas

#def createDot(rad, max_alpha = 100):
#  img = pngcanvas.PNGCanvas(int(rad * 2), int(rad * 2))
#  for y in range(0, int(rad * 2)):
#    for x in range(0, int(rad * 2)):
#      y_adj = math.pow(y - rad, 2)
#      x_adj = math.pow(x - rad, 2)
#      pt_rad = math.sqrt(y_adj + x_adj)
#      if pt_rad > rad:
#        img.canvas[y][x] = [ 0, 0, 0, 0]
#        continue
#      alpha = int(max_alpha * ((rad - pt_rad) / rad))
#      img.canvas[y][x] = [ 0, 0, 0, alpha]
#  return img

def createDot(rad, max_alpha = 100):
  level = []
  for i in range(int(rad * 2)):
    level.append([0.] * int(rad * 2))
  #level = [ [0., ] * int(rad * 2) ] * int(rad * 2)
  for y in range(0, int(rad * 2)):
    for x in range(0, int(rad * 2)):
      y_adj = math.pow(y - rad, 2)
      x_adj = math.pow(x - rad, 2)
      pt_rad = math.sqrt(y_adj + x_adj)
      if pt_rad > rad:
        level[y][x] = 0.
        continue
      level[y][x] = max_alpha * ((rad - pt_rad) / rad)
  return level

dot = []
for i in range(1, 31):
  dot.append(createDot(1.5 * i))

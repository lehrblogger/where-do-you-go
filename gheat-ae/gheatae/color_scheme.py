import pngcanvas

TRANSPARENCY = 100

def createScheme(steps=255, r_start=255, g_start=255, b_start=255, 
    r_step=-3.0, g_step=-1.0, b_step=-1.0):
  img = pngcanvas.PNGCanvas(30, steps)
  r_cur = r_start
  g_cur = g_start
  b_cur = b_start
  for y in range(0, steps):
    for x in range(0, 30):
      img.canvas[y][x] = [ r_cur, g_cur, b_cur, TRANSPARENCY]
    r_cur += r_step
    g_cur += g_step
    b_cur += b_step
    if r_cur > 255: r_step *= -1; r_cur = 255 + r_step;
    if r_cur < 0: r_step *= -1; r_cur = 0 + r_step;
    if g_cur > 255: g_step *= -1; g_cur = 255 + g_step;
    if g_cur < 0: g_step *= -1; g_cur = 0 + g_step;
    if b_cur > 255: b_step *= -1; b_cur = 255 + b_step;
    if b_cur < 0: b_step *= -1; b_cur = 0 + b_step;
  return img

cyan_red = createScheme()
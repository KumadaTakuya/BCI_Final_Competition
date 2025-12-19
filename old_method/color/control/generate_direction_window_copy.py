import pyglet
from pyglet import shapes

# ==============================
# 螢幕視窗
# ==============================
window = pyglet.window.Window(
    width=1600,
    height=800,
    caption="SSVEP Arrows",
    fullscreen=False,
)

# ==============================
# 計算時間（避免使用 frame-based）
# ==============================
freq_left = 12      # 左 12 Hz
freq_right = 15     # 右 15 Hz

period_left = 1.0 / freq_left / 2     # 半週期，因為亮→暗
period_right = 1.0 / freq_right / 2

# ==============================
# 建立箭頭 (用三角形和矩形組成)
# ==============================
batch = pyglet.graphics.Batch()

# 左箭頭 (紅色)
left_tri = shapes.Triangle(
    300, 400,   # tip
    400, 450,
    400, 350,
    color=(255, 0, 0),
    batch=batch
)
left_bar = shapes.Rectangle(400, 370, 200, 60, color=(255, 0, 0), batch=batch)

# 右箭頭 (綠色)
right_tri = shapes.Triangle(
    1600-300, 400,
    1600-400, 450,
    1600-400, 350,
    color=(0, 255, 0),
    batch=batch
)
right_bar = shapes.Rectangle(1600-600, 370, 200, 60, color=(0, 255, 0), batch=batch)


# ==============================
# 閃爍函式
# ==============================
left_visible = True
right_visible = True

def toggle_left(dt):
    global left_visible
    left_visible = not left_visible

def toggle_right(dt):
    global right_visible
    right_visible = not right_visible

# 計時器（用時間取代 frame）
pyglet.clock.schedule_interval(toggle_left, period_left)
pyglet.clock.schedule_interval(toggle_right, period_right)


# ==============================
# 視窗更新與繪製
# ==============================
@window.event
def on_draw():
    window.clear()

    if left_visible:
        left_tri.draw()
        left_bar.draw()

    if right_visible:
        right_tri.draw()
        right_bar.draw()


@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.ESCAPE:
        pyglet.app.exit()


# ==============================
# 主迴圈
# ==============================
pyglet.app.run()

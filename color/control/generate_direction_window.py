import tkinter as tk
from time import time
import math


shape = 2
L_arrow_x = 300
L_arrow_y = 400

R_arrow_x = 1300
R_arrow_y = 400


class FlashingArrows:
    def __init__(self, root):
        self.root = root
        self.root.title("閃爍箭頭")
        self.root.geometry("1600x800")
        self.root.configure(bg='black')
        
        # 創建畫布
        self.canvas = tk.Canvas(root, width=1600, height=800, bg='black', highlightthickness=0)
        self.canvas.pack()
        
        if shape == 1:
            self.arrow_func = self.create_arrow_shape_1

        else:
            self.arrow_func = self.create_arrow_shape_2


        # 左箭頭 (12 Hz - 紅色)
        self.left_arrow = self.arrow_func(L_arrow_x, L_arrow_y, 'left', 'red')
        
        # 右箭頭 (15 Hz - 藍色 or 綠)
        self.right_arrow = self.arrow_func(R_arrow_x, R_arrow_y, 'right', '#33FF33') # blue green

    
        # 開始時間
        self.start_time = time()
        
        # 開始動畫
        self.animate()
    
    def create_arrow_shape_1(self, x, y, direction, color):
        """創建箭頭形狀(窄型)"""
        size = 80
        if direction == 'left':
            # 向左箭頭
            points = [
                x + size, y - size//2,  # 右上
                x, y,                    # 左中
                x + size, y + size//2,  # 右下
                x + size*0.6, y          # 箭尾內凹
            ]
        else:
            # 向右箭頭
            points = [
                x - size, y - size//2,  # 左上
                x, y,                    # 右中
                x - size, y + size//2,  # 左下
                x - size*0.6, y          # 箭尾內凹
            ]

        arrow = self.canvas.create_polygon(points, fill=color, outline=color, width=2)
        return {'id': arrow, 'color': color, 'visible': True}
    
    def create_arrow_shape_2(self, x, y, direction, color):
        """創建箭頭形狀（寬扁型）"""
        arrow_length = 300  # 箭頭總長度
        arrow_width = 200    # 箭頭寬度
        head_length = 200    # 箭頭尖端長度
        
        if direction == 'left':
            # 向左箭頭
            points = [
                x - arrow_length//2, y,                           # 左尖端
                x - arrow_length//2 + head_length, y - arrow_width//2,  # 上左
                x - arrow_length//2 + head_length, y - arrow_width//4,  # 上右（身體）
                x + arrow_length//2, y - arrow_width//4,          # 身體右上
                x + arrow_length//2, y + arrow_width//4,          # 身體右下
                x - arrow_length//2 + head_length, y + arrow_width//4,  # 下右（身體）
                x - arrow_length//2 + head_length, y + arrow_width//2,  # 下左
            ]
        else:
            # 向右箭頭
            points = [
                x + arrow_length//2, y,                           # 右尖端
                x + arrow_length//2 - head_length, y - arrow_width//2,  # 上右
                x + arrow_length//2 - head_length, y - arrow_width//4,  # 上左（身體）
                x - arrow_length//2, y - arrow_width//4,          # 身體左上
                x - arrow_length//2, y + arrow_width//4,          # 身體左下
                x + arrow_length//2 - head_length, y + arrow_width//4,  # 下左（身體）
                x + arrow_length//2 - head_length, y + arrow_width//2,  # 下右
            ]
        
        arrow = self.canvas.create_polygon(points, fill=color, outline=color, width=2)
        return {'id': arrow, 'color': color, 'visible': True}

    
    def animate(self):
        """動畫更新"""
        current_time = time() - self.start_time
        
        # 12 Hz 左箭頭
        phase_12hz = (current_time * 12) % 1
        left_visible = phase_12hz < 0.5
        
        # 15 Hz 右箭頭
        phase_15hz = (current_time * 15) % 1
        right_visible = phase_15hz < 0.5
        
        # 更新左箭頭可見性
        if left_visible:
            self.canvas.itemconfig(self.left_arrow['id'], state='normal')
        else:
            self.canvas.itemconfig(self.left_arrow['id'], state='hidden')
        
        # 更新右箭頭可見性
        if right_visible:
            self.canvas.itemconfig(self.right_arrow['id'], state='normal')
        else:
            self.canvas.itemconfig(self.right_arrow['id'], state='hidden')
        
        # 繼續動畫 (約60 FPS)
        self.root.after(16, self.animate)

if __name__ == "__main__":
    root = tk.Tk()
    app = FlashingArrows(root)
    root.mainloop()
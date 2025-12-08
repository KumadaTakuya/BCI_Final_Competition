"""
SSVEP視覺刺激生成器 / SSVEP Visual Stimulus Generator
生成多頻率閃爍視覺刺激窗口 / Generate multi-frequency flickering visual stimulus window
用於SSVEP實驗和測試 / For SSVEP experiments and testing
"""
import pygame
import time
import math
import sys


class SSVEPStimulus:
    """SSVEP視覺刺激生成器 / SSVEP Visual Stimulus Generator"""
    
    def __init__(self, frequencies=[6.0, 7.5, 8.57, 10.0], 
                 labels=["Forward", "Left", "Right", "Backward"],
                 window_size=(1200, 800),
                 stimulus_size=200):
        """
        初始化SSVEP刺激生成器 / Initialize SSVEP Stimulus Generator
        
        Args:
            frequencies: 目標頻率列表 (Hz) / List of target frequencies (Hz)
            labels: 對應的標籤列表 / List of corresponding labels
            window_size: 窗口大小 (寬, 高) / Window size (width, height)
            stimulus_size: 刺激區域大小（像素） / Stimulus area size (pixels)
        """
        self.frequencies = frequencies
        self.labels = labels
        self.window_size = window_size
        self.stimulus_size = stimulus_size
        
        # 初始化pygame / Initialize pygame
        pygame.init()
        self.screen = pygame.display.set_mode(window_size)
        pygame.display.set_caption("SSVEP Visual Stimulus - Press ESC to exit")
        
        # 顏色定義 / Color definitions
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GRAY = (128, 128, 128)
        self.COLORS = [
            (255, 100, 100),  # 紅色 / Red - Forward
            (100, 255, 100),  # 綠色 / Green - Left
            (100, 100, 255),  # 藍色 / Blue - Right
            (255, 255, 100),  # 黃色 / Yellow - Backward
        ]
        
        # 計算刺激區域位置（2x2網格） / Calculate stimulus positions (2x2 grid)
        self.positions = []
        margin = 50
        center_x, center_y = window_size[0] // 2, window_size[1] // 2
        spacing = stimulus_size + 50
        
        # 上排：Forward, Left / Top row: Forward, Left
        # 下排：Right, Backward / Bottom row: Right, Backward
        self.positions = [
            (center_x - spacing // 2, center_y - spacing // 2),  # Forward (左上)
            (center_x + spacing // 2, center_y - spacing // 2),  # Left (右上)
            (center_x - spacing // 2, center_y + spacing // 2),  # Right (左下)
            (center_x + spacing // 2, center_y + spacing // 2),  # Backward (右下)
        ]
        
        # 狀態追蹤 / State tracking
        self.running = True
        self.clock = pygame.time.Clock()
        self.start_time = time.time()
        
        # 字體設置 / Font settings
        self.font_large = pygame.font.Font(None, 36)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)
    
    def get_phase(self, frequency, current_time):
        """
        計算給定頻率在當前時間的相位 / Calculate phase for given frequency at current time
        
        Args:
            frequency: 頻率 (Hz) / Frequency (Hz)
            current_time: 當前時間（秒） / Current time (seconds)
        
        Returns:
            float: 相位（0到2π） / Phase (0 to 2π)
        """
        return 2 * math.pi * frequency * current_time
    
    def is_on(self, phase):
        """
        根據相位判斷刺激是否應該亮起 / Determine if stimulus should be on based on phase
        
        Args:
            phase: 相位（0到2π） / Phase (0 to 2π)
        
        Returns:
            bool: 是否亮起 / Whether stimulus is on
        """
        # 使用方波：相位在0到π時亮起，π到2π時熄滅 / Square wave: on from 0 to π, off from π to 2π
        return (phase % (2 * math.pi)) < math.pi
    
    def draw_stimulus(self, index, current_time):
        """
        繪製單個刺激區域 / Draw single stimulus area
        
        Args:
            index: 刺激索引 / Stimulus index
            current_time: 當前時間（秒） / Current time (seconds)
        """
        frequency = self.frequencies[index]
        label = self.labels[index]
        position = self.positions[index]
        color = self.COLORS[index % len(self.COLORS)]
        
        # 計算相位 / Calculate phase
        phase = self.get_phase(frequency, current_time)
        
        # 判斷是否亮起 / Determine if on
        is_on = self.is_on(phase)
        
        # 繪製刺激區域 / Draw stimulus area
        x, y = position
        rect = pygame.Rect(
            x - self.stimulus_size // 2,
            y - self.stimulus_size // 2,
            self.stimulus_size,
            self.stimulus_size
        )
        
        # 根據狀態選擇顏色 / Choose color based on state
        if is_on:
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, self.WHITE, rect, 3)
        else:
            pygame.draw.rect(self.screen, self.BLACK, rect)
            pygame.draw.rect(self.screen, self.GRAY, rect, 3)
        
        # 繪製標籤 / Draw label
        label_text = self.font_medium.render(label, True, self.WHITE)
        label_rect = label_text.get_rect(center=(x, y))
        
        # 在標籤下方顯示頻率 / Display frequency below label
        freq_text = self.font_small.render(f"{frequency} Hz", True, self.WHITE)
        freq_rect = freq_text.get_rect(center=(x, y + 25))
        
        # 只在亮起時顯示文字 / Only show text when on
        if is_on:
            self.screen.blit(label_text, label_rect)
            self.screen.blit(freq_text, freq_rect)
    
    def draw_info(self, current_time):
        """繪製資訊面板 / Draw information panel"""
        # 標題 / Title
        title = self.font_large.render("SSVEP Visual Stimulus", True, self.WHITE)
        self.screen.blit(title, (20, 20))
        
        # 說明文字 / Instructions
        instructions = [
            "Focus on one of the flickering squares",
            "Press ESC to exit",
            "",
            f"Time: {current_time:.1f}s"
        ]
        
        y_offset = 60
        for instruction in instructions:
            text = self.font_small.render(instruction, True, self.WHITE)
            self.screen.blit(text, (20, y_offset))
            y_offset += 20
    
    def run(self, target_fps=120):
        """
        運行視覺刺激窗口 / Run visual stimulus window
        
        Args:
            target_fps: 目標幀率 / Target FPS
        """
        print("=" * 50)
        print("SSVEP Visual Stimulus Window")
        print("=" * 50)
        print(f"Frequencies: {self.frequencies} Hz")
        print(f"Labels: {self.labels}")
        print("Press ESC to exit")
        print("=" * 50)
        
        while self.running:
            # 處理事件 / Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
            
            # 計算當前時間 / Calculate current time
            current_time = time.time() - self.start_time
            
            # 清空屏幕 / Clear screen
            self.screen.fill(self.BLACK)
            
            # 繪製所有刺激 / Draw all stimuli
            for i in range(len(self.frequencies)):
                self.draw_stimulus(i, current_time)
            
            # 繪製資訊 / Draw info
            self.draw_info(current_time)
            
            # 更新顯示 / Update display
            pygame.display.flip()
            self.clock.tick(target_fps)
        
        # 清理 / Cleanup
        pygame.quit()
        print("Visual stimulus window closed.")


def main():
    """主函數：獨立運行視覺刺激測試 / Main function: Standalone visual stimulus test"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SSVEP Visual Stimulus Generator")
    parser.add_argument("--fps", type=int, default=120,
                        help="Target FPS for rendering (default: 120)")
    parser.add_argument("--frequencies", type=float, nargs=4,
                        default=[6.0, 7.5, 8.57, 10.0],
                        help="Frequencies in Hz (default: 6.0 7.5 8.57 10.0)")
    parser.add_argument("--labels", type=str, nargs=4,
                        default=["Forward", "Left", "Right", "Backward"],
                        help="Labels for each frequency (default: Forward Left Right Backward)")
    
    args = parser.parse_args()
    
    # 創建刺激生成器 / Create stimulus generator
    stimulus = SSVEPStimulus(
        frequencies=args.frequencies,
        labels=args.labels
    )
    
    # 運行 / Run
    try:
        stimulus.run(target_fps=args.fps)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()


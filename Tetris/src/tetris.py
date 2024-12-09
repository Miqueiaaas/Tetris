import pygame
import random
import serial
import mysql.connector
import time
import threading


class TetrisGame:
    def __init__(self, arduino):
        pygame.init()

        # Configuração da janela
        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = 300, 600
        self.BLOCK_SIZE = 30
        self.INFO_PANEL_WIDTH = 200
        self.SCREEN = pygame.display.set_mode((self.SCREEN_WIDTH + self.INFO_PANEL_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("Tetris")

        # Cores
        self.WHITE = (0, 0, 0)
        self.BLACK = (255, 255, 255)
        self.CYAN = (0, 255, 255)
        self.ORANGE = (255, 165, 0)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)
        self.BLUE = (0, 0, 255)
        self.YELLOW = (255, 255, 0)
        self.PURPLE = (128, 0, 128)

        # Estruturas das peças
        self.SHAPES = [
            [[1, 1, 1, 1]],  # Linha (I)
            [[1, 1], [1, 1]],  # Quadrado (O)
            [[1, 0, 0], [1, 1, 1]],  # J
            [[0, 0, 1], [1, 1, 1]],  # L
            [[1, 1, 0], [0, 1, 1]],  # Z
            [[0, 1, 1], [1, 1, 0]],  # S
            [[0, 1, 0], [1, 1, 1]]  # T
        ]
        self.SHAPES_COLORS = [
            self.CYAN, self.ORANGE, self.GREEN, self.RED, self.BLUE, self.YELLOW, self.PURPLE
        ]

        # Estado inicial do jogo
        self.grid = [[0] * (self.SCREEN_WIDTH // self.BLOCK_SIZE) for _ in range(self.SCREEN_HEIGHT // self.BLOCK_SIZE)]
        self.tetromino = self.create_tetromino()
        self.next_tetromino = self.create_tetromino()
        self.fall_time = 0
        self.fall_speed = 500
        self.score = 0
        self.level = 1
        self.move_left = False
        self.move_right = False
        self.move_down = False
        self.rotate = False
        self.running = True
        self.clock = pygame.time.Clock()

        # Comunicação com o Arduino
        self.arduino = arduino

    def create_tetromino(self):
        index = random.randint(0, len(self.SHAPES) - 1)
        tetromino = {
            "shape": self.SHAPES[index],
            "color": self.SHAPES_COLORS[index],
            "x": self.SCREEN_WIDTH // 2 // self.BLOCK_SIZE - len(self.SHAPES[index][0]) // 2,
            "y": 0
        }
        return tetromino

    def draw_grid(self):
        for x in range(0, self.SCREEN_WIDTH, self.BLOCK_SIZE):
            pygame.draw.line(self.SCREEN, self.BLACK, (x, 0), (x, self.SCREEN_HEIGHT))
        for y in range(0, self.SCREEN_HEIGHT, self.BLOCK_SIZE):
            pygame.draw.line(self.SCREEN, self.BLACK, (0, y), (self.SCREEN_WIDTH, y))

    def draw_tetromino(self, tetromino):
        for y, row in enumerate(tetromino["shape"]):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(
                        self.SCREEN,
                        tetromino["color"],
                        pygame.Rect(
                            (tetromino["x"] + x) * self.BLOCK_SIZE,
                            (tetromino["y"] + y) * self.BLOCK_SIZE,
                            self.BLOCK_SIZE, self.BLOCK_SIZE
                        )
                    )

    def check_collision(self, tetromino, dx=0, dy=0):
        for y, row in enumerate(tetromino["shape"]):
            for x, cell in enumerate(row):
                if cell:
                    nx, ny = tetromino["x"] + x + dx, tetromino["y"] + y + dy
                    if nx < 0 or nx >= self.SCREEN_WIDTH // self.BLOCK_SIZE or ny >= self.SCREEN_HEIGHT // self.BLOCK_SIZE:
                        return True
                    if ny >= 0 and self.grid[ny][nx]:
                        return True
        return False

    def merge_tetromino(self, tetromino):
        for y, row in enumerate(tetromino["shape"]):
            for x, cell in enumerate(row):
                if cell:
                    self.grid[tetromino["y"] + y][tetromino["x"] + x] = tetromino["color"]

    def clear_lines(self):
        cleared_lines = 0
        for y in range(len(self.grid)):
            if all(self.grid[y]):
                del self.grid[y]
                self.grid.insert(0, [0] * (self.SCREEN_WIDTH // self.BLOCK_SIZE))
                cleared_lines += 1
        return cleared_lines

    def draw_info_panel(self):
        pygame.draw.rect(self.SCREEN, self.WHITE, pygame.Rect(self.SCREEN_WIDTH, 0, self.INFO_PANEL_WIDTH, self.SCREEN_HEIGHT))
        self.draw_text(f"Score: {self.score}", (self.SCREEN_WIDTH + 10, 10))
        self.draw_text(f"Level: {self.level}", (self.SCREEN_WIDTH + 10, 40))
        self.draw_text("Next:", (self.SCREEN_WIDTH + 10, 70))
        for y, row in enumerate(self.next_tetromino["shape"]):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(
                        self.SCREEN,
                        self.next_tetromino["color"],
                        pygame.Rect(self.SCREEN_WIDTH + 10 + x * self.BLOCK_SIZE, 100 + y * self.BLOCK_SIZE, self.BLOCK_SIZE, self.BLOCK_SIZE)
                    )

    def draw_text(self, text, pos, size=36):
        font = pygame.font.Font(None, size)
        rendered_text = font.render(text, True, self.BLACK)
        self.SCREEN.blit(rendered_text, pos)

    def handle_serial_input(self):
        """Lê os dados da porta serial e controla o jogo."""
        if self.arduino.in_waiting > 0:
            data = self.arduino.readline().decode('utf-8').strip()
            print(f"Recebido do Arduino: {data}")
            if data == "1":
                self.move_left = True
            elif data == "2":
                self.move_right = True
            elif data == "3":
                self.move_down = True
            elif data == "4":
                self.rotate = True
        time.sleep(0.005)  # Menor tempo de pausa


    def update_level(self):
        new_level = self.score // 600 + 1
        if new_level > self.level:
            self.level = new_level
            self.fall_speed = max(100, 500 - (self.level - 1) * 50)

    def run(self):
        move_time = 0
        side_move_time = 0  # Novo temporizador para movimentos laterais
        side_move_delay = 50  # Tempo de atraso para movimentos laterais (em milissegundos)

        while self.running:
            self.handle_serial_input()  # Chama a função que lê os dados da porta serial

            self.SCREEN.fill(self.WHITE)
            self.draw_grid()
            self.draw_tetromino(self.tetromino)
            self.draw_info_panel()

            for y, row in enumerate(self.grid):
                for x, color in enumerate(row):
                    if color:
                        pygame.draw.rect(self.SCREEN, color, pygame.Rect(x * self.BLOCK_SIZE, y * self.BLOCK_SIZE, self.BLOCK_SIZE, self.BLOCK_SIZE))

            self.fall_time += self.clock.get_rawtime()
            move_time += self.clock.get_rawtime()
            side_move_time += self.clock.get_rawtime()  # Incrementa o temporizador lateral
            self.clock.tick()

            self.update_level()

            if self.fall_time > self.fall_speed or self.move_down:
                self.fall_time = 0
                if not self.check_collision(self.tetromino, dy=1):
                    self.tetromino["y"] += 1
                else:
                    self.merge_tetromino(self.tetromino)
                    self.score += self.clear_lines()
                    self.tetromino = self.next_tetromino
                    self.next_tetromino = self.create_tetromino()

            # Movimento lateral com controle de tempo
            if side_move_time > side_move_delay:
                if self.move_left:
                    if not self.check_collision(self.tetromino, dx=-1):
                        self.tetromino["x"] -= 1
                    self.move_left = False  # Reseta após processar

                if self.move_right:
                    if not self.check_collision(self.tetromino, dx=1):
                        self.tetromino["x"] += 1
                    self.move_right = False  # Reseta após processar
            
                side_move_time = 0  # Reseta o temporizador lateral

            if self.move_down:
                if not self.check_collision(self.tetromino, dy=1):
                    self.tetromino["y"] += 1
                self.move_down = False  # Reseta após processar

            if self.rotate:
                rotated = {
                    "shape": list(zip(*self.tetromino["shape"][::-1])),
                    "color": self.tetromino["color"],
                    "x": self.tetromino["x"],
                    "y": self.tetromino["y"]
                }
                if not self.check_collision(rotated):
                    self.tetromino = rotated
                self.rotate = False  # Reseta após processar

            pygame.display.update()
            if self.check_collision(self.tetromino):
                self.running = False

        pygame.quit()



def main():
    arduino = serial.Serial('/dev/ttyUSB0', 9600)
    game = TetrisGame(arduino)
    game.run()

if __name__ == "__main__":
    main() 
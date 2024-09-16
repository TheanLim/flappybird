import pygame
import random
import os
from os.path import abspath, dirname
import asyncio
import platform
import json

# Initialize the game
pygame.init()

BASE_PATH = abspath(dirname(__file__))
# Game constants
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
FONT_SIZE = 36
# Bird Velocity
GRAVITY = 0.5
BIRD_JUMP = -10
# Increasing Pipe Difficulty
PIPE_WIDTH = 70
INITIAL_PIPE_GAP = 300
INITIAL_PIPE_DISTANCE = 300
PIPE_SPEED = 5
DIFFICULTY_INCREASE_INTERVAL = 10000  # 10 seconds
DIFFICULTY_INCREASE_AMOUNT = 10
MIN_PIPE_GAP = 100
MIN_PIPE_DISTANCE = 100
# Scores
SCORE_HISTORY_FILE = BASE_PATH+'/score_history.txt'
TOP_N_SCORE = 5
# Colors
SKY_BLUE = (135, 206, 235)
WHITE = (255, 255, 255)
PIPE_COLOR = (0, 255, 0)
GROUND_COLOR = (200, 200, 200)

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flappy Baby for Esther")  # Set the window title
clock = pygame.time.Clock()

# Load and scale images
def load_and_scale_image(file_path, scale_factor):
    image = pygame.image.load(file_path)
    width = int(SCREEN_HEIGHT * scale_factor)
    height = int(image.get_height() * (width / image.get_width()))
    return pygame.transform.scale(image, (width, height))

class Bird:
    def __init__(self):
        self.image = load_and_scale_image(BASE_PATH+'/flappy_bird.png', 0.1)
        self.rect = self.image.get_rect(center=(100, SCREEN_HEIGHT // 2))
        self.velocity = 0

    def update(self):
        self.velocity += GRAVITY
        self.rect.y += self.velocity

    def jump(self):
        self.velocity = BIRD_JUMP

    def draw(self, screen):
        screen.blit(self.image, self.rect)

class Pipe:
    def __init__(self, x, gap):
        self.x = x
        self.gap = gap
        self.height = random.randint(100, SCREEN_HEIGHT - self.gap - 100)
        self.top_rect = pygame.Rect(self.x, 0, PIPE_WIDTH, self.height)
        self.bottom_rect = pygame.Rect(self.x, self.height + self.gap, PIPE_WIDTH, SCREEN_HEIGHT - self.height - self.gap)

    def update(self):
        self.x -= PIPE_SPEED
        self.top_rect.x = self.x
        self.bottom_rect.x = self.x

    def draw(self, screen):
        pygame.draw.rect(screen, PIPE_COLOR, self.top_rect)
        pygame.draw.rect(screen, PIPE_COLOR, self.bottom_rect)

class Ground:
    def __init__(self):
        self.image = pygame.Surface((SCREEN_WIDTH, 50))
        self.image.fill(GROUND_COLOR)
        self.rect = self.image.get_rect(topleft=(0, SCREEN_HEIGHT - 50))

    def draw(self, screen):
        screen.blit(self.image, self.rect)

def check_collision(bird, pipes, ground):
    if bird.rect.colliderect(ground.rect):
        return True
    for pipe in pipes:
        if bird.rect.colliderect(pipe.top_rect) or bird.rect.colliderect(pipe.bottom_rect):
            return True
    return False

def draw_text(surface, text, size, color, position=None, center=False):
    font = pygame.font.SysFont(None, size)
    text_surface = font.render(text, True, color)
    
    if center:
        _, pos_height = position
        text_rect = text_surface.get_rect(center=(surface.get_width() // 2, pos_height))
        surface.blit(text_surface, text_rect)
    else:
        surface.blit(text_surface, position)

async def save_score(score):
    with open(SCORE_HISTORY_FILE, 'a') as file:
        file.write('{}\n'.format(score))

async def get_top_scores():
    if not os.path.exists(SCORE_HISTORY_FILE):
        return []
    with open(SCORE_HISTORY_FILE, 'r') as file:
        scores = [int(line.strip()) for line in file if line.strip().isdigit()]
    return sorted(scores, reverse=True)[:TOP_N_SCORE]

async def display_scores():
    top_scores = await get_top_scores()
    screen.fill(SKY_BLUE)
    draw_text(screen, 'Top Scores', 36, WHITE, (SCREEN_WIDTH // 4, 50))
    
    for i, score in enumerate(top_scores):
        draw_text(screen, '{}. {}'.format(i + 1, score), 36, WHITE, (SCREEN_WIDTH // 4, 100 + i * 40))
    
    draw_text(screen, 'Press R to Restart', 24, WHITE, (SCREEN_WIDTH // 4, SCREEN_HEIGHT - 90), center=True)
    draw_text(screen, 'Press Q to Quit', 24, WHITE, (SCREEN_WIDTH // 4, SCREEN_HEIGHT - 60), center=True)

    pygame.display.update()
    await asyncio.sleep(0)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return
                if event.key == pygame.K_q:
                    pygame.quit()
                    return
        
        await asyncio.sleep(0)

async def game_loop():
    bird = Bird()
    ground = Ground()
    pipe_gap = INITIAL_PIPE_GAP
    pipe_distance = INITIAL_PIPE_DISTANCE
    pipes = [Pipe(SCREEN_WIDTH + pipe_distance, pipe_gap), Pipe(SCREEN_WIDTH + 2 * pipe_distance, pipe_gap)]
    score = 0
    start_time = pygame.time.get_ticks()

    while True:
        screen.fill(SKY_BLUE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                bird.jump()

        bird.update()
        for pipe in pipes:
            pipe.update()

        if check_collision(bird, pipes, ground):
            await save_score(score)
            await display_scores()
            return

        if pipes[0].x < -PIPE_WIDTH:
            pipes.pop(0)
            pipes.append(Pipe(SCREEN_WIDTH + pipe_distance, pipe_gap))
            score += 1

        current_time = pygame.time.get_ticks()
        if current_time - start_time >= DIFFICULTY_INCREASE_INTERVAL:
            pipe_gap = max(MIN_PIPE_GAP, pipe_gap - DIFFICULTY_INCREASE_AMOUNT)
            pipe_distance = max(MIN_PIPE_DISTANCE, pipe_distance - DIFFICULTY_INCREASE_AMOUNT)
            start_time = current_time

        bird.draw(screen)
        for pipe in pipes:
            pipe.draw(screen)
        ground.draw(screen)
        draw_text(screen, 'Score: {}'.format(score), FONT_SIZE, (0, 0, 0), (10, 10))

        pygame.display.update()
        clock.tick(60)

        await asyncio.sleep(0)  # Ensure the async loop doesn't block

async def main():
    while True:
        await game_loop()

if __name__ == "__main__":
    asyncio.run(main())

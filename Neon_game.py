"""
Neon Asteroids
A modern, polished take on the classic arcade game.
Features: Particle systems, screen shake, wrap-around physics, and progressive difficulty.

REQUIREMENTS:
- Python 3.6+
- Pygame (Install via terminal: pip install pygame)

TO RUN:
1. Save this code to a file named 'main.py'
2. Open your terminal or command prompt.
3. Run the command: python main.py
"""

import pygame
import math
import random
import sys

# --- Initialization ---
pygame.init()

# --- Constants ---
WIDTH, HEIGHT = 1000, 700
FPS = 60

# Colors (RGB)
BG_COLOR = (10, 10, 15)       # Deep space blue/black
WHITE = (255, 255, 255)
CYAN = (0, 255, 255)          # Player color
MAGENTA = (255, 0, 255)       # Enemy/Asteroid color
YELLOW = (255, 255, 0)        # Bullet/Thrust color
RED = (255, 50, 50)           # Explosion color

# Game settings
PLAYER_SPEED = 0.15
MAX_SPEED = 7
FRICTION = 0.98
ROTATION_SPEED = 4
BULLET_SPEED = 12
BULLET_LIFETIME = 60 # frames

# --- Setup Display ---
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neon Asteroids")
clock = pygame.time.Clock()

# --- Utility Functions ---
def wrap_position(pos):
    """Wraps coordinates around the screen edges."""
    x, y = pos
    if x < 0: x += WIDTH
    elif x > WIDTH: x -= WIDTH
    if y < 0: y += HEIGHT
    elif y > HEIGHT: y -= HEIGHT
    return [x, y]

# --- Game Classes ---

class Particle:
    def __init__(self, x, y, velocity, color, lifetime):
        self.pos = [x, y]
        self.vel = velocity
        self.color = color
        self.lifetime = lifetime
        self.initial_lifetime = lifetime
        self.size = random.uniform(1, 3)

    def update(self):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]
        self.lifetime -= 1

    def draw(self, surface, offset_x=0, offset_y=0):
        if self.lifetime > 0:
            # Fade out effect
            alpha = int(255 * (self.lifetime / self.initial_lifetime))
            color_with_alpha = (*self.color[:3], alpha)
            
            # Since pygame doesn't natively support alpha on primitive shapes easily, 
            # we scale down the size to simulate fading out instead.
            current_size = max(0.1, self.size * (self.lifetime / self.initial_lifetime))
            
            draw_x = int(self.pos[0] + offset_x)
            draw_y = int(self.pos[1] + offset_y)
            pygame.draw.circle(surface, self.color, (draw_x, draw_y), int(current_size))

class Bullet:
    def __init__(self, x, y, angle):
        self.pos = [x, y]
        rad_angle = math.radians(angle)
        self.vel = [math.cos(rad_angle) * BULLET_SPEED, -math.sin(rad_angle) * BULLET_SPEED]
        self.lifetime = BULLET_LIFETIME

    def update(self):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]
        self.pos = wrap_position(self.pos)
        self.lifetime -= 1

    def draw(self, surface, offset_x=0, offset_y=0):
        draw_x = int(self.pos[0] + offset_x)
        draw_y = int(self.pos[1] + offset_y)
        pygame.draw.circle(surface, YELLOW, (draw_x, draw_y), 3)

class Asteroid:
    def __init__(self, x, y, size_tier):
        self.pos = [x, y]
        self.size_tier = size_tier # 3 = Large, 2 = Medium, 1 = Small
        self.radius = size_tier * 20
        
        # Random velocity based on size (smaller = faster)
        speed = random.uniform(1, 3) + (4 - size_tier) * 0.5
        angle = random.uniform(0, 360)
        self.vel = [math.cos(math.radians(angle)) * speed, -math.sin(math.radians(angle)) * speed]
        
        self.rotation = 0
        self.rotation_speed = random.uniform(-2, 2)
        
        # Generate a jagged polygon shape
        self.points = []
        num_points = random.randint(8, 12)
        for i in range(num_points):
            angle = (i / num_points) * math.pi * 2
            # Add random variance to the radius to make it jagged
            variance = random.uniform(0.7, 1.3)
            self.points.append((math.cos(angle) * self.radius * variance, 
                                math.sin(angle) * self.radius * variance))

    def update(self):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]
        self.pos = wrap_position(self.pos)
        self.rotation += self.rotation_speed

    def draw(self, surface, offset_x=0, offset_y=0):
        # Rotate and translate points
        rotated_points = []
        rad_rot = math.radians(self.rotation)
        cos_val = math.cos(rad_rot)
        sin_val = math.sin(rad_rot)
        
        for px, py in self.points:
            # Rotate
            rx = px * cos_val - py * sin_val
            ry = px * sin_val + py * cos_val
            # Translate
            rotated_points.append((rx + self.pos[0] + offset_x, ry + self.pos[1] + offset_y))
            
        pygame.draw.polygon(surface, MAGENTA, rotated_points, 2)

class Player:
    def __init__(self):
        self.reset()
        self.radius = 12

    def reset(self):
        self.pos = [WIDTH // 2, HEIGHT // 2]
        self.vel = [0, 0]
        self.angle = 90 # Pointing straight up
        self.is_thrusting = False
        self.cooldown = 0
        self.invincible_timer = 120 # 2 seconds of invincibility on spawn

    def update(self, keys):
        # Rotation
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.angle += ROTATION_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.angle -= ROTATION_SPEED

        # Thrust
        self.is_thrusting = keys[pygame.K_UP] or keys[pygame.K_w]
        if self.is_thrusting:
            rad_angle = math.radians(self.angle)
            self.vel[0] += math.cos(rad_angle) * PLAYER_SPEED
            self.vel[1] -= math.sin(rad_angle) * PLAYER_SPEED

        # Apply friction
        self.vel[0] *= FRICTION
        self.vel[1] *= FRICTION

        # Speed limit
        speed = math.hypot(self.vel[0], self.vel[1])
        if speed > MAX_SPEED:
            self.vel[0] = (self.vel[0] / speed) * MAX_SPEED
            self.vel[1] = (self.vel[1] / speed) * MAX_SPEED

        # Update position
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]
        self.pos = wrap_position(self.pos)

        # Timers
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.invincible_timer > 0:
            self.invincible_timer -= 1

    def shoot(self):
        if self.cooldown == 0:
            self.cooldown = 10 # frames between shots
            return Bullet(self.pos[0], self.pos[1], self.angle)
        return None

    def draw(self, surface, offset_x=0, offset_y=0):
        # Blinking effect if invincible
        if self.invincible_timer > 0 and (self.invincible_timer // 5) % 2 == 0:
            return

        rad_angle = math.radians(self.angle)
        cos_val = math.cos(rad_angle)
        sin_val = math.sin(rad_angle)

        # Calculate triangle points
        front = (self.pos[0] + cos_val * self.radius * 1.5 + offset_x, 
                 self.pos[1] - sin_val * self.radius * 1.5 + offset_y)
        
        # 140 degrees back on each side
        left_angle = rad_angle + math.radians(140)
        left = (self.pos[0] + math.cos(left_angle) * self.radius + offset_x, 
                self.pos[1] - math.sin(left_angle) * self.radius + offset_y)
                
        right_angle = rad_angle - math.radians(140)
        right = (self.pos[0] + math.cos(right_angle) * self.radius + offset_x, 
                 self.pos[1] - math.sin(right_angle) * self.radius + offset_y)

        # Draw ship
        pygame.draw.polygon(surface, CYAN, [front, left, right], 2)
        
        # Draw thrust flame
        if self.is_thrusting:
            flame_length = random.uniform(0.5, 1.5)
            back_angle = rad_angle + math.pi
            flame_tip = (self.pos[0] + math.cos(back_angle) * self.radius * flame_length * 1.5 + offset_x,
                         self.pos[1] - math.sin(back_angle) * self.radius * flame_length * 1.5 + offset_y)
            pygame.draw.polygon(surface, YELLOW, [left, right, flame_tip], 0)

# --- Main Game Manager ---
class Game:
    def __init__(self):
        self.state = "MENU" # MENU, PLAYING, GAME_OVER
        self.font_large = pygame.font.SysFont("Courier New", 64, bold=True)
        self.font_medium = pygame.font.SysFont("Courier New", 32, bold=True)
        self.font_small = pygame.font.SysFont("Courier New", 20)
        self.reset_game()

    def reset_game(self):
        self.player = Player()
        self.asteroids = []
        self.bullets = []
        self.particles = []
        self.score = 0
        self.lives = 3
        self.level = 1
        self.shake_duration = 0
        self.shake_intensity = 0
        self.spawn_asteroids(3)

    def spawn_asteroids(self, count):
        for _ in range(count):
            # Spawn away from player
            while True:
                x = random.randint(0, WIDTH)
                y = random.randint(0, HEIGHT)
                dist = math.hypot(x - self.player.pos[0], y - self.player.pos[1])
                if dist > 150: # Minimum safe distance
                    break
            self.asteroids.append(Asteroid(x, y, 3))

    def create_explosion(self, x, y, color, count, speed_multiplier=1.0):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(0.5, 3.0) * speed_multiplier
            vel = [math.cos(angle) * speed, math.sin(angle) * speed]
            lifetime = random.randint(20, 50)
            self.particles.append(Particle(x, y, vel, color, lifetime))

    def trigger_shake(self, duration, intensity):
        self.shake_duration = duration
        self.shake_intensity = intensity

    def check_collisions(self):
        # Bullets vs Asteroids
        for bullet in self.bullets[:]:
            bullet_rect = pygame.Rect(bullet.pos[0] - 2, bullet.pos[1] - 2, 4, 4)
            for asteroid in self.asteroids[:]:
                # Simple circle collision estimation
                dist = math.hypot(bullet.pos[0] - asteroid.pos[0], bullet.pos[1] - asteroid.pos[1])
                if dist < asteroid.radius:
                    # Hit!
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    if asteroid in self.asteroids:
                        self.asteroids.remove(asteroid)
                        
                    self.score += (4 - asteroid.size_tier) * 100
                    self.create_explosion(asteroid.pos[0], asteroid.pos[1], MAGENTA, 15)
                    self.trigger_shake(5, 2)
                    
                    # Split asteroid
                    if asteroid.size_tier > 1:
                        for _ in range(2):
                            new_ast = Asteroid(asteroid.pos[0], asteroid.pos[1], asteroid.size_tier - 1)
                            self.asteroids.append(new_ast)
                    break # Stop checking this bullet

        # Player vs Asteroids
        if self.player.invincible_timer <= 0:
            for asteroid in self.asteroids:
                dist = math.hypot(self.player.pos[0] - asteroid.pos[0], self.player.pos[1] - asteroid.pos[1])
                if dist < asteroid.radius + self.player.radius * 0.8:
                    # Player Hit!
                    self.create_explosion(self.player.pos[0], self.player.pos[1], CYAN, 40, 2.0)
                    self.create_explosion(self.player.pos[0], self.player.pos[1], RED, 20, 1.5)
                    self.trigger_shake(20, 8)
                    self.lives -= 1
                    if self.lives <= 0:
                        self.state = "GAME_OVER"
                    else:
                        self.player.reset()
                    break

    def run_frame(self, events, keys):
        # Handle Screen Shake
        offset_x, offset_y = 0, 0
        if self.shake_duration > 0:
            self.shake_duration -= 1
            offset_x = random.randint(-self.shake_intensity, self.shake_intensity)
            offset_y = random.randint(-self.shake_intensity, self.shake_intensity)

        screen.fill(BG_COLOR)

        # Draw a faint grid background for vector aesthetic
        for x in range(0, WIDTH, 50):
            pygame.draw.line(screen, (20, 20, 30), (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, 50):
            pygame.draw.line(screen, (20, 20, 30), (0, y), (WIDTH, y))

        if self.state == "MENU":
            title = self.font_large.render("NEON ASTEROIDS", True, CYAN)
            prompt = self.font_medium.render("Press SPACE to Start", True, WHITE)
            screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3))
            
            # Pulse effect for the prompt
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT//2))

            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.reset_game()
                    self.state = "PLAYING"

        elif self.state == "PLAYING":
            # Level Progression
            if len(self.asteroids) == 0:
                self.level += 1
                self.player.invincible_timer = 60
                self.spawn_asteroids(3 + self.level)

            # Events
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    bullet = self.player.shoot()
                    if bullet:
                        self.bullets.append(bullet)
                        # Minimal kickback/shake on shoot
                        self.trigger_shake(2, 1)

            # Player Thrust particles
            if self.player.is_thrusting and random.random() > 0.5:
                back_angle = math.radians(self.player.angle + 180 + random.uniform(-15, 15))
                px = self.player.pos[0] + math.cos(back_angle) * self.player.radius
                py = self.player.pos[1] - math.sin(back_angle) * self.player.radius
                vel = [math.cos(back_angle) * random.uniform(1, 3), -math.sin(back_angle) * random.uniform(1, 3)]
                self.particles.append(Particle(px, py, vel, YELLOW, random.randint(10, 20)))

            # Updates
            self.player.update(keys)
            
            for bullet in self.bullets[:]:
                bullet.update()
                if bullet.lifetime <= 0:
                    self.bullets.remove(bullet)

            for asteroid in self.asteroids:
                asteroid.update()

            for particle in self.particles[:]:
                particle.update()
                if particle.lifetime <= 0:
                    self.particles.remove(particle)

            self.check_collisions()

            # Drawing
            for particle in self.particles:
                particle.draw(screen, offset_x, offset_y)
            for bullet in self.bullets:
                bullet.draw(screen, offset_x, offset_y)
            for asteroid in self.asteroids:
                asteroid.draw(screen, offset_x, offset_y)
            
            self.player.draw(screen, offset_x, offset_y)

            # UI
            score_text = self.font_medium.render(f"SCORE: {self.score}", True, WHITE)
            level_text = self.font_small.render(f"WAVE: {self.level}", True, MAGENTA)
            screen.blit(score_text, (20, 20))
            screen.blit(level_text, (20, 60))

            # Draw Lives as mini-ships
            for i in range(self.lives):
                lx = 40 + i * 30
                ly = 100
                pygame.draw.polygon(screen, CYAN, 
                    [(lx, ly - 10), (lx - 8, ly + 8), (lx + 8, ly + 8)], 1)

        elif self.state == "GAME_OVER":
            game_over = self.font_large.render("SYSTEM FAILURE", True, RED)
            final_score = self.font_medium.render(f"FINAL SCORE: {self.score}", True, WHITE)
            prompt = self.font_small.render("Press SPACE to Reboot", True, CYAN)
            
            screen.blit(game_over, (WIDTH//2 - game_over.get_width()//2, HEIGHT//3 - 30))
            screen.blit(final_score, (WIDTH//2 - final_score.get_width()//2, HEIGHT//2 - 10))
            screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT//2 + 50))

            # Update and draw leftover particles for effect
            for particle in self.particles[:]:
                particle.update()
                particle.draw(screen)
                if particle.lifetime <= 0:
                    self.particles.remove(particle)

            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.state = "MENU"

def main():
    game = Game()
    running = True

    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        
        # Run game logic and drawing
        game.run_frame(events, keys)

        # Update display and maintain frame rate
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
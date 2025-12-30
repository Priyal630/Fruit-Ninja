# Full script is too long for one message, so I'll break it into sections.
# Part 1 of 3: Imports, Config, Entity class, Helpers, Assets

import cv2
import math
import random
import time
from dataclasses import dataclass
from collections import deque

import pygame
from cvzone.HandTrackingModule import HandDetector

# ========== CONFIG ==========
WIDTH, HEIGHT = 960, 540
FPS = 60

TRACK_W, TRACK_H = 640, 360
SMOOTH_ALPHA = 0.97
MIN_SWIPE_SPEED = 70
HIT_RADIUS_EXTRA = 40
TRAIL_LEN = 3

PROB_ONE = 0.78
POWERUP_CHANCE = 0.16  # Increased to accommodate heart
ENTITY_LIFETIME = 8.0

FREEZE_SECONDS = 3.0
DOUBLE_SECONDS = 5.0
TIME_MODE_DURATION = 60  # seconds
MAX_LIVES = 5
LIVES_START = 3

GESTURE_HOLD_SEC = 0.35
GESTURE_COOLDOWN_SEC = 0.70

# ========== DATA ==========
@dataclass
class Entity:
    x: float
    y: float
    vx: float
    vy: float
    r: int
    kind: str  # fruit | bomb | freeze | double | heart
    img: pygame.Surface
    alive: bool = True
    born: float = 0.0

# ========== HELPERS ==========
def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def smooth_point(prev, cur, alpha):
    if prev is None:
        return (int(cur[0]), int(cur[1]))
    return (
        int(prev[0] + alpha * (cur[0] - prev[0])),
        int(prev[1] + alpha * (cur[1] - prev[1])),
    )

def load_image(path, size):
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.smoothscale(img, size)

def load_highscore():
    try:
        with open("highscore.txt", "r", encoding="utf-8") as f:
            return int((f.read().strip() or "0"))
    except:
        return 0

def save_highscore(val: int):
    with open("highscore.txt", "w", encoding="utf-8") as f:
        f.write(str(val))

def rounded_rect(surf, rect, color, radius=16):
    pygame.draw.rect(surf, color, rect, border_radius=radius)

def draw_pill(surf, x, y, text, font, bg, fg=(255,255,255)):
    padx, pady = 14, 8
    t = font.render(text, True, fg)
    w, h = t.get_width() + padx*2, t.get_height() + pady*2
    rounded_rect(surf, (x, y, w, h), bg, radius=18)
    surf.blit(t, (x+padx, y+pady))
    return w

def main():
    pygame.init()
    pygame.mixer.init()
    pygame.mixer.set_num_channels(8)

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Fruit Ninja - Hand Gesture (Upgraded)")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("Segoe UI", 22, bold=True)
    mid = pygame.font.SysFont("Segoe UI", 30, bold=True)
    big = pygame.font.SysFont("Segoe UI", 62, bold=True)

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, TRACK_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, TRACK_H)
    cap.set(cv2.CAP_PROP_FPS, FPS)
    if not cap.isOpened():
        raise RuntimeError("Webcam could not be opened.")

    detector = HandDetector(detectionCon=0.7, maxHands=1)

    # Assets
    fruit_imgs = [
        load_image("assets/images/apple.png", (64, 64)),
        load_image("assets/images/banana.png", (64, 64)),
        load_image("assets/images/watermelon.png", (72, 72)),
    ]
    bomb_img   = load_image("assets/images/bomb.png", (64, 64))
    freeze_img = load_image("assets/images/freeze.png", (64, 64))
    double_img = load_image("assets/images/double.png", (64, 64))
    heart_img  = load_image("assets/images/heart.png", (64, 64))

    sounds = {
        "slice": pygame.mixer.Sound("assets/sounds/slice.wav"),
        "bomb": pygame.mixer.Sound("assets/sounds/bomb.wav"),
        "miss": pygame.mixer.Sound("assets/sounds/miss.wav"),
        "start": pygame.mixer.Sound("assets/sounds/start.wav"),
        "gameover": pygame.mixer.Sound("assets/sounds/gameover.wav"),
    }

    MENU, PLAY, PAUSE, GAMEOVER = "MENU", "PLAY", "PAUSE", "GAMEOVER"
    mode = "CLASSIC"  # or "TIME"
    state = MENU
    difficulty = "EASY"

    GRAVITY = 520.0
    SPAWN_INTERVAL = 1.4
    BOMB_CHANCE = 0.06

    def apply_difficulty():
        nonlocal GRAVITY, SPAWN_INTERVAL, BOMB_CHANCE
        if difficulty == "EASY":
            GRAVITY = 480.0
            SPAWN_INTERVAL = 1.8   # was 1.4
            BOMB_CHANCE = 0.04
        elif difficulty == "MEDIUM":
            GRAVITY = 650.0
            SPAWN_INTERVAL = 1.15
            BOMB_CHANCE = 0.10
        else:  # HARD
            GRAVITY = 820.0
            SPAWN_INTERVAL = 0.95
            BOMB_CHANCE = 0.16

    apply_difficulty()

    entities = []
    trail = deque(maxlen=TRAIL_LEN)

    score = 0
    lives = LIVES_START
    highscore = load_highscore()
    time_left = TIME_MODE_DURATION
    freeze_until = 0.0
    double_until = 0.0
    last_spawn = time.time()

    last_tip = None
    last_tip_time = time.time()

    gesture_candidate = None
    gesture_candidate_since = 0.0
    gesture_cooldown_until = 0.0

    def reset_to_menu():
        nonlocal state
        state = MENU

    def start_game():
        nonlocal entities, score, lives, freeze_until, double_until, last_spawn, state, time_left
        entities = []
        trail.clear()
        score = 0
        lives = LIVES_START
        freeze_until = 0.0
        double_until = 0.0
        last_spawn = time.time()
        time_left = TIME_MODE_DURATION
        state = PLAY
        sounds["start"].play()

    def spawn_drop():
        nonlocal entities
        count = 1  # always one fruit per interval in easy mode
        if difficulty != "EASY" and random.random() < 0.5:
            count = 2

        for _ in range(count):
            x = random.uniform(100, WIDTH - 100)
            y = -60
            vx = random.uniform(-120, 120)
            vy = random.uniform(80, 220)

            roll = random.random()
            if roll < BOMB_CHANCE:
                kind, img, r = "bomb", bomb_img, 30
            elif roll < BOMB_CHANCE + (POWERUP_CHANCE / 4):
                kind, img, r = "freeze", freeze_img, 30
            elif roll < BOMB_CHANCE + (POWERUP_CHANCE / 2):
                kind, img, r = "double", double_img, 30
            elif roll < BOMB_CHANCE + (POWERUP_CHANCE * 0.75):
                kind, img, r = "heart", heart_img, 30
            else:
                kind, img, r = "fruit", random.choice(fruit_imgs), 32

            entities.append(Entity(x, y, vx, vy, r, kind, img, True, time.time()))

    # Background
    def draw_background():
        screen.fill((12, 12, 18))
        pygame.draw.rect(screen, (18, 18, 28), (0, 0, WIDTH, 92))
        pygame.draw.rect(screen, (10, 10, 14), (0, 92, WIDTH, HEIGHT - 160))
        pygame.draw.rect(screen, (8, 8, 10), (0, HEIGHT - 68, WIDTH, 68))

    running = True
    while running:
        dt = clock.tick(FPS) / 1_000.0
        now = time.time()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key == pygame.K_r:
                    reset_to_menu()
                elif state == MENU:
                    if event.key == pygame.K_1:
                        difficulty = "EASY"; apply_difficulty()
                    elif event.key == pygame.K_2:
                        difficulty = "MEDIUM"; apply_difficulty()
                    elif event.key == pygame.K_3:
                        difficulty = "HARD"; apply_difficulty()
                    elif event.key == pygame.K_RETURN:
                        start_game()
                    elif event.key == pygame.K_c:
                        mode = "CLASSIC"
                    elif event.key == pygame.K_t:
                        mode = "TIME"

        ok, frame = cap.read()
        if not ok: break
        frame = cv2.flip(frame, 1)

        tip, tip_speed, gesture = None, 0.0, None
        hands, _ = detector.findHands(frame, draw=False)
        if hands:
            hand = hands[0]
            lm = hand["lmList"]
            raw_tip = (lm[8][0], lm[8][1])
            sx, sy = WIDTH / TRACK_W, HEIGHT / TRACK_H
            tip = smooth_point(last_tip, (raw_tip[0] * sx, raw_tip[1] * sy), SMOOTH_ALPHA)

            tip_speed = dist(tip, last_tip) / max(1e-6, (now - last_tip_time)) if last_tip else 0
            last_tip = tip
            last_tip_time = now
            trail.append(tip)

            gesture = detector.fingersUp(hand)

        # Gestures: PAUSE = [0,0,0,0,0], RESUME = [0,1,1,0,0], MENU = [1,1,0,0,1]
        action = None
        if gesture:
            g = tuple(gesture)
            if g == (0,0,0,0,0): action = "PAUSE"
            elif g == (0,1,1,0,0): action = "RESUME"
            elif g == (1,1,0,0,1): action = "MENU"

        if now < gesture_cooldown_until:
            action = None

        if action:
            if gesture_candidate != action:
                gesture_candidate, gesture_candidate_since = action, now
            elif (now - gesture_candidate_since) >= GESTURE_HOLD_SEC:
                if action == "PAUSE" and state == PLAY:
                    state = PAUSE
                elif action == "RESUME" and state == PAUSE:
                    state = PLAY
                elif action == "MENU" and state in (PLAY, PAUSE, GAMEOVER):
                    reset_to_menu()
                gesture_cooldown_until = now + GESTURE_COOLDOWN_SEC
                gesture_candidate, gesture_candidate_since = None, 0.0
        else:
            gesture_candidate, gesture_candidate_since = None, 0.0

        # ======= GAME UPDATE =======
        if state == PLAY:
            if mode == "TIME":
                time_left -= dt
                if time_left <= 0:
                    state = GAMEOVER
                    sounds["gameover"].play()

            if (now - last_spawn) >= SPAWN_INTERVAL:
                if len([e for e in entities if e.alive]) >= 6:
                    return  # too many entities, skip spawning

                spawn_drop()
                last_spawn = now

            frozen = now < freeze_until

            for e in entities:
                if not e.alive: continue
                if not frozen:
                    e.vy += GRAVITY * dt
                    e.x += e.vx * dt
                    e.y += e.vy * dt
                else:
                    e.x += e.vx * dt * 0.1
                    e.y += e.vy * dt * 0.1

                if e.y > HEIGHT + 90:
                    e.alive = False
                    if e.kind == "fruit" and mode == "CLASSIC":
                        lives -= 1
                        sounds["miss"].play()
                        if lives <= 0:
                            state = GAMEOVER
                            sounds["gameover"].play()

            if tip and tip_speed >= MIN_SWIPE_SPEED:
                for e in entities:
                    if not e.alive: continue
                    if dist((e.x, e.y), tip) <= (e.r + HIT_RADIUS_EXTRA):
                        e.alive = False
                        if e.kind == "bomb":
                            sounds["bomb"].play()
                            state = GAMEOVER
                            sounds["gameover"].play()
                            break
                        elif e.kind == "freeze":
                            sounds["slice"].play()
                            freeze_until = now + FREEZE_SECONDS
                        elif e.kind == "double":
                            sounds["slice"].play()
                            double_until = now + DOUBLE_SECONDS
                        elif e.kind == "heart":
                            sounds["slice"].play()
                            if lives < MAX_LIVES: lives += 1
                        else:
                            sounds["slice"].play()
                            score += (2 if now < double_until else 1)

            entities = [e for e in entities if e.alive and (now - e.born) < ENTITY_LIFETIME]

        # HIGHSCORE
        if state == GAMEOVER and score > highscore:
            highscore = score
            save_highscore(score)

        # ========== DRAW ==========
        draw_background()

        # Top HUD
        rounded_rect(screen, (14, 14, WIDTH - 28, 62), (0, 0, 0), 18)
        rounded_rect(screen, (14, 14, WIDTH - 28, 62), (255, 255, 255), 18)
        rounded_rect(screen, (15, 15, WIDTH - 30, 60), (0, 0, 0), 18)

        x = 28
        x += draw_pill(screen, x, 26, f"Score: {score}", font, (40, 120, 180)) + 10
        if mode == "CLASSIC":
            x += draw_pill(screen, x, 26, f"Lives: {lives}", font, (180, 60, 60)) + 10
        else:
            x += draw_pill(screen, x, 26, f"Time: {int(time_left)}s", font, (180, 120, 60)) + 10
        x += draw_pill(screen, x, 26, f"High: {highscore}", font, (90, 90, 120)) + 10
        mult = "x2" if now < double_until else "x1"
        x += draw_pill(screen, x, 26, f"Mult: {mult}", font, (80, 150, 90)) + 10
        if now < freeze_until:
            draw_pill(screen, x, 26, "FREEZE", font, (120, 160, 255))

        for e in entities:
            rect = e.img.get_rect(center=(int(e.x), int(e.y)))
            screen.blit(e.img, rect)

        if len(trail) >= 2:
            pts = list(trail)
            for i in range(1, len(pts)):
                a, b = pts[i - 1], pts[i]
                pygame.draw.line(screen, (0, 120, 150), a, b, 10)
                pygame.draw.line(screen, (0, 220, 255), a, b, 4)

        if tip:
            x, y = int(tip[0]), int(tip[1])
            pygame.draw.circle(screen, (255, 255, 255), (x, y), 10, 2)
            pygame.draw.line(screen, (255, 255, 255), (x - 14, y), (x + 14, y), 2)
            pygame.draw.line(screen, (255, 255, 255), (x, y - 14), (x, y + 14), 2)

        # MENUS
        if state == MENU:
            screen.blit(big.render("FRUIT NINJA", True, (255,255,255)), (WIDTH//2 - 200, 80))
            screen.blit(mid.render("Hand Gesture Mode", True, (215,215,215)), (WIDTH//2 - 150, 150))
            screen.blit(mid.render(f"Difficulty: {difficulty} (1/2/3)", True, (215,215,215)), (WIDTH//2 - 180, 200))
            screen.blit(mid.render("Press C for Classic or T for Time Mode", True, (220,220,220)), (WIDTH//2 - 220, 250))
            screen.blit(mid.render("Press ENTER to Start", True, (255,255,255)), (WIDTH//2 - 150, 300))
            screen.blit(font.render("Gestures: FIST=Pause | TWO=Resume | OK=Menu", True, (200,200,200)), (WIDTH//2 - 200, 360))
        elif state == PAUSE:
            screen.blit(big.render("PAUSED", True, (255,255,255)), (WIDTH//2 - 120, HEIGHT//2 - 70))
            screen.blit(mid.render("Hold TWO FINGERS to Resume", True, (220,220,220)), (WIDTH//2 - 180, HEIGHT//2 + 10))
        elif state == GAMEOVER:
            screen.blit(big.render("GAME OVER", True, (255,90,90)), (WIDTH//2 - 180, HEIGHT//2 - 90))
            screen.blit(mid.render(f"Score: {score}   High: {highscore}", True, (255,255,255)), (WIDTH//2 - 160, HEIGHT//2 - 20))
            screen.blit(mid.render("Press R for Menu or Hold OK SIGN", True, (220,220,220)), (WIDTH//2 - 210, HEIGHT//2 + 50))

        pygame.display.flip()

    cap.release()
    pygame.quit()

if __name__ == "__main__":
    main()

import pygame
import random
import os
import sys

# -------------------- Inicialização --------------------
pygame.init()
pygame.mixer.quit()  # Reinicia
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)


# Tela
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Mãe Multitarefa: Caos no Café da Manhã")

clock = pygame.time.Clock()
FPS = 60

# Cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (50, 50, 50)

# -------------------- Assets e Sons --------------------
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

def load_image(name, scale=None, convert_alpha=True):
    path = os.path.join(ASSETS_DIR, name)
    image = pygame.image.load(path)
    if convert_alpha:
        image = image.convert_alpha()
    else:
        image = image.convert()
    if scale:
        image = pygame.transform.smoothscale(image, scale)
    return image

#path para o boss_lines
BOSS_LINE_PATH = os.path.join(ASSETS_DIR, "sounds", "boss_lines")

#Arquivos de fala
fala_arquivos = [
    "fala1.mp3",
    "fala2.mp3",
    "fala3.mp3",
    "fala4.mp3",
    "fala5.mp3",
    "fala6.mp3",
    "fala7.mp3",
]

#loop das falas
boss_lines = [pygame.mixer.Sound(os.path.join(BOSS_LINE_PATH, nome)) for nome in fala_arquivos]

# Sons
catch_sound      = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "sounds", "catch.flac"))
lose_life_sound  = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "sounds", "lose_life.wav"))
boss_music       = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "sounds", "boss_music.wav"))
pygame.mixer.music.load(os.path.join(ASSETS_DIR, "sounds", "background_music.mp3"))

# -------------------- Classes --------------------

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image_normal = load_image("veia.png", (80, 80))
        self.image_shield = load_image("veia_panescudo.png", (80, 80))
        self.image = self.image_normal
        self.rect = self.image.get_rect(midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20))
        self.speed = 7
        self.lives = 3
        self.power_up = False
        self.power_timer = 0
        self.shield_active = False
        self.shield_time = 5000  # ms
        self.shield_timer = 0

    def update(self):
        keys = pygame.key.get_pressed()
        dx = 0
        if keys[pygame.K_LEFT]:
            dx = -self.speed if not self.power_up else -self.speed * 1.5
        if keys[pygame.K_RIGHT]:
            dx = self.speed if not self.power_up else self.speed * 1.5
        self.rect.x += dx
        self.rect.clamp_ip(screen.get_rect())  # Keep inside screen

        if keys[pygame.K_SPACE] and not self.shield_active:
            self.shield_active = True
            self.shield_timer = pygame.time.get_ticks()

        if self.shield_active:
            elapsed = pygame.time.get_ticks() - self.shield_timer
            if elapsed > self.shield_time:
                self.shield_active = False

        self.image = self.image_shield if self.shield_active else self.image_normal


class Item(pygame.sprite.Sprite):
    def __init__(self, image, points, power_up=False):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)
        self.rect.y = random.randint(-150, -40)
        self.speed_y = random.randint(3, 7)
        self.points = points
        self.is_power = power_up

    def update(self):
        self.rect.y += self.speed_y
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


class CaixaMissil(pygame.sprite.Sprite):
    def __init__(self, x, y, target):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill((150, 75, 0))  # marrom
        self.rect = self.image.get_rect(center=(x, y))
        self.target = target
        self.speed = 4

    def update(self):
        dx = self.target.rect.centerx - self.rect.centerx
        dy = self.target.rect.centery - self.rect.centery
        dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)
        self.rect.x += int(self.speed * dx / dist)
        self.rect.y += int(self.speed * dy / dist)
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


# Carregamento da imagem do mini boss
boss_img = pygame.image.load("assets/entregador_temporal.png").convert_alpha()
boss_img = pygame.transform.smoothscale(boss_img, (160, 120))  # ajuste o tamanho conforme necessário


class MiniBossTemporal(pygame.sprite.Sprite):
    def __init__(self, target):
        super().__init__()
        self.image = boss_img  # Imagem já carregada no início do código
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.speed_x = 4
        self.last_shot = pygame.time.get_ticks()
        self.health = 5
        self.target = target

        # Frases para exibir como texto
        self.phrases = [
            "Dona Neide: Essas entregas tinham dono!",
            "Dona Neide: Cuidado com o frete!",
            "Dona Neide: A greve acabou!",
            "Dona Neide: Isso não estava nos Correios!",
        ]

        # Carregamento seguro das falas de voz
        boss_line_path = os.path.join("assets", "sounds", "boss_lines")
        fala_arquivos = [
            "fala1.mp3",
            "fala2.mp3",
            "fala3.mp3",
            "fala4.mp3",
            "fala5.mp3",
            "fala6.mp3",
            "fala7.mp3",
        ]
        self.voices = [pygame.mixer.Sound(os.path.join(boss_line_path, f)) for f in fala_arquivos]

    def update(self):
        self.rect.x += self.speed_x
        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            self.speed_x *= -1

        now = pygame.time.get_ticks()
        if now - self.last_shot > 1800:
            caixa = CaixaMissil(self.rect.centerx, self.rect.bottom, self.target)
            all_sprites.add(caixa)
            boss_missiles.add(caixa)
            self.last_shot = now

    def speak_random(self):
        # Fala uma frase aleatória e imprime no console
        texto = random.choice(self.phrases)
        voz = random.choice(self.voices)
        print(f"[MiniBoss]: {texto}")
        voz.play()


# -------------------- Funções --------------------

def load_assets():
    global background_img, meia_img, caneca_img, cubo_img, banana_img, toalha_img

    background_img = load_image("background.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
    meia_img = load_image("Gold_1.png", (70, 70))
    caneca_img = load_image("Silver.png", (70, 70))
    cubo_img = load_image("cubomagico.png", (90, 90))
    banana_img = load_image("banana.png", (70, 70))
    toalha_img = pygame.Surface((30, 30))
    toalha_img.fill(BLUE)

def spawn_item():
    choice = random.choices(
        population=["meia", "caneca", "cubo", "power", "banana", "toalha"],
        weights=[30, 25, 15, 10, 10, 10],
        k=1,
    )[0]

    if choice == "meia":
        return Item(meia_img, 10)
    elif choice == "caneca":
        return Item(caneca_img, 20)
    elif choice == "cubo":
        return Item(cubo_img, 50)
    elif choice == "banana":
        return Item(banana_img, -10)
    elif choice == "toalha":
        return Item(toalha_img, 0, power_up=True)
    else:
        return Item(cubo_img, 0, power_up=True)

def show_text_center(text, size=36, color=WHITE, y=None):
    font = pygame.font.SysFont("arial", size, bold=True)
    surface = font.render(text, True, color)
    x = SCREEN_WIDTH // 2 - surface.get_width() // 2
    if y is None:
        y = SCREEN_HEIGHT // 2 - surface.get_height() // 2
    screen.blit(surface, (x, y))


def show_start_screen():
    screen.fill(BLACK)
    show_text_center("Mãe Multitarefa: Caos no Café da Manhã", 48, YELLOW, SCREEN_HEIGHT // 3)
    show_text_center("Pressione qualquer tecla para começar", 28, WHITE, SCREEN_HEIGHT // 2)
    pygame.display.flip()
    waiting = True
    while waiting:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYUP:
                waiting = False


def show_game_over(score, highscore):
    screen.fill(RED)
    show_text_center("GAME OVER", 72, WHITE, SCREEN_HEIGHT // 3)
    show_text_center(f"Sua pontuação: {score}", 36, WHITE, SCREEN_HEIGHT // 2)
    show_text_center(f"Recorde: {highscore}", 36, WHITE, SCREEN_HEIGHT // 2 + 50)
    pygame.display.flip()
    pygame.time.wait(3000)


def show_cutscene(text):
    screen.fill(BLACK)
    font = pygame.font.SysFont("comic sans ms", 30)
    lines = text.split('\n')
    y = SCREEN_HEIGHT // 3
    for line in lines:
        txt = font.render(line, True, WHITE)
        screen.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2, y))
        y += 40
    pygame.display.flip()
    pygame.time.wait(3000)


def mini_boss_fight():
    global score
    boss = MiniBossTemporal(player)
    all_sprites.add(boss)

    pygame.mixer.music.stop()
    boss_music.play(-1)
    boss_running = True

    while boss_running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        all_sprites.update()

        hits = pygame.sprite.spritecollide(player, boss_missiles, True)
        for hit in hits:
            if player.shield_active:
                boss.health -= 1
                phrase = random.choice(boss.phrases)
                print(f"[Boss]: {phrase}")
                score += 20
            else:
                player.lives -= 1
                lose_life_sound.play()

        if boss.health <= 0 or player.lives <= 0:
            boss_running = False

        screen.blit(background_img, (0, 0))
        all_sprites.draw(screen)

        # Interface
        font = pygame.font.SysFont("arial", 24)
        screen.blit(font.render(f"Boss HP: {boss.health}", True, BLACK), (10, 10))
        screen.blit(font.render(f"Vidas: {player.lives}", True, BLACK), (10, 40))

        if player.shield_active:
            remaining = 1 - ((pygame.time.get_ticks() - player.shield_timer) / player.shield_time)
            bar_height = int(100 * remaining)
            pygame.draw.rect(screen, (100, 100, 255), (SCREEN_WIDTH - 30, 500 - bar_height, 20, bar_height))
            pygame.draw.rect(screen, BLACK, (SCREEN_WIDTH - 30, 400, 20, 100), 2)

        pygame.display.flip()

    boss_music.stop()
    all_sprites.remove(boss)
    boss_missiles.empty()

# -------------------- Variáveis globais --------------------

all_sprites = pygame.sprite.Group()
items = pygame.sprite.Group()
boss_missiles = pygame.sprite.Group()
player = Player()
all_sprites.add(player)

score = 0
highscore = 0
level = 1

# -------------------- Função para checar o nível --------------------

def check_level():
    global level
    if score > 200 and level == 1:
        level = 2
        show_cutscene("Fase 2: Velocidade Máxima!")
    elif score > 500 and level == 2:
        level = 3
        show_cutscene("Fase 3: Chefão Chegando!")
        mini_boss_fight()


# -------------------- Loop principal --------------------

def game_loop():
    global score, highscore

    pygame.mixer.music.play(-1)

    spawn_timer = 0
    dialogue_timer = 0
    lore_dialogues = [
        "Ah, essas meias! Nunca param de cair do céu...",
        "Se eu ganhasse uma moeda por cada caneca que eu pego... Espera, agora ganho pontos!",
        "Um cubo mágico? Sério? Como isso foi parar aqui?",
        "Eu devia estar tomando meu café, não correndo atrás de objetos voadores!",
    ]

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        spawn_timer += 1
        if spawn_timer > max(30 - level * 5, 10):
            item = spawn_item()
            all_sprites.add(item)
            items.add(item)
            spawn_timer = 0

        all_sprites.update()

        hits = pygame.sprite.spritecollide(player, items, True)
        for hit in hits:
            catch_sound.play()
            if hit.is_power:
                player.power_up = True
                player.power_timer = pygame.time.get_ticks()
            else:
                score += hit.points

        check_level()

        screen.blit(background_img, (0, 0))
        all_sprites.draw(screen)

        font = pygame.font.SysFont("comic sans ms", 30)
        score_text = font.render(f"Score: {score}", True, BLACK)
        screen.blit(score_text, (10, 10))
        life_text = font.render(f"Lives: {player.lives}", True, BLACK)
        screen.blit(life_text, (10, 40))
        highscore_text = font.render(f"Highscore: {highscore}", True, BLACK)
        screen.blit(highscore_text, (10, 70))

        if pygame.time.get_ticks() - dialogue_timer > 8000:
            dialogue = random.choice(lore_dialogues)
            dialogue_surface = font.render(dialogue, True, RED)
            screen.blit(dialogue_surface, (SCREEN_WIDTH // 2 - dialogue_surface.get_width() // 2, SCREEN_HEIGHT - 50))
            dialogue_timer = pygame.time.get_ticks()

        pygame.display.flip()

        if player.lives <= 0:
            running = False

    pygame.mixer.music.stop()

    if score > highscore:
        highscore = score

    show_game_over(score, highscore)


# -------------------- Função principal --------------------

def main():
    load_assets()
    show_start_screen()
    game_loop()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

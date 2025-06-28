import pygame
import random
import os
import sys
import json

# ==================== CONFIGURAÇÕES ====================
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')
SAVE_FILE = os.path.join(os.path.dirname(__file__), 'save_data.json')

# Estados do jogo
STATE_MENU = 'menu'
STATE_INTRO = 'intro'
STATE_PHASE1 = 'phase1'
STATE_MINI_BOSS = 'mini_boss'
STATE_INTERMEDIATE = 'intermediate'
STATE_FINAL_BOSS = 'final_boss'
STATE_GAME_OVER = 'game_over'
STATE_OPTIONS = 'options'

# ==================== INICIALIZAÇÃO ====================
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Dona Neide: Café da Manhã do Caos')
clock = pygame.time.Clock()

# ==================== UTILITÁRIOS ====================
def load_image(path, colorkey=None):
    full_path = os.path.join(ASSETS_DIR, path)
    try:
        img = pygame.image.load(full_path).convert_alpha()
    except Exception:
        img = pygame.Surface((50,50), pygame.SRCALPHA)
    return img

def load_sound(path):
    full_path = os.path.join(ASSETS_DIR, path)
    try:
        return pygame.mixer.Sound(full_path)
    except Exception:
        return None

def load_font(path, size):
    full_path = os.path.join(ASSETS_DIR, path) if path else None
    try:
        if full_path and os.path.isfile(full_path):
            return pygame.font.Font(full_path, size)
    except Exception:
        pass
    return pygame.font.SysFont(None, size)

# Carregar spritesheet e fatiar em frames
def load_spritesheet(path, frame_width, frame_height):
    sheet = load_image(path)
    frames = []
    sheet_width, sheet_height = sheet.get_size()
    # calcula número de frames na horizontal e vertical
    cols = sheet_width // frame_width
    rows = sheet_height // frame_height
    for row in range(rows):
        for col in range(cols):
            rect = pygame.Rect(col * frame_width, row * frame_height, frame_width, frame_height)
            frame = sheet.subsurface(rect).copy()
            frames.append(frame)
    return frames

# Save/Load progresso
def load_save():
    if os.path.isfile(SAVE_FILE):
        try:
            with open(SAVE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {'highscore': 0}

def save_data(data):
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f)
    except Exception:
        pass

save_data_dict = load_save()
HIGH_SCORE = save_data_dict.get('highscore', 0)

# ==================== ASSETS ====================
# Fontes
font_title = load_font('fonts/PressStart2P.ttf', 32)
font_menu = load_font('fonts/PressStart2P.ttf', 24)
font_small = load_font(None, 20)
font_scroll = load_font('fonts/starjedi.ttf', 24)

# Imagens HUD
heart_img = load_image('img/heart.png')  # ícone vida
shield_icon = load_image('img/shield_icon.png')

# Player e objetos
player_img = load_image('img/dona_neide.png')
projectile_img = load_image('img/projetil.png')
item_imgs = [load_image(f'img/item_{i}.png') for i in range(3)]
banana_img = load_image('img/banana.png')

# Boss images
entregador_img = load_image('img/entregador_temporal.png')
missile_img = load_image('img/caixa_missil.png')
# Explosão via spritesheet
# Ajuste frame_width e frame_height conforme sua spritesheet
EXPLOSION_FRAME_WIDTH = 64
EXPLOSION_FRAME_HEIGHT = 64
explosion_frames = load_spritesheet('img/explosion_spritesheet.png', EXPLOSION_FRAME_WIDTH, EXPLOSION_FRAME_HEIGHT)

fanhos_img = load_image('img/fanhos.png')
fanhos_projectile_img = load_image('img/fanhos_proj.png')

# Sons e canais
CHANNEL_MUSIC = 0
CHANNEL_SFX = 1
pygame.mixer.set_num_channels(8)
# Música de fundo
bg_music = load_sound('sfx/background_music.mp3')
if bg_music:
    pygame.mixer.Channel(CHANNEL_MUSIC).play(bg_music, loops=-1)
# Efeitos
sfx_catch = load_sound('sfx/catch.wav')
sfx_lose_life = load_sound('sfx/lose_life.wav')
sfx_shield = load_sound('sfx/shield.wav')
sfx_shot = load_sound('sfx/shot.wav')
sfx_explosion = load_sound('sfx/explosion.wav')
# Volumes iniciais
vol_music = 0.5
vol_sfx = 0.7
pygame.mixer.Channel(CHANNEL_MUSIC).set_volume(vol_music)
for ch in range(1,8): pygame.mixer.Channel(ch).set_volume(vol_sfx)

# ==================== CLASSES ====================
class Button:
    def __init__(self, text, x, y, w, h, callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.base_color = (50,50,100)
        self.hover_color = (80,80,150)
        self.current_color = self.base_color
        self.text_surf = font_menu.render(text, True, (255,255,255))
    def draw(self, surf):
        mx, my = pygame.mouse.get_pos()
        if self.rect.collidepoint((mx,my)):
            self.current_color = self.hover_color
        else:
            self.current_color = self.base_color
        pygame.draw.rect(surf, self.current_color, self.rect)
        txt = self.text_surf
        surf.blit(txt, txt.get_rect(center=self.rect.center))
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button==1:
            if self.rect.collidepoint(event.pos):
                self.callback()

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = player_img
        self.rect = self.image.get_rect(midbottom=(SCREEN_WIDTH//2, SCREEN_HEIGHT-10))
        self.speed = 7
        self.lives = 3
        self.shield_active = False
        self.shield_timer = 0
        self.shield_duration = 2000  # ms
    def update(self, dt):
        keys = pygame.key.get_pressed()
        dx=0
        if keys[pygame.K_LEFT]: dx=-self.speed
        if keys[pygame.K_RIGHT]: dx=self.speed
        self.rect.x += dx
        self.rect.clamp_ip(screen.get_rect())
        if keys[pygame.K_SPACE] and not self.shield_active:
            self.shield_active = True
            self.shield_timer = pygame.time.get_ticks()
            if sfx_shield: pygame.mixer.Channel(CHANNEL_SFX).play(sfx_shield)
        if self.shield_active:
            if pygame.time.get_ticks() - self.shield_timer > self.shield_duration:
                self.shield_active = False
    def draw(self, surf):
        surf.blit(self.image, self.rect)
        if self.shield_active:
            icon = pygame.transform.scale(shield_icon, (self.rect.width+20, self.rect.height+20))
            surf.blit(icon, icon.get_rect(center=self.rect.center))
    def shoot(self):
        proj = Projectile(self.rect.centerx, self.rect.top)
        if sfx_shot: pygame.mixer.Channel(CHANNEL_SFX).play(sfx_shot)
        return proj

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = projectile_img
        self.rect = self.image.get_rect(center=(x,y))
        self.speed = -10
    def update(self, dt):
        self.rect.y += self.speed
        if self.rect.bottom < 0: self.kill()

class Item(pygame.sprite.Sprite):
    def __init__(self, image, points, power=False):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(
            x=random.randint(0, SCREEN_WIDTH-image.get_width()), y=random.randint(-150,-40)
        )
        self.speed = random.randint(3,7)
        self.points = points
        self.power = power
    def update(self, dt):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT: self.kill()

class Explosion(pygame.sprite.Sprite):
    def __init__(self, center):
        super().__init__()
        self.frames = explosion_frames
        self.index = 0
        if self.frames:
            self.image = self.frames[0]
            self.rect = self.image.get_rect(center=center)
        else:
            self.image = pygame.Surface((30,30), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (255,150,0), (15,15), 15)
            self.rect = self.image.get_rect(center=center)
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 50
    def update(self, dt):
        if not self.frames: return
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.index += 1
            if self.index >= len(self.frames):
                self.kill()
            else:
                self.image = self.frames[self.index]
                self.rect = self.image.get_rect(center=self.rect.center)

class EntregadorTemporal(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = entregador_img
        self.rect = self.image.get_rect(midtop=(SCREEN_WIDTH//2, -100))
        self.health = 100
        self.max_health = 100
        self.speed = 3
        self.direction=1
        self.last_attack = pygame.time.get_ticks()
        self.attack_delay=1500
        self.missiles = pygame.sprite.Group()
        intro = load_sound('sfx/boss_intro.wav')
        if intro: pygame.mixer.Channel(CHANNEL_SFX).play(intro)
    def update(self, dt):
        if self.rect.top<50: self.rect.y += 2
        else:
            self.rect.x += self.speed * self.direction
            if self.rect.left<=0 or self.rect.right>=SCREEN_WIDTH: self.direction*=-1
            now=pygame.time.get_ticks()
            if now-self.last_attack>self.attack_delay:
                self.last_attack=now; self.attack()
        self.missiles.update(dt)
    def attack(self):
        missile = BossMissile(self.rect.centerx, self.rect.bottom)
        self.missiles.add(missile)
        s = load_sound('sfx/missile_launch.wav');
        if s: pygame.mixer.Channel(CHANNEL_SFX).play(s)
    def draw(self, surf):
        surf.blit(self.image, self.rect)
        bar_w=120; bar_h=10
        x=self.rect.centerx-bar_w//2; y=self.rect.top-15
        pygame.draw.rect(surf, (255,0,0), (x,y,bar_w,bar_h))
        pygame.draw.rect(surf, (0,255,0), (x,y,bar_w*(self.health/self.max_health),bar_h))
        self.missiles.draw(surf)
    def take_damage(self, amount):
        self.health-=amount; s=load_sound('sfx/hit.wav');
        if s: pygame.mixer.Channel(CHANNEL_SFX).play(s)
        if self.health<=0: self.health=0

class BossMissile(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = missile_img
        self.rect = self.image.get_rect(center=(x,y))
        self.speed=5
    def update(self, dt):
        self.rect.y += self.speed
        if self.rect.top>SCREEN_HEIGHT: self.kill()

class Fanhos(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = fanhos_img
        self.rect = self.image.get_rect(midtop=(SCREEN_WIDTH//2, -150))
        self.health = 300
        self.max_health=300
        self.phase=1
        self.timer=0
        self.projectiles=pygame.sprite.Group()
        #intro = load_sound('sfx/fanhos_intro.wav')
        #if intro: pygame.mixer.Channel(CHANNEL_SFX).play(intro)
    def update(self, dt):
        if self.rect.top<50: self.rect.y+=2
        else:
            self.timer+=dt
            if self.health<=200 and self.phase==1: self.phase=2
            if self.health<=100 and self.phase==2: self.phase=3
            if self.phase==1:
                self.rect.x += int(3 * (((self.timer//500)%2)*2 -1))
            elif self.phase==2:
                self.rect.x += int(5 * (((self.timer//400)%2)*2 -1))
            else:
                self.rect.x += int(7 * (((self.timer//300)%2)*2 -1))
            self.rect.clamp_ip(screen.get_rect())
            interval = max(800 - self.phase*200, 200)
            if self.timer % interval < dt:
                self.shoot()
        self.projectiles.update(dt)
    def shoot(self):
        if self.phase==1:
            proj=FanhosProjectile(self.rect.centerx, self.rect.bottom, 0)
            self.projectiles.add(proj)
        elif self.phase==2:
            for angle in (-1,0,1):
                proj=FanhosProjectile(self.rect.centerx + angle*20, self.rect.bottom, angle*2)
                self.projectiles.add(proj)
        else:
            for _ in range(5): proj=FanhosProjectile(random.randint(self.rect.left,self.rect.right), self.rect.bottom, random.uniform(-3,3)); self.projectiles.add(proj)
        s=load_sound('sfx/attack.wav');
        if s: pygame.mixer.Channel(CHANNEL_SFX).play(s)
    def draw(self, surf):
        surf.blit(self.image, self.rect)
        bar_w=300; bar_h=20; x=SCREEN_WIDTH//2-bar_w//2; y=10
        pygame.draw.rect(surf, (0,0,0), (x,y,bar_w,bar_h),2)
        pygame.draw.rect(surf, (255,0,0), (x,y,bar_w*(self.health/self.max_health),bar_h))
        self.projectiles.draw(surf)
    def take_damage(self, amount):
        self.health-=amount; s=load_sound('sfx/hit.wav');
        if s: pygame.mixer.Channel(CHANNEL_SFX).play(s)
        if self.health<0: self.health=0

class FanhosProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y, vx):
        super().__init__()
        self.image = fanhos_projectile_img
        self.rect = self.image.get_rect(center=(x,y))
        self.speed_y = 6
        self.vx = vx
    def update(self, dt):
        self.rect.y += self.speed_y
        self.rect.x += self.vx
        if self.rect.top>SCREEN_HEIGHT or self.rect.left<0 or self.rect.right>SCREEN_WIDTH:
            self.kill()

# ==================== CUTSCENE ====================
intro_lines = [
    "Em uma manhã caótica...",
    "Dona Neide preparava o café com pressa...",
    "Mas o tempo decidiu interferir...",
    "Objetos misteriosos começaram a cair...",
    "O Entregador Temporal surge!",
    "E algo ainda mais fanhóso aguarda..."
]
y_offset = SCREEN_HEIGHT
scroll_speed = 1
bg_color=(0,0,0); text_color=(255,255,0)
def play_intro():
    global y_offset
    y_offset=SCREEN_HEIGHT
    text_surfs=[font_scroll.render(line,True,text_color) for line in intro_lines]
    while y_offset + len(text_surfs)*40 > -100:
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.quit(); sys.exit()
        screen.fill(bg_color)
        cx=SCREEN_WIDTH//2
        for i,surf in enumerate(text_surfs):
            scale=1 - (i*0.02)
            surf_s=pygame.transform.rotozoom(surf,0,max(scale,0.2))
            rect=surf_s.get_rect(center=(cx, y_offset + i*40))
            screen.blit(surf_s, rect)
        y_offset -= scroll_speed
        pygame.display.flip()
        clock.tick(FPS)

# ==================== FASES ====================

def phase1_loop():
    player = Player()
    all_sprites=pygame.sprite.Group(player)
    items=pygame.sprite.Group()
    score=0; spawn_timer=0
    while True:
        dt=clock.tick(FPS)
        for e in pygame.event.get():
            if e.type==pygame.QUIT: return False, score
            if e.type==pygame.KEYDOWN and e.key==pygame.K_z:
                proj=player.shoot(); all_sprites.add(proj)
        spawn_timer+=dt
        if spawn_timer>1000:
            choice=random.choices(['item','banana'],weights=[70,30])[0]
            if choice=='item': img=random.choice(item_imgs); itm=Item(img,10)
            else: itm=Item(banana_img,-10)
            items.add(itm); all_sprites.add(itm)
            spawn_timer=0
        all_sprites.update(dt)
        for itm in pygame.sprite.spritecollide(player, items, True):
            if itm.points>0:
                score+=itm.points; ch=sfx_catch; 
                if ch: pygame.mixer.Channel(CHANNEL_SFX).play(ch)
            else:
                if not player.shield_active:
                    player.lives-=1; ch=sfx_lose_life; 
                    if ch: pygame.mixer.Channel(CHANNEL_SFX).play(ch)
        screen.fill((20,20,40))
        all_sprites.draw(screen)
        for i in range(player.lives): screen.blit(heart_img, (10+i*34,10))
        txt=font_small.render(f'Score: {score}',True,(255,255,255)); screen.blit(txt,(10,50))
        pygame.display.flip()
        if score>200: return True, score
        if player.lives<=0: return False, score

def mini_boss_loop():
    player=Player(); boss=EntregadorTemporal()
    all_sprites=pygame.sprite.Group(player); explosions=pygame.sprite.Group()
    while True:
        dt=clock.tick(FPS)
        for e in pygame.event.get():
            if e.type==pygame.QUIT: return False
            if e.type==pygame.KEYDOWN and e.key==pygame.K_z:
                proj=player.shoot(); all_sprites.add(proj)
        player.update(dt); boss.update(dt)
        for proj in [s for s in all_sprites if isinstance(s, Projectile)]:
            if boss.rect.colliderect(proj.rect): boss.take_damage(10); proj.kill(); explosions.add(Explosion(proj.rect.center))
        for m in list(boss.missiles):
            m.update(dt)
            if m.rect.colliderect(player.rect):
                if not player.shield_active: player.lives-=1
                else: boss.take_damage(5)
                boss.missiles.remove(m)
        explosions.update(dt)
        screen.fill((30,30,60))
        player.draw(screen); boss.draw(screen); explosions.draw(screen)
        for i in range(player.lives): screen.blit(heart_img,(10+i*34,10))
        pygame.display.flip()
        if boss.health<=0: return True
        if player.lives<=0: return False

def intermediate_loop():
    player=Player(); all_sprites=pygame.sprite.Group(player)
    items=pygame.sprite.Group(); waves=5; wave=1; spawn_timer=0
    while True:
        dt=clock.tick(FPS)
        for e in pygame.event.get():
            if e.type==pygame.QUIT: return False
            if e.type==pygame.KEYDOWN and e.key==pygame.K_z: all_sprites.add(player.shoot())
        spawn_timer+=dt
        if spawn_timer> max(1000- wave*100,300):
            for _ in range(wave): img=random.choice(item_imgs); itm=Item(img,10); items.add(itm); all_sprites.add(itm)
            spawn_timer=0; wave+=1
        all_sprites.update(dt)
        for itm in pygame.sprite.spritecollide(player, items, True): score+=itm.points if hasattr(itm,'points') else 0
        screen.fill((40,20,20)); all_sprites.draw(screen)
        for i in range(player.lives): screen.blit(heart_img,(10+i*34,10))
        txt=font_small.render(f'Wave {wave-1}',True,(255,255,255)); screen.blit(txt,(SCREEN_WIDTH-120,10))
        pygame.display.flip()
        if wave>waves: return True
        if player.lives<=0: return False

def final_boss_loop():
    player=Player(); boss=Fanhos(); explosions=pygame.sprite.Group(); bullets=pygame.sprite.Group()
    while True:
        dt=clock.tick(FPS)
        for e in pygame.event.get():
            if e.type==pygame.QUIT: return False
            if e.type==pygame.KEYDOWN and e.key==pygame.K_z: bullets.add(player.shoot()); all_sprites=pygame.sprite.Group()
        player.update(dt); boss.update(dt)
        for proj in list(bullets):
            if boss.rect.colliderect(proj.rect): boss.take_damage(10); proj.kill(); explosions.add(Explosion(proj.rect.center))
        for p in list(boss.projectiles):
            p.update(dt)
            if p.rect.colliderect(player.rect):
                if not player.shield_active: player.lives-=1
                boss.projectiles.remove(p)
        explosions.update(dt)
        screen.fill((10,10,30))
        player.draw(screen); boss.draw(screen); explosions.draw(screen); bullets.draw(screen)
        for i in range(player.lives): screen.blit(heart_img,(10+i*34,10))
        pygame.display.flip()
        if boss.health<=0:
            if HIGH_SCORE<0: save_data({'highscore':0})
            return True
        if player.lives<=0: return False

# ==================== MENU E OPÇÕES ====================
options = {'music_volume': vol_music, 'sfx_volume': vol_sfx}
buttons = []
def start_game():
    global game_state, HIGH_SCORE
    play_intro()
    ok, score1 = phase1_loop()
    if not ok: game_state=STATE_GAME_OVER; return
    ok = mini_boss_loop()
    if not ok: game_state=STATE_GAME_OVER; return
    ok = intermediate_loop()
    if not ok: game_state=STATE_GAME_OVER; return
    ok = final_boss_loop()
    if ok:
        if score1 > HIGH_SCORE: HIGH_SCORE = score1; save_data({'highscore': HIGH_SCORE})
    else:
        game_state=STATE_GAME_OVER

def open_options():
    global game_state
    game_state=STATE_OPTIONS

def quit_game():
    pygame.quit(); sys.exit()

button_start = Button('Jogar', SCREEN_WIDTH//2-100, 200, 200, 50, start_game)
button_options = Button('Opções', SCREEN_WIDTH//2-100, 270, 200, 50, open_options)
button_quit = Button('Sair', SCREEN_WIDTH//2-100, 340, 200, 50, quit_game)
buttons_menu = [button_start, button_options, button_quit]

def options_loop():
    global game_state, options
    slider_music = pygame.Rect(300, 200, 200, 10)
    slider_sfx = pygame.Rect(300, 260, 200, 10)
    dragging=None
    while game_state==STATE_OPTIONS:
        for e in pygame.event.get():
            if e.type==pygame.QUIT: quit_game()
            if e.type==pygame.MOUSEBUTTONDOWN:
                if slider_music.collidepoint(e.pos): dragging='music'
                if slider_sfx.collidepoint(e.pos): dragging='sfx'
            if e.type==pygame.MOUSEBUTTONUP: dragging=None
            if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE:
                game_state=STATE_MENU; return
            for b in buttons_menu: b.handle_event(e)
        if dragging:
            mx,_=pygame.mouse.get_pos()
            if dragging=='music':
                rel = max(0, min(mx-slider_music.x, slider_music.w))
                options['music_volume']=rel/slider_music.w; pygame.mixer.Channel(CHANNEL_MUSIC).set_volume(options['music_volume'])
            if dragging=='sfx':
                rel = max(0, min(mx-slider_sfx.x, slider_sfx.w))
                options['sfx_volume']=rel/slider_sfx.w
                for ch in range(1,8): pygame.mixer.Channel(ch).set_volume(options['sfx_volume'])
        screen.fill((30,30,30))
        txt=font_title.render('Opções',True,(255,255,255)); screen.blit(txt,txt.get_rect(center=(SCREEN_WIDTH//2,100)))
        pygame.draw.rect(screen,(100,100,100),slider_music); pygame.draw.rect(screen,(0,200,0),(slider_music.x,slider_music.y,slider_music.w*options['music_volume'],slider_music.h))
        mtxt=font_small.render('Volume Música',True,(255,255,255)); screen.blit(mtxt,(slider_music.x,slider_music.y-25))
        pygame.draw.rect(screen,(100,100,100),slider_sfx); pygame.draw.rect(screen,(0,200,0),(slider_sfx.x,slider_sfx.y,slider_sfx.w*options['sfx_volume'],slider_sfx.h))
        stxt=font_small.render('Volume Efeitos',True,(255,255,255)); screen.blit(stxt,(slider_sfx.x,slider_sfx.y-25))
        pygame.display.flip(); clock.tick(FPS)

# ==================== MAIN LOOP ====================
game_state = STATE_MENU
while True:
    if game_state==STATE_MENU:
        for e in pygame.event.get():
            if e.type==pygame.QUIT: quit_game()
            for b in buttons_menu: b.handle_event(e)
        screen.fill((0,0,50))
        title=font_title.render('Dona Neide: Caos no Café',True,(255,255,0)); screen.blit(title,title.get_rect(center=(SCREEN_WIDTH//2,100)))
        for b in buttons_menu: b.draw(screen)
        pygame.display.flip(); clock.tick(FPS)
    elif game_state==STATE_OPTIONS:
        options_loop()
    elif game_state==STATE_GAME_OVER:
        screen.fill((100,0,0))
        txt=font_title.render('Game Over',True,(255,255,255)); screen.blit(txt,txt.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT//2-30)))
        txt2=font_small.render(f'Highscore: {HIGH_SCORE}',True,(255,255,255)); screen.blit(txt2,txt2.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT//2+10)))
        pygame.display.flip()
        pygame.time.wait(3000); game_state=STATE_MENU
    # início é tratado por callback start_game

# main.py (no início do arquivo)
DEBUG_BOSS_ONLY = False # ← coloque False quando quiser o fluxo normal


import pygame
import random
import os
import sys
import cv2
import numpy as np

# -------------------- Inicialização --------------------
pygame.init()
pygame.mixer.quit()  # Reinicia
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
pygame.mixer.set_num_channels(8)  # Mais canais para múltiplos sons
pygame.mixer.music.set_volume(0.7)

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
BOSS_LINE_PATH = os.path.join(ASSETS_DIR, "boss_lines")

#Arquivos de fala
fala_arquivos = [
    "fala1.mp3",
    "fala2.mp3",
    "fala3.mp3",
    "fala4.mp3",
    "fala5.mp3",
    "fala6.mp3",

]

#loop das falas
boss_lines = [pygame.mixer.Sound(os.path.join(BOSS_LINE_PATH, nome)) for nome in fala_arquivos]

# Sons
catch_sound      = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "sounds", "catch.flac"))
lose_life_sound  = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "sounds", "lose_life.wav"))
boss_music       = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "sounds", "boss_music.wav"))
explosion_sound      = pygame.mixer.Sound(os.path.join(ASSETS_DIR, "sounds", "explosion_sound.wav"))
pygame.mixer.music.load(os.path.join(ASSETS_DIR, "sounds", "background_music.mp3"))

explosion_frames = []
for i in range(1, 7):
    img = load_image(f"explosao_{i}.png")
    explosion_frames.append(img)

# -------------------- Classes --------------------

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Sprites
        self.image_normal = load_image("neide_img.png", (80, 80))
        self.image_shield = load_image("veia_panescudo.png", (80, 80))
        self.image = self.image_normal
        self.rect = self.image.get_rect(midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20))

        # Movimento
        self.speed = 7
        self.lives = 3

        # Escudo
        self.shield_active = False
        self.shield_time = 5000  # duração do escudo em ms
        self.shield_timer = 0

        # Power‑up de velocidade
        self.power_up = False
        self.power_timer = 0
        self.power_duration = 6000  # duração do power em ms

        # Escorregão (banana)
        # Momento em que o slip termina (timestamp em ms)
        self.slip_end = 0
        # Duração do slip (2s = 2000ms)
        self.slip_duration = 2000

        #pulo
        self.jump_speed = -12     # Velocidade de impulso para cima
        self.gravity = 0.6        # Força da gravidade
        self.vel_y = 0            # Velocidade vertical atual
        self.on_ground = True     # Se está no chão ou não

        self.stuck = False
        self.stuck_end = 0



    def start_slip(self):
        """Gira 90° e imobiliza o player por slip_duration."""
        now = pygame.time.get_ticks()
        self.slip_end = now + self.slip_duration
        # Utilize sempre a imagem normal para rotacionar
        self.image = pygame.transform.rotate(self.image_normal, 90)

    def update(self):
        now = pygame.time.get_ticks()

        # Se estiver preso, ignora movimento
        if self.stuck:
            if now >= self.stuck_end:
                self.stuck = False
            else:
                return  # ❗️IMPORTANTE: não executa nada enquanto presa


        # Slip (escorregão)
        if now < self.slip_end:
            return
        else:
            self.image = self.image_shield if self.shield_active else self.image_normal

        # Teclado
        keys = pygame.key.get_pressed()
        dx = 0
        speed = self.speed * (1.5 if self.power_up else 1)

        if keys[pygame.K_LEFT]:
            dx = -speed
        elif keys[pygame.K_RIGHT]:
            dx = speed
        self.rect.x += dx
        self.rect.clamp_ip(screen.get_rect())

        # PULO
        if keys[pygame.K_UP] and self.on_ground:
            self.vel_y = self.jump_speed
            self.on_ground = False

        # GRAVIDADE
        self.vel_y += self.gravity
        self.rect.y += self.vel_y

        # COLISÃO COM CHÃO
        ground_y = SCREEN_HEIGHT - self.rect.height - 10
        if self.rect.bottom >= ground_y:
            self.rect.bottom = ground_y
            self.vel_y = 0
            self.on_ground = True

        # ESCUDO
        if keys[pygame.K_SPACE] and not self.shield_active:
            self.shield_active = True
            self.shield_timer = now

        if self.shield_active and now - self.shield_timer > self.shield_time:
            self.shield_active = False

        # BOOST
        if self.power_up and now - self.power_timer > self.power_duration:
            self.power_up = False

        # Restaura velocidade se estava lento
        if hasattr(self, "slow_until") and now > self.slow_until:
            self.speed = 7


class Item(pygame.sprite.Sprite):
    def __init__(self, image, points, power_up=False, tipo=None):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - self.rect.width)
        self.rect.y = random.randint(-150, -40)
        self.speed_y = random.randint(3, 7)
        self.points = points
        self.is_power = power_up
        self.tipo = tipo


    def update(self):
        self.rect.y += self.speed_y
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


class CaixaMissil(pygame.sprite.Sprite):
    def __init__(self, x, y, target):
        super().__init__()
        self.image = load_image("caixa_missil.png", (70, 70))
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

class meia_neon(pygame.sprite.Sprite):
    def __init__(self, x, y, target):
        super().__init__()
        self.image = load_image("meia_neon.png", (70, 70))
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
boss_img = load_image("entregador_temporal.png", (140,140)).convert_alpha()
boss_img = pygame.transform.smoothscale(boss_img, (140, 140))  # ajuste o tamanho conforme necessário


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
        boss_line_path = os.path.join(ASSETS_DIR, "boss_lines")
        fala_arquivos = [
            "fala1.mp3",
            "fala2.mp3",
            "fala3.mp3",
            "fala4.mp3",
            "fala5.mp3",
            "fala6.mp3",

        ]
        self.voices = [pygame.mixer.Sound(os.path.join(boss_line_path, f)) for f in fala_arquivos]

    def update(self):
        self.rect.x += self.speed_x
        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            self.speed_x *= -1

        now = pygame.time.get_ticks()
        if now - self.last_shot > 1800:
            missile = CaixaMissil(self.rect.centerx, self.rect.bottom, self.target)
            boss_missiles.add(missile)
            all_sprites.add(missile)
            self.last_shot = now


    def speak_random(self):
        # Fala uma frase aleatória e imprime no console
        texto = random.choice(self.phrases)
        voz = random.choice(self.voices)
        print(f"[MiniBoss]: {texto}")
        voz.play()


class MeiaPegajosa(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.frames = [load_image(f"meias_pegajosas/meia_{i}.png", (100, 100)) for i in range(8)]
        self.reverse_frames = list(reversed(self.frames[1:-1]))  # ignora o frame_0 e o final duplicado
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(x, y))
        self.state = "falling"
        self.velocity_y = 6  # queda livre
        self.frame_index = 0
        self.last_update = pygame.time.get_ticks()
        self.animation_speed = 100  # ms por frame
        self.hold_duration = 3000  # tempo parada no frame final
        self.hold_start = None

    def update(self):
        now = pygame.time.get_ticks()

        if self.state == "falling":
            self.rect.y += self.velocity_y
            ground_y = SCREEN_HEIGHT - 15  # ajuste conforme o solo do jogo
            if self.rect.bottom >= ground_y:
                self.rect.bottom = ground_y
                self.state = "growing"
                self.frame_index = 1
                self.last_update = now

        elif self.state == "growing":
            if now - self.last_update > self.animation_speed:
                self.frame_index += 1
                if self.frame_index < len(self.frames):
                    self.image = self.frames[self.frame_index]
                    self.last_update = now
                else:
                    self.state = "hold"
                    self.hold_start = now

        elif self.state == "hold":
            self.image = self.frames[-1]
            if now - self.hold_start > self.hold_duration:
                self.state = "shrinking"
                self.frame_index = 0
                self.last_update = now

        elif self.state == "shrinking":
            if now - self.last_update > self.animation_speed:
                if self.frame_index < len(self.reverse_frames):
                    self.image = self.reverse_frames[self.frame_index]
                    self.frame_index += 1
                    self.last_update = now
                else:
                    self.kill()


class FanhosBoss(pygame.sprite.Sprite):
    def __init__(self, target):
        super().__init__()
        self.image = load_image("fanhos.png", (200, 160))
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, 100))
        
        # Vida
        self.health = 10
        self.max_health = 10
        
        # Referência ao jogador
        self.target = target
        
        # Movimento
        self.speed_x = 3
        
        # Timer de ataque
        self.last_attack = pygame.time.get_ticks()
        self.attack_interval = 2000  # em ms entre ataques
        self.attack_count = 0
        
        # Explosão da lã cósmica
        self.explosao_iniciada = False
        self.explodiu_com_lã = False
        self.explosao_timer = 0
        
        # Fala na tela
        self.fala_mostrada = False
        self.fala_timer = 0

    def get_attack_info(self):
        """
        Retorna a posição atual no ciclo de ataque (1 a 5).
        """
        return {"cycle_position": (self.attack_count % 5) + 1}

    def update(self):
        now = pygame.time.get_ticks()

        # Se a explosão estiver iniciada e ainda não explodiu por completo, pausa tudo
        if self.explosao_iniciada and not self.explodiu_com_lã:
            # Exibe fala apenas uma vez
            if self.fala_mostrada and now - self.fala_timer > 2000:
                self.fala_mostrada = False
            return

        # Movimento lateral
        self.rect.x += self.speed_x
        if self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
            self.speed_x *= -1

        # Checa explosão de Lã Cósmica aos 50% de vida
        if self.health <= self.max_health // 2 and not self.explodiu_com_lã:
            if not self.explosao_iniciada:
                # Inicia explosão
                self.explosao_iniciada = True
                self.explosao_timer = now
                self.fala_mostrada = True
                self.fala_timer = now
                print("FANHOS: Lã... Cósmica... ATIVAR!")
                return
            elif now - self.explosao_timer > 3000:
                # Conclui explosão
                self.explodiu_com_lã = True
                self.health -= 3
                explosion_sound.play()

        if now - self.last_attack >= self.attack_interval:
                # Incrementa o contador de ciclos
                self.attack_count += 1

                # Calcula em que posição do ciclo estamos (1–5)
                cycle = (self.attack_count - 1) % 5 + 1

                # 1 a 4 → meia neon; 5 → meia pegajosa
                if cycle < 5:
                    meia = meia_neon(self.rect.centerx, self.rect.bottom, self.target)
                    boss_missiles.add(meia)
                else:
                    meia = MeiaPegajosa(self.rect.centerx, self.rect.bottom)
                    meias_pegajosas.add(meia)

                all_sprites.add(meia)
                # Reseta timer
                self.last_attack = now

import pygame
import cv2
import numpy as np
import os
import threading
import time

class VideoCutsceneManager:
    def __init__(self, screen, clock, assets_dir):
        self.screen = screen
        self.clock = clock
        self.cutscenes_dir = os.path.join(assets_dir, "cutscenes")
        
        # Caminhos dos vídeos (sem áudio)
        self.videos_dir = os.path.join(self.cutscenes_dir, "videos")
        # Caminhos dos áudios separados
        self.audio_dir = os.path.join(self.cutscenes_dir, "audio")
        
        self.videos = {
            "intro1": "intro1.mp4",
            "intro2": "intro2.mp4", 
            "after_phase1": "after_phase1.mp4",
            "after_phase2": "after_phase2.mp4",
            "before_final": "before_final.mp4",
            "ending": "ending.mp4"
        }
        
        # Controle de áudio
        self.current_sound = None
        self.audio_thread = None
        self.stop_audio_flag = False
    
    def play_audio_thread(self, audio_path, delay=0):
        """Thread separada para reproduzir áudio"""
        try:
            if delay > 0:
                time.sleep(delay)
            
            if self.stop_audio_flag:
                return
            
            # Tenta diferentes formatos de áudio
            audio_formats = [
                audio_path,  # Formato original (.ogg)
                audio_path.replace('.ogg', '.wav'),  # Alternativa WAV
                audio_path.replace('.ogg', '.mp3'),  # Alternativa MP3
            ]
            
            for audio_file in audio_formats:
                if os.path.exists(audio_file):
                    print(f"Tentando reproduzir áudio: {audio_file}")
                    
                    # Para música de fundo atual
                    pygame.mixer.music.stop()
                    
                    if audio_file.endswith('.mp3'):
                        # Usa pygame.mixer.music para MP3
                        pygame.mixer.music.load(audio_file)
                        pygame.mixer.music.set_volume(0.8)
                        pygame.mixer.music.play()
                        self.current_sound = "music"
                        print(f"Áudio MP3 iniciado: {audio_file}")
                    else:
                        # Usa pygame.mixer.Sound para WAV/OGG
                        self.current_sound = pygame.mixer.Sound(audio_file)
                        self.current_sound.set_volume(0.8)
                        self.current_sound.play()
                        print(f"Áudio Sound iniciado: {audio_file}")
                    
                    return  # Sucesso, sai da função
                    
            print(f"Nenhum arquivo de áudio encontrado para: {audio_path}")
            
        except Exception as e:
            print(f"Erro ao reproduzir áudio: {e}")
    
    def play_video(self, video_name, can_skip=True):
        """Reproduz um vídeo com áudio sincronizado"""
        if video_name not in self.videos:
            print(f"Vídeo {video_name} não encontrado")
            return
        
        # Caminhos dos arquivos
        video_path = os.path.join(self.videos_dir, self.videos[video_name])
        audio_path = os.path.join(self.audio_dir, f"{video_name}.ogg")
        
        # Verifica se o vídeo existe
        if not os.path.exists(video_path):
            print(f"Vídeo não existe: {video_path}")
            return
        
        print(f"Iniciando cutscene: {video_name}")
        print(f"Vídeo: {video_path}")
        print(f"Áudio: {audio_path}")
        
        # Para qualquer áudio anterior
        self.stop_all()
        
        # Inicia thread de áudio
        self.stop_audio_flag = False
        self.audio_thread = threading.Thread(
            target=self.play_audio_thread, 
            args=(audio_path, 0.1)  # Pequeno delay para sincronizar
        )
        self.audio_thread.daemon = True
        self.audio_thread.start()
        
        # Abre o vídeo
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Erro ao abrir vídeo: {video_path}")
            return
        
        # Propriedades do vídeo
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"Vídeo: {video_width}x{video_height} @ {fps}fps, {total_frames} frames")
        
        # Escala para caber na tela mantendo proporção
        screen_w, screen_h = self.screen.get_size()
        scale = min(screen_w / video_width, screen_h / video_height)
        new_w, new_h = int(video_width * scale), int(video_height * scale)
        x_offset, y_offset = (screen_w - new_w) // 2, (screen_h - new_h) // 2
        
        # Controle de tempo mais preciso
        clock = pygame.time.Clock()
        running = True
        frame_count = 0
        start_time = time.time()
        
        while running and frame_count < total_frames:
            ret, frame = cap.read()
            if not ret:
                print(f"Fim do vídeo ou erro na leitura (frame {frame_count})")
                break
            
            # Eventos
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and can_skip:
                    if event.key == pygame.K_SPACE:
                        print("Cutscene pulada pelo usuário")
                        running = False
            
            # Processamento do frame
            try:
                # Converte BGR (OpenCV) para RGB (Pygame)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Redimensiona
                frame = cv2.resize(frame, (new_w, new_h))
                # Rotaciona para o pygame (troca x,y)
                frame = np.transpose(frame, (1, 0, 2))
                # Cria surface
                frame_surface = pygame.surfarray.make_surface(frame)
                
                # Renderiza
                self.screen.fill((0, 0, 0))  # Fundo preto
                self.screen.blit(frame_surface, (x_offset, y_offset))
                
                # Instruções na tela
                if can_skip:
                    font = pygame.font.SysFont("arial", 18)
                    skip_text = font.render("ESPAÇO para pular", True, (255, 255, 255))
                    text_rect = skip_text.get_rect(topleft=(10, screen_h - 30))
                    pygame.draw.rect(self.screen, (0, 0, 0, 128), text_rect.inflate(10, 5))
                    self.screen.blit(skip_text, (10, screen_h - 30))
                
                # Mostra informações de debug (opcional)
                debug_font = pygame.font.SysFont("arial", 12)
                debug_text = debug_font.render(f"Frame: {frame_count}/{total_frames}", True, (200, 200, 200))
                self.screen.blit(debug_text, (10, 10))
                
                pygame.display.flip()
                
            except Exception as e:
                print(f"Erro ao processar frame {frame_count}: {e}")
                break
            
            # Sincronização de FPS
            frame_count += 1
            expected_time = frame_count / fps
            actual_time = time.time() - start_time
            
            if actual_time < expected_time:
                time.sleep(expected_time - actual_time)
            
            # Alternativa: usar clock.tick(fps) se preferir
            # clock.tick(fps)
        
        # Limpeza
        cap.release()
        self.stop_all()
        
        print(f"Cutscene {video_name} finalizada (frames: {frame_count})")
    
    def stop_all(self):
        """Para todos os vídeos e áudios"""
        self.stop_audio_flag = True
        
        # Para música
        pygame.mixer.music.stop()
        
        # Para sons
        if self.current_sound and self.current_sound != "music":
            try:
                self.current_sound.stop()
            except:
                pass
        
        # Espera thread de áudio terminar
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=1.0)
        
        self.current_sound = None
        print("Todos os áudios/vídeos parados")

# Função de teste para verificar se os arquivos existem
def debug_cutscene_files(assets_dir):
    """Função para debugar e verificar se os arquivos de cutscene existem"""
    cutscenes_dir = os.path.join(assets_dir, "cutscenes")
    videos_dir = os.path.join(cutscenes_dir, "videos")
    audio_dir = os.path.join(cutscenes_dir, "audio")
    
    print("=== DEBUG: Verificando arquivos de cutscene ===")
    print(f"Diretório base: {assets_dir}")
    print(f"Diretório cutscenes: {cutscenes_dir}")
    print(f"Diretório vídeos: {videos_dir}")
    print(f"Diretório áudio: {audio_dir}")
    
    videos = ["intro1.mp4", "intro2.mp4", "after_phase1.mp4", "after_phase2.mp4", "before_final.mp4", "ending.mp4"]
    
    for video in videos:
        video_path = os.path.join(videos_dir, video)
        video_name = video.replace('.mp4', '')
        
        # Verifica vídeo
        if os.path.exists(video_path):
            print(f"✓ Vídeo encontrado: {video}")
        else:
            print(f"✗ Vídeo não encontrado: {video_path}")
        
        # Verifica áudios em diferentes formatos
        audio_formats = ['.ogg', '.wav', '.mp3']
        audio_found = False
        
        for fmt in audio_formats:
            audio_path = os.path.join(audio_dir, f"{video_name}{fmt}")
            if os.path.exists(audio_path):
                print(f"✓ Áudio encontrado: {video_name}{fmt}")
                audio_found = True
                break
        
        if not audio_found:
            print(f"✗ Nenhum áudio encontrado para: {video_name}")
    
    print("=== Fim do debug ===")

# Exemplo de uso no seu código principal:
# debug_cutscene_files(ASSETS_DIR)  # Adicione esta linha para debugar

def final_boss_fight():
    global score, boss_missiles, all_sprites, background_img, player, cutscene_manager, explosion_frames

    # Inicialização de música e boss
    boss = FanhosBoss(player)
    all_sprites.add(boss)
    pygame.mixer.music.stop()
    boss_music.play(-1)

    cutscene_manager = VideoCutsceneManager(screen, clock, ASSETS_DIR)

    boss_running = True
    show_debug = False  # Pressione 'D' para ativar/desativar debug
    snap_triggered = False  # Controla o estalo de dedos

    print("=== LUTA FINAL CONTRA FANHOS INICIADA ===")
    print("Padrão de ataque: 4 Meias Neon → 1 Meia Pegajosa")
    print("Pressione 'D' durante a luta para ver informações de debug")

    while boss_running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_d:
                show_debug = not show_debug
                print(f"Debug {'ativado' if show_debug else 'desativado'}")

        all_sprites.update()

        if not snap_triggered and boss.health <= boss.max_health // 2:
            snap_triggered = True
            print("✨ FANHOS estalou os dedos! Explosão cósmica ativada! ✨")
            try:
                snap_sound.play()
            except:
                pass

            boss_music.stop()
            pygame.mixer.music.stop()

            # Anima a explosão crescendo com fala
            for frame in explosion_frames:
                screen.blit(background_img, (0, 0))
                all_sprites.draw(screen)

                explosion_rect = frame.get_rect(center=boss.rect.center)
                screen.blit(frame, explosion_rect)

                fala_font = pygame.font.SysFont("arial", 28, bold=True)
                fala_text = fala_font.render("FANHOS: Eu xou inevitável", True, (255, 200, 0))
                fala_bg = fala_text.get_rect(center=(SCREEN_WIDTH // 2, boss.rect.bottom + 40)).inflate(20, 10)
                pygame.draw.rect(screen, (0, 0, 0), fala_bg)
                screen.blit(fala_text, fala_text.get_rect(center=fala_bg.center))

                pygame.display.flip()
                pygame.time.delay(150)

            cutscene_manager.play_video("ending", can_skip=False)
            pygame.quit()
            sys.exit()

        if pygame.sprite.spritecollideany(player, meias_pegajosas) and not player.stuck:
            player.stuck = True
            player.stuck_end = pygame.time.get_ticks() + 2000
            print("🦶 Player pisou na meia pegajosa e ficou preso!")

        hits_neon = pygame.sprite.spritecollide(player, boss_missiles, True)
        for _ in hits_neon:
            if player.shield_active:
                boss.health -= 1
                score += 30
                print(f"🛡️ Meia neon bloqueada! Boss HP: {boss.health}")
            else:
                player.lives -= 1
                lose_life_sound.play()
                print(f"💔 Player atingido! Vidas restantes: {player.lives}")

        if boss.health <= 0 or player.lives <= 0:
            boss_running = False

        screen.blit(background_img, (0, 0))
        all_sprites.draw(screen)

        bar_width, bar_height = 300, 25
        bx = SCREEN_WIDTH // 2 - bar_width // 2
        by = 30
        pygame.draw.rect(screen, BLACK, (bx, by, bar_width, bar_height), 2)
        fill = int(bar_width * (boss.health / boss.max_health))
        pygame.draw.rect(screen, RED, (bx, by, fill, bar_height))

        boss_font = pygame.font.SysFont("arial", 20, bold=True)
        boss_name = boss_font.render("FANHOS - REI DAS MEIAS", True, BLACK)
        screen.blit(boss_name, (SCREEN_WIDTH // 2 - boss_name.get_width() // 2, 5))

        hud_font = pygame.font.SysFont("arial", 24)
        screen.blit(hud_font.render(f"Vidas: {player.lives}", True, BLACK), (10, 40))
        screen.blit(hud_font.render(f"Score: {score}", True, BLACK), (10, 10))

        attack_info = boss.get_attack_info()
        pattern_font = pygame.font.SysFont("arial", 18, bold=True)
        pattern_x, pattern_y = SCREEN_WIDTH - 200, 60
        screen.blit(pattern_font.render("Padrão de Ataque:", True, BLACK), (pattern_x, pattern_y))
        square_size = 25
        for i in range(5):
            sx = pattern_x + i * (square_size + 5)
            sy = pattern_y + 25
            if i < 4:
                color = (100,255,100) if i < attack_info['cycle_position']-1 else (50,150,50)
            else:
                color = (255,100,100) if i < attack_info['cycle_position']-1 else (150,50,50)
            if i == attack_info['cycle_position']-1:
                pygame.draw.rect(screen, (255,255,0), (sx-2, sy-2, square_size+4, square_size+4))
            pygame.draw.rect(screen, color, (sx, sy, square_size, square_size))
            pygame.draw.rect(screen, BLACK, (sx, sy, square_size, square_size), 2)
            symbol = "⚡" if i < 4 else "🧦"
            sym_surf = pattern_font.render(symbol, True, BLACK)
            sym_rect = sym_surf.get_rect(center=(sx+square_size//2, sy+square_size//2))
            screen.blit(sym_surf, sym_rect)

        legend_font = pygame.font.SysFont("arial", 14)
        screen.blit(legend_font.render("⚡ = Meia Neon", True, (100,255,100)), (pattern_x, pattern_y+60))
        screen.blit(legend_font.render("🧦 = Meia Pegajosa", True, (255,100,100)), (pattern_x, pattern_y+75))

        if player.stuck:
            stuck_font = pygame.font.SysFont("arial", 20, bold=True)
            stuck_text = stuck_font.render("PRESO NA MEIA!", True, (255,0,0))
            stuck_rect = stuck_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT-50))
            pygame.draw.rect(screen, WHITE, stuck_rect.inflate(20,10))
            screen.blit(stuck_text, stuck_rect)

        if boss.fala_mostrada:
            now = pygame.time.get_ticks()
            if now - boss.fala_timer < 6000:
                fala_font = pygame.font.SysFont("arial", 28, bold=True)
                fala_surf = fala_font.render("FANHOS: Lã... Cósmica... ATIVAR!", True, (255,255,0))
                bg_rect = fala_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT-40)).inflate(20,10)
                pygame.draw.rect(screen, BLACK, bg_rect)
                screen.blit(fala_surf, fala_surf.get_rect(center=bg_rect.center))
            else:
                boss.fala_mostrada = False

        pygame.display.flip()

    print("💀 GAME OVER! Fim de jogo.")
    show_text_center("GAME OVER", 72, WHITE, SCREEN_HEIGHT // 3)

    boss_music.stop()
    all_sprites.remove(boss)
    boss_missiles.empty()
    print("=== LUTA FINAL FINALIZADA ===")
# -------------------- Funções --------------------

def load_assets():
    global background_img, meia_img, caneca_img, cubo_img, banana_img, toalha_img

    background_img = load_image("background.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
    meia_img = load_image("item_0.png", (70, 70))
    caneca_img = load_image("item_2.png", (70, 70))
    cubo_img = load_image("item_1.png", (90, 90))
    banana_img = load_image("banana.png", (50, 50))
    toalha_img = load_image("item_3.png", (55, 55))
def spawn_item():

    ##"""Gera um item aleatório com image, pontos, power_up e tipo."""
    choice = random.choices(
        population=["meia", "caneca", "cubo", "banana", "toalha"],
        weights=[30, 25, 15, 10, 20],  # ajuste de pesos conforme desejar
        k=1,
    )[0]

    if choice == "meia":
        return Item(meia_img,   10, power_up=False, tipo="meia")
    elif choice == "caneca":
        return Item(caneca_img, 20, power_up=False, tipo="caneca")
    elif choice == "cubo":
        return Item(cubo_img,   50, power_up=False, tipo="cubo")
    elif choice == "banana":
        return Item(banana_img, -10, power_up=False, tipo="banana")
    elif choice == "toalha":
        return Item(toalha_img,  0, power_up=True,  tipo="toalha")

    # caso algo dê errado, volta como meia genérica
    return Item(meia_img, 5, power_up=False, tipo="meia")


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
    global score, boss_missiles
    boss = MiniBossTemporal(player)
    all_sprites.add(boss)
    random.choice(boss_lines).play()


    pygame.mixer.music.stop()
    boss_music.play(-1)
    boss_running = True
    
    hint_start_time = pygame.time.get_ticks()
    show_hint = True


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
        # --- Legenda temporária no início da luta ---
        if show_hint:
            now = pygame.time.get_ticks()
            if now - hint_start_time < 3000:  # 3 segundos
                hint_font = pygame.font.SysFont("arial", 24, bold=True)
                hint_text = hint_font.render("clique 'espaço' para se defender", True, RED)
                hint_bg = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 550)).inflate(20, 10)
                pygame.draw.rect(screen, (250, 250, 250), hint_bg, border_radius=8)
                pygame.draw.rect(screen, BLACK, hint_bg, 2, border_radius=8)
                screen.blit(hint_text, hint_text.get_rect(center=hint_bg.center))
            else:
                show_hint = False

        pygame.display.flip()

    boss_music.stop()
    all_sprites.remove(boss)

    for missile in boss_missiles:
        missile.kill()  # remove de todos os grupos
        
    boss_missiles.empty()


# -------------------- Variáveis globais --------------------

all_sprites = pygame.sprite.Group()
items = pygame.sprite.Group()
boss_missiles = pygame.sprite.Group()
player = Player()
all_sprites.add(player)
meias_pegajosas = pygame.sprite.Group()


score = 0
highscore = 0
level = 1

# -------------------- Função para checar o nível --------------------

def check_level():
    global level
    if score > 200 and level == 1:
        level = 2
        cutscene_manager.play_video("after_phase1")
        show_cutscene("Fase 2: Velocidade Máxima!")
        
    elif score > 500 and level == 2:
        level = 3
        cutscene_manager.play_video("after_phase2")
        show_cutscene("Fase 3: Chefão Chegando!")
        mini_boss_fight()
        
    elif score > 900 and level == 3:
        level = 4
        show_cutscene("Fase 4: Vem Pra Cima!")
    elif score > 1300 and level == 4:
        level = 5
        show_cutscene("Fase 5: Me DE Papai!")
    elif score > 1600 and level == 5:
        level = 6
        show_cutscene("Fase 6: Está Esquentando!")
    elif score > 1800 and level == 6:
        level = 7
        cutscene_manager.play_video("before_final")
        show_cutscene("Fase 7: Fanhos chegou!")
        player.image_normal = load_image("neide_img.png", (50, 50))
        player.image_shield = load_image("veia_panescudo.png", (50, 50))
        player.image = player.image_normal
        global background_img
        background_img = load_image("fanhos_arena.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
        final_boss_fight()


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

        # Spawn de itens
        spawn_timer += 1
        if level < 7 and spawn_timer > max(30 - level * 5, 10):
            item = spawn_item()
            all_sprites.add(item)
            items.add(item)
            spawn_timer = 0

        # Atualiza todos os sprites
        all_sprites.update()

        # Colisões
        hits = pygame.sprite.spritecollide(player, items, True)
        for hit in hits:
            catch_sound.play()
            if hit.tipo == "banana":
                player.start_slip()
            elif hit.is_power:
                player.power_up = True
                player.power_timer = pygame.time.get_ticks()
            else:
                score += hit.points

        check_level()

        # Renderização
        screen.blit(background_img, (0, 0))
        all_sprites.draw(screen)

        # HUD
        font = pygame.font.SysFont("comic sans ms", 30)
        score_text = font.render(f"Score: {score}", True, BLACK)
        life_text = font.render(f"Lives: {player.lives}", True, BLACK)
        highscore_text = font.render(f"Highscore: {highscore}", True, BLACK)
        screen.blit(score_text, (10, 10))
        screen.blit(life_text, (10, 40))
        screen.blit(highscore_text, (10, 70))

        # Barra Fúria da Mãe (com texto abaixo)
        if player.power_up:
            now = pygame.time.get_ticks()
            remaining = max(0, player.power_duration - (now - player.power_timer))
            frac = remaining / player.power_duration

            bar_w, bar_h = 30, 150
            x = SCREEN_WIDTH - bar_w - 20
            y = 100

            pad = 8
            box = pygame.Rect(x - pad, y - pad, bar_w + pad*2, bar_h + pad*2)
            pygame.draw.rect(screen, (240,240,240), box, border_radius=8)
            pygame.draw.rect(screen, BLACK, box, 2, border_radius=8)

            inner_h = int(bar_h * frac)
            inner = pygame.Rect(x, y + (bar_h - inner_h), bar_w, inner_h)
            pygame.draw.rect(screen, (0,150,255), inner, border_radius=4)
            pygame.draw.rect(screen, BLACK, (x, y, bar_w, bar_h), 2, border_radius=4)

            # Texto inferior “Fúria da Mãe”
            bottom_font = pygame.font.SysFont("arial", 20, bold=True)
            text_surf = bottom_font.render("Fúria da Mãe", True, BLACK)
            bx = SCREEN_WIDTH // 2 - text_surf.get_width() // 2
            by = SCREEN_HEIGHT - 30
            bg_rect = text_surf.get_rect(center=(SCREEN_WIDTH//2, by + 10)).inflate(16, 8)
            pygame.draw.rect(screen, (240,240,240), bg_rect, border_radius=6)
            pygame.draw.rect(screen, BLACK, bg_rect, 2, border_radius=6)
            screen.blit(text_surf, (bx, by))

        # Lore aleatório
        if pygame.time.get_ticks() - dialogue_timer > 8000:
            dialogue = random.choice(lore_dialogues)
            dialogue_surface = font.render(dialogue, True, RED)
            x = SCREEN_WIDTH // 2 - dialogue_surface.get_width() // 2
            screen.blit(dialogue_surface, (x, SCREEN_HEIGHT - 50))
            dialogue_timer = pygame.time.get_ticks()

        pygame.display.flip()

        # Fim de jogo
        if player.lives <= 0:
            running = False

    pygame.mixer.music.stop()
    if score > highscore:
        highscore = score

    show_game_over(score, highscore)


def test_final_mission_only():
    """
    Inicializa apenas o que é preciso para rodar
    toda a última missão: cutscene antes do boss,
    troca de cenário e luta final.
    """
    # 1) Inicialização mínima
    pygame.init()
    load_assets()  # carrega imagens, sons, fontes...
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    # 2) Criar player e gerenciador de cutscenes
    player = Player()
    cutscene_manager = VideoCutsceneManager(screen, clock, ASSETS_DIR)

    # 3) Tocar a cutscene “before_final”
    cutscene_manager.play_video("before_final", can_skip=True)
    show_cutscene("Fase 7: Fanhos chegou!")

    # 4) Ajustes visuais da fase 7 (mesmo que em check_level)
    player.image_normal = load_image("neide_img.png", (50, 50))
    player.image_shield = load_image("veia_panescudo.png", (50, 50))
    player.image = player.image_normal
    global background_img
    background_img = load_image("fanhos_arena.png", (SCREEN_WIDTH, SCREEN_HEIGHT))

    # 5) Finalmente, entra na luta final
    final_boss_fight()


# -------------------- Função principal --------------------

def main():
    global cutscene_manager
    
    load_assets()
    
    # Inicializa gerenciador de cutscenes
    cutscene_manager = VideoCutsceneManager(screen, clock, ASSETS_DIR)
    
    # Cutscenes de introdução
    cutscene_manager.play_video("intro1")
    cutscene_manager.play_video("intro2")
    
    show_start_screen()
    game_loop()
    pygame.quit()
    sys.exit()

# Chamada da função main no final do arquivo
if __name__ == "__main__":
    if DEBUG_BOSS_ONLY:
        # ao invés de test_boss_only(), chama o teste da missão completa
        test_final_mission_only()
    else:
        main()
import pygame
import os

# 초기화
pygame.init()

# 화면 크기 설정
screen_width = 800
screen_height = 400
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("공룡 게임")  # 여기서 함수 이름을 수정했습니다.

# 이미지 및 사운드 경로 설정
base_path = 'C:\\Users\\sm759\\Documents\\LSM'
cactus_image = pygame.image.load(os.path.join(base_path, 'cactus.png'))
cloud_image = pygame.image.load(os.path.join(base_path, 'cloud.png'))
dino_dead_image = pygame.image.load(os.path.join(base_path, 'dino_dead.png'))
dino_jump_image = pygame.image.load(os.path.join(base_path, 'dino_jump.png'))
dino_run1_image = pygame.image.load(os.path.join(base_path, 'dino_run1.png'))
dino_run2_image = pygame.image.load(os.path.join(base_path, 'dino_run2.png'))

point_sound = pygame.mixer.Sound(os.path.join(base_path, 'point.wav'))
die_sound = pygame.mixer.Sound(os.path.join(base_path, 'die.wav'))
jump_sound = pygame.mixer.Sound(os.path.join(base_path, 'jump.wav'))

# 이미지 크기 조정
cactus_image = pygame.transform.scale(cactus_image, (30, 60))

# 색상 설정
white = (255, 255, 255)
black = (0, 0, 0)

# 게임 속도 및 점수 설정
clock = pygame.time.Clock()
score = 0

# 공룡 클래스
class Dino:
    def __init__(self):
        self.run_images = [dino_run1_image, dino_run2_image]
        self.jump_image = dino_jump_image
        self.dead_image = dino_dead_image
        self.image = self.run_images[0]
        self.rect = self.image.get_rect()
        self.rect.x = 50
        self.rect.y = screen_height - 150
        self.is_jumping = False
        self.is_dead = False
        self.jump_speed = 10
        self.gravity = 1
        self.run_index = 0
        self.jump_pressed = False

    def draw(self):
        screen.blit(self.image, self.rect.topleft)

    def update(self):
        if self.jump_pressed:
            self.rect.y -= self.jump_speed
        else:
            if self.rect.y < screen_height - 150:
                self.rect.y += self.jump_speed
        if not self.is_dead:
            self.run_index = (self.run_index + 1) % 20
            self.image = self.run_images[self.run_index // 10]
        if self.is_dead:
            self.image = self.dead_image

    def jump(self):
        self.jump_pressed = True
        jump_sound.play()

# 장애물 클래스
class Cactus:
    def __init__(self):
        self.image = cactus_image
        self.rect = self.image.get_rect()
        self.rect.x = screen_width
        self.rect.y = screen_height - 120

    def draw(self):
        screen.blit(self.image, self.rect.topleft)

    def update(self):
        self.rect.x -= 10
        if self.rect.x < -self.rect.width:
            self.rect.x = screen_width

# 구름 클래스
class Cloud:
    def __init__(self):
        self.image = cloud_image
        self.rect = self.image.get_rect()
        self.rect.x = screen_width
        self.rect.y = 50

    def draw(self):
        screen.blit(self.image, self.rect.topleft)

    def update(self):
        self.rect.x -= 5
        if self.rect.x < -self.rect.width:
            self.rect.x = screen_width

# 게임 루프
running = True
dino = Dino()
cactus = Cactus()
cloud = Cloud()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                dino.jump()
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                dino.jump_pressed = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                dino.rect.x -= 5
            if event.key == pygame.K_RIGHT:
                dino.rect.x += 5
            if event.key == pygame.K_DOWN:
                dino.rect.y += 5

    # 화면 색상 채우기
    screen.fill(white)

    # 공룡, 장애물 및 구름 그리기
    dino.draw()
    cactus.draw()
    cloud.draw()

    # 공룡, 장애물 및 구름 업데이트
    dino.update()
    cactus.update()
    cloud.update()

    # 충돌 감지
    if dino.rect.colliderect(cactus.rect):
        dino.is_dead = True
        die_sound.play()
        print("충돌 발생! 게임 종료")
        running = False

    # 점수 표시
    score += 1
    if score % 100 == 0:
        point_sound.play()
    font = pygame.font.Font(None, 36)
    text = font.render(f'Score: {score}', True, black)
    screen.blit(text, (10, 10))

    # 화면 업데이트
    pygame.display.flip()

    # FPS 설정
    clock.tick(30)

pygame.quit()

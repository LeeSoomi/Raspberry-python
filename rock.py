import pygame
import sys
import random
from time import sleep

BLACK = (0, 0, 0)
padWidth = 480
padHeigh = 640

rockImage = ['./Spaceship/rock01.png','./Spaceship/rock02.png','./Spaceship/rock03.png','./Spaceship/rock04.png','./Spaceship/rock05.png',\
'./Spaceship/rock06.png','./Spaceship/rock07.png','./Spaceship/rock08.png','./Spaceship/rock09.png','./Spaceship/rock10.png',\
'./Spaceship/rock11.png','./Spaceship/rock12.png','./Spaceship/rock13.png','./Spaceship/rock14.png','./Spaceship/rock15.png',\
'./Spaceship/rock16.png','./Spaceship/rock17.png','./Spaceship/rock18.png','./Spaceship/rock19.png','./Spaceship/rock20.png',\
'./Spaceship/rock21.png','./Spaceship/rock22.png','./Spaceship/rock23.png','./Spaceship/rock24.png','./Spaceship/rock25.png',\
'./Spaceship/rock26.png','./Spaceship/rock27.png','./Spaceship/rock28.png','./Spaceship/rock29.png','./Spaceship/rock30.png']

def writeScore(count):
    global gamePad
    font = pygame.font.Font('./spaceship/NanumGothic.ttf', 20)
    text = font.render('파괴한 운석 수 : ' + str(count), True, (255, 255, 255))
    gamePad.blit(text, (10,0))

def writePassed(count):
    global gamePad
    font = pygame.font.Font('./spaceship/NanumGothic.ttf', 20)
    text = font.render('놓친 운석 수 : ' + str(count), True, (255, 0, 0))
    gamePad.blit(text, (300,0))

def drawObejct(obj, x, y):
    global gamePad
    gamePad.blit(obj, (x, y))

def initGame():
    global gamePad, clock, background, fighter, missile, explosion
    pygame.init()
    gamePad = pygame.display.set_mode((padWidth, padHeigh))
    pygame.display.set_caption('SpaceShip')
    background = pygame.image.load('./Spaceship/background.jpg')
    fighter = pygame.image.load('./Spaceship/spaceship.png')
    missile = pygame.image.load('./Spaceship/missile.png')
    explosion = pygame.image.load('./Spaceship/explosion.png')
    clock = pygame.time.Clock()

def runGame():
    global gamePad, clock, background, fighter, missile, explosion

    fighterSize = fighter.get_rect().size
    fighterWidth = fighterSize[0]
    fighterHeigh = fighterSize[1]

    x = padWidth * 0.45
    y = padHeigh * 0.9
    fighterX = 0

    missileXY =[]

    rock = pygame.image.load(random.choice(rockImage))
    rockSize = rock.get_rect().size
    rockWidth = rockSize[0]
    rockHeigh = rockSize[1]

    rockX = random.randrange(0, padWidth - rockWidth)
    rockY = 0
    rockSpeed = 2

    isShot = False
    shotCount = 0
    rockPassed = 0

    onGame = False
    while not onGame:
        for event in pygame.event.get():
            if event.type in [pygame.QUIT]:
                pygame.quit()
                sys.exit()
            if event.type in [pygame.KEYDOWN]:
                if event.key == pygame.K_LEFT:
                    fighterX -= 5
                elif event.key == pygame.K_RIGHT:
                    fighterX += 5
                elif event.key == pygame.K_SPACE:
                    missileX = x + fighterWidth/2
                    missileY = y - fighterHeigh/2
                    missileXY.append([missileX, missileY])
            if event.type in [pygame.KEYUP]:
                if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    fighterX = 0

        drawObejct(background, 0, 0)
        drawObejct(fighter, x, y)
        x += fighterX
        if x < 0:
            x = 0
        elif x > padWidth - fighterWidth:
            x = padWidth - fighterWidth
        if len(missileXY) != 0:
            for i, bxy in enumerate(missileXY):
                bxy[1] -= 10
                missileXY[i][1] = bxy[1]

                if bxy[1] < rockY:
                    if bxy[0] > rockX and bxy[0] < rockX + rockWidth:
                        missileXY.remove(bxy)
                        isShot = True
                        shotCount += 1

                if bxy[1] <= 0:
                    try:
                        missileXY.remove(bxy)
                    except:
                        pass
        if len(missileXY) != 0:
            for bx, by in missileXY:
                drawObejct(missile, bx, by)

        rockY += rockSpeed
        writeScore(shotCount)

        if rockY > padHeigh:
            rock = pygame.image.load(random.choice(rockImage))
            rockSize = rock.get_rect().size
            rockWidth = rockSize[0]
            rockHeigh = rockSize[1]
            rockX = random.randrange(0, padWidth - rockWidth)
            rockY = 0
            rockPassed += 1

        writePassed(rockPassed)

        if isShot == True:
            drawObejct(explosion, rockX, rockY)
            rockSize = rock.get_rect().size
            rockWidth = rockSize[0]
            rockHeigh = rockSize[1]
            rockX = random.randrange(0, padWidth - rockWidth)
            rockY = 0
            isShot = False

            rockSpeed += 0.02
            if rockSpeed >= 10:
                rockSpeed = 10

        drawObejct(rock, rockX, rockY)

        pygame.display.update()
        clock.tick(60)
    pygame.quit()

initGame()
runGame()

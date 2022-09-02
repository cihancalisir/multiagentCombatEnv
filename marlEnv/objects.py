import pygame
import math

class Square:
    def __init__(self, color, x, y, width, height, speed, target_x=None, target_y=None, target_id=None):
        self.rect = pygame.Rect(x,y,width,height)
        self.x = x
        self.y = y
        self.color = color
        self.direction = 'E'
        self.speed = speed

        self.dx_n = 0
        self.dy_n = 0
        self.x_n = 0
        self.y_n = 0
        self.stepcount = 0
        self.callHelp = False
        self.callHelpTime = 0
        self.gotoHelp = False

        self.numEnemiesINRadarArea = 0
        self.alive = True
        self.no = None
        self.target = None

        if not target_y == None:
            angle = math.atan2(target_y - y, target_x - x) #get angle to target in radians
            self.dx = math.cos(angle) * self.speed
            self.dy = math.sin(angle) * self.speed
            self.x = x
            self.y = y
            self.target_id = target_id

    def move(self):
        #self.x and self.y are floats (decimals) so I get more accuracy
        #if I change self.x and y and then convert to an integer for
        #the rectangle.
        self.stepcount += 1
        self.x = self.x_n + self.dx_n
        self.y = self.y_n + self.dy_n
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def moveDirection_b(self, direction=None, targetCoordinates=None):
        # if self.gotoHelp == False:
        #     if direction == 'E':
        #         self.rect.x = self.rect.x + self.speed
        #     elif direction == 'W':
        #         self.rect.x = self.rect.x - self.speed
        #     elif direction == 'N':
        #         self.rect.y = self.rect.y - self.speed
        #     elif direction == 'S':
        #         self.rect.y = self.rect.y + self.speed
        # else:
        #     self.gotoHelp = False
        angle = math.atan2(targetCoordinates[1] - self.y, targetCoordinates[0] - self.x) #get angle to target in radians
        self.dx = math.cos(angle) * self.speed
        self.dy = math.sin(angle) * self.speed
        self.x = self.x + self.dx
        self.y = self.y + self.dy
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)


    def moveDirection(self):
        self.x = self.x + self.dx
        self.y = self.y + self.dy
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def collided(self, other_rect):
        #Return True if self collided with other_rect
        return self.rect.colliderect(other_rect)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)


#Inheritance
class Bullet(Square):
    def __init__(self, color, x, y, width, height, speed, targetx, targety):
        super().__init__(color, x, y, width, height, speed)
        angle = math.atan2(targety-y, targetx-x) #get angle to target in radians
        # print('Angle in degrees:', int(angle * 180 / math.pi))
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed
        self.x = x
        self.y = y
        self.stepcount = 0

    # Override
    def move(self):
        #self.x and self.y are floats (decimals) so I get more accuracy
        #if I change self.x and y and then convert to an integer for
        #the rectangle.
        self.stepcount += 1
        self.x = self.x + self.dx
        self.y = self.y + self.dy
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
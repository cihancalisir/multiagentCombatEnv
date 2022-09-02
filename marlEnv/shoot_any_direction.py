import numpy as np
from math import sin, cos, radians, pi
import pygame, math, random
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import time
import math
from constants import *
from objects import Square, Bullet

pygame.init()
pygame.font.init()
maxtimestep = 300
maxepisode = 100000
font = pygame.font.SysFont('Arial', 25)
#Initialize variables:
clock = pygame.time.Clock()
surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# ----------------
# Build a square
# ----------------
def point_pos(x0, y0, d, theta):
    theta_rad = pi/2 - radians(theta)
    return x0 + d*cos(theta_rad), y0 + d*sin(theta_rad)

for episode in range(maxepisode):
    # ------------------- RESET --------------
    surface.fill(BLACK)
    surface.blit(font.render('RESET', True, YELLOW), (600, 375))
    pygame.display.flip()
    # surface.fill(black)
    time.sleep(0.5)
    num_agents = 4
    num_enemies = 20
    agents = []

    for i in range(num_agents):
        if i == 0:
            x = random.randint(50, 100)
        else:
            x += 250
        y = random.randint(30, int(SCREEN_HEIGHT / 2))
        sq = Square(GREEN, x, y, 25, 25, 10)
        agents.append(sq) # create agents

    bullets = []
    enemies = []

    obs_area = 400  # observation interval
    done = False
    direction = 0
    timestep = 0
    getmessage = False
    messagecounter = 0
    # spawn enemies on the top of the screen and tell them to move down
    while len(enemies) < num_enemies:  # 8'den az düşman kalmışsa hemen düşmanı artır
        a = random.randint(0, SCREEN_WIDTH - 40)
        b = random.randint(0, SCREEN_HEIGHT - 40)

        distances = []
        for agent in agents:
            a_x = agent.rect.centerx
            a_y = agent.rect.centery
            dist = math.sqrt((a_x - a) ** 2 + (a_y - b) ** 2)
            distances.append(dist)

        nearest_agent_id = np.where(distances == np.min(distances))[0][0]
        e = Square(YELLOW, a, b, 25, 25, 2,
                   target_x=agents[nearest_agent_id].rect.centerx,
                   target_y=agents[nearest_agent_id].rect.centery,
                   target_id=nearest_agent_id)
        enemies.append(e) # create target follower enemies

    while not done:
        timestep += 1
        #Get user input
        action = np.random.choice([0, 1], p=[.5, .5])
        agent_id = np.random.randint(len(agents)) #np.random.choice([0, 1, 2], p=[0.3, 0.3, 0.4])
        direction_action = np.random.choice([0, 1, 2, 3], p=[0.25, 0.25, 0.25, 0.25])

        # shotting action
        if action == 0:
            agent_x, agent_y = agents[agent_id].rect.centerx, agents[agent_id].rect.centery
            angle = np.random.randint(0, 360, 1)
            distance = np.random.randint(75, 125)
            target_x, target_y = point_pos(agent_x, agent_y, distance, angle)
            b = Bullet(RED, agent_x, agent_y, 7, 7, 20, target_x, target_y)
            bullets.append(b)

        # moving action
        elif action == 1:
            if direction_action == 0:
                agents[agent_id].moveDirection_b('N')
            elif direction_action == 1:
                agents[agent_id].moveDirection_b('W')
            elif direction_action == 3:
                agents[agent_id].moveDirection_b('S')
            else:
                agents[agent_id].moveDirection_b('E')


        # Update game objects
        for counter, b in enumerate(bullets):
            if b.stepcount < 8: # bir kurşun en fazla sqrt(dx, dy)*8 oranında yol alabilir
                b.move()
            else:
                del bullets[counter]


        agentID = -1
        for agent in agents:
            agentID += 1
            count = 0
            polygon = Polygon([
                               (agent.rect.x - obs_area / 2, agent.rect.y + obs_area / 2),
                               (agent.rect.x + obs_area / 2, agent.rect.y + obs_area / 2),
                               (agent.rect.x - obs_area / 2, agent.rect.y - obs_area / 2),
                               (agent.rect.x + obs_area / 2, agent.rect.y - obs_area / 2)
                               ])
            # ------------------------- is enemy in agent' particle observation area ---------------------------- #
              # to count enemies in radar area
            for s, e in enumerate(enemies):
                point = Point(e.rect.x, e.rect.y)
                if polygon.contains(point) and not getmessage:
                    count += 1
                    # print(count)
                    if count >= 3:
                        print("dostu çağır")
                        num_agents_last = len(agents)
                        for id, target_agent in enumerate(agents):
                            if not id == agentID: # mesaj atan hariç diğerlerinin mesaj bayrağını True yap
                                target_agent.getMessage()
                        getmessage = True
                        break
                else:
                    pass

        if getmessage: # yardım çağırma süresi
            messagecounter += 1
            print("help: ", messagecounter)
            if messagecounter == 10:
                getmessage = False
                messagecounter = 0



        for s, e in enumerate(enemies):
            e.moveDirection() # update enemy
            if e.rect.x < 0 or e.rect.x > SCREEN_WIDTH: # snır ihlali
                enemies.pop(s)

            if e.rect.y > SCREEN_HEIGHT or e.rect.y < 0:
                enemies.pop(s)

            distances = [] # follow the agents
            for agent in agents:
                a_x = agent.rect.centerx
                a_y = agent.rect.centery
                dist = math.sqrt((a_x - e.rect.centerx) ** 2 + (a_y - e.rect.centery) ** 2)
                distances.append(dist)

            nearest_agent_id = np.where(distances == np.min(distances))[0][0] # update goto point coordinates at any timestep
            target_x = agents[nearest_agent_id].rect.centerx
            target_y = agents[nearest_agent_id].rect.centery
            e.target_id = nearest_agent_id
            angle = math.atan2(target_y - e.y, target_x - e.x) #get angle to target in radians
            e.dx = math.cos(angle) * e.speed
            e.dy = math.sin(angle) * e.speed

        for i in reversed(range(len(bullets))): # vurulan düşmanları sil, vuran kurşunu atan agent'a ödül ver
            for j in reversed(range(len(enemies))):
                if bullets[i].collided(enemies[j].rect):
                    #e.color = white #TESTING
                    del enemies[j]
                    del bullets[i]
                    break

        for ii in reversed(range(len(agents))): # if an enemy arrives into agent bbox, which means "killed agent"
            for jj in reversed(range(len(enemies))):
                if agents[ii].collided(enemies[jj].rect): # new target assign to enemies
                    # del enemies[jj]
                    del agents[ii] # todo bu agent ceza alacak

                    if len(agents) == 0:
                        break

                    for enemy in enemies:
                        if enemy.target_id == ii:
                            distances = []
                            for agent in agents:
                                a_x_new = agent.rect.centerx
                                a_y_new = agent.rect.centery
                                dist = math.sqrt((a_x_new - enemy.x) ** 2 + (a_y_new - enemy.y) ** 2)
                                distances.append(dist)

                            nearest_agent_id = np.where(distances == np.min(distances))[0][0] # get new nearest target agent ID
                            enemy.target_id = nearest_agent_id

                            target_x = agents[nearest_agent_id].rect.centerx # go to the new target
                            target_y = agents[nearest_agent_id].rect.centery
                            angle = math.atan2(target_y - enemy.y, target_x - enemy.x)  # get angle to target in radians
                            enemy.dx = math.cos(angle) * enemy.speed
                            enemy.dy = math.sin(angle) * enemy.speed
                            enemy.x = enemy.x
                            enemy.y = enemy.y

                    #e.color = white #TESTING

                break

        for l, agent in enumerate(agents): # sınır dışına çıkan agentı sil
            if agent.rect.x < 0 or agent.rect.x > SCREEN_WIDTH:
                agents.pop(l) # todo bu agent sınır ihlali yaptı, ceza alacak

            if agent.rect.y > SCREEN_HEIGHT or agent.rect.y < 0:
                agents.pop(l)

        if timestep == maxtimestep or len(enemies) == 0 or len(agents) == 0: # done True
            done = True
            pygame.display.init()
            enemies = []
            agents = []
            bullets = []

        # All the drawing
        # fill surface with black
        surface.fill(BLACK)
        for b in bullets:
            b.draw(surface)

        for e in enemies:
            e.draw(surface)

        for agent in agents:
            agent.draw(surface)

        surface.blit(font.render('episode/timestep: {}/{}'.format(episode, timestep), True, YELLOW), (970, 10))
        surface.blit(font.render('num. agent: {}'.format(len(agents)), True, YELLOW), (1000, 35))
        surface.blit(font.render('num. enemy: {}'.format(len(enemies)), True, YELLOW), (1000, 60))
        pygame.display.flip()
        clock.tick(30) # -------------  30 FPS  -----------------

pygame.quit()
exit()

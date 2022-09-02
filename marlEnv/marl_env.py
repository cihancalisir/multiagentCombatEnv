import numpy as np
from math import sin, cos, radians, pi
import pygame, math, random
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import time
import math
from .constants import *
from .objects import Square, Bullet
from math import atan2, degrees, radians
import gym
import torch
from operator import itemgetter

class MarlDefenseEnv(gym.Env):
    """there many agents and per agent defense only yourself, no connection between agents"""
    def __init__(self, maxTimeStep=300, maxEpisode=100000, numAgents=4, numEnemies=20, agentPower=10, enemyPower=5):
        super().__init__()
        pygame.init()
        pygame.font.init()
        self.font = pygame.font.SysFont('Arial', 25)
        #Initialize variables:
        self.clock = pygame.time.Clock()
        self.surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

        self.maxTimeStep = maxTimeStep
        self.maxEpisode = maxEpisode

        self.numAgents = numAgents
        self.numEnemies = numEnemies

        self.agents = []
        self.bullets = []
        self.enemies = []
        self.state = []

        self.getmessage = False
        self.obs_area = agentPower * 50 # observation interval
        self.direction = 0
        self.messagecounter = 0
        self.episode = 0
        self.agentPower = agentPower
        self.bulletPower = int((agentPower / 10) * 5) # bullet effective range
        self.enemyPower = enemyPower

    def point_pos(self, x0, y0, d, theta):
        theta_rad = pi/2 - radians(theta)
        return x0 + d*cos(theta_rad), y0 + d*sin(theta_rad)

    def get_angle(self, point_1, point_2):  # These can also be four parameters instead of two arrays
        angle = atan2(point_1[1] - point_2[1], point_1[0] - point_2[0])
        # Optional
        angle = degrees(angle)
        return angle

    def getState(self):
        # her agent kaç düşmanı radarında görüyor, yardım istiyor mu, düşmanlarla ve agentlarla relatif baş açıları, agentlara olan uzaklıklar
        # agentların mühimmat sayısına göre shot action revizesi, her atışa ceza, kurşun boşa gitmişse ceza, kurşun hedefi vurduysa ödül
        # her agentın ödül değeri, her agentın diğer agentlarla yaptığı relatif baş açıları
        # todo
        # her agentın diğer agentlara olan uzaklığı ve relatif baş açısı


        for t, agent in enumerate(self.agents):
            selfState = [0] * (((self.numAgents - 1) * 2 + 5))
            if agent.alive:
                selfState[0] = t # agent ID
                selfState[1] = 1 if agent.callHelp else 0
                selfState[2] = agent.alive
                selfState[3] = agent.callHelpTime
                selfState[4] = agent.numEnemiesINRadarArea
                ids = list(range(0, len(self.agents)))
                ids.pop(t)
                c = 4
                for id in ids:
                    c += 1
                    angle = self.get_angle([agent.rect.x, agent.rect.y], [self.agents[id].rect.x, self.agents[id].rect.y])
                    selfState[c] = angle  # relative angle
                    c += 1
                    distance = math.sqrt((agent.rect.x - self.agents[id].rect.x) ** 2 + (agent.rect.y - self.agents[id].rect.y) ** 2)
                    selfState[c] = distance  # distance

            self.state["agent_{}".format(agent.no)] += selfState
            self.state["agent_{}".format(agent.no)] = torch.tensor(self.state["agent_{}".format(agent.no)]).float()
        return self.state

    def getReward(self):
        # toplam ödül
        # yardıma gitme ödülü-cezası
        # relatif konum ödülü, radar alanına giren düşmanı öldürebiliyor mu, yakınına gelmesine ne kadar izin veriyor vb.
        # kurşunu biten agent kaçmalı ya da yardım istemeli, bunun cezası ya da ödülü


        self.reward = 0

    def reset(self):
        # ------------------- RESET --------------
        # reset params
        self.episode += 1
        pygame.display.init()
        self.agents = []
        self.bullets = []
        self.enemies = []
        self.direction = 0
        self.timestep = 0
        self.getmessage = False
        self.messagecounter = 0
        self.reward = 0
        self.state = {}
        for i in range(self.numAgents):
            self.state["agent_{}".format(i)] = []


        # reset UI
        self.surface.fill(BLACK)
        self.surface.blit(self.font.render('RESET', True, YELLOW), (600, 375))
        pygame.display.flip()
        # surface.fill(black)
        time.sleep(0.5)
        # ----------------------------create agents--------------------------------------
        for i in range(self.numAgents):
            x = random.randint(30, 200) # 200 300
            y = random.randint(30, SCREEN_HEIGHT - 30)
            sq = Square(WHITE, x, y, 15, 15, self.agentPower) # power means that agent velocity, high speed high attack capacity
            sq.no = i
            self.agents.append(sq)  # create agents


        # -------------------------- create enemies --------------------------------------------------------------------------------
        # spawn enemies on the top of the screen and tell them to move down
        while len(self.enemies) < self.numEnemies:  # 8'den az düşman kalmışsa hemen düşmanı artır
            a = random.randint(300, SCREEN_WIDTH - 40)
            b = random.randint(0, SCREEN_HEIGHT - 40)

            distances = []
            for agent in self.agents:
                a_x = agent.rect.centerx
                a_y = agent.rect.centery
                dist = math.sqrt((a_x - a) ** 2 + (a_y - b) ** 2)
                distances.append(dist)

            nearest_agent_id = np.where(distances == np.min(distances))[0][0]
            e = Square(RED, a, b, 15, 15, self.enemyPower,
                       target_x=self.agents[nearest_agent_id].rect.centerx,
                       target_y=self.agents[nearest_agent_id].rect.centery,
                       target_id=nearest_agent_id)
            self.enemies.append(e)  # create target follower enemies

        self.updateObjects()
        _ = self.getState()

        return self.state

    def actionInterpreter(self, actionList):
        # print("*" * 50)
        for A in actionList:
            shottingAction = A[1][0]
            # print(shottingAction)
            directionAction = A[1][1]
            gotoHelp = A[1][2]
            chosedAgent = self.agents[A[0]]
            # print("agent ", A[0])
            if chosedAgent.alive: # seçilen agent ölü değilse
                # print(chosedAgent.numEnemiesINRadarArea, shottingAction)
                if not shottingAction == 1 and chosedAgent.numEnemiesINRadarArea != 0: # 61 >>> don't shot
                    targetInfo = chosedAgent.target[directionAction]
                    targetRelativeHeading = int(targetInfo[1]) if not targetInfo[1] == None else None
                    if not targetRelativeHeading == None:
                        # angle = shottingAction * 1 - 180
                        # if angle < 90:angle += 270
                        # else:angle -= 90
                        #
                        # if angle > 180:
                        #     act = angle // 30
                        # else:
                        #     act = -(angle // 30)
                        distance = 100
                        agent_x, agent_y = chosedAgent.rect.centerx, chosedAgent.rect.centery
                        target_x, target_y = targetInfo[2], targetInfo[3] #self.point_pos(agent_x, agent_y, targetInfo[0], targetRelativeHeading)
                        b = Bullet(YELLOW, agent_x, agent_y, 4, 4, 30, target_x, target_y)
                        # -------------------------------------------------------------------------------------------------------
                        # ---------------------------------   shot the nearest target    ---------------------------------------
                        # -------------------------------------------------------------------------------------------------------
                        # if not chosedAgent.target == None:
                        #     #print(angle) # , chosedAgent.target
                        #     # print(chosedAgent.target)
                        #     # bulletAngle = targetRelativeHeading + act
                        #     diff = np.abs(act)
                        #     if diff < 3:
                        #         diff = 1
                        #     gimbalReward = (1 / diff) * 50
                        #     self.reward += gimbalReward
                        # -------------------------------------------------------------------------------------------------------
                        # -------------------------------------------------------------------------------------------------------
                        # -------------------------------------------------------------------------------------------------------
                        self.reward -= 100 # used bullet punishment
                        self.bullets.append(b)
                    else:
                        self.reward -= 10 # no target
                    # time.sleep(2)
                elif not shottingAction == 1 and not chosedAgent.numEnemiesINRadarArea != 0: # düşman var ve ateş etmiyorsa
                    self.reward -= 10
                elif shottingAction == 1 and chosedAgent.numEnemiesINRadarArea == 0: # düşman yok ve ateş etmiyorsa
                    self.reward += 10
                    pass

                targetPoints = []
                # print(chosedAgent.callHelp, gotoHelp)
                if chosedAgent.callHelp == False and gotoHelp == 1: # yardım istenirken
                    for i, agent in enumerate(self.agents):
                        if i != chosedAgent.no and agent.callHelp == True and agent.alive:
                            chosedAgent.gotoHelp = True
                            targetPoints = [agent.rect.x, agent.rect.y]
                            # print("go to help")
                            chosedAgent.moveDirection_b(targetCoordinates=targetPoints)
                            self.reward += 100
                            break

                # directionList = ["N", "W", "S", "E", "DoNothing"]
                # direction = directionList[directionAction]
                # if not direction == "DoNothing":
                #     chosedAgent.moveDirection_b(direction)
                # else:
                #     chosedAgent.gotoHelp = False

                if len(targetPoints) == 0 and gotoHelp == 1: # yardım istenmezken yardım aksiyonunu alırsa ceza ver
                    self.reward -= 10
            else: # ölüyse, bu durumu state'de veriyoruz
                # print("agent is dead")
                if shottingAction == 1 and directionAction == 4 and gotoHelp == 0: # agent is dead, selected "do nothing action" means extra reward
                    self.reward += 50
                else:
                    self.reward -= 100

        "sınır dışına çıkan agentı sil"
        for l, agent in enumerate(self.agents):  #
            if agent.rect.x < 0 or agent.rect.x > SCREEN_WIDTH:
                # self.agents.pop(l) #bu agent sınır ihlali yaptı, ceza alacak
                agent.alive = False
                self.reward -= 1000

            if agent.rect.y > SCREEN_HEIGHT or agent.rect.y < 0:
                # self.agents.pop(l)
                agent.alive = False
                self.reward -= 1000

    def updateObjects(self):
        for counter, b in enumerate(self.bullets):
            if b.stepcount < self.bulletPower: # bir kurşun en fazla sqrt(dx, dy)*8 oranında yol alabilir
                b.move()
            else:
                del self.bullets[counter]

        "control agents radar area and whether agents called for help"
        agentID = -1

        for agent in self.agents:
            PO_state = [0] * self.numEnemies * 2
            agentID += 1
            count = 0
            if agent.alive:
                polygon = Polygon([
                                   (agent.rect.x - self.obs_area / 2, agent.rect.y + self.obs_area / 2),
                                   (agent.rect.x + self.obs_area / 2, agent.rect.y + self.obs_area / 2),
                                   (agent.rect.x - self.obs_area / 2, agent.rect.y - self.obs_area / 2),
                                   (agent.rect.x + self.obs_area / 2, agent.rect.y - self.obs_area / 2)
                                   ])

                # ------------------------- is enemy in agent' particle observation area ---------------------------- #
                # to count enemies in radar area
                c = 0
                targetsDistanceandAngle = []
                for s, e in enumerate(self.enemies):
                    point = Point(e.rect.x, e.rect.y) #
                    dist = math.sqrt( (e.rect.x - agent.rect.x)**2 + (e.rect.y - agent.rect.y)**2)
                    angle = self.get_angle([agent.rect.x, agent.rect.y], [e.rect.x, e.rect.y])

                    if dist < 30:
                        agent.alive = False # çok yakına gelirse agent ölür todo: ölen agentı cezalandır
                        self.reward -= 1000
                        # del self.agents[agentID]
                        break

                    if e.rect.x > (agent.rect.x - self.obs_area / 2) and e.rect.x < (agent.rect.x + self.obs_area / 2) \
                            and e.rect.y < (agent.rect.y + self.obs_area / 2) and e.rect.y > (agent.rect.y - self.obs_area / 2): # number of enemies in radar areas
                        PO_state[c] = dist
                        c += 1
                        PO_state[c] = angle
                        c += 1
                        count += 1
                        # print(count)
                        if angle < 0:
                            angle = 180 + np.abs(angle)
                        else:
                            angle = 180 - angle
                        targetsDistanceandAngle.append([dist, angle, e.rect.x, e.rect.y])
                        if count >= 3:
                            # print("call friends to help")
                            if not agent.callHelp:  # daha önce çağırmış olabilir
                                agent.callHelp = True
                                break
                    else:
                        c += 2



            if agent.alive: # agent hayattaysa update et, ayrı bir if olmasının sebebi yukarıda ölmüş olma ihtimalinin olmasıdır
                if count < 3:
                    agent.callHelp = False

                if count > 0:
                    res = sorted(targetsDistanceandAngle, key=itemgetter(0)) # nearest 5 target
                    while len(res) < 5:
                        res.append([None, None])
                    agent.target = res
                    agent.numEnemiesINRadarArea = count
                else:
                    agent.numEnemiesINRadarArea = 0




            self.state["agent_{}".format(agent.no)] += PO_state # her agentın radar alanı taramasını ekle



        " control and update enemies "
        for s, e in enumerate(self.enemies):
            e.moveDirection() # update enemy position
            # if e.rect.x < 0 or e.rect.x > SCREEN_WIDTH: # sınır ihlali
            #     self.enemies.pop(s)
            #
            # if e.rect.y > SCREEN_HEIGHT or e.rect.y < 0:
            #     self.enemies.pop(s)

            distances = [] # follow the agents
            agentNoList = []
            for agent in self.agents:
                if agent.alive:
                    a_x = agent.rect.centerx
                    a_y = agent.rect.centery
                    dist = math.sqrt((a_x - e.rect.centerx) ** 2 + (a_y - e.rect.centery) ** 2)
                    distances.append(dist)
                    agentNoList.append(agent.no)

            if len(agentNoList) > 0: # agent kalmamış done True geleceğinden bu adıma gerek yok
                nearest_agent_id = np.where(distances == np.min(distances))[0][0] # update goto point coordinates at any timestep
                target_x = self.agents[agentNoList[nearest_agent_id]].rect.centerx
                target_y = self.agents[agentNoList[nearest_agent_id]].rect.centery
                e.target_id = nearest_agent_id
                angle = math.atan2(target_y - e.y, target_x - e.x) #get angle to target in radians
                e.dx = math.cos(angle) * e.speed
                e.dy = math.sin(angle) * e.speed

        for i in reversed(range(len(self.bullets))): # vurulan düşmanları sil,  vuran kurşunu atan agent'a ödül ver
            for j in reversed(range(len(self.enemies))):
                if self.bullets[i].collided(self.enemies[j].rect):
                    #e.color = white #TESTING
                    del self.enemies[j]
                    del self.bullets[i]
                    self.reward += 1500
                    break

    def checkTermination(self):
        done = False
        numDeadAgents = 0
        for agent in self.agents:
            if not agent.alive:
                numDeadAgents += 1

        # print(numDeadAgents)
        if numDeadAgents == len(self.agents):
            done = True

        if self.timestep == self.maxTimeStep or len(self.enemies) == 0: # done True
            done = True
        else:
            # All the drawing
            # fill surface with black
            self.surface.fill(BLACK)
            for b in self.bullets:
                b.draw(self.surface)

            for e in self.enemies:
                e.draw(self.surface)

            for agent in self.agents:
                if agent.alive:
                    agent.draw(self.surface)

            self.surface.blit(self.font.render('episode/timestep: {}/{}'.format(self.episode, self.timestep), True, YELLOW), (SCREEN_WIDTH - 230, 10))
            self.surface.blit(self.font.render('num. agent: {}'.format(len(self.agents)-numDeadAgents), True, YELLOW), (SCREEN_WIDTH - 200, 35))
            self.surface.blit(self.font.render('num. enemy: {}'.format(len(self.enemies)), True, YELLOW), (SCREEN_WIDTH - 200, 60))
            pygame.display.flip()
            self.clock.tick(30) # -------------  30 FPS  -----------------
        return done

    def step(self, actionList): # [agentNo, actions[]]

        self.timestep += 1
        for i in range(self.numAgents):
            self.state["agent_{}".format(i)] = []
        self.reward = 0
        # update agents
        self.actionInterpreter(actionList)

        # Update game objects like enemies, bullets
        self.updateObjects()

        # check episode over?
        done = self.checkTermination()

        _ = self.getState()
        state = {}
        state["numAliveAgents"] = len(self.agents)
        state["stateVector"] = self.state
        reward = self.reward
        return self.state, reward, done, {}

    def close(self):
        pygame.quit()
        exit()

    def render(self):
        pass


class RandomAgent:
    def __init__(self, numAgents=4):
        self.numAgents = numAgents

    def selectAction(self, state=None):
        # Get user input
        # numAliveAgents = state["numAliveAgents"]
        actions = []
        for i in range(self.numAgents):
            shottingAction = np.random.randint(2)
            agent_id = i #np.random.choice([0, 1, 2], p=[0.3, 0.3, 0.4])
            direction_action = np.random.randint(5) # 5 is for do nothing
            gotoHelp = np.random.randint(2)
            actions.append([agent_id, [shottingAction, direction_action, gotoHelp]])
        return actions

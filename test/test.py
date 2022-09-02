from marlEnv.marl_env import MarlDefenseEnv, RandomAgent
import marlEnv
import gym

numAgents = 4
env = gym.make("Bullet-v0", maxTimeStep=300, maxEpisode=100000, numAgents=numAgents, numEnemies=10, agentPower=10, enemyPower=7)
#MarlDefenseEnv(maxTimeStep=300, maxEpisode=100000, numAgents=numAgents, numEnemies=20, agentPower=10, enemyPower=2)
agent = RandomAgent(numAgents=numAgents)


for e in range(100):
    state = env.reset()
    done = False
    episodeReward = 0
    while not done:
        # print(len(state["stateVector"]))
        actions = agent.selectAction(state)
        # print("shottingAction: {} agent ID: {} directionAction: {}".format(shottingAction, agent_id, direction_action, gotoHelp))
        state, reward, done, _ = env.step(actions)
        # print(reward)
        episodeReward += reward
    print("episode reward: ", episodeReward)

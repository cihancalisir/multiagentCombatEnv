from gym.envs.registration import register
from marlEnv.marl_env import MarlDefenseEnv


register(id='Bullet-v0', entry_point='marlEnv.marl_env:MarlDefenseEnv')


from gym.envs.registration import register
from custom_marl_env.marlEnv.marl_env import MarlDefenseEnv


register(id='Bullet-v0', entry_point='custom_marl_env.marlEnv.marl_env:MarlDefenseEnv')


from mesa import Agent
from mesa import Model
from mesa.space import MultiGrid
import random

class Household(Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model, pos)


class House(Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model, pos)
import random

from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation
from agents import *

class HouseActivation(RandomActivation):
    def __init__(self, model):
        super().__init__(model)
        self.model = model

    def get_available(self):
        return [house for house in self.model.schedule_House.agents if house.available] 


def compute_savings(model):
    total = 0
    for agents in self.schedule_Household:
        total += agents.savings
    
    return total


class HousingMarket(Model):
    def __init__(self, width, height):
        super().__init__()
        self.height = width
        self.width = height

        self.grid = MultiGrid(self.width, self.height, torus=True)
        self.stage_list = ["stage1", "stage2", "stage3"]
        self.schedule_House = HouseActivation(self)
        self.schedule_Household = RandomActivation(self)

        self.datacollector = DataCollector({
            "Overall Savings": compute_savings
        })


    def assign_houses(self):
        for i in range(len(self.schedule_House.agents)):
            self.schedule_House.agents[i].set_avalaibility(False)
            self.schedule_Household.agents[i].house = self.schedule_House.agents[i]
            self.schedule_House.agents[i].owner = self.schedule_Household.agents[i]
            



    def init_population(self, agent_type, n):
        '''
        Method that provides an easy way of making a bunch of agents at once.
        '''
        for i in range(n):
            x = random.randrange(self.width)
            y = random.randrange(self.height)

            self.new_agent(agent_type, (x, y))

    def new_agent(self, agent_type, pos):
        '''
        Method that creates a new agent, and adds it to the correct scheduler.
        '''
        agent = agent_type(self.next_id(), self, pos)

        self.grid.place_agent(agent, pos)
        getattr(self, f'schedule_{agent_type.__name__}').add(agent)

    def remove_agent(self, agent):
        '''
        Method that removes an agent from the grid and the correct scheduler.
        '''
        self.grid.remove_agent(agent)
        getattr(self, f'schedule_{type(agent).__name__}').remove(agent)

    def step(self):
        '''
        Method that calls the step method
        '''
        self.schedule_Household.step()

    def run_model(self, step_count=200):
        '''
        Method that runs the model for a specific amount of steps.
        '''
        for i in range(step_count):
            self.step()
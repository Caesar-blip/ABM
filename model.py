import random
import numpy as np

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
    for agent in model.schedule_Household.agents:
        total += agent.savings
    
    return total


def gini_coefficient(model):
    """Compute Gini coefficient of array of values"""
    # https://stackoverflow.com/questions/39512260/calculating-gini-coefficient-in-python-numpy
    x = np.empty(len(model.schedule_Household.agents))
    for i, agent in enumerate(model.schedule_Household.agents):
        x[i] = agent.savings
    diffsum = 0
    for i, xi in enumerate(x[:-1], 1):
        diffsum += np.sum(np.abs(xi - x[i:]))
    return diffsum / (len(x)**2 * np.mean(x))


class HousingMarket(Model):
    def __init__(self, height=20, width=20, initial_houses=20, initial_households=30, rental_cost=1000):
        super().__init__()
        self.height = width
        self.width = height
        self.initial_houses = initial_houses
        self.initial_households = initial_households
        self.rentals = self.initial_households - initial_houses
        self.rental_cost = rental_cost

        self.grid = MultiGrid(self.width, self.height, torus=True)
        self.stage_list = ["stage1", "stage2", "stage3"]
        self.schedule_House = HouseActivation(self)
        self.schedule_Household = RandomActivation(self)

        self.datacollector = DataCollector({
            "Overall Savings": compute_savings,
            "Gini": gini_coefficient
        })

        self.initialize_population(House, self.initial_houses)
        self.initialize_population(Household, self.initial_households)
        self.assign_houses()


    def initialize_population(self, agent_type, n):
        for i in range(n):
            x = random.randrange(self.width)
            y = random.randrange(self.height)   
            self.new_agent(agent_type, (x, y))  


    def assign_houses(self):
        for i in range(len(self.schedule_House.agents)):
            self.schedule_House.agents[i].set_avalaibility(False)
            self.schedule_Household.agents[i].house = self.schedule_House.agents[i]
            self.schedule_House.agents[i].owner = self.schedule_Household.agents[i]
            MultiGrid.move_agent(self=self.grid, agent=self.schedule_Household.agents[i], pos=self.schedule_House.agents[i].pos)
            

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
        i = 0
        # change the housing prices every year
        if i == 11:
            self.house_price_change = random.random()
            self.schedule_House.step()
            i = 0
        self.schedule_Household.step()

        self.datacollector.collect(self)
        i += 1


    def run_model(self, step_count=200):
        '''
        Method that runs the model for a specific amount of steps.
        '''
        for i in range(step_count):
            self.step()
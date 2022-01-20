import random
import numpy as np
import csv

from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation, StagedActivation
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


def compute_mean_income(model):
    total = 0
    agent_count = 0
    for agent in model.schedule_Household.agents:
        total += agent.income
        agent_count += 1
    return total / agent_count
    

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


def collect_income(Agent):
    if type(Agent) == Household:
        return Agent.income
    else:
        return None

def collect_ages(Agent):
    if type(Agent) == Household:
        return Agent.age
    else:
        return 0


class HousingMarket(Model):
    def __init__(self, height=20, width=20, initial_houses=10, initial_households=15, rental_cost=1000, 
    savings_lower = 0, savings_upper=500000, price_lower = 100000, price_upper=1000000):
        super().__init__()
        self.height = width
        self.width = height
        self.initial_houses = initial_houses
        self.initial_households = initial_households
        self.rentals = self.initial_households - initial_houses
        self.rental_cost = rental_cost
        self.savings_lower = savings_lower
        self.savings_upper = savings_upper
        self.price_lower = price_lower
        self.price_upper = price_upper
        self.incomes, self.income_distr = self.draw_income_distribution()
        self.ages, self.age_distr = self.draw_age_distribution()

        self.grid = MultiGrid(self.width, self.height, torus=True)

        self.schedule_House = HouseActivation(self)
        self.schedule_Household = RandomActivation(self)
        self.schedule = HouseActivation(self)

        # self.schedule_hhld = StagedActivation(self)
        # self.schedule_hhld.stage_list = ["stage1", "stage2", "stage3"]

        self.n_households = self.initial_households

        # keep track of number of periods that the model goes through, one step increases the period by 1
        self.period = 0

        self.datacollector = DataCollector(
            model_reporters={
                "Gini": gini_coefficient
            },
            agent_reporters={
                "Income": collect_income,
                "Price": 'price',
                "Age": collect_ages
            })


        self.initialize_population(House, self.initial_houses)
        self.initialize_population(Household, self.initial_households)
        self.assign_houses()


    def draw_income_distribution(self):
        incomes  = []
        counts = []

        with open('input_data/incomes.csv') as file:
            csv_reader = csv.reader(file, delimiter=',')
            for row in csv_reader:
                incomes.append([int(row[0])*1000/12,int(row[1])*1000/12])
                counts.append(int(row[2]))

        cum_counts = []
        for i in range(len(counts)):
            cum_counts.append(sum(counts[:i+1]))

        hhld_count = sum(counts)

        cum_ratios = [x / hhld_count for x in cum_counts]

        return incomes, cum_ratios
        

    def draw_age_distribution(self):
        ages = []
        age_counts = []

        with open('input_data/ages.csv') as file:
            csv_reader = csv.reader(file, delimiter=',')
            for row in csv_reader:
                ages.append(int(row[0]))
                age_counts.append(int(row[1]))

        # we consider housing market participants in age range 20-100
        ages = ages[20:]
        age_counts = age_counts[20:]
        cum_counts = []
        for i in range(len(age_counts)):
            cum_counts.append(sum(age_counts[:i+1]))

        pop_count = sum(age_counts)

        cum_ratios = [x / pop_count for x in cum_counts]

        return ages, cum_ratios

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
        if isinstance(agent_type,Household):
            self.n_households += 1

        agent = agent_type(self.next_id(), self, pos)

        self.grid.place_agent(agent, pos)
        getattr(self, f'schedule_{agent_type.__name__}').add(agent)
        getattr(self, "schedule").add(agent)


    def remove_agent(self, agent):
        '''
        Method that removes an agent from the grid and the correct scheduler.
        '''
        if isinstance(agent,Household):
            self.n_households -= 1

        self.grid.remove_agent(agent)
        getattr(self, f'schedule_{type(agent).__name__}').remove(agent)
        getattr(self, "schedule").remove(agent)


    def step(self):
        '''
        Method that calls the step method
        '''
        i = 1
        # change the housing prices every year
        if i == 12:
            self.house_price_change = random.random()
            self.schedule_House.step()
            i = 0
        self.schedule_Household.step()

        self.datacollector.collect(self)

        # check if population is still of same size 
        if self.n_households != self.initial_households:
            # if someone has died, add a new household agent to the model 
            n_deaths = self.n_households - self.initial_households
            self.initialize_population(Household,n_deaths)
        
        i += 1
        self.period += 1

    def run_model(self, step_count=200):
        '''
        Method that runs the model for a specific amount of steps.
        '''
        for i in range(step_count):
            self.step()
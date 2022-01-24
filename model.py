import random
import numpy as np
import csv

from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation, StagedActivation
from agents import *
from datacollection import *


class HouseActivation(RandomActivation):
    def __init__(self, model):
        super().__init__(model)
        self.model = model

    def get_available(self):
        return [house for house in self.model.schedule_House.agents if house.available]


class HousingMarket(Model):
    def __init__(self, height=20, width=20, initial_houses=100, initial_households=150, rental_cost=1000,
                 savings_lower=0, savings_upper=500000, price_lower=100000, price_upper=1000000,
                 payoff_perc_freehold=0.0025, inflation=0):
        super().__init__()
        self.height = width
        self.width = height
        self.initial_houses = initial_houses
        self.initial_households = initial_households
        self.rentals = self.initial_households - initial_houses

        # rental_cost is obsolete now, we use payoff_perc_freehold
        self.rental_cost = rental_cost

        # determines the percentage of house price that you pay off
        self.payoff_perc_freehold = payoff_perc_freehold

        self.savings_lower = savings_lower
        self.savings_upper = savings_upper
        self.price_lower = price_lower
        self.price_upper = price_upper
        self.incomes, self.income_distr = self.draw_income_distribution()
        self.ages, self.age_distr = self.draw_age_distribution()
        self.inflation = inflation

        self.grid = MultiGrid(self.width, self.height, torus=True)

        self.schedule_House = HouseActivation(self)
        self.schedule_Household = RandomActivation(self)
        self.schedule = HouseActivation(self)
        self.running = True

        self.n_households = self.initial_households

        # keep track of number of periods that the model goes through, one step increases the period by 1
        self.period = 0

        self.datacollector = DataCollector(
            model_reporters={
                "Gini": gini_coefficient,
                "Average Savings": average_savings,
                "Age -25 Savings": age_25_minus_savings,
                "Age 25-34 Savings": age_25_34_savings,
                "Age 35-44 Savings": age_35_44_savings,
                "Age 45-54 Savings": age_45_54_savings,
                "Age 55-64 Savings": age_55_64_savings,
                "Age 65-74 Savings": age_65_74_savings,
                "Age 75+ Savings": age_75_plus_savings,
                "Average Household Income": average_household_income,
                'Mean Household Age': mean_household_age,
                "Age -25 amount": age_25_amount,
                "Age 25-34 amount": age_25_34_amount,
                "Age 35-44 amount": age_35_44_amount,
                "Age 45-54 amount": age_45_54_amount,
                "Age 55-64 amount": age_55_64_amount,
                "Age 65-74 amount": age_65_74_amount,
                "Age 75+ amount": age_75_plus_amount,
                "Agent count": total_agents,
            },
            agent_reporters={
                "Income": collect_income,
                "Price": 'price',
                "Age": collect_ages,
            })
    
        self.initialize_population(House, self.initial_houses)
        self.initialize_population(Household, self.initial_households)
        self.assign_houses()

    def draw_income_distribution(self):
        incomes = []
        counts = []

        with open('input_data/incomes.csv') as file:
            csv_reader = csv.reader(file, delimiter=',')
            for row in csv_reader:
                incomes.append([int(row[0]) * 1000 / 12, int(row[1]) * 1000 / 12])
                counts.append(int(row[2]))

        cum_counts = []
        for i in range(len(counts)):
            cum_counts.append(sum(counts[:i + 1]))

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
            cum_counts.append(sum(age_counts[:i + 1]))

        pop_count = sum(age_counts)

        cum_ratios = [x / pop_count for x in cum_counts]

        return ages, cum_ratios

    def initialize_population(self, agent_type, n):
        for i in range(n):
            x = random.randrange(self.width)
            if x == 0:
                y = random.randrange(1, self.height)
            else:
                y = random.randrange(self.height)
            
            self.new_agent(agent_type, (x, y))

    def assign_houses(self):
        _len = len(self.schedule_House.agents)
        if len(self.schedule_Household.agents) < len(self.schedule_House.agents) : _len = len(self.schedule_Household.agents)
        for i in range(_len):
            self.schedule_House.agents[i].set_availability(False)
            self.schedule_Household.agents[i].house = self.schedule_House.agents[i]
            self.schedule_House.agents[i].owner = self.schedule_Household.agents[i]
            MultiGrid.move_agent(self=self.grid, agent=self.schedule_Household.agents[i],
                                 pos=self.schedule_House.agents[i].pos)

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
        if isinstance(agent_type, Household):
            self.n_households += 1

        agent = agent_type(self.next_id(), self, pos)

        self.grid.place_agent(agent, pos)
        getattr(self, f'schedule_{agent_type.__name__}').add(agent)
        getattr(self, "schedule").add(agent)

    def remove_agent(self, agent):
        '''
        Method that removes an agent from the grid and the correct scheduler.
        '''
        if isinstance(agent, Household):
            self.n_households -= 1

        self.grid.remove_agent(agent)
        getattr(self, f'schedule_{type(agent).__name__}').remove(agent)
        getattr(self, "schedule").remove(agent)

    def step(self):
        '''
        Method that calls the step method
        '''

        self.schedule.steps += 1
        # change the housing prices every year
        if self.period % 12 == 0:
            self.house_price_change = random.randint(-3 + self.inflation,3 + self.inflation)
            self.schedule_House.step()

        self.schedule_Household.step()
        self.datacollector.collect(self)

        # check if population is still of same size 
        if self.n_households != self.initial_households:
            # if someone has died, add a new household agent to the model 
            n_deaths = self.n_households - self.initial_households
            self.initialize_population(Household, n_deaths)

        self.period += 1

    def run_model(self, step_count=2):
        '''
        Method that runs the model for a specific amount of steps.
        '''
        for i in range(step_count):
            self.step()

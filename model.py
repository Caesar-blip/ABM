import random
import numpy as np
import csv
#
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
    def __init__(self, height=20, width=20, initial_houses=150, initial_households=150,
                 savings_lower=0, savings_upper=100000, price_lower=100000, price_upper=1000000,
                 payoff_perc_freehold=0.0025, inflation=0.02, house_price=400_000,
                 chi_parameter=6.5, maximum_age=100, minimum_age=20, age_utility_scaling = 0.01,
                 maximum_moving_age=65, bank_income_multiplier=8, fraction_good_houses=0.5,
                 price_shock_range=6, s_policy=False, a_policy=False, income_policy=False,
                 alpha_mean = .79, beta_mean = 1.13, lmbda_mean = 1.35):
        super().__init__()
        self.height = width
        self.width = height
        self.initial_houses = initial_houses
        self.initial_households = initial_households
        self.rentals = self.initial_households - initial_houses
        self.house_price = house_price
        self.chi_parameter = chi_parameter
        self.maximum_age = maximum_age
        self.minimum_age = minimum_age
        self.age_utility_scaling = age_utility_scaling
        self.maximum_moving_age = maximum_moving_age
        self.bank_income_multiplier = bank_income_multiplier
        self.fraction_good_houses = fraction_good_houses
        self.price_shock_range = price_shock_range

        # determines the percentage of house price that you pay off
        self.payoff_perc_freehold = payoff_perc_freehold

        self.savings_lower = savings_lower
        self.savings_upper = savings_upper
        self.price_lower = price_lower
        self.price_upper = price_upper
        self.incomes, self.income_distr = self.draw_income_distribution()
        self.ages, self.age_distr = self.draw_age_distribution()

        self.inflation = inflation
        self.total_inflation = 0
        self.yearly_inflation = 0
        self.income_distribution = np.load("Income Data/income_distribution.npy")

        self.grid = MultiGrid(self.width, self.height, torus=True)

        self.schedule_House = HouseActivation(self)
        self.schedule_Household = RandomActivation(self)
        self.schedule = HouseActivation(self)
        self.running = True

        self.n_households = self.initial_households

        self.s_policy = s_policy
        self.a_policy = a_policy
        self.income_policy = income_policy

        # behavioural data
        self.alpha_mean = alpha_mean
        self.beta_mean = beta_mean
        self.lmbda_mean = lmbda_mean

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
                'Mean House Price': mean_house_price,
                'Mean House Price Change': mean_house_price_change,
                "Age -25 amount": age_25_amount,
                "Age 25-34 amount": age_25_34_amount,
                "Age 35-44 amount": age_35_44_amount,
                "Age 45-54 amount": age_45_54_amount,
                "Age 55-64 amount": age_55_64_amount,
                "Age 65-74 amount": age_65_74_amount,
                "Age 75+ amount": age_75_plus_amount,
                "Agent count": total_agents,
                "Inflation": get_inflation,
                "Total Inflation": get_total_inflation,
                "Percentage Owned": percentage_owned
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

        '''
        cum_counts = []
        for i in range(len(age_counts)):
            cum_counts.append(sum(age_counts[:i + 1]))

        pop_count = sum(age_counts)

        cum_ratios = [x / pop_count for x in cum_counts]
        '''

        return ages, [ages, age_counts]

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
        if len(self.schedule_Household.agents) < len(self.schedule_House.agents): _len = len(
            self.schedule_Household.agents)
        for i in range(_len):
            self.schedule_House.agents[i].set_availability(False)
            self.schedule_Household.agents[i].house = self.schedule_House.agents[i]
            self.schedule_House.agents[i].owner = self.schedule_Household.agents[i]
            MultiGrid.move_agent(self=self.grid, agent=self.schedule_Household.agents[i],
                                 pos=self.schedule_House.agents[i].pos)
    '''
    def init_population(self, agent_type, n):
        for i in range(n):
            x = random.randrange(self.width)
            y = random.randrange(self.height)

            self.new_agent(agent_type, (x, y))
    '''         

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
        #print(f"Step: {self.schedule.steps}") 

        self.schedule.steps += 1

        """ Calculate monthly adjusted inflation and adjust incomes based on that """
        # Derived from Historical CPI data (US 2010->2021)
        self.monthly_inflation = np.random.normal(loc=self.inflation/12, scale=.00115, size=1)[0]
        self.total_inflation += self.monthly_inflation
        self.income_distribution[:, 1] *= 1 + self.monthly_inflation

        # Introduce a market shock every month and year
        self.house_price_shock = random.uniform(-0.5*self.price_shock_range + 100*self.monthly_inflation,0.5*self.price_shock_range + 100*self.monthly_inflation)
    

        self.schedule_House.step()

        self.schedule_Household.step()
        self.datacollector.collect(self)

        # check if population is still of same size 
        self.n_households = len(self.schedule_Household.agents)
        if self.n_households != self.initial_households:
            # if someone has died, add a new household agent to the model 
            n_deaths = self.initial_households - self.n_households
            self.initialize_population(Household, n_deaths)

        self.period += 1

    def run_model(self, step_count=2):
        '''
        Method that runs the model for a specific amount of steps.
        '''
        for i in range(step_count):
            self.step()

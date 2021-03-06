# from zoneinfo import available_timezones
from mesa import Agent
from mesa import Model
from mesa.space import MultiGrid
import random
import scipy
import numpy as np
import math
import pandas as pd
import copy


class Household(Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)
        self.pos = pos
        self.model = model
        self.savings = random.randint(int(self.model.savings_lower), int(self.model.savings_upper))
        self.age = self.set_age()

        self.income, self.bin, self.percentile = self.initialize_income_bin_percentile()
        self.house = None

        # No one starts with a mortgage
        self.mortgage = 0

        self.monthly_ageing = 0
        self.strategy = np.random.choice(["naive", "sophisticated"])
        self.months_renting = 0

        # Fix risk attitude parameters
        self.alpha = np.random.normal(loc = self.model.alpha_mean, scale=0.3)
        self.beta = np.random.normal(loc = self.model.beta_mean, scale=0.66)
        self.lmbda = np.random.normal(loc = self.model.lmbda_mean, scale=2.59)

        self.sold_house = None



    def get_mortgage_quote(self):
        """
        Calculates mortage quote based on monthly household disposable income
        Example:
        - Disposable income (mean) of 3500 per month ~ 42k per year ~ 60k gross per year
        - Based on several mortgage calculators, mortgage is ~ 5-6x gross income. 
        - i.e. 60k should result in 300k. Thus, disposable income is ~ 8x to mortgage
        - (this is a naive and deterministic mortgage quote)
        """
        
        deterministic_quote = self.income * 12 * self.model.bank_income_multiplier
        return deterministic_quote

    def set_age(self):
        # if model is past initialisation, new agents in the model are "born" at youngest available age

        if self.model.period > 0:
            return self.model.minimum_age

        # if model is initialised, distribute age following Dutch age distribution among agents
        # This is done using Acceptance-Rejection Sampling
        ages_counts = self.model.age_distr[1]

        for i in range(len(self.model.ages)):
            while True:
                x = random.randrange(0, 80)
                y = random.uniform(0, 250000)

                if ages_counts[x] >= y:
                    # Shift to match age
                    return x + 20

    def initialize_income_bin_percentile(self):
        # Get column relative to the age
        column = 8
        for inx, column_age in enumerate([25, 35, 45, 55, 65, 75]):
            if self.age < column_age:
                column = inx + 2
                break

        rn = np.random.uniform(0, 1, 1)[0]
        for row in self.model.income_distribution:
            if rn < row[column]:
                return row[1], int(row[0]), row[column]


    def step(self):
        """
        Step of an agent represents the actions of the agent during one month
        """
        self.monthly_ageing += 1

        if self.monthly_ageing == 12:
            self.age += 1
            self.monthly_ageing = 0

        # Update the income of the agent
        self.income, self.bin, self.percentile = self.update_income_bin_percentile()
        # calculate equity
        if self.house:
            self.savings += self.model.payoff_perc_freehold * self.house.price
            self.equity = self.house.price + self.savings - self.mortgage
            self.months_renting = 0
        else:
            self.equity = self.savings - self.mortgage
            self.months_renting += 1

        # all available houses
        available_houses = self.model.schedule_House.get_available()

        # decide whether to sell your house
        if (self.age < self.model.minimum_age or self.age > self.model.maximum_moving_age):
            pass

        # depending on their strategy an agent will have a different procedure for deciding whether to sell:
        elif (self.house and self.strategy == "naive"):
            # not everybody is actively checking the market at every step

            if random.random() < (1 - self.model.age_utility_scaling * self.age) or self.empty_neighborhood() == True:

                # get new mortgage quote based on current income
                mortgage_quote = self.get_mortgage_quote()

                if self.house:
                    # calculate expected money gained from selling current house
                    house_mortgage_differential = self.house.priceChangeForecast - self.mortgage
                else:
                    house_mortgage_differential = 0

                # calculate total available money for buying a house
                available_money = mortgage_quote + house_mortgage_differential + self.savings

                # sample houses
                house_sample = random.sample(available_houses, k = len(available_houses)) # k is to be adjusted depending on what's realistic

                # obtain probability of ending up in a given house:
                attractive_houses = 0
                affordable_houses = 0
                for house in house_sample:
                    if self.house.priceChangeForecast > house.priceChangeForecast and house.price < available_money:
                        attractive_houses += 1
                    if house.price < available_money:
                        affordable_houses += 1

                if attractive_houses == 0 or affordable_houses == 0:
                    prob_buy = 0
                else:
                    prob_buy = attractive_houses/affordable_houses

                # obtain expected utility of buying a new house on the market:
                expected_utility = 0
                for house in house_sample:
                    expected_utility += self.utility(house)*prob_buy

                # list own house
                if expected_utility > 0:
                    self.house.set_availability(True)

        elif (self.house and self.strategy == "sophisticated"):
            # not everybody is actively checking the market at every step
            if random.random() < (1 - self.model.age_utility_scaling * self.age) or self.empty_neighborhood() == True:

                # get new mortgage quote based on current income
                mortgage_quote = self.get_mortgage_quote()

                if self.house:
                    # calculate expected money gained from selling current house
                    house_mortgage_differential = self.house.priceChangeForecast - self.mortgage
                else:
                    house_mortgage_differential = 0

                # calculate total available money for buying a house
                available_money = mortgage_quote + house_mortgage_differential + self.savings

                # sample houses (in neighborhood?)
                house_sample = random.sample(available_houses, k = len(available_houses))

                # obtain probability of ending up in a given house:
                attractive_houses = 0
                affordable_houses = 0
                for house in house_sample:
                    if self.house.priceChangeForecast_av > house.priceChangeForecast_av and house.price < available_money:
                        attractive_houses += 1
                    if house.price < available_money:
                        affordable_houses += 1

                if attractive_houses == 0 or affordable_houses == 0:
                    prob_buy = 0
                else:
                    prob_buy = attractive_houses/affordable_houses

                # obtain expected utility of buying a new house on the market:
                expected_utility = 0
                for house in house_sample:
                    expected_utility += self.utility(house)*prob_buy

                # list own house
                if expected_utility > 0:
                    self.house.set_availability(True)

        # always buy a house if you are renting, this could be enhanced if there was a bidding stage
        elif self.house is None:
            self.buy_house(available_houses)

        # for now implement simple death rule, agent exits model at age of 100
        if self.age == self.model.maximum_age:
            if self.house:
                self.house.set_availability(True)
                self.house.owner = None
            self.model.remove_agent(self)

        # Death dynamics modeled after Gompertz law 
        if self.monthly_ageing == 11:
            if 0.0005 + 10 ** (-4.2 + 0.038 * self.age) >= random.uniform(0, 1):
                if self.house:
                    self.house.set_availability(True)
                    self.house.owner = None
                self.model.remove_agent(self)

        # S_Policy Implementation
        if self.model.s_policy == True and self.model.period > 30 and self.age == 20 and self.monthly_ageing == 0:
            self.savings += 20_000

        if self.model.a_policy == True and self.model.period > 30 and self.age == 75:
            self.savings += 40_000

        '''
        Income Policy: if 25, 0 months and lower 10% then grant
        '''
        if self.model.income_policy == True and self.age == 25 and self.monthly_ageing == 0 and self.model.period == 1 and self.bin in range(0,15):
            self.savings += 20_000


    def utility(self, house):
        # This function defines the agents' utility, where x is the expected gain or loss, alpha and beta 
        # are risk attitude parameters for gains and losses respectively and lambda is the loss aversion constant.
        if not house:
            return 0

        if self.strategy=="naive":
            x = house.priceChangeForecast - self.sold_house.priceChangeForecast if self.sold_house else house.priceChangeForecast
        else:
            x = house.priceChangeForecast_av - self.sold_house.priceChangeForecast_av if self.sold_house else house.priceChangeForecast_av
        distance = self.get_distance(house)
        if x > 0:
            return x**self.alpha - distance
        if x == 0:
            return 0
        else:
            return (abs(x)**(self.beta)*self.lmbda*(-1)) - distance


    def get_distance(self, house):
        if self.house == None and self.sold_house == None:
            return 0
        else:
            if self.house != None:
                x1, y1 = self.house.pos
            if self.sold_house != None: 
                x1, y1 = self.sold_house.pos
        x2, y2 = house.pos
        dx = x1-x2
        dy = y1-y2
        return math.sqrt(dx**2+dy**2)

    def buy_house(self, available_houses):
        """Method that let's household buy a house from antoher household

        Args:
            available_houses (list): A list of all available houses

        Note: you enter this function with assumption that you do NOT have a house anymore! (otherwise have to change this function)
        """
        # try to buy a house
        
        if self.sold_house == None:
            available_houses.sort(key=lambda x: x.priceChange, reverse=True)

        else: 
            for house in available_houses:
                house.set_utility(self.utility(house))
            
            
            # resort the avalaible houses list to be sorted on utility
            available_houses.sort(key=lambda x: x.utility, reverse=True)

        for house in available_houses:
            if house.owner == self:
                continue
            # buy the best house avalaible
            mortgage_quote = self.get_mortgage_quote()
            available_money = self.savings + mortgage_quote
            if house.price < available_money:
                # wire the money
                previous_owner = house.owner
                if previous_owner:
                    previous_owner.sold_house=previous_owner.house
                    previous_owner.house = None
                    MultiGrid.move_agent(self=self.model.grid, agent=previous_owner, pos=(0, 0))

                    # pay off mortgage of previous owner and push cash remainder into savings
                    earnings_from_sale = house.price - previous_owner.mortgage
                    previous_owner.savings += earnings_from_sale
                    previous_owner.mortgage = 0

                if house.price > mortgage_quote:
                    # take the mortgage
                    self.mortgage = mortgage_quote

                    # pay remainder with savings
                    pay_with_savings = house.price - mortgage_quote
                    self.savings -= pay_with_savings
                else:
                    # if able to get a mortgage larger than house price
                    # only get mortgage up to house price, and afford entire house with mortgage
                    self.mortgage = house.price

                # change ownership
                self.house = house
                self.house.owner = self
                house.set_availability(False)
                MultiGrid.move_agent(self=self.model.grid, agent=self, pos=house.pos)
                break


    def update_income_bin_percentile(self):
        # Get column relative to the age
        column = 8
        for inx, column_age in enumerate([25, 35, 45, 55, 65, 75]):
            if self.age < column_age:
                column = inx + 2
                break
        random_walk_bin = np.random.normal(loc=0, scale=1, size=1).astype(int)[0]
        for row in self.model.income_distribution:
            if self.percentile <= row[column]:
                bin = int(row[0] + random_walk_bin)
                if bin > 72: bin = 72
                elif bin < 0: bin = 0
                return self.model.income_distribution[bin, 1], bin, self.model.income_distribution[bin, column]
        return self.model.income_distribution[72, 1], 72, self.model.income_distribution[72, column]


    def empty_neighborhood(self):
       # an agent looks around and checks if the majority of houses in their vincinity are empty
       # if they are, the agent decides to move away too
        houses = 0
        empty_houses = 0
        for neighbor in self.model.grid.neighbor_iter(self.pos):
            if type(neighbor) == House:
                houses += 1
                if neighbor.available:
                    empty_houses+=1
        
        
        if houses > 0: 
            if empty_houses / houses > 0.4:
                return True
            else:
                return False
        return True


    def get_mortgage_quote(self):
        """
        Calculates mortage quote based on monthly household disposable income
        Example:
        - Disposable income (mean) of 3500 per month ~ 42k per year ~ 60k gross per year
        - Based on several mortgage calculators, mortgage is ~ 5-6x gross income. 
        - i.e. 60k should result in 300k. Thus, disposable income is ~ 8x to mortgage
        - (this is a naive and deterministic mortgage quote)
        """
        deterministic_quote = self.income * 12 * self.model.bank_income_multiplier
        return deterministic_quote

class House(Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)
        self.pos = pos

        # set initial house price

        self.price = self.set_initial_house_price()

        self.house_price_change = random.random() if random.random() < self.model.fraction_good_houses else random.random() * (-1)

        self.priceChange = self.price * random.normalvariate(mu=self.house_price_change,
                                                             sigma=2 * self.house_price_change) / 100
        self.priceChange_past = self.price * random.normalvariate(mu=self.house_price_change,
                                                                  sigma=2 * self.house_price_change) / 100
        self.priceChange_av = (self.priceChange + self.priceChange_past) / 2
        self.owner = None
        self.available = True

        # naive agents assume the price change in the next period will be the same as in the last period
        self.priceChangeForecast = self.priceChange

        # more sophisticated agents have a memory and use a weighted average to make a forecast
        self.priceChange_past = self.priceChange_past + self.priceChange
        self.priceChangeForecast_av = (self.priceChange_past) / (self.model.period + 1)

        self.utility = 0


    def set_availability(self, set_to):
        self.available = set_to

    def set_utility(self, set_to):
        self.utility = set_to
    

    def step(self):
        # Price shock once every year
        if self.model.period % 12 == 0:
            
            if random.random() < 0.95:
                self.priceChange = (self.price * random.normalvariate(mu=self.model.house_price_shock,
                                                             sigma=2 * self.model.house_price_shock) / 100)
            else:
                self.priceChange = (self.price * random.normalvariate(mu=self.model.house_price_shock,
                                                             sigma=2 * self.model.house_price_shock) / 100)*(-1)
        else:                                                     
        
        # add milder monthly price shocks
            if random.random() < 0.95:
                self.priceChange = (self.price * random.normalvariate(mu=self.model.house_price_shock*0.2,
                                                             sigma=2 * self.model.house_price_shock*0.2) / 100)
            else:
                self.priceChange = (self.price * random.normalvariate(mu=self.model.house_price_shock*0.2,
                                                             sigma=2 * self.model.house_price_shock*0.2) / 100)*(-1)
    
        self.price += self.priceChange

        # naive agents assume the price change in the next period will be the same as in the last period
        self.priceChangeForecast = self.priceChange

        # more sophisticated agents have a memory and use a weighted average to make a forecast
        self.priceChange_past = self.priceChange_past + self.priceChange
        self.priceChangeForecast_av = (self.priceChange_past) / (self.model.period + 1)

    def set_initial_house_price(self):
        cd = scipy.random.chisquare(self.model.chi_parameter, size=1)

        """ Scale for Std """
        cd = cd / (2 * self.model.chi_parameter) ** 1 / 2

        """ Adjust Mean so ~= 3484 (mean monthly Dutch Household Income) """
        mean_chi = self.model.chi_parameter / (2 * self.model.chi_parameter) ** 1 / 2
        cd = cd * (1 / mean_chi) * self.model.house_price
        return cd[0]


age_coef_dict = {
    18: 0.15190790211711158,
    19: 0.2352803285733691,
    20: 0.28917488419300963,
    21: 0.3235238459215871,
    22: 0.38186837776123933,
    23: 0.4656984696436133,
    24: 0.5180297776234675,
    25: 0.6476242253202377,
    26: 0.6864301922600129,
    27: 0.7556463866672888,
    28: 0.7403816046083588,
    29: 0.8065922023844624,
    30: 0.8232749662653331,
    31: 0.9226411592664203,
    32: 0.9170315557005079,
    33: 0.9228596827924056,
    34: 0.9451169052832582,
    35: 1.0359230366181207,
    36: 1.063442942909901,
    37: 1.079785503617365,
    38: 1.042574805277224,
    39: 1.0970818203288792,
    40: 1.1360596070532032,
    41: 1.2049768350353642,
    42: 1.1134926403507501,
    43: 1.3008241588488905,
    44: 1.163347869035451,
    45: 1.2355576326889808,
    46: 1.1751529816325876,
    47: 1.2238891949204627,
    48: 1.073537042852539,
    49: 1.1786549812413019,
    50: 1.2763276559659535,
    51: 1.183640097990281,
    52: 1.2539649986073098,
    53: 1.2621347169630002,
    54: 1.2090872328811855,
    55: 1.2075616293941958,
    56: 1.2005124884333722,
    57: 1.2205318363303777,
    58: 1.142836491755419,
    59: 1.2281186170170353,
    60: 1.1463919116971477,
    61: 1.2119927054379072,
    62: 1.2124939506093775,
    63: 1.2057006649277273,
    64: 1.1496953813548059,
    65: 1.1624445655681364,
    66: 1.2385043419939938,
    67: 1.4596112565399266,
    68: 1.3144227575971088,
    69: 1.2880937186120562,
    70: 1.1896895602046387,
    71: 1.198750867042334,
    72: 1.537697569224636,
    73: 1.4410072350681913,
    74: 1.098669435138111,
    75: 1.1062093558835275,
    76: 1.1062093558835275,
    77: 1.1062093558835275,
    78: 1.1062093558835275,
    79: 1.1062093558835275,
    80: 1.1062093558835275,
    81: 1.1062093558835275,
    82: 1.1062093558835275,
    83: 1.1062093558835275,
    84: 1.1062093558835275,
    85: 1.1062093558835275,
    86: 1.1062093558835275,
    87: 1.1062093558835275,
    88: 1.1062093558835275,
    89: 1.1062093558835275,
    90: 1.1062093558835275,
    91: 1.1062093558835275,
    92: 1.1062093558835275,
    93: 1.1062093558835275,
    94: 1.1062093558835275,
    95: 1.1062093558835275,
    96: 1.1062093558835275,
    97: 1.1062093558835275,
    98: 1.1062093558835275,
    99: 1.1062093558835275,
    100: 1.1062093558835275
}

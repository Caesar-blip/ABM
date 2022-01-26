# from zoneinfo import available_timezones
from mesa import Agent
from mesa import Model
from mesa.space import MultiGrid
import random
import scipy
import numpy as np


class Household(Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)
        self.pos = pos

        self.savings = random.randint(self.model.savings_lower, self.model.savings_upper)
        self.age = self.set_age()

        self.income, self.bin, self.percentile = self.initialize_income_bin_percentile()
        self.house = None

        # No one starts with a mortgage
        self.mortgage = 0

        self.monthly_ageing = 0
        self.strategy = np.random.choice(["naive", "sophisticated"])

    def get_mortgage_quote(self):
        """
        Calculates mortage quote based on monthly household disposable income
        Example:
        - Disposable income (mean) of 3500 per month ~ 42k per year ~ 60k gross per year
        - Based on several mortgage calculators, mortgage is ~ 5-6x gross income. 
        - i.e. 60k should result in 300k. Thus, disposable income is ~ 8x to mortgage
        - (this is a naive and deterministic mortgage quote)
        """
        deterministic_quote = self.income * 12 * 8
        return deterministic_quote

    def set_age(self):
        # if model is past initialisation, new agents in the model are "born" at youngest available age

        if self.model.period > 0:
            return 20

        # if model is initialised, distribute age following Dutch age distribution among agents
        # This is done using Acceptance-Rejection Sampling
        ages = self.model.age_distr[0]
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
                column = inx + 2;
                break

        rn = np.random.uniform(0, 1, 1)[0]
        for row in self.model.income_distribution:
            if rn < row[column]:
                return row[1], int(row[0]), row[column]

    def update_income_bin_percentile(self):
        # Get column relative to the age
        column = 8
        for inx, column_age in enumerate([25, 35, 45, 55, 65, 75]):
            if self.age < column_age:
                column = inx + 2;
                break

        random_walk_bin = np.random.normal(loc=0, scale=1, size=1).astype(int)[0];
        bin = None
        for row in self.model.income_distribution:
            if self.percentile < row[column]:
                print(row[column])
                bin = int(row[0] + random_walk_bin)
                break
        return self.model.income_distribution[bin, 1], bin, self.model.income_distribution[bin, column]

    def empty_neighborhood(self):
        # an agent looks around and checks if the majority of houses in their vincinity are empty
        # if they are, the agent decides to move away too
        houses = 0
        for neighbor in self.model.grid.neighbor_iter(self.pos):
            if neighbor.type != self.type:
                houses += 1

        empty_houses = 0
        for neighbor in self.model.grid.neighbor_iter(self.pos):
            if neighbor.type != self.type & neighbor.available:
                empty_houses += 1

        if empty_houses / houses > 0.4:
            return True
        else:
            return False

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
            # print(self.house.price)
            self.savings += self.model.payoff_perc_freehold * self.house.price
            self.equity = self.house.price + self.savings
        else:
            self.equity = self.savings

        # all available houses
        available_houses = self.model.schedule_House.get_available()

        # decide whether to sell your house
        # agents only sell if they are between 20 and 65
        if (self.age < 20 or self.age > 65):
            pass

        # depending on their strategy an agent will have a different procedure for deciding whether to sell:
        elif (self.house and self.strategy == "naive"):
            # not everybody is actively checking the market at every step
            if random.random() < (1 - 0.01 * self.age) or self.empty_neighborhood == True:

                # get new mortgage quote based on current income
                mortgage_quote = self.get_mortgage_quote()

                if self.house:
                    # calculate expected money gained from selling current house
                    house_mortgage_differential = self.house.priceChangeForecast - self.mortgage
                else:
                    house_mortgage_differential = 0

                # calculate total available money for buying a house
                available_money = mortgage_quote + house_mortgage_differential + self.savings

                for house in available_houses:
                    if house.priceChangeForecast > self.house.priceChangeForecast and house.price < available_money:
                        # list own house
                        self.house.set_availability(True)

        elif (self.house and self.strategy == "sophisticated"):
            # not everybody is actively checking the market at every step
            if random.random() < (1 - 0.01 * self.age) or self.empty_neighborhood == True:

                # get new mortgage quote based on current income
                mortgage_quote = self.get_mortgage_quote()

                if self.house:
                    # calculate expected money gained from selling current house
                    house_mortgage_differential = self.house.priceChangeForecast - self.mortgage
                else:
                    house_mortgage_differential = 0

                # calculate total available money for buying a house
                available_money = mortgage_quote + house_mortgage_differential + self.savings

                for house in available_houses:
                    if house.priceChangeForecast_av > self.house.priceChangeForecast_av and house.price < available_money:
                        # list own house
                        self.house.set_availability(True)

        # always buy a house if you are renting, this could be enhanced if there was a bidding stage
        elif self.house is None:
            self.buy_house(available_houses)

        # for now implement simple death rule, agent exits model at age of 100
        if self.age == 100:
            if self.house:
                self.house.set_availability(True)
                self.house.owner = None
            self.model.remove_agent(self)

        # Death dynamics modeld after Gompertz law 
        if self.monthly_ageing == 11:
            if 0.0005 + 10 ** (-4.2 + 0.038 * self.age) >= random.uniform(0, 1):
                if self.house:
                    self.house.set_availability(True)
                    self.house.owner = None
                self.model.remove_agent(self)

    def buy_house(self, available_houses):
        """Method that let's household buy a house from antoher household

        Args:
            available_houses (list): A list of all available houses

        Note: you enter this function with assumption that you do NOT have a house anymore! (otherwise have to change this function)
        """
        # try to buy a house
        if self.strategy == "naive":
            available_houses.sort(key=lambda x: x.priceChangeForecast, reverse=True)
        else:
            available_houses.sort(key=lambda x: x.priceChangeForecast_av, reverse=True)

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


class House(Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)
        self.pos = pos
        # set initial house price
        self.house_price_change = random.random() if random.random() < 0.7 else random.random() * (-1)
        self.price = self.set_initial_house_price()
        self.priceChange = self.price * random.normalvariate(mu=self.house_price_change,
                                                             sigma=2 * self.house_price_change) / 100
        self.priceChange_past = self.price * random.normalvariate(mu=self.house_price_change,
                                                                  sigma=2 * self.house_price_change) / 100
        self.priceChange_av = (self.priceChange + self.priceChange_past) / 2
        self.owner = None
        self.available = True

    def set_availability(self, set_to):
        self.available = set_to

    def step(self):
        # Price shock once every year
        if self.model.period % 12 == 0:
            self.price += (self.price * random.normalvariate(mu=self.model.house_price_shock,
                                                             sigma=2 * self.model.house_price_shock) / 100)
            # redraw the house change in the new market to introduce some stochasticity
            self.house_price_change = random.random() if random.random() < 0.7 else random.random() * (-1)

        self.priceChange = self.price * random.normalvariate(mu=self.house_price_change,
                                                             sigma=2 * self.house_price_change) / 100
        self.price += self.priceChange
        self.priceChangeForecast = self.price + self.priceChange

        self.priceChange_past = self.priceChange_past + self.priceChange
        self.priceChangeForecast_av = (self.priceChange_past) / (self.model.period + 1)

    def set_initial_house_price(self):
        mean_house_price = 400_000
        parameter = 6.5
        cd = scipy.random.chisquare(parameter, size=1)

        """ Scale for Std """
        cd = cd / (2 * parameter) ** 1 / 2

        """ Adjust Mean so ~= 3484 (mean monthly Dutch Household Income) """
        mean_chi = parameter / (2 * parameter) ** 1 / 2
        cd = cd * (1 / mean_chi) * mean_house_price
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

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

        self.income = self.set_income()
        self.house = None

        self.monthly_ageing = 0
        self.strategy = np.random.choice(["naive", "sophisticated"])

        


    def set_age(self):
        # if model is past initialisation, new agents in the model are "born" at youngest available age

        if self.model.period > 0:
            return 20

        # if model is initialised, distribute age following Dutch age distribution among agents
        rand = random.random()
        for i in range(len(self.model.ages)):
            if rand < self.model.age_distr[i]:
                return self.model.ages[i]

    def set_income(self):
        age = self.age
        step = 0  # TODO : get step from model
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
        """
        age (integer)   : from [18, 100] (inclusive)
        step            : to be perceived as a month, to increase income with inflation.
        """
        parameter = 6.5
        inflation = 1 + 0.02 * (step / 12)
        cd = scipy.random.chisquare(parameter, size=1)

        """ Scale for Std """
        cd = cd / (2 * parameter) ** 1 / 2

        """ Adjust Mean so ~= 3484 (mean monthly Dutch Household Income) """
        mean_chi = parameter / (2 * parameter) ** 1 / 2
        cd = cd * (3484 / mean_chi) * age_coef_dict[age] * np.random.normal(loc=inflation, scale=.002, size=1)
        return cd[0]
    
    def empty_neighborhood(self):
        houses = 0
        for neighbor in self.model.grid.neighbor_iter(self.pos):
            if neighbor.type != self.type:
                houses += 1
        
        empty_houses = 0
        for neighbor in self.model.grid.neighbor_iter(self.pos):
            if neighbor.type != self.type & neighbor.available:
                empty_houses += 1

        if empty_houses/houses > 0.4:
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

        # receive income 
        self.savings += self.income
        # calculate equity
        if self.house:
            # print(self.house.price)
            self.savings += self.model.payoff_perc_freehold * self.house.price
            self.equity = self.house.price + self.savings
        else:
            # self.savings -= self.model.rental_cost
            self.equity = self.savings

        # all available houses
        available_houses = self.model.schedule_House.get_available()

        # decide whether to sell your house
        if (self.age < 20 or self.age > 65):
            pass
        elif (self.house & self.strategy == "naive"):
            # not everybody is actively checking the market at every step
            if random.random() < 0.5 or self.empty_neighborhood == True:
                for house in available_houses:
                    if house.priceChangeForecast > self.house.priceChangeForecast and house.price < self.equity:
                        # list own house
                        self.house.set_availability(True)
                        self.buy_house(available_houses)
        elif (self.house & self.strategy == "sophisticated"):
            # not everybody is actively checking the market at every step
            if random.random() < 0.5 or self.empty_neighborhood == True:
                for house in available_houses:
                    if house.priceChangeForecast_av > self.house.priceChangeForecast_av and house.price < self.equity:
                        # list own house
                        self.house.set_availability(True)
                        self.buy_house(available_houses)
            # small percentage to try and sell your house even if you have a house
            # this could be the increased and decreased if someone is risk averse
            #if random.random() < 0.1:
            #    self.house.set_availability(True)
        # always buy a house if you are renting, this could be enhanced if there was a bidding stage
        else:
            self.buy_house(available_houses)

        # for now implement simple death rule, agent exits model at age of 100
        if self.age == 100:
            if self.house:
                self.house.set_availability(True)
            self.model.remove_agent(self)

    def buy_house(self, available_houses):
        """Method that let's household buy a house from antoher household

        Args:
            available_houses (list): A list of all available houses
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
            if house.price < self.savings:
                # wire the money
                previous_owner = house.owner
                if previous_owner:
                    previous_owner.house = None
                    MultiGrid.move_agent(self=self.model.grid, agent=previous_owner, pos=(0, 0))
                    previous_owner.savings += house.price
                self.savings -= house.price

                # change ownership
                self.house = house
                self.house.owner = self
                house.set_availability(False)
                MultiGrid.move_agent(self=self.model.grid, agent=self, pos=house.pos)
                break


def set_initial_house_price():
    mean_house_price = 400_000
    parameter = 6.5
    cd = scipy.random.chisquare(parameter, size=1)

    """ Scale for Std """
    cd = cd / (2 * parameter) ** 1 / 2

    """ Adjust Mean so ~= 3484 (mean monthly Dutch Household Income) """
    mean_chi = parameter / (2 * parameter) ** 1 / 2
    cd = cd * (1 / mean_chi) * mean_house_price
    return cd[0]


class House(Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)
        self.pos = pos
        # set initial house price
        self.house_price_change = random.random() if random.random() < 0.7 else random.random()*(-1) 
        self.past_house_price_change = random.random() if random.random() < 0.7 else random.random()*(-1) 
        self.price = set_initial_house_price()
        self.priceChange = self.house_price_change*self.price
        self.priceChange_past = self.past_house_price_change*self.price
        self.priceChange_av = (self.priceChange + self.priceChange_past)/2
        self.owner = None
        self.available = True

    def set_availability(self, set_to):
        self.available = set_to

    def step(self):
        # this method  gets called once every year
        #self.priceChange = self.model.house_price_change*self.price
        self.priceChange = self.house_price_change*self.price
        self.price *= self.model.house_price_change
        self.priceChangeForecast = self.price*self.model.house_price_change 
        self.priceChange_past = (self.priceChange_past + self.priceChange)/(self.period+1)
        self.priceChangeForecast_av = self.price*self.model.house_price_change 


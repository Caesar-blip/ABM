# from zoneinfo import available_timezones
from mesa import Agent
from mesa import Model
from mesa.space import MultiGrid
import random


class Household(Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)
        self.pos = pos
    
        self.savings = random.randint(self.model.savings_lower,self.model.savings_upper)
        self.income = self.set_income()
        self.house = None

        self.age = self.set_age()
        self.monthly_ageing = 0

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
        # for now even agents past initialisation get an income from generic income distribution (so not based on young age)
        # Note: CBS has income distribution of people <25, just need to get csv and transform data again
        if len(self.model.incomes) == 0:
            return random.randint(self.model.income_lower, self.model.income_upper)
        rand = random.random()
        for i in range(len(self.model.incomes)):
            if rand < self.model.income_distr[i]:
                 return random.uniform(self.model.incomes[i][0], self.model.incomes[i][1])

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
            self.equity = self.house.price + self.savings
        else:
            self.savings -= self.model.rental_cost
            self.equity = self.savings

        # all available houses
        available_houses = self.model.schedule_House.get_available()

        # decide whether to sell your house
        if self.house:
            # not everybody is actively checking the market at every step
            if random.random() < 0.5:
                for house in available_houses:
                    if house.price > self.house.price and house.price < self.equity:
                        # list own house
                        self.house.set_avalaibility(True)
            # small percentage to try and sell your house even if you have a house
            # this could be the increased and decreased if someone is risk averse
            if random.random() < 0.1:
                self.house.set_avalaibility(True)
        # always buy a house if you are renting, this could be enhanced if there was a bidding stage
        else:
            self.buy_house(available_houses)

        # for now implement simple death rule, agent exits model at age of 100
        if self.age == 100:
            if self.house:
                self.house.set_avalaibility(True)
            self.model.remove_agent(self)

            
    def buy_house(self, available_houses):
        """Method that let's household buy a house from antoher household

        Args:
            available_houses (list): A list of all available houses
        """
        # try to buy a house
        available_houses.sort(key=lambda x:x.price, reverse=True)
        for house in available_houses:
            if house.owner == self:
                continue
            # buy the best house avalaible
            if house.price < self.savings:
            # wire the money
                previous_owner = house.owner
                if previous_owner:
                    previous_owner.house = None
                    MultiGrid.move_agent(self=self.model.grid, agent=previous_owner, pos=(0,0))
                    previous_owner.savings += house.price
                self.savings -= house.price

                # change ownership
                self.house = house
                self.house.owner = self
                house.set_avalaibility(False)
                MultiGrid.move_agent(self=self.model.grid, agent=self, pos=house.pos)
                break

class House(Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)  
        self.pos = pos        
        # set initial house price
        self.price = random.randint(self.model.price_lower,self.model.price_upper)
        self.owner = None 
        self.available = True


    def set_avalaibility(self, set_to):
        self.available = set_to

    def step(self):
        # this method  gets called once every year
        self.price *= self.model.house_price_change

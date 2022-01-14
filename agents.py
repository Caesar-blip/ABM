from zoneinfo import available_timezones
from mesa import Agent
from mesa import Model
from mesa.space import MultiGrid
import random


class Household(Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)
        self.pos = pos
    
        self.savings = random.randint(0,500000)
        self.income = random.randint(500, 10000)
        #self.equity = self.savings + self.house
        self.house = None


    def step(self):
        # receive income 
        self.savings += self.income
        if self.house == None:
            self.savings -= 1000
        # calculate equity
        if self.house:
            self.equity = self.house.price + self.savings
        else:
            self.equity = self.savings

        # all available houses
        available_houses = self.model.schedule_House.get_available()

        # decide whether to sell your house
        if self.house:
            if random.random() < 0.5:
                for house in available_houses:
                    if house.price > self.house.price and self.house.price < self.equity:
                        # list own house
                        print("im here")
                        self.house.set_avalaibility(True)
            # small percentage to try and buy a house even if you have a house
            if random.random() < 0.1:
                self.house.set_avalaibility(True)
                self.buy_house(available_houses)
        # always buy a house if you are renting
        else:
            self.buy_house(available_houses)

            
    def buy_house(self, available_houses):
        # try to buy a house
        available_houses.sort(key=lambda x:x.price, reverse=True)
        for house in available_houses:
            if house.price < self.equity:
            # wire the money
                previous_owner = house.owner
                if previous_owner != -1:
                    previous_owner.savings += house.price
                self.savings -= house.price

                # change ownership
                self.house = house
                self.house.owner = self
                print("no longer avalaible")
                house.set_avalaibility(False)
                MultiGrid.move_agent(self=self.model.grid, agent=self, pos=house.pos)
                break
        
    
class House(Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)  
        self.pos = pos        
        # set initial house price
        self.price = random.randint(0,500000)
        self.owner = -1 
        self.available = True

    def set_avalaibility(self, set_to):
        self.available = set_to

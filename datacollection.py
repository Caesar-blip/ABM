'''
Model level data collection
'''
import numpy as np
from agents import *
from model import *

def average_household_income(model):
    total = 0   ;   agent_count = 0
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
    return diffsum / (len(x) ** 2 * np.mean(x))


def collect_income(Agent):
    if type(Agent) == Household:
        return Agent.income
    else:
        return None


def collect_ages(Agent):
    if type(Agent) == Household:
        return Agent.age
    else:
        return None


def mean_household_age(model):
    ages = 0 ;   counter = 0
    for agent in model.schedule_Household.agents:
        ages += agent.age
        counter += 1

    return ages / counter


def average_savings(model):
    age_savings = 0 ;   age_count = 0

    for agent in model.schedule_Household.agents:
        age_savings += agent.savings
        age_count += 1

    if age_count == 0:  return age_savings
    else:   return age_savings / age_count


def age_25_minus_savings(model):
    age_savings = 0 ;   age_count = 0

    for agent in model.schedule_Household.agents:
        if agent.age in range(18, 25):
            age_savings += agent.savings
            age_count += 1

    if age_count == 0:  return age_savings
    else:   return age_savings / age_count


def age_25_34_savings(model):
    age_savings = 0 ;   age_count = 0

    for agent in model.schedule_Household.agents:
        if agent.age in range(25, 35):
            age_savings += agent.savings
            age_count += 1

    if age_count == 0:  return age_savings
    else:   return age_savings / age_count


def age_35_44_savings(model):
    age_savings = 0 ;   age_count = 0

    for agent in model.schedule_Household.agents:
        if agent.age in range(35, 45):
            age_savings += agent.savings
            age_count += 1

    if age_count == 0:  return age_savings
    else:   return age_savings / age_count


def age_45_54_savings(model):
    age_savings = 0 ;age_count = 0

    for agent in model.schedule_Household.agents:
        if agent.age in range(45, 55):
            age_savings += agent.savings
            age_count += 1

    if age_count == 0:  return age_savings
    else:   return age_savings / age_count


def age_55_64_savings(model):
    age_savings = 0 ;   age_count = 0

    for agent in model.schedule_Household.agents:
        if agent.age in range(55, 65):
            age_savings += agent.savings
            age_count += 1

    if age_count == 0:  return age_savings
    else:   return age_savings / age_count


def age_65_74_savings(model):
    age_savings = 0 ;   age_count = 0

    for agent in model.schedule_Household.agents:
        if agent.age in range(65, 75):
            age_savings += agent.savings
            age_count += 1

    if age_count == 0:  return age_savings
    else:   return age_savings / age_count


def age_75_plus_savings(model):
    age_savings = 0 ;age_count = 0

    for agent in model.schedule_Household.agents:
        if agent.age in range(75, 101):
            age_savings += agent.savings
            age_count += 1

    if age_count == 0:  return age_savings
    else:   return age_savings / age_count
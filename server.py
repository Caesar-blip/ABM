from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import ChartModule
from mesa.visualization.ModularVisualization import VisualizationElement
from model import *

import IPython
import os
import sys
import numpy as np

# Change stdout so we can ignore most prints etc.
orig_stdout = sys.stdout
sys.stdout = open(os.devnull, 'w')
sys.stdout = orig_stdout


def choose_color(agent):
    if type(agent) is House:
        if agent.available: color = 'green'
        else:   color = 'red'
    else:   color = 'black'
    return color


def agent_portrayal(agent):
    if type(agent) is House:
        portrayal = {"Shape": "rect",
                     "Color": choose_color(agent),
                     "Filled": "true",
                     "Layer": 0,
                     'w': 0.99,
                     'h': 0.99}
    else:
        portrayal = {"Shape": "circle",
                     "Color": choose_color(agent),
                     "Filled": "true",
                     "Layer": 1,
                     'r': .4}
    return portrayal


grid = CanvasGrid(agent_portrayal, 20, 20, 500, 500)

""" Create a dynamic linegraph """
gini_char = ChartModule(
                    [{"Label": "Gini", "Color": "red"}],
                    data_collector_name='datacollector',
                    canvas_width=500,
                    canvas_height=200)


average_savings_chart = ChartModule([
                    {"Label": "Average Savings", "Color": 'red'},
                    {"Label": "Age -25 Savings", "Color": "005F73"},
                    {"Label": "Age 25-34 Savings", "Color": "0A9396"},
                    {"Label": "Age 45-54 Savings", "Color": "94D2BD"},
                    {"Label": "Age 55-64 Savings", "Color": "E9D8A6"},
                    {"Label": "Age 65-74 Savings", "Color": "EE9B00"},
                    {"Label": "Age 75+ Savings", "Color": "AE2012"}],
                    canvas_width=500, canvas_height=200,
                    data_collector_name='datacollector')


average_income_chart = ChartModule([
                    {"Label": "Average Household Income", "Color": 'red'}],
                    canvas_width=500, canvas_height=200,
                    data_collector_name='datacollector')


mean_household_age_chart = ChartModule([
                    {"Label": "Mean Household Age", "Color": 'green'}],
                    canvas_width=500, canvas_height=200,
                    data_collector_name='datacollector')

# Create the server, and pass the grid and the graph
server = ModularServer(
                    HousingMarket,
                    [grid, gini_char, average_savings_chart, average_income_chart, mean_household_age_chart],
                    "Housing Market Model",
                    {'rental_cost': 2000,
                     'initial_houses': 700,
                     'initial_households': 1000
                     })

server.port = 8522
server.launch()

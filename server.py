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
                    {"Label": "Age -25 Savings", "Color": "green"},
                    {"Label": "Age 25-34 Savings", "Color": "blue"},
                    {"Label": "Age 35-44 Savings", "Color": "pink"},
                    {"Label": "Age 45-54 Savings", "Color": "purple"},
                    {"Label": "Age 55-64 Savings", "Color": "black"},
                    {"Label": "Age 65-74 Savings", "Color": "yellow"},
                    {"Label": "Age 75+ Savings", "Color": "orange"}],
                    canvas_width=500, canvas_height=200,
                    data_collector_name='datacollector')

average_income_chart = ChartModule([
                    {"Label": "Average Household Income", "Color": 'red'}],
                    canvas_width=500, canvas_height=200,
                    data_collector_name='datacollector')


mean_household_age_chart = ChartModule([
                    {"Label": "Age -25 amount", "Color": "green"},
                    {"Label": "Age 25-34 amount", "Color": "blue"},
                    {"Label": "Age 35-44 amount", "Color": "pink"},
                    {"Label": "Age 45-54 amount", "Color": "purple"},
                    {"Label": "Age 55-64 amount", "Color": "black"},
                    {"Label": "Age 65-74 amount", "Color": "yellow"},
                    {"Label": "Age 75+ amount", "Color": "orange"},
                    {"Label": "Mean Household Age", "Color": 'green'}],
                    canvas_width=500, canvas_height=200,
                    data_collector_name='datacollector')

mean_house_price_chart = ChartModule([
                    {"Label": "Mean House Price", "Color": 'green'}],
                    canvas_width=500, canvas_height=200,
                    data_collector_name='datacollector')

mean_forecasted_price_chart = ChartModule([
                    {"Label": "Mean Forecasted House Price Change", "Color": 'green'}],
                    canvas_width=500, canvas_height=200,
                    data_collector_name='datacollector')

inflation_chart = ChartModule([
                    {"Label": "Inflation", "Color": 'blue'}],
                    canvas_width=500, canvas_height=200,
                    data_collector_name='datacollector')

total_inflation_chart = ChartModule([
                    {"Label": "Total Inflation", "Color": 'blue'}],
                    canvas_width=500, canvas_height=200,
                    data_collector_name='datacollector')

# Create the server, and pass the grid and the graph
server = ModularServer(
                    HousingMarket,
                    [grid, gini_char, average_savings_chart, average_income_chart, mean_household_age_chart,
                     mean_house_price_chart, mean_forecasted_price_chart, inflation_chart, total_inflation_chart],
                    "Housing Market Model",
                    {'rental_cost': 2000,
                     'initial_houses': 900,
                     'initial_households': 1000
                     })

server.port = 8522
server.launch()

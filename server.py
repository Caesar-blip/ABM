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
        if agent.available == True:
            color='green'
        else:
            color='red'
    else:
        color='blue'
    return color

def agent_portrayal(agent):
    portrayal = {"Shape": "circle",
                 "Color": choose_color(agent),
                 "Filled": "true",
                 "Layer": 0,
                 "r": 0.5 if type(agent) is House else 0.2}
    return portrayal


grid = CanvasGrid(agent_portrayal, 20, 20, 500, 500)

# Create a dynamic linegraph
chart = ChartModule([
                      {"Label": "Gini","Color": "red"}
		      ],
                    data_collector_name='datacollector')


chart2 = ChartModule([
                      {"Label": "Average Savings", "Color": "pink"},
                      {"Label": "Age 20 Savings", "Color": "blue"},
                      {"Label": "Age 40 Savings", "Color": "orange"},
                      {"Label": "Age 60 Savings", "Color": "red"},
                      {"Label": "Age 100 Savings", "Color": "green"},
		      ],
                    data_collector_name='datacollector')

# Create the server, and pass the grid and the graph
server = ModularServer(HousingMarket,
                       [grid, chart, chart2],
                       "Housing Market Model",
                       {})

server.port = 8522

server.launch()

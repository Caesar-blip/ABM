from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import ChartModule
from model import *

import IPython
import os
import sys

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


grid = CanvasGrid(agent_portrayal, 10, 10, 500, 500)

# Create a dynamic linegraph
chart = ChartModule([{"Label": "Overall Savings",
                      "Color": "green"}],
                    data_collector_name='datacollector')


# Create the server, and pass the grid and the graph
server = ModularServer(HousingMarket,
                       [grid, chart],
                       "Housing Market Model",
                       {})

server.port = 8522

server.launch()
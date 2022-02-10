# Running the Housing Market model

## Setup

### First Time
To install the environment, install pipenv onto your computer.<br>
For first time users, first run pipenv install from your shell in the right repository.<br>
Warning, this might take a while!

### Normal setup
From then on out, you can run 'pipenv shell' in the repository, followed by 'ipyhton server.py'.<br>
This will open a window on your default browser in which you can see the model.

Adjust the speed at which the model runs with the slider in the top right.

The squares represent houses, while dots represent households. A house will be green when avalaible, <br>
red when unavalaible. 

## The Model

### Basic Ideas
This model aims to model the dutch housing market. It shows how inequality increases in a simple representation of a market without<br>
inheritance and people owning multiple homes. It draws agent attributes from real data from the dutch market.<br>
Agents are bounded rational, and try to maximize their profits based on their predictions of the market. 


### Altering the model
The model can be toyed with by changing it's default values in model.py. Furthermore, one could try to add things to the model
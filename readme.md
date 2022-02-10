# Running the Housing Market model

## Setup

### First Time
To install the environment, install pipenv onto your computer.<br>
For first time users, first run pipenv install from your shell in the right repository.<br>
Warning, this might take a while!

### Normal setup
From then on out, you can run 'pipenv shell' in the repository, followed by 'ipython server.py'.<br>
This will open a window on your default browser in which you can see the model.

Adjust the speed at which the model runs with the slider in the top right.

The squares represent houses, while dots represent households. A house will be green when avalaible, <br>
red when unavalaible. If you scroll down, several live graphs from the model are visible.

## The Model

### Basic Ideas
This model aims to model the dutch housing market. It shows how inequality increases in a simple representation of a market without<br>
inheritance and people owning multiple homes. It draws agent attributes from real data from the dutch market.<br>
Agents are bounded rational, and try to maximize their profits based on their predictions of the market. 


### Altering the model
The model can be toyed with by changing it's default values in model.py. Furthermore, one could try to add things to the model.<br>
The model uses a standard MESA setup. This means it is defined in several different files.

### model.py
Here the model is defined, plus an extension of the 'randomactivation' class to add an easy way to check the status of all houses in the model<br>
Also, all the default can be found here.

### agents.py
Here the agents are defined. There are only two, Houses and Households.

### server.py
In this file you can add graphs to the visualization. Also, you can change the parameters with which the server is started.

### datacollection.py
In this file the methods for collectting data from the agents and the model are declared. 


## Statistical Analysis
There are several examples of statistical analysis done with the model in the notebooks. I will go through the most basic ones.

### saltelli_creator.ipynb
This Notebook prepares the parallelised global sensitivity analysis. We had 5 computers avalaible, so the saltelli samples is split up <br>
into 5 parts

### BatchRunner.ipynb
This Notebook contains a function with which one can run experiments. Fill in the starting parameters into kwarg and run the model in parallel! <br>
It is advised to make the number of runs a multiple of your amount of cores to ensure an evenly distributed workload.

Furthermore, this notebook contains the code for running the global sensitivity analysis on parallel on a single computer.<br>
It takes only the part of the saltelli sample that is assigned to the person who runs it.

### OFAT.ipynb
This Notebook contains the code to run a One Factor At a Time sensitivity anlysis.

### Experiments.ipynb
Here, we defined some experiments we did with the model.
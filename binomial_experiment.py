import random
import pathlib

from typing import Optional

import click
from src.schnapsen.bots.rdeep_ML import RdeepMLBot
from src.schnapsen.bots import MLDataBot, train_ML_model, MLPlayingBot, RandBot
from src.schnapsen.bots.bully import BullyBot
from src.schnapsen.bots.example_bot import ExampleBot

from src.schnapsen.game import (Bot, Move, PlayerPerspective,
                            SchnapsenGamePlayEngine, Trump_Exchange)
from src.schnapsen.twenty_four_card_schnapsen import \
    TwentyFourSchnapsenGamePlayEngine
from src.schnapsen.bots.bot2 import SecondBot
from src.schnapsen.bots.rdeep import RdeepBot
import pandas as pd

def experimennt_binomial():
    bot1: Bot
    bot2: Bot
    bot3: Bot
    engine = SchnapsenGamePlayEngine()
    rdeep = bot1 = RdeepMLBot(num_samples=12, depth=6, rand=random.Random(4564654644))
    rdeep = bot2 = RdeepBot(num_samples=12, depth=6, rand=random.Random(4564654644))
    bot3 = RandBot(464566)
    bot4 = BullyBot(random.Random(464566))
    bot5 = SecondBot(random.Random(464566))
    wins = 0
    amount = 100
    iter = 100
    result_rdeepML = []
    result_rdeep = []
    for i in range(iter):
        for bot in [bot3,bot4,bot5]:
            winning_rdeepML =[]
            for game_number in range(1, amount + 1):
                if game_number % 2 == 0:
                    bot1, bot = bot, bot1
                winner_id, _, _ = engine.play_game(bot1, bot, random.Random(game_number))
                if winner_id == rdeep:
                    wins += 1
            winning_rdeepML.append(wins)
        result_rdeepML.append(winning_rdeepML)
    print(len(result_rdeepML), len(result_rdeepML[0]))
    for i in range(iter):
        for bot in [bot3,bot4,bot5]:
            winning_rdeep =[]
            for game_number in range(1, amount + 1):
                if game_number % 2 == 0:
                    bot2, bot = bot, bot2
                winner_id, _, _ = engine.play_game(bot2, bot, random.Random(game_number))
                if winner_id == rdeep:
                    wins += 1
            winning_rdeep.append(wins)
        result_rdeep.append(winning_rdeepML)
    print(len(result_rdeep), len(result_rdeep[0]))
    
    df_rdeepML = pd.DataFrame(result_rdeepML)
    df_rdeep = pd.DataFrame(result_rdeep)
    df_rdeepML.to_csv("DataFrame_Experiment/df_rdeepML.csv", index = False)
    df_rdeep.to_csv("DataFrame_Experiment/df_rdeep.csv", index = False)
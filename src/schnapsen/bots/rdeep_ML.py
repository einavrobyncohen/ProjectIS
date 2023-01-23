import pathlib
from typing import Optional, cast
from src.schnapsen.game import Bot, PlayerPerspective, Move, GameState, GamePlayEngine, Trick
from random import Random
from src.schnapsen.bots import MLPlayingBot, RdeepBot
import joblib
import numpy as np

class RdeepMLBot(Bot):
    def __init__(self, num_samples: int, depth: int, rand: Random) -> None:
        """
        Create a new rdeep bot.

        :param num_samples: how many samples to take per move
        :param depth: how deep to sample
        :param rand: the source of randomness for this Bot
        """
        assert num_samples >= 1, f"we cannot work with less than one sample, got {num_samples}"
        assert depth >= 1, f"it does not make sense to use a dept <1. got {depth}"
        self.__num_samples = num_samples
        self.__depth = depth
        self.__rand = rand

    def get_move(self, state: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        # get the list of valid moves, and shuffle it such
        # that we get a random move of the highest scoring
        # ones if there are multiple highest scoring moves.
        moves = state.valid_moves()
        self.__rand.shuffle(moves)

        best_score = float('-inf')
        best_move = None
        for move in moves:
            sum_of_scores = 0.0
            for _ in range(self.__num_samples):
                gamestate = state.make_assumption_ML(leader_move=leader_move, rand=self.__rand, my_move=move)
                score = self.__evaluate(state, gamestate, state.get_engine(), leader_move, move)
                sum_of_scores += score
            average_score = sum_of_scores / self.__num_samples
            if average_score > best_score:
                best_score = average_score
                best_move = move
        assert best_move is not None
        return best_move

    def __evaluate(self, perspective: PlayerPerspective, gamestate: GameState, engine: GamePlayEngine, leader_move: Optional[Move], my_move: Move) -> float:
        """
        Evaluates the value of the given state for the given player
        :param state: The state to evaluate
        :param player: The player for whom to evaluate this state (1 or 2)
        :return: A float representing the value of this state for the given player. The higher the value, the better the
                state is for the player.
        """
        me: Bot
        opponent : Bot
        leader_bot: Bot
        follower_bot: Bot
        game_history: list[tuple[PlayerPerspective, Trick]] = cast(list[tuple[PlayerPerspective, Trick]], perspective.get_game_history()[:-1])
        KNN_model = joblib.load("ML_models/KNN_model")
        prediction=[0,0,0,0]
        for round_player_perspective, round_trick in game_history:

            if round_trick.is_trump_exchange():
                leader_move = round_trick.exchange
                follower_move = None
            else:
                leader_move = round_trick.leader_move
                follower_move = round_trick.follower_move

            # we do not want this representation to include actions that followed. So if this agent was the leader, we ignore the followers move
            if round_player_perspective.am_i_leader():
                follower_move = None

            state_actions_representation = perspective.create_state_and_actions_vector_representation(
                state=round_player_perspective, leader_move=leader_move, follower_move=follower_move)
            pred_index = KNN_model.predict(np.array(state_actions_representation).reshape(1,-1))[0]
            prediction[pred_index] += 1
        pred = np.argmax(prediction)
        model_dir: str = 'ML_models'
        if pred == 1:
            model_name = "bully_model"
        elif pred == 2:
            model_name = "rdeep_model"
        elif pred == 3:
            model_name = "2ndBot_model"
        else:
            model_name = "random_model"
        model_path = pathlib.Path(model_dir) / model_name
        opponent = MLPlayingBot(model_location=model_path)
        if leader_move:
            # we know what the other bot played
            leader_bot = FirstFixedMoveThenBaseBot(opponent, leader_move)
            # I am the follower
            me = follower_bot = FirstFixedMoveThenBaseBot(RdeepBot(num_samples=8,depth=5,rand=self.__rand), my_move)
        else:
            # I am the leader bot
            me = leader_bot = FirstFixedMoveThenBaseBot(RdeepBot(num_samples=8,depth=5,rand=self.__rand), my_move)
            # We assume the other bot just random
            follower_bot = opponent

        new_game_state, _ = engine.play_at_most_n_tricks(game_state=gamestate, new_leader=leader_bot, new_follower=follower_bot, n=self.__depth)

        if new_game_state.leader.implementation is me:
            my_score = new_game_state.leader.score.direct_points
            opponent_score = new_game_state.follower.score.direct_points
        else:
            my_score = new_game_state.follower.score.direct_points
            opponent_score = new_game_state.leader.score.direct_points

        heuristic = my_score / (my_score + opponent_score)
        return heuristic

'''
class RandBot(Bot):

    def __init__(self, rand: Random) -> None:
        self.rand = rand

    def get_move(self, state: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        return self.rand.choice(state.valid_moves())
'''

class FirstFixedMoveThenBaseBot(Bot):
    def __init__(self, base_bot: Bot, first_move: Move) -> None:
        self.first_move = first_move
        self.first_move_played = False
        self.base_bot = base_bot

    def get_move(self, state: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        if not self.first_move_played:
            self.first_move_played = True
            return self.first_move
        return self.base_bot.get_move(state=state, leader_move=leader_move)
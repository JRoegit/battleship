from bauhaus import Encoding, proposition, constraint, Or, And
from bauhaus.utils import count_solutions, likelihood
import random
# import pprint
# pp = pprint.PrettyPrinter(indent=4)

# import numpy as np 
# import seaborn as sn 
# import matplotlib.pyplot as plt 


# These two lines make sure a faster SAT solver is used.
from nnf import config

config.sat_backend = "kissat"

# Encoding that will store all of your constraints
E = Encoding()


# To create propositions, create classes for them first, annotated with "@proposition" and the Encoding
@proposition(E)
class BasicPropositions:

    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return f"A.{self.data}"


class Hashable:
    def __hash__(self):
        return hash(str(self))

    def __eq__(self, __value: object) -> bool:
        return hash(self) == hash(__value)

    def __repr__(self):
        return str(self)


BOARD_SIZE = 6
VALID = True


# ----------------------------------------- Propositions -----------------------------------------
@proposition(E)
class Boat(Hashable):
    def __init__(self, coords: tuple, length: int, orientation: str):
        self.coords = coords
        self.length = length
        self.orientation = orientation

    def __str__(self):
        boat_coords = ""
        for coord in self.coords:
            boat_coords += (f"({coord[0]},{coord[1]}),")
        boat_coords.rstrip(",")
        return f"{boat_coords} + {self.length} + {self.orientation}"


@proposition(E)
class Game(Hashable):
    def __init__(self, boats:tuple):
        self.boats = boats

    def __str__(self):
        game = ""
        for boat in self.boats:
            game+=(f"({boat}, ")
        game.rstrip(", ")
        game+=")"
        return f"{game}"

@proposition(E)
class Guess(Hashable):
    def __init__(self, coords: tuple):
        self.coords = coords

    def __str__(self):
        return f"{self.coords}"


@proposition(E)
class Around(Hashable):
    def __init__(self, boat1: Boat, boat2: Boat):
        self.boat1 = boat1
        self.boat2 = boat2

    def __str__(self):
        return f"({self.boat1} (-) {self.boat2})"


# Create the propositions
def create_coords(length, orientation, board_size):
    boats = []

    if orientation == "vertical":
        for start in range((board_size + 1) - length):
            for r in range(board_size):
                temp_coords = []
                for c in range(length):
                    temp_coords.append((r, c + start))
                coords = tuple(temp_coords)
                boats.append(Boat(coords, length, orientation))

    elif orientation == "horizontal":
        for start in range((board_size + 1) - length):
            for r in range(board_size):
                temp_coords = []
                for c in range(length):
                    temp_coords.append((r, c + start))
                coords = tuple(temp_coords)
                boats.append(Boat(coords, length, orientation))

    return boats


# Boats by size and orientation
all_boats_5_horizontal = create_coords(5, "horizontal", BOARD_SIZE)
all_boats_5_vertical = create_coords(5, "vertical", BOARD_SIZE)
all_boats_4_horizontal = create_coords(4, "horizontal", BOARD_SIZE)
all_boats_4_vertical = create_coords(4, "vertical", BOARD_SIZE)
all_boats_3_horizontal = create_coords(3, "horizontal", BOARD_SIZE)
all_boats_3_vertical = create_coords(3, "vertical", BOARD_SIZE)
# all_boats += create_coords(2, "horizontal", BOARD_SIZE)
# all_boats += create_coords(2, "vertical", BOARD_SIZE)

# Boats by size
all_boats_5 = all_boats_5_horizontal + all_boats_5_vertical
all_boats_4 = all_boats_4_horizontal + all_boats_4_vertical
all_boats_3 = all_boats_3_horizontal + all_boats_3_vertical

# All the boats
all_boats = all_boats_5 + all_boats_4 + all_boats_3

# Mini-Game will have one boat of lengths 5, 4, and 3
all_games = []

# there is only one boat of length 5,4, and 3 in each game
for boat1 in all_boats_5:
    for boat2 in all_boats_4:
        for boat3 in all_boats_3:
            all_games.append(Game(tuple([boat1, boat2, boat3])))


# ----------------------------------------- Propositions -----------------------------------------

def build_theory():
    # loop through each possible variation
    for game in all_games:
        valid_game = True
        # check each boat pair for separation and add constraints based on if it is a valid game or not
        for i in range(len(game.boats)):
            for j in range(i + 1, len(game.boats)):
                boat1 = game.boats[i]
                boat2 = game.boats[j]
                if not boats_are_separated(boat1, boat2):
                    valid_game = False
                    break
            if not valid_game:
                break
        if valid_game:
            E.add_constraint(Game(game.boats))

    return E


# Create the propositions
def create_coords(length, orientation, board_size):
    boats = []

    if orientation == "vertical":
        for start in range((board_size+1)-length):
            for r in range(board_size):
                temp_coords = []
                for c in range(length):
                    temp_coords.append((r,c+start))
                coords = tuple(temp_coords)
                boats.append(Boat(coords, length, orientation))

    elif orientation == "horizontal":
        for start in range((board_size+1)-length):
            for r in range(board_size):
                temp_coords = []
                for c in range(length):
                    temp_coords.append((r,c+start))
                coords = tuple(temp_coords)
                boats.append(Boat(coords, length, orientation))

    return boats


def boats_are_separated(boat1, boat2):
    for x1, y1 in boat1.coords:
        for x2, y2 in boat2.coords:
            if abs(x1 - x2) <= 1 and abs(y1 - y2) <= 1:
                return False
    return True

def count_boat_occupancy(possible_games, board_size):
    occupancy_count = [[0 for _ in range(board_size)] for _ in range(board_size)]

    for game in possible_games:
        for boat in game.boats:
            for coord in boat.coords:
                x, y = coord
                occupancy_count[x][y] += 1

    return occupancy_count


def initialize_board(sol):
    board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    for game in sol:
        for boat in game.boats:
            for coord in boat.coords:
                board[coord[0]][coord[1]] += 1
    return board


def print_board(sol, reveal=False):
    # if reveal == true, show boats too (if not hit ofc) ⛵
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            coord = (row, col)
            # itterate through the props and find out what is the state at a given coord
            # if board[row][col] == '1':
            #     print("🟢", end="")
            # if board[row][col] == '2':
            #     print("❌", end="")
            # elif board[row][col] == '3':
            #     print("💥", end="")
            # else:
            #     print("⬛", end="")

    if reveal:
        ...
        # data = np.random.randint(low=1,
        #                         high=100,
        #                         size=(10, 10))

        # # setting the parameter values
        # annot = True

        # # plotting the heatmap
        # hm = sn.heatmap(data=data,
        #                 annot=annot)

        # # displaying the plotted heatmap
        # plt.show()


# for each coord: (satisfiable)/(total possiblites for that coord), remove non-satisfibale to figure out the probability map
# using that map recommend a value

def generate_guesses(guesses):
    # generate at most n guesses
    coords = []
    for _ in range(guesses):
        x = random.randint(0, BOARD_SIZE)
        y = random.randint(0, BOARD_SIZE)
        coords.append((x, y))
    unique_guesses = set(coords)

    return sorted(unique_guesses)


# Similar to print graph in graph theory example
def play_game(sol, score):
    # define the possible guesses

    # print game board - (needs to be adjusted)
    print_board(sol)

    # print probability density board - (needs to be adjusted)
    print_board(sol)

    # if game is finished, exit and print score
    print("Lower scores are better; your score is: " + score)
    # else play the game but with the added constraint
    # play_game(sol, score+1)


def example_game():
    desired_boats = {
        ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4)),
        ((2, 0), (3, 0), (4, 0), (5, 0)),
        ((5, 3), (5, 4), (5, 5))
    }
    desired_guesses = generate_guesses(20)

    ...
    # E.add_constraint(Game(Boat[desired_boats[0]],Boat[desired_boats[1]],Boat[desired_boats[2]]))
    # for guess in desired_guesses:
    #     E.add_constraint(Guess(guess))


if __name__ == "__main__":

    T = build_theory()
    # Don't compile until you're finished adding all your constraints!
    T = T.compile()

    print("\nSatisfiable: %s" % T.satisfiable())
    satisfied = T.solve()

    print("Finding frequency map")
    occupancy_count = count_boat_occupancy(satisfied, BOARD_SIZE)

    for row in occupancy_count:
        print(row)

"""
    To do list
        - implement guessing mechanics
        - make an example game
        - displaya
"""
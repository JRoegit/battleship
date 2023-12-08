
from bauhaus import Encoding, proposition, constraint, Or, And

from bauhaus.utils import count_solutions, likelihood
import string
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
# ----------------------------------------- Propositions -----------------------------------------
@proposition(E)
class Boat(Hashable):
    def __init__(self, coords: tuple, length: int, orientation: str):
        self.coords = coords
        self.length = length
        self.orientation = orientation
        self.hits = 0  # New attribute to track hits

    def hit(self, coord):
        if coord in self.coords:
            self.hits += 1
            return True
        return False

    def is_sunk(self):
        return self.hits == self.length

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
        return f"Guess({self.coords})"


# ----------------------------------------- Variables -----------------------------------------
board_status = [[' ' for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
guesses = []
# Mini-Game will have one boat of lengths 5, 4, and 3
all_games = []
# ----------------------------------------- Create all variations -----------------------------------------


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

# Boats by size
all_boats_5 = all_boats_5_horizontal + all_boats_5_vertical
all_boats_4 = all_boats_4_horizontal + all_boats_4_vertical
all_boats_3 = all_boats_3_horizontal + all_boats_3_vertical

# All the boats
all_boats = all_boats_5 + all_boats_4 + all_boats_3

# generate all possible variations
for boat1 in all_boats_5:
    for boat2 in all_boats_4:
        for boat3 in all_boats_3:
            all_games.append(Game(tuple([boat1, boat2, boat3])))


# ----------------------------------------- Guessing Stuff -----------------------------------------


def get_user_guess(board_status):
    while True:
        try:
            col_input = input("Enter column (A, B, C, etc.): ").upper()
            row_input = input("Enter row (1, 2, 3, etc.): ")

            col = string.ascii_uppercase.index(col_input)
            row = int(row_input) - 1

            if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
                if board_status[row][col] in ['H', 'M']:
                    print("Spot already guessed. Please choose another spot.")
                else:
                    return (row, col)  # Return row and column as zero-indexed values
            else:
                print("Invalid input. Please enter a valid coordinate.")
        except (ValueError, IndexError):
            print("Invalid input. Please enter a valid coordinate.")


def process_guess(game_board, player_board, x, y):
    """
    Check if the guess is a hit or a miss and update the player's board accordingly.
    """
    if game_board[x][y] == 1:
        player_board[x][y] = 'H'  # Mark as hit on the player's board
        return True
    else:
        player_board[x][y] = 'M'  # Mark as miss on the player's board
        return False

# ----------------------------------------- Generate Random Game -----------------------------------------


BOAT_LENGTHS = [5, 4, 3]  # Lengths of boats to be placed


def is_valid_placement(board, boat_coords):
    for x, y in boat_coords:
        if x < 0 or x >= BOARD_SIZE or y < 0 or y >= BOARD_SIZE or board[x][y] == 1:
            return False
        # Check surrounding cells
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                adj_x, adj_y = x + dx, y + dy
                if 0 <= adj_x < BOARD_SIZE and 0 <= adj_y < BOARD_SIZE and board[adj_x][adj_y] == 1:
                    return False
    return True


def place_boat(board, length, max_attempts=1000):
    attempts = 0
    while attempts < max_attempts:
        orientation = random.choice(['horizontal', 'vertical'])
        if orientation == 'horizontal':
            x = random.randint(0, BOARD_SIZE - 1)
            y = random.randint(0, BOARD_SIZE - length)
            boat_coords = [(x, y + i) for i in range(length)]
        else:
            x = random.randint(0, BOARD_SIZE - length)
            y = random.randint(0, BOARD_SIZE - 1)
            boat_coords = [(x + i, y) for i in range(length)]

        if is_valid_placement(board, boat_coords):
            for coord in boat_coords:
                board[coord[0]][coord[1]] = 1  # Mark the boat position
            return True
        attempts += 1

    return False  # Failed to place the boat


def generate_game():
    board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    for length in BOAT_LENGTHS:
        if not place_boat(board, length):
            # Could not place a boat, so start over or handle it differently
            return generate_game()  # This is a simple recursive approach to start over
    return board
# ----------------------------------------- Frequency Map Stuff -----------------------------------------


def is_valid_game(game):
    # Check each pair of boats for separation
    for i in range(len(game.boats)):
        for j in range(i + 1, len(game.boats)):
            if not boats_are_separated(game.boats[i], game.boats[j]):
                return False
    return True


def boats_are_separated(boat1, boat2):
    # check if boats are separated
    for x1, y1 in boat1.coords:
        for x2, y2 in boat2.coords:
            if abs(x1 - x2) <= 1 and abs(y1 - y2) <= 1:
                return False
    return True


def count_boat_occupancy(solutions):
    occupancy_count = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    if solutions is None:
        return occupancy_count  # Return empty or default occupancy count

    # for each solution, get each boat coord and add them to frequency map
    for sol in solutions:
        if hasattr(sol, 'boats') and sol:
            for boat in sol.boats:
                for coord in boat.coords:
                    x, y = coord
                    occupancy_count[x][y] += 1

    return occupancy_count


# ----------------------------------------- Display -----------------------------------------


def print_board(board_status):
    # Print column headers
    print(" ", end=" ")
    for col in range(BOARD_SIZE):
        print(chr(ord('A') + col), end=" ")
    print()

    # Print each row
    for row in range(BOARD_SIZE):
        # Print row number
        print(f"{row + 1}", end=" ")

        # Print each cell in the row
        for col in range(BOARD_SIZE):
            print(board_status[row][col], end=" ")
        print()
# ----------------------------------------- Main -----------------------------------------


def build_theory():
    # clear all previous constraints for a new turn
    E.clear_constraints()
    E._custom_constraints.clear()


    valid_games = []
    # First, find all valid games (with separated boats)
    for game in all_games:
        if is_valid_game(game):
            valid_games.append(game)

    # then remove all invalid games(ones that do not align with the guesses)
    for x, y, is_hit in guesses:
        invalid_games = 0
        for game in valid_games:
            # get true or false based on whether there is a boat at guessed location or not
            boat_at_guess = any(coord == (x, y) for boat in game.boats for coord in boat.coords)
            # if there is a hit but not a boat at the guessed hit or...
            # if there is not a hit at a location but there is a boat:
            # remove that corresponding game from the list
            if (is_hit and not boat_at_guess) or (not is_hit and boat_at_guess):
                invalid_games += 1
                valid_games.remove(game)
        # FOR DEBUGGING
        print(f"Guess at ({x},{y}), Hit: {is_hit}, Invalidated Games: {invalid_games}")

    # all remaining games in valid_games should theoretically align with the separation rules and guesses
    for game in valid_games:
        E.add_constraint(Game(game.boats))

    return E


if __name__ == "__main__":
    # generate a random game
    board_status = generate_game()
    print_board(board_status)

    # set up player board
    player_board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    game_over = False
    while not game_over:
        # Recompile the theory with the updated constraints
        A = build_theory()
        A_new = A.compile()
        new_solution = A_new.solve()

        print("\nSatisfiable: %s" % A_new.satisfiable())

        # Count boat occupancy based on the solutions
        print("Frequency Map:")
        occupancy_count = count_boat_occupancy(new_solution)
        for row in occupancy_count:
            print(row)

        print("Your Board:")
        print_board(player_board)  # Print the current board status

        guess_coord = get_user_guess(player_board)  # Get user guessA
        print(guess_coord)
        x, y = guess_coord

        # determine if the guess is a hit or miss
        # and hold those results inside guesses
        result = process_guess(board_status, player_board, x, y)
        guesses.append((x, y, result))

        # need a game stopper
        if result:  # If the guess is a hit
            for boat in all_boats:  # Assuming all_boats is a list of Boat objects
                if boat.hit((x, y)):
                    print(f"Hit at {x}, {y}!")
                    break

            # Check if all boats are sunk
        all_sunk = all(boat.is_sunk() for boat in all_boats)
        if all_sunk:
            print("All boats have been sunk! Game Over.")
            game_over = True





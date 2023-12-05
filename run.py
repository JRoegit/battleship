
from bauhaus import Encoding, proposition, constraint
from bauhaus.utils import count_solutions, likelihood


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


# Different classes for propositions are useful because this allows for more dynamic constraint creation
# for propositions within that class. For example, you can enforce that "at least one" of the propositions
# that are instances of this class must be true by using a @constraint decorator.
# other options include: at most one, exactly one, at most k, and implies all.
# For a complete module reference, see https://bauhaus.readthedocs.io/en/latest/bauhaus.html
@constraint.at_least_one(E)
@proposition(E)
class FancyPropositions:

    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return f"A.{self.data}"

# Proposition for board cells
@proposition(E)
class BoardCell:
    def __init__(self, player, x, y):
        self.player = player  # Player 1 or 2
        self.x = x  # X-coordinate
        self.y = y  # Y-coordinate

    def __repr__(self):
        return f"BoardCell_Player{self.player}({self.x},{self.y})"

# Proposition for ships
@proposition(E)
class Ship:
    def __init__(self, player, ship_type, x, y):
        self.player = player
        self.ship_type = ship_type  # 'C', 'B', 'D', 'S', 'P'
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Ship{self.ship_type}_Player{self.player}({self.x},{self.y})"

# Proposition for guesses
@proposition(E)
class Guess:
    def __init__(self, player, guess_number, x, y):
        self.player = player
        self.guess_number = guess_number  # Guess turn number
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Guess{self.guess_number}_Player{self.player}({self.x},{self.y})"

# Proposition for hits and misses
@proposition(E)
class HitMiss:
    def __init__(self, player, guess_number, x, y, outcome):
        self.player = player
        self.guess_number = guess_number
        self.x = x
        self.y = y
        self.outcome = outcome  # 'Hit' or 'Miss'

    def __repr__(self):
        return f"HitMiss{self.outcome}_Player{self.player}_Guess{self.guess_number}({self.x},{self.y})"



# Call your variables whatever you want


def map_init(size):
    map = []
    for i in range(size):
        row = []
        for j in range(size):
            row.append()
        map.append(row)
    return map

a = BasicPropositions("a")
b = BasicPropositions("b")
c = BasicPropositions("c")
d = BasicPropositions("d")
e = BasicPropositions("e")
# At least one of these will be true
x = FancyPropositions("x")
y = FancyPropositions("y")
z = FancyPropositions("z")


# Build an example full theory for your setting and return it.
#
#  There should be at least 10 variables, and a sufficiently large formula to describe it (>50 operators).
#  This restriction is fairly minimal, and if there is any concern, reach out to the teaching staff to clarify
#  what the expectations are.
def example_theory():
    # Add custom constraints by creating formulas with the variables you created. 
    E.add_constraint((a | b) & ~x)
    # Implication
    E.add_constraint(y >> z)
    # Negate a formula
    E.add_constraint(~(x & y))
    # You can also add more customized "fancy" constraints. Use case: you don't want to enforce "exactly one"
    # for every instance of BasicPropositions, but you want to enforce it for a, b, and c.:
    constraint.add_exactly_one(E, a, b, c)

    return E


if __name__ == "__main__":

    T = example_theory()
    # Don't compile until you're finished adding all your constraints!
    T = T.compile()
    # After compilation (and only after), you can check some of the properties
    # of your model:
    #print("\nSatisfiable: %s" % T.satisfiable())
    #print("# Solutions: %d" % count_solutions(T))
    #print("   Solution: %s" % T.solve())

    #print("\nVariable likelihoods:")
    #for v,vn in zip([a,b,c,x,y,z], 'abcxyz'):
        # Ensure that you only send these functions NNF formulas
        # Literals are compiled to NNF here
       # print(" %s: %.2f" % (vn, likelihood(T, v)))
    #print()

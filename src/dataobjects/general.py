from enum import Enum
from pprint import pformat

class Player:
    def __init__(self):
        self.id = ''
        self.name = ''
        self.team = ''
        self.handedness = ''
        self.cost = ''
        self.ottoneuPlayerPage = ''
        self.fangraphsPlayerPage  = ''
        self.fangraphsSplitsYearAPIPage = ''
        self.fangraphsStatsYearAPIPage = ''
        self.homeOrAway = ''
        self.league = '' # MLB is empty

    def __repr__(self):
        return pformat(vars(self), indent=4, width=1)

# This allows me to compare Enums and downgrade where appropriate
class OrderedEnum(Enum):
    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented
    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented
    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


class PredictionType(OrderedEnum):
    Empty = 1
    Minors = 2
    Projection = 3
    MajorsOverall = 4
    MajorsSplit = 5

class ProjectionType(OrderedEnum):
    Empty = 1
    Zips = 2
    Steamer = 3

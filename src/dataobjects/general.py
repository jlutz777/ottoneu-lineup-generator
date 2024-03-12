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
        self.homeOrAway = ''
        self.league = '' # MLB is empty

    def __repr__(self):
        return pformat(vars(self), indent=4, width=1)
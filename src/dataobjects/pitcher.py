from pprint import pformat
from .general import Player, PredictionType, ProjectionType

class PitcherData:
    def __init__(self, predictionType: PredictionType, projectionType: ProjectionType):
        self.ab = 0
        self.tbf = 0
        self.h = 0
        self.x2b = 0
        self.x3b = 0
        self.hr = 0
        self.r = 0
        self.er = 0
        self.bb = 0
        self.hbp = 0
        self.so = 0

        self.predictionType = predictionType
        self.projectionType = projectionType

    def __repr__(self):
        return pformat(vars(self), indent=4, width=1)


class Pitcher(Player):
    def __init__(self):
        super().__init__()
        self.opposingTeam = None
        self.pOverall: PitcherData = None
        self.pvsL: PitcherData = None
        self.pvsR: PitcherData = None

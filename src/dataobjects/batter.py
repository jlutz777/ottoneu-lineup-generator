from pprint import pformat
from .general import Player, PredictionType, ProjectionType

class BatterData:
    def __init__(self):
        self.g = 0
        self.ab = 0
        self.h = 0
        self.x2b = 0
        self.x3b = 0
        self.hr = 0
        self.bb = 0
        self.hbp = 0
        self.sb = 0
        self.cs = 0
        self.so = 0

    def __repr__(self):
        return pformat(vars(self), indent=4, width=1)

class Batter(Player):
    def __init__(self):
        super().__init__()
        self.positions = ''
        self.opposingPitcher: Player = None
        self.bOverall: BatterData = None
        self.bvsL: BatterData = None
        self.bvsR: BatterData = None
        self.predictionData: OttoneuBatterPredictionData = None

class OttoneuBatterPredictionData:
    def __init__(self):
        self.predictionType: PredictionType = PredictionType.Empty
        self.projectionType: ProjectionType = ProjectionType.Empty
        self.ab = 0.0
        self.h = 0.0
        self.x2b = 0.0
        self.x3b = 0.0
        self.hr = 0.0
        self.bb = 0.0
        self.hbp = 0.0
        self.sb = 0.0
        self.cs = 0.0
        self.totalPoints = 0.0

    def __repr__(self):
        return pformat(vars(self), indent=4, width=1)
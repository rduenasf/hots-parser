from helpers import *

class eventHandler():

    unitsInGame = {}
    heroActions = {} # this is a dictionary , the key is the hero indexId, the value is a list of tuples
                    # (secsInGame, action)
    heroList = {} # key = playerId - content = hero instance
    heroDeathsList = list()

    def processEvent(self, event):
        event_name = event['_event'].replace('.','_')

        if hasattr(self, event_name):
          getattr(self, event_name)(event)


    def NNet_Replay_Tracker_SUnitBornEvent(self, event):
        """
        This function process the events of the type NNet.Replay.Tracker.SUnitBornEvent
        """
        if event['_event'] != 'NNet.Replay.Tracker.SUnitBornEvent':
            return None

        # Populate unitsInGame
        getUnitsInGame(event, self.unitsInGame)

        # Populate Heroes
        getHero(event, self.heroList)

    def NNet_Replay_Tracker_SUnitDiedEvent(self, event):
        # Populate Hero Death events
        if event['_event'] != 'NNet.Replay.Tracker.SUnitDiedEvent':
            return None

        getHeroDeathsFromReplayEvt(event, self.heroList)
        getUnitDestruction(event, self.unitsInGame)


    def NNet_Game_SCameraUpdateEvent(self, event):
        # Populate Hero Death events based game Events
        if event['_event'] != 'NNet.Game.SCameraUpdateEvent':
            return None

        getHeroDeathsFromGameEvt(event, self.heroList)

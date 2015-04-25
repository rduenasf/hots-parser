from helpers import *
import datetime

class Replay():

    EVENT_FILES = {
      'replay.game.events': 'decode_replay_game_events',
      'replay.tracker.events': 'decode_replay_tracker_events'
    }

    replayInfo = HeroReplay()

    unitsInGame = {}
    heroActions = {} # this is a dictionary , the key is the hero indexId, the value is a list of tuples
                    # (secsInGame, action)
    heroList = {} # key = playerId - content = hero instance
    heroDeathsList = list()

    mapName = ''
    time = None
    players = []

    def __init__(self, protocol, replayFile):
      self.protocol = protocol
      self.replayFile = replayFile

    def process_replay_details(self):
      contents = self.replayFile.read_file('replay.details')
      details = self.protocol.decode_replay_details(contents)

      self.replayInfo.map = details['m_title']
      self.replayInfo.startTime = datetime.datetime.fromtimestamp(int((details['m_timeUTC']/10000000) - 11644473600)).strftime('%Y-%m-%d %H:%M:%S')


      self.players = {}

      for player in details['m_playerList']:
        id = player['m_workingSetSlotId']
        team = player['m_teamId']
        hero = player['m_hero']
        name = player['m_name']
        self.players[player['m_workingSetSlotId']] = Player(id, team, name, hero)


    def process_replay_header(self):
        contents = self.replayFile.header['user_data_header']['content']
        header = self.protocol.decode_replay_header(contents)
        self.replayInfo.duration = header['m_elapsedGameLoops']


    def get_players_in_game(self):
      return self.players.itervalues()


    def process_replay(self):
      for meta in self.EVENT_FILES:
        contents = self.replayFile.read_file(meta)
        events = getattr(self.protocol, self.EVENT_FILES[meta])(contents)
        for event in events:
          self.process_event(event)


    def process_event(self, event):
        event_name = event['_event'].replace('.','_')

        if hasattr(self, event_name):
          getattr(self, event_name)(event)


    def units_in_game(self):
      return self.unitsInGame.itervalues()

    def heroes_in_game(self):
      return self.heroList.itervalues()

    def NNet_Replay_Tracker_SUnitBornEvent(self, event):
        """
        This function process the events of the type NNet.Replay.Tracker.SUnitBornEvent
        """
        if event['_event'] != 'NNet.Replay.Tracker.SUnitBornEvent':
            return None

        # Populate unitsInGame
        unit = getUnitsInGame(event)
        if unit:
          self.unitsInGame[unit.unitTag] = unit


        # Populate Heroes
        hero = getHeroes(event, self.players)
        if hero:
          self.heroList[hero.playerId] = hero

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

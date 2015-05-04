__author__ = 'Rodrigo Duenas, Cristian Orellana'
from helpers import *
from data import *


class Replay():

    EVENT_FILES = {
        'replay.tracker.events': 'decode_replay_tracker_events',
        'replay.game.events': 'decode_replay_game_events'
    }

    replayInfo = HeroReplay()


    unitsInGame = {}
    heroActions = {} # this is a dictionary , the key is the hero indexId, the value is a list of tuples
                    # (secsInGame, action)
    heroList = {} # key = playerId - content = hero instance
    team0 = Team()
    team1 = Team()
    heroDeathsList = list()
    abilityList = list()

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
      self.replayInfo.startTime = win_timestamp_to_date(details['m_timeUTC'])


      self.players = {}
      totalHumans = 0

      for player in details['m_playerList']:
        toonHandle = '-'.join([str(player['m_toon']['m_region']),player['m_toon']['m_programId'],str(player['m_toon']['m_realm']),str(player['m_toon']['m_id'])])
        id = player['m_workingSetSlotId']
        team = player['m_teamId']
        hero = player['m_hero']
        name = player['m_name']
        if (player['m_toon']['m_region'] != 0):
            userId = totalHumans
            totalHumans += 1
        else:
            userId = -1
        gameResult = int(player['m_result'])

        self.players[player['m_workingSetSlotId']] = Player(id, userId, team, name, hero, gameResult,  toonHandle)


    def process_replay_header(self):
        contents = self.replayFile.header['user_data_header']['content']
        header = self.protocol.decode_replay_header(contents)
        self.replayInfo.gameLoops = header['m_elapsedGameLoops']

    def process_replay_attributes(self):
        contents = self.replayFile.read_file('replay.attributes.events')
        attributes = self.protocol.decode_replay_attributes_events(contents)

        # Get if players are human or not
        for playerId in attributes['scopes'].keys():
            if playerId <= len(self.heroList):
                self.heroList[playerId - 1].isHuman = (attributes['scopes'][playerId][500][0]['value'] == 'Humn')

        # If player is human, get the level this player has for the selected hero
                if self.heroList[playerId - 1].isHuman:
                    self.players[playerId - 1].heroLevel = attributes['scopes'][playerId][4008][0]['value']

        # Get game type
        self.replayInfo.gameType = attributes['scopes'][16][3009][0]['value']


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

    def get_clicked_units(self):
        return [unit for unit in self.unitsInGame.itervalues() if len(unit.clickerList) > 0]


    def units_in_game(self):
      return self.unitsInGame.itervalues()

    def heroes_in_game(self):
      return self.heroList.itervalues()

    def calculate_game_strength(self):
      self.army_strength = [
        [[t, 0] for t in xrange(1, self.replayInfo.durations_in_secs() + 1)],
        [[t, 0] for t in xrange(1, self.replayInfo.durations_in_secs() + 1)]
      ]


      self.merc_strength = [
        [[t, 0] for t in xrange(1, self.replayInfo.durations_in_secs() + 1)],
        [[t, 0] for t in xrange(1, self.replayInfo.durations_in_secs() + 1)]
      ]

      for unit in self.units_in_game():
        if unit.team not in [0,1] and (not unit.is_army_unit() or not unit.is_hired_mercenary() or not unit.is_advanced_unit()):
          continue

        end = unit.get_death_time(self.replayInfo.durations_in_secs())
        # if end > self.replayInfo.durations_in_secs():
        #     continue
            # end = self.replayInfo.durations_in_secs()
        for second in xrange(unit.bornAt, end):
          #print "army_strength[%s][%s][1]" % (unit.team, second)
          self.army_strength[unit.team][second][1] += unit.get_strength()

          if unit.is_mercenary():
            self.merc_strength[unit.team][second][1] += unit.get_strength()

    def setTeamsLevel(self):

        if len(self.team0.memberList) > 0:
        # Team 0
            maxTalentSelected = max([len(self.heroList[x].pickedTalents) for x in self.heroList if self.heroList[x].team == 0])
            self.team0.level = num_choices_to_level[maxTalentSelected]
        # Team 1
        if len(self.team1.memberList) > 0:
            maxTalentSelected = max([len(self.heroList[x].pickedTalents) for x in self.heroList if self.heroList[x].team == 1])
            self.team1.level = num_choices_to_level[maxTalentSelected]



    def NNet_Replay_Tracker_SUnitBornEvent(self, event):
        """
        This function process the events of the type NNet.Replay.Tracker.SUnitBornEvent
        """
        if event['_event'] != 'NNet.Replay.Tracker.SUnitBornEvent':
            return None

        # Populate Heroes
        hero = getHeroes(event, self.players)
        if hero:
            self.heroList[hero.playerId] = hero
            # create/update team
            if hero.team == 0:
                if hero.playerId not in self.team0.memberList:
                    self.team0.memberList.append(hero.playerId)
                    if self.team0.isWinner is None:
                        self.team0.id = self.players[hero.playerId].team
                        self.team0.isWinner = self.players[hero.playerId].is_winner()
                        self.team0.isLoser = self.players[hero.playerId].is_loser()

            elif hero.team == 1:
                if hero.playerId not in self.team1.memberList:
                    self.team1.memberList.append(hero.playerId)
                    if self.team1.isWinner is None:
                        self.team1.id = self.players[hero.playerId].team
                        self.team1.isWinner = self.players[hero.playerId].is_winner()
                        self.team1.isLoser = self.players[hero.playerId].is_loser()


        # Populate unitsInGame
        unit = getUnitsInGame(event)
        if unit: #There is a bug in the replay where random units are created at game loop 4294996406
            self.unitsInGame[unit.unitTag] = unit





    def NNet_Replay_Tracker_SUnitDiedEvent(self, event):
        # Populate Hero Death events
        if event['_event'] != 'NNet.Replay.Tracker.SUnitDiedEvent':
            return None

        #getHeroDeathsFromReplayEvt(event, self.heroList)
        getUnitDestruction(event, self.unitsInGame)


    def NNet_Replay_Tracker_SUnitOwnerChangeEvent(self, event):
        if event['_event'] != 'NNet.Replay.Tracker.SUnitOwnerChangeEvent':
            return None

        getUnitOwners(event, self.unitsInGame)


    def NNet_Game_SCameraUpdateEvent(self, event):
        # Populate Hero Death events based game Events
        if event['_event'] != 'NNet.Game.SCameraUpdateEvent':
            return None
        getHeroDeathsFromGameEvt(event, self.heroList)

    def NNet_Game_SCmdUpdateTargetUnitEvent(self, event):
        if event['_event'] != 'NNet.Game.SCmdUpdateTargetUnitEvent':
            return None

        getUnitClicked(event, self.unitsInGame)


    def NNet_Game_SCmdEvent(self, event):
        if event['_event'] != 'NNet.Game.SCmdEvent':
            return None

        ability = getAbilities(event)
        if ability:
            # update hero stat
            playerId = findPlayerKeyFromUserId(self.players, ability.userId)
            self.heroList[playerId].castedAbilities[ability.castedAtGameLoops] = ability


    def NNet_Game_SHeroTalentTreeSelectedEvent(self, event):
        if event['_event'] != 'NNet.Game.SHeroTalentTreeSelectedEvent':
            return None

        playerId = event['_userid']['m_userId'] #findPlayerKeyFromUserId(self.players, event['_userid']['m_userId'])
        hero = self.heroList[playerId]
        heroName = hero.internalName


        #talentName = hero_talent_options[heroName][event['m_index']][0]
        hero.pickedTalents[event['_gameloop']] = event['m_index']







        # totalPickedTalents = hero.get_total_picked_talents()
        # talentIndex = 1 + event['m_index'] - hero._lastTalentTierLen
        #
        # # if talentIndex < 0:
        # #     print "Getting talent index %s total %s (%s) %s" % (talentIndex, totalPickedTalents, heroName, playerId)
        # #     print "m_index: %s lastTalentTierLen: %s TalentIndex: %s" % ( event['m_index'], hero._lastTalentTierLen, talentIndex)
        # #     #return 0
        # # if talentIndex > len(hero_talent_options[heroName][totalPickedTalents][1]) - 1:
        # #     print "Getting talent index %s total %s (%s) %s" % (talentIndex, totalPickedTalents, heroName, playerId)
        # #     print "m_index: %s lastTalentTierLen: %s TalentIndex: %s" % ( event['m_index'], hero._lastTalentTierLen, talentIndex)
        # #     #return 0
        # try:
        #
        # except IndexError, e:
        #     print "Getting talent index %s total %s (%s) %s" % (talentIndex, totalPickedTalents, heroName, playerId)
        #     print "m_index: %s lastTalentTierLen: %s TalentIndex: %s" % ( event['m_index'], hero._lastTalentTierLen, talentIndex)


__author__ = 'Rodrigo Duenas, Cristian Orellana'

from data import *
from models import *
from hashlib import sha256

class Replay():

    EVENT_FILES = {
        'replay.tracker.events': 'decode_replay_tracker_events',
        'replay.game.events': 'decode_replay_game_events'
    }

    # Stores functions to process specific map logic
    MAP_LOGIC = {
        'Cursed Hollow': 'process_cursed_hollow',
        'Dragon Shire': 'process_dragon_shire',
        'Tomb of the Spider Queen': 'process_tom_of_the_spider_queen',
        'Haunted Mines': 'process_haunted_mines',
        'Sky Temple': 'process_sky_temple',
        'Garden of Terror': 'process_garden_of_terror',
        'Blackheart\'s Bay': 'process_blackhearts_bay'
    }

    replayInfo = None
    unitsInGame = {}
    heroActions = {} # this is a dictionary , the key is the hero indexId, the value is a list of tuples
                    # (secsInGame, action)
    heroList = {} # key = playerId - content = hero instance
    team0 = Team()
    team1 = Team()
    heroDeathsList = list()
    abilityList = list()

    time = None
    players = []
    # stores NNet_Game_SCmdUpdateTargetPointEvent events
    utpe = {}
    utue = {}

    def __init__(self, protocol, replayFile):
      self.protocol = protocol
      self.replayFile = replayFile

    def get_replay_id(self):
        _id = list()
        for h in self.team0.memberList:
            _id.append(self.players[h].toonHandle)
        for h in self.team1.memberList:
            _id.append(self.players[h].toonHandle)
        _id = '_'.join(_id)
        id = "%s_%s" % (self.replayInfo.randomVal,_id)
        return sha256(id).hexdigest()

    def process_replay_details(self):
        contents = self.replayFile.read_file('replay.details')
        details = self.protocol.decode_replay_details(contents)

        self.replayInfo = HeroReplay(details)
        self.players = {}
        totalHumans = 0
        for player in details['m_playerList']:
            p = Player(player)
            if p.isHuman:
                p.userId = totalHumans
                totalHumans += 1
            else:
                p.userId = -1
            self.players[player['m_workingSetSlotId']] = p

    def process_replay_initdata(self):
        return 0
        # contents = self.replayFile.read_file('replay.initData')
        # initdata = self.protocol.decode_replay_initdata(contents)
        # self.replayInfo.randomVal = initdata['m_syncLobbyState']['m_gameDescription']['m_randomValue']
        # self.replayInfo.speed = initdata['m_syncLobbyState']['m_gameDescription']['m_gameSpeed']


    def process_replay_header(self):
        contents = self.replayFile.header['user_data_header']['content']
        header = self.protocol.decode_replay_header(contents)
        self.replayInfo.gameLoops = header['m_elapsedGameLoops']
        self.replayInfo.gameVersion = header['m_dataBuildNum']

    def process_replay_attributes(self):
        contents = self.replayFile.read_file('replay.attributes.events')
        attributes = self.protocol.decode_replay_attributes_events(contents)

        # Get if players are human or not
        for playerId in attributes['scopes'].keys():
            # if playerId <= len(self.heroList):
            if self.heroList.get((playerId - 1), None) is not None:
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

    def get_lifespan_time_in_gameloops(self, unitTag):
        return self.unitsInGame[unitTag].gameLoopsAlive if self.unitsInGame[unitTag].gameLoopsAlive >= 0 else self.replayInfo.gameLoops - self.unitsInGame[unitTag].bornAtGameLoops

    def get_lifespan_time_in_seconds(self, unitTag):
        return get_seconds_from_int_gameloop(self.unitsInGame[unitTag].gameLoopsAlive) if self.unitsInGame[unitTag].gameLoopsAlive >= 0 else self.replayInfo.duration_in_secs() - self.unitsInGame[unitTag].bornAt

    def process_event(self, event):
        event_name = event['_event'].replace('.', '_')

        if hasattr(self, event_name):
          getattr(self, event_name)(event)

    def get_clicked_units(self):
        return [unit for unit in self.unitsInGame.itervalues() if len(unit.clickerList) > 0]

    def process_regen_globes_stats(self):
        for capturedUnitTag in self.unitsInGame.keys():
            if self.unitsInGame[capturedUnitTag].is_regen_globe():
                if len(self.unitsInGame[capturedUnitTag].ownerList) > 0:
                    self.heroList[self.unitsInGame[capturedUnitTag].ownerList[-1][0]].regenGlobesTaken += 1
                else: # if there is no one in the ownerlist then this regenglobe wasn't used
                    if self.unitsInGame[capturedUnitTag].team == 0:
                        self.team0.missedRegenGlobes += 1
                    elif self.unitsInGame[capturedUnitTag].team == 1:
                        self.team1.missedRegenGlobes += 1


    def process_clicked_unit(self,e):
        if e['_event'] != 'NNet.Game.SCmdUpdateTargetUnitEvent':
            return None
        unitTag = e['m_target']['m_tag']
        if unitTag in self.unitsInGame.keys():
            # Process Tributes
            if self.unitsInGame[unitTag].is_tribute():

                playerId = e['_userid']['m_userId']
                self.unitsInGame[unitTag].clickerList[get_gameloops(e)] = playerId
                # Increment Hero clickedTributes attribute
                self.heroList[playerId].clickedTributes += 1
            #TODO Add else conditions for each type of clickable unit

    def process_cursed_hollow(self):
         for capturedUnitTag in self.unitsInGame.keys():
            candidates = {}
            if self.unitsInGame[capturedUnitTag].is_tribute():
                # Capturer is the last player that clicked the tribute before it "die"
                for loop in self.unitsInGame[capturedUnitTag].clickerList.keys():
                    if self.unitsInGame[capturedUnitTag].diedAtGameLoops:
                        if (int(self.unitsInGame[capturedUnitTag].diedAtGameLoops) - int(loop)) in xrange(97,120):
                            candidates[int(self.unitsInGame[capturedUnitTag].diedAtGameLoops) - int(loop)] = loop

                if len(candidates) > 0:
                    minloop = min(candidates.keys())
                    capturerId = self.unitsInGame[capturedUnitTag].clickerList[candidates[minloop]]
                    # Increment Hero capturedTributes attribute
                    #print "%s captured by %s at %s" % (i, self.heroList[capturerId].name, loop)
                    self.heroList[capturerId].capturedTributes += 1
                # if no click in the range, just take the last one (sometime happens)
                else:
                    if self.unitsInGame[capturedUnitTag].diedAtGameLoops: # discard last clickers of non-taken tributes (i.e. the game ends while someone clicked a tribute)
                        lastLoop = self.unitsInGame[capturedUnitTag].clickerList.keys()[-1]
                        capturerId = self.unitsInGame[capturedUnitTag].clickerList[lastLoop]
                        #print "%s captured by %s at %s" % (i, self.heroList[capturerId].name, loop)
                        self.heroList[capturerId].capturedTributes += 1
# TODO: build a time line with important events
    def process_tomb_of_the_spider_queen(self):
        for unitTag in self.unitsInGame.keys():
            if self.unitsInGame[unitTag].is_tomb_of_the_spider_pickable():

                # process non-picked souls
                if self.unitsInGame[unitTag].gameLoopsAlive == PICKUNITS[self.unitsInGame[unitTag].internalName]:
                    team = self.unitsInGame[unitTag].team
                    if team == 0:
                        self.team0.wastedSoulGems += 1
                    elif team == 1:
                        self.team1.wastedSoulGems += 1
                # process picked souls
                else:
                    team = self.unitsInGame[unitTag].team
                    if team == 0:
                        self.team0.pickedSoulGems += 1
                    elif team == 1:
                        self.team1.pickedSoulGems += 1


            # process spider boss
            # get how many seconds each spider lived
            # get how many structures died in the lane the spider was
            elif self.unitsInGame[unitTag].is_spider_summon():
                duration = self.get_lifespan_time_in_seconds(unitTag)
                team = self.unitsInGame[unitTag].team
                if team == 0:
                    self.team0.summonedSpiderBosses += 1
                    self.team0.spiderBossesTotalAliveTime += duration
                    self.team0.totalBuildingsKilledDuringSpiders +=  self.unitsInGame[unitTag].buildingsKilled
                    self.team0.totalUnitsKilledDuringSpiders += self.unitsInGame[unitTag].unitsKilled
                elif team == 1:
                    self.team1.summonedSpiderBosses += 1
                    self.team1.spiderBossesTotalAliveTime += duration
                    self.team1.totalBuildingsKilledDuringSpiders +=  self.unitsInGame[unitTag].buildingsKilled
                    self.team1.totalUnitsKilledDuringSpiders += self.unitsInGame[unitTag].unitsKilled


                for unit in self.unitsInGame.keys():
                    targetDiedAt = self.unitsInGame[unit].diedAtGameLoops
                    spiderY = self.unitsInGame[unitTag].bornAtY
                    targetDiedY = self.unitsInGame[unit].diedAtY
                    bornAt = self.unitsInGame[unitTag].bornAtGameLoops
                    diedAt = self.unitsInGame[unitTag].diedAtGameLoops if self.unitsInGame[unitTag].diedAtGameLoops is not None else self.replayInfo.gameLoops
                    # TODO calculate unitEffectivity by calculating dead units around the spider (unitValue * distance to spider when died)
                    if targetDiedAt in xrange(bornAt, diedAt) and targetDiedY in xrange(spiderY - 10, spiderY + 10):
                        if team == 0:
                            if self.unitsInGame[unit].is_building():
                                self.team0.totalBuildingsKilledDuringSpiders += 1
                            elif self.unitsInGame[unit].is_hired_mercenary() or self.unitsInGame[unit].is_army_unit():
                                self.team0.totalUnitsKilledDuringSpiders += 1
                        if team == 1:
                            if self.unitsInGame[unit].is_building():
                                self.team1.totalBuildingsKilledDuringSpiders += 1
                            elif self.unitsInGame[unit].is_hired_mercenary() or self.unitsInGame[unit].is_army_unit():
                                self.team1.totalUnitsKilledDuringSpiders += 1

                if SOUL_EATER_POSITIONS[self.unitsInGame[unitTag].bornAtY] == 'North':
                    if team == 0:
                        self.team0.spiderBossesNorthTotalAliveTime += duration
                    if team == 1:
                        self.team1.spiderBossesNorthTotalAliveTime += duration
                elif SOUL_EATER_POSITIONS[self.unitsInGame[unitTag].bornAtY] == 'Center':
                    if team == 0:
                        self.team0.spiderBossesCenterTotalAliveTime += duration
                    if team == 1:
                        self.team1.spiderBossesCenterTotalAliveTime += duration
                elif SOUL_EATER_POSITIONS[self.unitsInGame[unitTag].bornAtY] == 'South':
                    if team == 0:
                        self.team0.spiderBossesSouthTotalAliveTime += duration
                    if team == 1:
                        self.team1.spiderBossesSouthTotalAliveTime += duration


                    # TODO: add lost structures per team


                    # minDist = (9999, None) # dist,playerId
                    # for loop in self.utpe.keys():
                    #     userId = self.utpe[loop].get('_userid', None).get('m_userId', None)
                    #     if userId:
                    #         team = self.heroList[userId].team
                    #         if (self.unitsInGame[capturedUnitTag].diedAtGameLoops - loop) in xrange(100) and self.unitsInGame[capturedUnitTag].team == team:
                    #             soulX = self.unitsInGame[capturedUnitTag].diedAtX
                    #             soulY = self.unitsInGame[capturedUnitTag].diedAtY
                    #             playerX = self.utpe[loop]['m_target']['x']
                    #             playerY = self.utpe[loop]['m_target']['y']
                    #             dist = calculate_distance(soulX, playerX, soulY, playerY)
                    #             minDist = (dist, userId) if dist < minDist[0] else minDist
                    #
                    #     else:
                    #         pass

    def process_sky_temple(self):
        for unitTag in self.unitsInGame.keys():
            if self.unitsInGame[unitTag].internalName == 'LuxoriaTemple':
                for team, gameloop, duration in self.unitsInGame[unitTag].ownerList:
                    if team == 0:
                        self.team0.luxoriaTemplesCaptured += 1
                        self.team0.luxoriaTemplesCapturedSeconds += duration
                    if team == 1:
                        self.team1.luxoriaTemplesCaptured += 1
                        self.team1.luxoriaTemplesCapturedSeconds += duration
                    if SKY_TEMPLE_POSITIONS[self.unitsInGame[unitTag].bornAtY] == 'North':
                        if team == 0:
                            self.team0.luxoriaTempleNorthCaptured += 1
                            self.team0.luxoriaTempleNorthCapturedSeconds += duration
                        if team == 1:
                            self.team1.luxoriaTempleNorthCaptured += 1
                            self.team1.luxoriaTempleNorthCapturedSeconds += duration
                    elif SKY_TEMPLE_POSITIONS[self.unitsInGame[unitTag].bornAtY] == 'Center':
                        if team == 0:
                            self.team0.luxoriaTempleCenterCaptured += 1
                            self.team0.luxoriaTempleCenterCapturedSeconds += duration
                        if team == 1:
                            self.team1.luxoriaTempleCenterCaptured += 1
                            self.team1.luxoriaTempleCenterCapturedSeconds += duration
                    elif SKY_TEMPLE_POSITIONS[self.unitsInGame[unitTag].bornAtY] == 'South':
                        if team == 0:
                            self.team0.luxoriaTempleSouthCaptured += 1
                            self.team0.luxoriaTempleSouthCapturedSeconds += duration
                        if team == 1:
                            self.team1.luxoriaTempleSouthCaptured += 1
                            self.team1.luxoriaTempleSouthCapturedSeconds += duration








    def process_map_events(self):
        # Run a custom logic for each map
        map_name = self.replayInfo.internalMapName.replace('\'','').replace(' ', '_').lower()
        process_name = 'process_' + map_name
        if hasattr(self, process_name):
            getattr(self, process_name)()



    def process_generic_events(self):
        self.process_regen_globes_stats()





    def get_unit_destruction(self, e):
        """
        Gets information when a non-hero unit is destroyed
        """
        if e['_event'] == 'NNet.Replay.Tracker.SUnitDiedEvent':
            deadUnitTag = get_unit_tag(e)
            try:
                self.unitsInGame[deadUnitTag].diedAt = get_seconds_from_event_gameloop(e)
                self.unitsInGame[deadUnitTag].diedAtX = e['m_x']
                self.unitsInGame[deadUnitTag].diedAtY = e['m_y']
                self.unitsInGame[deadUnitTag].diedAtGameLoops = get_gameloops(e)
                self.unitsInGame[deadUnitTag].gameLoopsAlive = self.unitsInGame[deadUnitTag].diedAtGameLoops - self.unitsInGame[deadUnitTag].bornAtGameLoops
                self.unitsInGame[deadUnitTag].killerPlayerId = e['m_killerPlayerId']
                if self.unitsInGame[deadUnitTag].is_building():
                    self.unitsInGame[e['m_killerPlayerId']].buildingsKilled += 1
                elif self.unitsInGame[deadUnitTag].is_army_unit() or self.unitsInGame[deadUnitTag].is_hired_mercenary():
                    self.unitsInGame[e['m_killerPlayerId']].unitsKilled += 1


            except:
               pass

    def units_in_game(self):
      return self.unitsInGame.itervalues()

    def heroes_in_game(self):
      return self.heroList.itervalues()

    def calculate_game_strength(self):
      #print "TOTAL DURATION %s" % self.replayInfo.durations_in_secs()
      self.army_strength = [
        [[t, 0] for t in xrange(1, self.replayInfo.duration_in_secs() + 1)],
        [[t, 0] for t in xrange(1, self.replayInfo.duration_in_secs() + 1)]
      ]


      self.merc_strength = [
        [[t, 0] for t in xrange(1, self.replayInfo.duration_in_secs() + 1)],
        [[t, 0] for t in xrange(1, self.replayInfo.duration_in_secs() + 1)]
      ]

      for unit in self.units_in_game():
        if unit.team not in [0,1] and (not unit.is_army_unit() or not unit.is_hired_mercenary() or not unit.is_advanced_unit()):
          continue

        end = unit.get_death_time(self.replayInfo.duration_in_secs())
        # if end > self.replayInfo.durations_in_secs():
        #     continue
            # end = self.replayInfo.durations_in_secs()
        for second in xrange(unit.bornAt, end):
          #print "army_strength[%s][%s][1]" % (unit.team, second)
          try:
              self.army_strength[unit.team][second][1] += unit.get_strength()

              if unit.is_mercenary():
                self.merc_strength[unit.team][second][1] += unit.get_strength()
          except IndexError:
              # for some cosmic reason some events are happening after the game is over D:
              pass

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
        if event['m_unitTypeName'].startswith('Hero') and event['m_unitTypeName'] not in ('ChenFire', 'ChenStormConduit', 'ChenEarthConduit', 'ChenFireConduit'):
            hero = HeroUnit(event, self.players)
            if hero:
                self.heroList[hero.playerId] = hero
                # create/update team
                if hero.team == 0:
                    if hero.playerId not in self.team0.memberList:
                        self.team0.add_member(hero, self.players)

                elif hero.team == 1:
                    if hero.playerId not in self.team1.memberList:
                        self.team1.add_member(hero, self.players)


        # Populate unitsInGame
        unit = GameUnit(event)
        if unit:
            self.unitsInGame[unit.unitTag] = unit
            # Get Map Name based on the unique units of each map
            if self.replayInfo.internalMapName is None:
                self.replayInfo.internalMapName = UNIQUEMAPUNITS.get(unit.internalName, None)




    def NNet_Replay_Tracker_SUnitDiedEvent(self, event):
        # Populate Hero Death events
        if event['_event'] != 'NNet.Replay.Tracker.SUnitDiedEvent':
            return None

        get_hero_death_from_tracker_events(event, self.heroList)
        self.get_unit_destruction(event)


    def NNet_Replay_Tracker_SUnitOwnerChangeEvent(self, event):
        if event['_event'] != 'NNet.Replay.Tracker.SUnitOwnerChangeEvent':
            return None

        get_unit_owners(event, self.unitsInGame)


    def NNet_Game_SCameraUpdateEvent(self, event):
        # Populate Hero Death events based game Events
        if event['_event'] != 'NNet.Game.SCameraUpdateEvent':
            return None
        get_hero_deaths_from_game_event(event, self.heroList)

    def NNet_Game_SCmdUpdateTargetUnitEvent(self, event):
        if event['_event'] != 'NNet.Game.SCmdUpdateTargetUnitEvent':
            return None
        self.utue[event['_gameloop']] = event
        self.process_clicked_unit(event)


    def NNet_Game_SCmdEvent(self, event):
        if event['_event'] != 'NNet.Game.SCmdEvent':
            return None

        ability = None

        if event['m_abil']: # If this is an actual user available ability
            if event['m_data'].get('TargetPoint'):
                ability = TargetPointAbility(event)

            elif event['m_data'].get('TargetUnit'):
                ability = TargetUnitAbility(event)

            else: # e['m_data'].get('None'):
                ability = BaseAbility(event)


        if ability:
            # update hero stat
            playerId = find_player_key_from_user_id(self.players, ability.userId)
            self.heroList[playerId].castedAbilities[ability.castedAtGameLoops] = ability


    def NNet_Game_SHeroTalentTreeSelectedEvent(self, event):
        if event['_event'] != 'NNet.Game.SHeroTalentTreeSelectedEvent':
            return None

        playerId = event['_userid']['m_userId'] #findPlayerKeyFromUserId(self.players, event['_userid']['m_userId'])
        hero = self.heroList[playerId]

        #talentName = hero_talent_options[heroName][event['m_index']][0]
        hero.pickedTalents[event['_gameloop']] = event['m_index']


    def NNet_Game_SCmdUpdateTargetPointEvent(self, event):
        self.utpe[event['_gameloop']] = event





    def NNet_Game_SCommandManagerStateEvent(self, event):
        if event['_event'] != 'NNet.Game.SCommandManagerStateEvent':
            return None

        # Get the _gameloops, find the accompanying NNet.Game.SCmdUpdateTargetPointEvent (if any) and get data

        try:
            if event['m_state'] == 1:
                if self.utpe.get(event['_gameloop']):
                    if self.utpe[event['_gameloop']]['_userid']['m_userId'] == event['_userid']['m_userId']:
                        playerId = find_player_key_from_user_id(self.players, event['_userid']['m_userId'])
                        abilities = self.heroList[playerId].castedAbilities
                        if len(abilities) > 0:
                            self.utpe.get(event['_gameloop'])['m_abilityTag'] = abilities[abilities.keys()[-1]].abilityTag # use last known ability (it's a repetition)
                            ability = TargetPointAbility(self.utpe.get(event['_gameloop']))
                            if ability:
                                self.heroList[playerId].castedAbilities[ability.castedAtGameLoops] = ability

                elif self.utue.get(event['_gameloop']):
                    playerId = find_player_key_from_user_id(self.players, event['_userid']['m_userId'])
                    abilities = self.heroList[playerId].castedAbilities
                    if len(abilities) > 0:
                        self.utue.get(event['_gameloop'])['m_abilityTag'] = abilities[abilities.keys()[-1]].abilityTag
                        ability = TargetUnitAbility(self.utue.get(event['_gameloop']))
                        if ability:
                            self.heroList[playerId].castedAbilities[ability.castedAtGameLoops] = ability

                else:
                # This was not a targeted skill
                    playerId = find_player_key_from_user_id(self.players, event['_userid']['m_userId'])
                    abilities = self.heroList[playerId].castedAbilities
                    if len(abilities) > 0:
                        event['m_abilityTag'] = abilities[abilities.keys()[-1]].abilityTag
                        ability = BaseAbility(event)
                        if ability:
                            self.heroList[playerId].castedAbilities[ability.castedAtGameLoops] = ability
        except Exception, e:
            print abilities


    # TODO: Increase hero stats (beacons taken, etc)





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


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
    temp_indexes = {} # key = UnitTagIndex, UnitTag

    timeline = {} # key = when (in seconds), value = event {} key = team - value = description


    heroActions = {} # this is a dictionary , the key is the hero indexId, the value is a list of tuples
                    # (secsInGame, action)
    heroList = {} # key = playerId - content = hero instance
    upgrades = {} # key = gameloop - content = upgrade instance
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
                    if targetDiedAt in xrange(bornAt, diedAt + 1) and targetDiedY in xrange(spiderY - 20, spiderY + 21) and self.unitsInGame[unit].team != team:
                        if team == 0:
                            if self.unitsInGame[unit].is_building():
                                self.team0.totalBuildingsKilledDuringSpiders += 1
                            elif self.unitsInGame[unit].is_hired_mercenary() or self.unitsInGame[unit].is_army_unit() or self.unitsInGame[unit].is_advanced_unit():
                                self.team0.totalUnitsKilledDuringSpiders += 1
                            if SOUL_EATER_POSITIONS[spiderY] == 'North':
                                if self.unitsInGame[unit].is_building():
                                    self.team0.totalBuildingsKilledDuringNorthSpider += 1
                                elif self.unitsInGame[unit].is_hired_mercenary() or self.unitsInGame[unit].is_army_unit() or self.unitsInGame[unit].is_advanced_unit():
                                    self.team0.totalUnitsKilledDuringNorthSpider += 1
                            if SOUL_EATER_POSITIONS[spiderY] == 'Center':
                                if self.unitsInGame[unit].is_building():
                                    self.team0.totalBuildingsKilledDuringCenterSpider += 1
                                elif self.unitsInGame[unit].is_hired_mercenary() or self.unitsInGame[unit].is_army_unit() or self.unitsInGame[unit].is_advanced_unit():
                                    self.team0.totalUnitsKilledDuringCenterSpider += 1
                            if SOUL_EATER_POSITIONS[spiderY] == 'South':
                                if self.unitsInGame[unit].is_building():
                                    self.team0.totalBuildingsKilledDuringSouthSpider += 1
                                elif self.unitsInGame[unit].is_hired_mercenary() or self.unitsInGame[unit].is_army_unit() or self.unitsInGame[unit].is_advanced_unit():
                                    self.team0.totalUnitsKilledDuringSouthSpider += 1
                        if team == 1:
                            if self.unitsInGame[unit].is_building():
                                self.team1.totalBuildingsKilledDuringSpiders += 1
                            elif self.unitsInGame[unit].is_hired_mercenary() or self.unitsInGame[unit].is_army_unit() or self.unitsInGame[unit].is_advanced_unit():
                                self.team1.totalUnitsKilledDuringSpiders += 1
                            if SOUL_EATER_POSITIONS[spiderY] == 'North':
                                if self.unitsInGame[unit].is_building():
                                    self.team1.totalBuildingsKilledDuringNorthSpider += 1
                                elif self.unitsInGame[unit].is_hired_mercenary() or self.unitsInGame[unit].is_army_unit() or self.unitsInGame[unit].is_advanced_unit():
                                    self.team1.totalUnitsKilledDuringNorthSpider += 1
                            if SOUL_EATER_POSITIONS[spiderY] == 'Center':
                                if self.unitsInGame[unit].is_building():
                                    self.team1.totalBuildingsKilledDuringCenterSpider += 1
                                elif self.unitsInGame[unit].is_hired_mercenary() or self.unitsInGame[unit].is_army_unit() or self.unitsInGame[unit].is_advanced_unit():
                                    self.team1.totalUnitsKilledDuringCenterSpider += 1
                            if SOUL_EATER_POSITIONS[spiderY] == 'South':
                                if self.unitsInGame[unit].is_building():
                                    self.team1.totalBuildingsKilledDuringSouthSpider += 1
                                elif self.unitsInGame[unit].is_hired_mercenary() or self.unitsInGame[unit].is_army_unit() or self.unitsInGame[unit].is_advanced_unit():
                                    self.team1.totalUnitsKilledDuringSouthSpider += 1

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



    def process_blackhearts_bay(self):
        t0_cannons = {}
        t1_cannons = {}
        t0 = 0
        t1 = 0

        for unitTag in self.unitsInGame.keys():
            unit = self.unitsInGame[unitTag]
            if unit.internalName == 'GhostShipBeacon':
                #print unit.ownerList
                for team, when, duration in unit.ownerList:
                    effectiveness = 0
                    units_killed = 0
                    buildings_destroyed = 0
                    for u in self.unitsInGame.keys():
                        enemy = self.unitsInGame[u]
                        if enemy.diedAtGameLoops is not None:
                                if enemy.team != unit.team and enemy != unit and enemy.get_death_time(self.replayInfo.duration_in_secs()) in xrange(when, when + duration + 1) and enemy.isDead:
                                    effectiveness += enemy.get_strength()
                                    if enemy.is_building():
                                        buildings_destroyed += 1
                                    else:
                                        units_killed += 1

                    if team == 0:
                        t0 += 1
                        self.team0.totalShipsControlled[t0] = duration
                        self.team0.totalUnitsKilledDuringShip[t0] = units_killed
                        self.team0.totalBuildingsDestroyedDuringShip[t0] = buildings_destroyed
                        self.team0.shipEffectiveness[t0] = effectiveness

                    elif team == 1:
                        t1 += 1
                        self.team1.totalShipsControlled[t1] = duration
                        self.team1.totalUnitsKilledDuringShip[t1] = units_killed
                        self.team1.totalBuildingsDestroyedDuringShip[t1] = buildings_destroyed
                        self.team1.shipEffectiveness[t1] = effectiveness






    def process_dragon_shire(self):
        dragon_count_0 = 0
        dragon_count_1 = 0
        general_dragon_count = 0
        dragon_creation_time = {}

        for unitTag in self.unitsInGame.keys():
            if self.unitsInGame[unitTag].is_dragon_statue():
                # Populate list of dragons statues
                dragon_creation_time[self.unitsInGame[unitTag].bornAtGameLoops] = self.unitsInGame[unitTag]



        dragon_creation_time_sorted = sorted(dragon_creation_time.keys(), key=lambda s: s)


        for upgrade in self.upgrades.keys():

            if self.upgrades[upgrade].is_dragon_upgrade():
                general_dragon_count += 1
                dragon_effectiveness = 0
                units_killed_during = 0
                buildings_killed_during = 0
                dragon_unit = dragon_creation_time[max([gl for gl in dragon_creation_time_sorted if gl < upgrade])]
                contested_time = sum([dur for team, when, dur in dragon_unit.ownerList if team == -1 and when not in dragon_creation_time])
                wasted_dragon_time_t0 = sum([dur for team, when, dur in dragon_unit.ownerList if team == 0 and when not in dragon_creation_time])
                wasted_dragon_time_t1 = sum([dur for team, when, dur in dragon_unit.ownerList if team == 1 and when not in dragon_creation_time])
                dragon_created_at = get_seconds_from_int_gameloop(self.upgrades[upgrade].gameloops)
                dragon_unit.positions[self.upgrades[upgrade].gameloops] = [dragon_unit.bornAtX, dragon_unit.bornAtY]
                dragon_unit.bornAtGameLoops = self.upgrades[upgrade].gameloops
                controller_of_dragon = self.upgrades[upgrade].upgradedPlayerId
                owner_team = self.heroList[controller_of_dragon].team
                diedAt = dragon_unit.get_death_time(self.replayInfo.duration_in_secs())
                positions = get_position_by_second(dragon_unit, self.replayInfo.duration_in_secs())
                dragon_duration_in_secs = diedAt - dragon_created_at
                totalUnits =  dragon_unit.unitsKilled
                totalBuildings = dragon_unit.buildingsKilled

                try:
                    for unit in self.unitsInGame.keys():
                        if self.unitsInGame[unit].diedAtGameLoops is not None:
                            if self.unitsInGame[unit].team != self.heroList[controller_of_dragon].team and unit != dragon_unit.unitTag and self.unitsInGame[unit].get_death_time(self.replayInfo.duration_in_secs()) in xrange(dragon_created_at, diedAt + 1) and self.unitsInGame[unit].isDead:
                                if self.unitsInGame[unit].is_hired_mercenary() or self.unitsInGame[unit].is_army_unit() or self.unitsInGame[unit].is_advanced_unit() or self.unitsInGame[unit].is_building():
                                    targetDiedAt = self.unitsInGame[unit].diedAtGameLoops # when the unit died
                                    targetDiedY = self.unitsInGame[unit].diedAtY # Y coord when unit died
                                    targetDiedX = self.unitsInGame[unit].diedAtX # X coord when unit died
                                    dragon_x = positions[get_seconds_from_int_gameloop(targetDiedAt)][0] # X coord of dragon when unit died
                                    dragon_y = positions[get_seconds_from_int_gameloop(targetDiedAt)][1] # Y coord of dragon when unit died
                                    distance_from_dragon = calculate_distance(targetDiedX, targetDiedY, dragon_x, dragon_y)
                                    if distance_from_dragon > 0:
                                        dragon_effectiveness += 10/distance_from_dragon * self.unitsInGame[unit].get_strength() # that 10 is just a made up number LOL
                                    if self.unitsInGame[unit].is_building():
                                        buildings_killed_during += 1
                                    else:
                                        units_killed_during += 1
                except Exception, e:
                    pass

                self.team0.wastedDragonTime[general_dragon_count] = wasted_dragon_time_t0
                self.team1.wastedDragonTime[general_dragon_count] = wasted_dragon_time_t1

                print self.team0.wastedDragonTime[general_dragon_count], self.team1.wastedDragonTime[general_dragon_count], contested_time

                #
                if owner_team == 0:
                    dragon_count_0 += 1
                    self.team0.totaldragonsSummoned[dragon_count_0] = dragon_created_at
                    self.team0.totaldragonsDuration[dragon_count_0] = dragon_duration_in_secs
                    self.team0.totalUnitsKilledBydragons[dragon_count_0] = totalUnits
                    self.team0.totalBuildingsKilledBydragons[dragon_count_0] = totalBuildings
                    self.team0.dragonEffectiveness[dragon_count_0] = round(dragon_effectiveness,2)
                    self.team0.totalBuildingsKilledDuringdragon[dragon_count_0] = buildings_killed_during
                    self.team0.totalUnitsKilledDuringdragon[dragon_count_0] = units_killed_during
                #
                elif owner_team == 1:
                    dragon_count_1 += 1
                    self.team1.totaldragonsSummoned[dragon_count_1] = dragon_created_at
                    self.team1.totaldragonsDuration[dragon_count_1] = dragon_duration_in_secs
                    self.team1.totalUnitsKilledBydragons[dragon_count_1] = totalUnits
                    self.team1.totalBuildingsKilledBydragons[dragon_count_1] = totalBuildings
                    self.team1.dragonEffectiveness[dragon_count_1] = round(dragon_effectiveness,2)
                    self.team1.totalBuildingsKilledDuringdragon[dragon_count_1] = buildings_killed_during
                    self.team1.totalUnitsKilledDuringdragon[dragon_count_1] = units_killed_during

                #     # Update Hero Stats
                self.heroList[controller_of_dragon].totalDragonsControlled += 1
                if self.heroList[controller_of_dragon].team == 0:
                    self.heroList[controller_of_dragon].totalUnitsKilledAsDragon[dragon_count_0] =  units_killed_during
                    self.heroList[controller_of_dragon].totalBuildingsKilledAsDragon[dragon_count_0] =  buildings_killed_during
                elif self.heroList[controller_of_dragon].team == 1:
                    self.heroList[controller_of_dragon].totalUnitsKilledAsDragon[dragon_count_1] =  units_killed_during
                    self.heroList[controller_of_dragon].totalBuildingsKilledAsDragon[dragon_count_1] =  buildings_killed_during


    def process_garden_of_terror(self):
        plant_count_0 = 0
        plant_count_1 = 0
        for unitTag in self.unitsInGame.keys():

            if self.unitsInGame[unitTag].is_plant_vehicle():
                #print "Plant Count %s " % plant_count
                # When a hero clicks on the Overgrowth plant 2 things happen:
                # 1.- PlantHorrorOvergrowthPlant unit is created, the m_upkeepPlayerId of this unit is the controller of the plant
                # 2.- VehiclePlantHorror unit is created, this is the actual unit the player controlls
                # After the unit dies (by time up or damage) two things happen:
                # 1.- There is a unitDie event for the unit, so we can get the diedAtGameLoop
                # 2.- there is a NNet.Replay.Tracker.SUnitOwnerChangeEvent event the m_upkeepPlayerId is the same as the one who created the plant
                # Notes:
                # * There is also a NNet.Game.SCmdUpdateTargetUnitEvent in gameevent it doesn't add any new info.
                # Update hero count
                #print "Tag: %s , TagIndex: %s, Recycle: %s, Owner: %s" % (unitTag, self.unitsInGame[unitTag].unitTagIndex, self.unitsInGame[unitTag].unitTagRecycle, self.unitsInGame[unitTag].ownerList)
                # Update Team Stats
                if len(self.unitsInGame[unitTag].ownerList) > 0: # if the unit was controlled
                    plant_effectiveness = 0
                    units_killed_during = 0
                    buildings_killed_during = 0
                    positions = get_position_by_second(self.unitsInGame[unitTag], self.replayInfo.duration_in_secs())
                    bornAt = self.unitsInGame[unitTag].ownerList[0][1]

                    diedAt = self.unitsInGame[unitTag].get_death_time(self.replayInfo.duration_in_secs())
                    plant_duration_in_secs = diedAt - self.unitsInGame[unitTag].ownerList[0][1]
                    controller_playerId = self.unitsInGame[unitTag].ownerList[0][0]
                    totalUnits =  self.unitsInGame[unitTag].unitsKilled
                    totalBuildings = self.unitsInGame[unitTag].buildingsKilled
                                        # self.team0.totalPlantsSummoned = 0
                    # self.team0.totalPlantsDuration[plant_count] = 0# plant number, value
                    # self.team0.totalUnitsKilledByPlants[plant_count] = 0 # plant number, value
                    # self.team0.totalBuildingsKilledByPlants[plant_count] = 0 # plant number, value
                    #
                    #
                    # self.team1.totalPlantsDuration[plant_count] = 0 # plant number, value
                    # self.team1.totalUnitsKilledByPlants[plant_count] = 0 # plant number, value
                    # self.team1.totalBuildingsKilledByPlants[plant_count] = 0 # plant number, value
                    # calculate self.totalPlantPotsKilled = 0 # plant number, value

                    # Get units that died while this plant was active. Include only those who were in the nearby of the unit.
                    try:
                        for unit in self.unitsInGame.keys():
                            if self.unitsInGame[unit].diedAtGameLoops is not None:
                                if self.unitsInGame[unit].team != self.heroList[controller_playerId].team and unit != unitTag and self.unitsInGame[unit].get_death_time(self.replayInfo.duration_in_secs()) in xrange(bornAt, diedAt + 1) and self.unitsInGame[unit].isDead:
                                    if self.unitsInGame[unit].is_hired_mercenary() or self.unitsInGame[unit].is_army_unit() or self.unitsInGame[unit].is_advanced_unit() or self.unitsInGame[unit].is_building():
                                        targetDiedAt = self.unitsInGame[unit].get_death_time(self.replayInfo.duration_in_secs()) # when the unit died
                                        targetDiedY = self.unitsInGame[unit].diedAtY # Y coord when unit died
                                        targetDiedX = self.unitsInGame[unit].diedAtX # X coord when unit died
                                        plant_x = positions[targetDiedAt][0] # X coord of plant when unit died
                                        plant_y = positions[targetDiedAt][1] # Y coord of plant when unit died
                                        distance_from_plant = calculate_distance(targetDiedX, targetDiedY, plant_x, plant_y)
                                        if distance_from_plant > 0:
                                            plant_effectiveness += 10/distance_from_plant * self.unitsInGame[unit].get_strength() # that 10 is just a made up number LOL
                                        if self.unitsInGame[unit].is_building():
                                            buildings_killed_during += 1
                                        else:
                                            units_killed_during += 1
                    except Exception, e:
                        pass


                    if self.unitsInGame[unitTag].team == 0:
                        plant_count_0 += 1
                        self.team0.totalPlantsSummoned[plant_count_0] = bornAt
                        self.team0.totalPlantsDuration[plant_count_0] = plant_duration_in_secs
                        self.team0.totalUnitsKilledByPlants[plant_count_0] = totalUnits
                        self.team0.totalBuildingsKilledByPlants[plant_count_0] = totalBuildings
                        self.team0.plantEffectiveness[plant_count_0] = round(plant_effectiveness,2)
                        self.team0.totalBuildingsKilledDuringPlant[plant_count_0] = buildings_killed_during
                        self.team0.totalUnitsKilledDuringPlant[plant_count_0] = units_killed_during

                    elif self.unitsInGame[unitTag].team == 1:
                        plant_count_1 += 1
                        self.team1.totalPlantsSummoned[plant_count_1] = bornAt
                        self.team1.totalPlantsDuration[plant_count_1] = plant_duration_in_secs
                        self.team1.totalUnitsKilledByPlants[plant_count_1] = totalUnits
                        self.team1.totalBuildingsKilledByPlants[plant_count_1] = totalBuildings
                        self.team1.plantEffectiveness[plant_count_1] = round(plant_effectiveness,2)
                        self.team1.totalBuildingsKilledDuringPlant[plant_count_1] = buildings_killed_during
                        self.team1.totalUnitsKilledDuringPlant[plant_count_1] = units_killed_during
                    # Update Hero Stats
                    self.heroList[controller_playerId].totalPlantsControlled += 1
                    if self.heroList[controller_playerId].team == 0:
                        self.heroList[controller_playerId].totalUnitsKilledAsPlant[plant_count_0] =  units_killed_during
                        self.heroList[controller_playerId].totalBuildingsKilledAsPlant[plant_count_0] =  buildings_killed_during
                    elif self.heroList[controller_playerId].team == 1:
                        self.heroList[controller_playerId].totalUnitsKilledAsPlant[plant_count_1] =  units_killed_during
                        self.heroList[controller_playerId].totalBuildingsKilledAsPlant[plant_count_1] =  buildings_killed_during

            if self.unitsInGame[unitTag].is_plant_pot():
                self.team1.totalPlantPotsPlaced[plant_count_1] = 0# plant number, value
                self.team0.totalPlantPotsPlaced[plant_count_0] = 0 # plant number, value
                if self.unitsInGame[unitTag].team == 0:
                    if self.unitsInGame[unitTag].killerTag is not None:
                        self.team1.totalPlantPotsKilled += 1
                    self.team0.totalPlantPotsPlaced[plant_count_0] += 1
                elif self.unitsInGame[unitTag].team == 1:
                    if self.unitsInGame[unitTag].killerTag is not None:
                        self.team0.totalPlantPotsKilled += 1
                    self.team1.totalPlantPotsPlaced[plant_count_1] += 1


    def process_haunted_mines(self):

        golem_body_positions = {}
        units_killed_during_golem = 0
        buildings_destroyed_during_golem = 0
        golem_effectiveness = 0
        golems = {}
        t1_count = 0
        t0_count = 0

        for unitTag in self.unitsInGame.keys():
            if self.unitsInGame[unitTag].is_golem_body():
                golem_body_positions[self.unitsInGame[unitTag].bornAtGameLoops] = self.unitsInGame[unitTag]


            elif self.unitsInGame[unitTag].is_golem():# and self.unitsInGame[unitTag].bornAtX != 0 and self.unitsInGame[unitTag].bornAtY != 0:
                if self.unitsInGame[unitTag].bornAtX == 0 and self.unitsInGame[unitTag].bornAtY == 0:
                    position = [gl for gl in golem_body_positions.keys() if gl <= self.unitsInGame[unitTag].bornAtGameLoops]
                    if len(position) > 0:
                        self.unitsInGame[unitTag].bornAtX = golem_body_positions[position[-1]].bornAtX
                        self.unitsInGame[unitTag].bornAtY = golem_body_positions[position[-1]].bornAtY
                team = self.unitsInGame[unitTag].team
                golems[self.unitsInGame[unitTag].bornAtGameLoops] = self.unitsInGame[unitTag]
                bornAt = self.unitsInGame[unitTag].bornAt
                diedAt = self.unitsInGame[unitTag].get_death_time(self.replayInfo.duration_in_secs())
                # if the unit was alive at the end of the game, then update the positions.
                if diedAt == self.replayInfo.duration_in_secs():
                    self.unitsInGame[unitTag].diedAtGameLoops = self.replayInfo.gameLoops
                    # use last known position
                    last_known_position = self.unitsInGame[unitTag].positions.keys()[-1]
                    last_x = self.unitsInGame[unitTag].positions[last_known_position][0]
                    last_y = self.unitsInGame[unitTag].positions[last_known_position][1]
                    self.unitsInGame[unitTag].positions[self.replayInfo.gameLoops] = [last_x, last_y]

                positions = get_position_by_second(self.unitsInGame[unitTag], self.replayInfo.duration_in_secs())
                distance_traveled = calculate_distance(self.unitsInGame[unitTag].bornAtX, self.unitsInGame[unitTag].positions[self.unitsInGame[unitTag].diedAtGameLoops][0], self.unitsInGame[unitTag].bornAtY, self.unitsInGame[unitTag].positions[self.unitsInGame[unitTag].diedAtGameLoops][1])


                golem_duration_in_secs = diedAt - bornAt
                units_killed_by_golem =  self.unitsInGame[unitTag].unitsKilled
                buildings_destroyed_by_golem = self.unitsInGame[unitTag].buildingsKilled
                for unit in self.unitsInGame.keys():
                    if self.unitsInGame[unit].team != team and unit != unitTag and self.unitsInGame[unit].get_death_time(self.replayInfo.duration_in_secs()) in xrange(bornAt, diedAt + 1) and self.unitsInGame[unit].isDead:
                        if self.unitsInGame[unit].is_hired_mercenary() or self.unitsInGame[unit].is_army_unit() or self.unitsInGame[unit].is_advanced_unit() or self.unitsInGame[unit].is_building():
                            targetDiedAt = self.unitsInGame[unit].get_death_time(self.replayInfo.duration_in_secs()) # when the unit died
                            targetDiedY = self.unitsInGame[unit].diedAtY # Y coord when unit died
                            targetDiedX = self.unitsInGame[unit].diedAtX # X coord when unit died
                            golem_x = positions[targetDiedAt][0] # X coord of plant when unit died
                            golem_y = positions[targetDiedAt][1] # Y coord of plant when unit died
                            distance_from_golem = calculate_distance(targetDiedX, targetDiedY, golem_x, golem_y)
                            if distance_from_golem > 0:
                                golem_effectiveness += 10/distance_from_golem * self.unitsInGame[unit].get_strength() # that 10 is just a made up number LOL
                            if self.unitsInGame[unit].is_building():
                                buildings_destroyed_during_golem += 1
                            else:
                                units_killed_during_golem += 1

                if self.unitsInGame[unitTag].team == 0:
                    t0_count += 1
                    self.team0.totalGolemsSummoned[t0_count] = bornAt
                    self.team0.totalGolemDuration[t0_count] = golem_duration_in_secs
                    self.team0.totalUnitsKilledByGolem = units_killed_by_golem
                    self.team0.totalBuildingsKilledByGolem = buildings_destroyed_by_golem
                    self.team0.totalUnitsKilledDuringGolem = units_killed_during_golem
                    self.team0.totalGolemDistanceTraveled[t0_count] = distance_traveled

                elif self.unitsInGame[unitTag].team == 1:
                    t1_count += 1
                    self.team1.totalGolemsSummoned[t1_count] = bornAt
                    self.team1.totalGolemDuration[t1_count] = golem_duration_in_secs
                    self.team1.totalUnitsKilledByGolem = units_killed_by_golem
                    self.team1.totalBuildingsKilledByGolem = buildings_destroyed_by_golem
                    self.team1.totalUnitsKilledDuringGolem = units_killed_during_golem
                    self.team1.totalGolemDistanceTraveled[t1_count] = distance_traveled


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
            # try:
            self.unitsInGame[deadUnitTag].diedAt = get_seconds_from_event_gameloop(e)
            self.unitsInGame[deadUnitTag].isDead = True
            self.unitsInGame[deadUnitTag].diedAtX = e['m_x']
            self.unitsInGame[deadUnitTag].diedAtY = e['m_y']
            self.unitsInGame[deadUnitTag].diedAtGameLoops = get_gameloops(e)
            self.unitsInGame[deadUnitTag].gameLoopsAlive = self.unitsInGame[deadUnitTag].diedAtGameLoops - self.unitsInGame[deadUnitTag].bornAtGameLoops
            self.unitsInGame[deadUnitTag].killerPlayerId = e['m_killerPlayerId']
            self.unitsInGame[deadUnitTag].positions[get_gameloops(e)] = [e['m_x'], e['m_y']]
            # if self.unitsInGame[deadUnitTag].is_building():
            #     if e['m_killerPlayerId'] in self.heroList.keys():
            #         self.unitsInGame[e['m_killerPlayerId']].buildingsKilled += 1
            # elif self.unitsInGame[deadUnitTag].is_army_unit() or self.unitsInGame[deadUnitTag].is_hired_mercenary() or self.unitsInGame[deadUnitTag].is_advanced_unit():
            #     if e['m_killerPlayerId'] in self.heroList.keys():
            #         self.unitsInGame[e['m_killerPlayerId']].unitsKilled += 1
            # remove the entry in loop_per_index
            # update owner list duration
            if self.unitsInGame[deadUnitTag].is_plant_vehicle():
                self.unitsInGame[deadUnitTag].ownerList[0][2] = self.unitsInGame[deadUnitTag].diedAt - self.unitsInGame[deadUnitTag].ownerList[0][1]

            if self.temp_indexes.get(deadUnitTag):
                del self.temp_indexes[deadUnitTag]



            # except:
            #    print "FAIL"

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
        for second in xrange(unit.bornAt, end + 1):
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

    def NNet_Replay_Tracker_SUpgradeEvent(self, event):
        """
        Process an upgrade i.e. Dragon
        """
        if event['_event'] != 'NNet.Replay.Tracker.SUpgradeEvent':
            return None
        upgrade = UnitUpgrade(event)
        if upgrade:
            self.upgrades[upgrade.gameloops] = upgrade


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

            self.temp_indexes[unit.unitTagIndex] = unit.unitTag




    def NNet_Replay_Tracker_SUnitDiedEvent(self, event):
        # Populate Hero Death events
        if event['_event'] != 'NNet.Replay.Tracker.SUnitDiedEvent':
            return None

        get_hero_death_from_tracker_events(event, self.heroList)
        self.get_unit_destruction(event)


    def NNet_Replay_Tracker_SUnitOwnerChangeEvent(self, event):
        if event['_event'] != 'NNet.Replay.Tracker.SUnitOwnerChangeEvent':
            return None

        get_unit_owners(event, self.unitsInGame, self.replayInfo.duration_in_secs())


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


    def NNet_Replay_Tracker_SUnitPositionsEvent(self, event):
        if event['_event'] != 'NNet.Replay.Tracker.SUnitPositionsEvent':
            return None

        unitIndex = event['m_firstUnitIndex']
        for i in xrange(0, len(event['m_items']), 3):
            unitIndex += event['m_items'][i + 0]
            x = event['m_items'][i + 1] #* 4
            y = event['m_items'][i + 2] #* 4
            unitTag = self.temp_indexes.get(unitIndex,None)
            if unitTag:
                self.unitsInGame[unitTag].positions[event['_gameloop']] = [x, y]



            # for unitTag in self.unitsInGame.keys():
            #     if not self.unitsInGame[unitTag].is_hero() and not self.unitsInGame[unitTag].is_building():
            #         if gameloop in xrange(self.unitsInGame[unitTag].bornAtGameLoops, self.unitsInGame[unitTag].bornAtGameLoops + self.get_lifespan_time_in_gameloops(unitTag)):
            #             if unitIndex == self.unitsInGame[unitTag].unitTagIndex:
            #                 self.unitsInGame[unitTag].positions[gameloop] = {'x': x, 'y': y}


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


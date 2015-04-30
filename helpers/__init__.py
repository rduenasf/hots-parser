
from models import *
from data import *
import datetime
import json



#def getArmyStr()

def win_timestamp_to_date(timestamp=None, date_format='%Y-%m-%d %H:%M:%S'):
    if timestamp:
        return datetime.datetime.fromtimestamp(int((timestamp/10000000) - 11644473600)).strftime(date_format)
    else:
        return None


def getHeroes(e, players):
    """
    Parse the event and looks if the unit created is a hero or not
    if so, adds a new hero to the heroList.
    Also creates/updates the team of the hero.
    """

    # if a new hero unit is born
    if e['_event'] == 'NNet.Replay.Tracker.SUnitBornEvent' and e['m_unitTypeName'].startswith('Hero'):
        playerId = e['m_upkeepPlayerId'] - 1

        hero = HeroUnit()
        hero.playerId = playerId
        hero.name = players[playerId].hero
        hero.team = players[playerId].team
        hero.userId = e['m_upkeepPlayerId'] - 1
        hero.internalName = e['m_unitTypeName'][4:]
        hero.unitTagIndex = e['m_unitTagIndex']
        hero.unitTagRecycle = e['m_unitTagRecycle']
        hero.unitTag = hero.unit_tag()


        return hero


def getUnitOwners(e, unitsInGame):
    """
    Get the owner of the unit and the time the unit was owned.
    """
    if e['_event'] == 'NNet.Replay.Tracker.SUnitOwnerChangeEvent' and e['m_upkeepPlayerId'] in (11, 12):
        unitTag = (e['m_unitTagIndex'] << 18) + e['m_unitTagRecycle']
        owner = e['m_upkeepPlayerId'] - 11
        ownerTuple = (owner, int(e['_gameloop']/16))
        unitsInGame[unitTag].ownerList.append(ownerTuple)

def getUnitClicked(e, unitsInGame):
    """
    Gets information when a unit has been clicked by another one. i.e: When clicking tribute or returning souls
    """

    if e['_event'] == 'NNet.Game.SCmdUpdateTargetUnitEvent':
        unitTag = e['m_target']['m_tag']
        if unitTag in unitsInGame.keys():
            if unitsInGame[unitTag].is_tribute():
                playerId = e['_userid']['m_userId']
                clickTuple = (playerId, int(e['_gameloop']/16))
                unitsInGame[unitTag].clickerList.append(clickTuple)


def getUnitDestruction(e, unitsInGame):
    """
    Gets information when a non-hero unit is destroyed
    """
    if e['_event'] == 'NNet.Replay.Tracker.SUnitDiedEvent':
        deadUnitTag = (e['m_unitTagIndex'] << 18) + e['m_unitTagRecycle']
        try:
            unitsInGame[deadUnitTag].diedAt = int(e['_gameloop']/16)
            unitsInGame[deadUnitTag].diedAtGameLoops = e['_gameloop']
            unitsInGame[deadUnitTag].gameLoopsAlive = unitsInGame[deadUnitTag].diedAtGameLoops - unitsInGame[deadUnitTag].bornAtGameLoops
            unitsInGame[deadUnitTag].killerPlayerId = e['m_killerPlayerId']

        except:
           pass

def findHeroKeyFromTag(heroList=None, tag=None):
    if len(heroList) == 0 or not heroList:
        return None
    else:
        for k, v in heroList.iteritems():
            if v.unitTag == tag:
                return k

def findPlayerKeyFromUserId(playerList=None, userId=None):
    if len(playerList) == 0 or not playerList:
        return None
    else:
        for k, v in playerList.iteritems():
            if v.userId == userId:
                return k

def findHeroKeyFromUserId(heroList=None, userId=None):
    if len(heroList) == 0 or not heroList:
        return None
    else:
        for k, v in heroList.iteritems():
            if v.userId == userId:
                return k

def getHeroDeathsFromReplayEvt(e, heroList):
    """
    This function works by reading the specific Replay Tracker Event information
    Parse the event and looks if a hero unit was destroyed, if so, adds a new entry to the deathList
    """

    deadUnitTag = (e['m_unitTagIndex'] << 18) + e['m_unitTagRecycle']
    playerId = findHeroKeyFromTag(heroList, deadUnitTag)

    if e['_event'] == 'NNet.Replay.Tracker.SUnitDiedEvent' and playerId is not None:

        if e['m_killerUnitTagIndex']:
            killerUnitTag = (e['m_killerUnitTagIndex'] << 18) + e['m_killerUnitTagRecycle']
            heroDeathEvent = {'killerPlayerId': e['m_killerPlayerId'], 'killerUnitIndex': killerUnitTag}
            heroList[playerId].deathList[int(e['_gameloop']/16)] = heroDeathEvent
            heroList[playerId].deathCount += 1
        else:
            # There is a bug that cause m_killerUnitTagIndex and m_killerUnitTagRecycle to be null
            heroDeathEvent = {'killerPlayerId': e['m_killerPlayerId'], 'killerUnitIndex': None}
            heroList[playerId].deathList[int(e['_gameloop']/16)] = heroDeathEvent
            heroList[playerId].deathCount += 1

def getAbilities(e):
    """
    This function read an NNet.Game.SCmdEvent and gets relevant information

    """

    if e['m_abil']: # If this is an actual user available ability
        if e['m_data'].get('TargetPoint'):
            tpa = TargetPointAbility()
            tpa.abilityTag = e['m_abil']['m_abilLink'] << 5 | e['m_abil']['m_abilCmdIndex']
            tpa.castedAt = int(e['_gameloop'] / 16)
            tpa.userId = e['_userid']['m_userId']
            tpa.castedAtGameLoops = e['_gameloop']
            tpa.x = e['m_data']['TargetPoint']['x']/4096.0
            tpa.y = e['m_data']['TargetPoint']['y']/4096.0
            tpa.z = e['m_data']['TargetPoint']['z']/4096.0

            return tpa




        elif e['m_data'].get('TargetUnit'):
            tua = TargetUnitAbility()
            tua.abilityTag = e['m_abil']['m_abilLink'] << 5 | e['m_abil']['m_abilCmdIndex']
            tua.castedAt = int(e['_gameloop'] / 16)
            tua.userId = e['_userid']['m_userId']
            tua.castedAtGameLoops = e['_gameloop']
            tua.x = e['m_data']['TargetUnit']['m_snapshotPoint']['x']/4096.0
            tua.y = e['m_data']['TargetUnit']['m_snapshotPoint']['y']/4096.0
            tua.z = e['m_data']['TargetUnit']['m_snapshotPoint']['z']/4096.0
            tua.targetPlayerId = e['m_data']['TargetUnit']['m_snapshotControlPlayerId']
            tua.targetTeamId = e['m_data']['TargetUnit']['m_snapshotUpkeepPlayerId']
            tua.targetUnitTag = e['m_data']['TargetUnit']['m_tag']

            return tua

        elif e['m_data'].get('None'):
            abil = BaseAbility()
            abil.abilityTag = e['m_abil']['m_abilLink'] << 5 | e['m_abil']['m_abilCmdIndex']
            abil.castedAtGameLoops = e['_gameloop']
            abil.castedAt = int(e['_gameloop'] / 16)
            abil.userId =  e['_userid']['m_userId']

            return abil



def getHeroDeathsFromGameEvt(e, heroList):
    """
    This function works by reading the specific Game Event information
    Parse the event and looks if a there is a NNet.Game.SCameraUpdateEvent with no m_target (None)
    this only happens when the camera is pointing to the spawn area. It uses the m_userId instead of
    the unitIndex
    """

    if e['_event'] == 'NNet.Game.SCameraUpdateEvent' and not e['m_target'] and e['_gameloop'] > 10:
        # find the hero
        playerId =  findHeroKeyFromUserId(heroList, (e['_userid']['m_userId']))
        unitTag = [key for (key, value) in sorted(heroList.items()) if value.playerId == playerId][0]
        eventTime = int(e['_gameloop']/16)

        if len(heroList[unitTag].deathList.keys()) > 0:
            if eventTime - int(heroList[unitTag].deathList.keys()[0]) > 12: # we need this to rule out the first event which is actually tracked
                heroDeathEvent = {'killerPlayerId': None , 'killerUnitIndex': None} # sadly, we don't know who killed it
                heroList[unitTag].deathList[eventTime] = heroDeathEvent # and this is actually the respawn time, not death time
                heroList[unitTag].deathCount += 1

def getUnitsInGame(e):

    """
    Stores all units
    """
    if e['_event'] == 'NNet.Replay.Tracker.SUnitBornEvent' and not e['m_unitTypeName'].startswith('Hero'):
        unit = GameUnit()
        unit.unitTagIndex = e['m_unitTagIndex']
        unit.unitTagRecycle = e['m_unitTagRecycle']
        unit.unitTag = unit.unit_tag()
        unit.bornAt = int(e['_gameloop']/16)
        unit.bornAtGameLoops = e['_gameloop']
        unit.internalName = e['m_unitTypeName']
        unit.team = e['m_upkeepPlayerId'] - 11
        unit.bornAtX = e['m_x']
        unit.bornAtY = e['m_y']

        return unit


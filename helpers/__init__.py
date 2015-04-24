
from models import *

def getGemPicked(e, unitList):
    """
    Gets soul gems that were never picked up
    This function should run after the events are parsed and the unitList creation/destruction info is populated
    """

    gemUnitIndexes = [key for (key, value) in sorted(unitList.items()) if value.internalName == 'ItemSoulPickup']
    for gemIndex in gemUnitIndexes:
        if unitList[gemIndex].gameLoopsAlive in xrange(0,127):
            unitList[gemIndex].wasPicked = True



#def getArmyStr()


def getHero(e, heroList):
    """
    Parse the event and looks if the unit created is a hero or not
    if so, adds a new hero to the heroList
    """

    # if a new hero unit is born
    if e['_event'] == 'NNet.Replay.Tracker.SUnitBornEvent' and e['m_unitTypeName'].startswith('Hero'):
        newHero = HeroUnit()
        newHero.internalName = e['m_unitTypeName'].split('Hero')[1]
        newHero.unitIndex = (e['m_unitTagIndex'] << 18) + e['m_unitTagRecycle']
        newHero.playerId = e['m_upkeepPlayerId']

        heroList[newHero.unitIndex]= newHero

def getUnitDestruction(e, unitsInGame):
    """
    Gets information when a non-hero unit is destroyed
    """
    if e['_event'] == 'NNet.Replay.Tracker.SUnitDiedEvent':
        deadUnitIndex = (e['m_unitTagIndex'] << 18) + e['m_unitTagRecycle']
        try:
            unitsInGame[deadUnitIndex].diedAt = int(e['_gameloop']/16)
            unitsInGame[deadUnitIndex].diedAtGameLoops = e['_gameloop']
            unitsInGame[deadUnitIndex].gameLoopsAlive = unitsInGame[deadUnitIndex].diedAtGameLoops - unitsInGame[deadUnitIndex].bornAtGameLoops
        except:
           pass

def getHeroDeathsFromReplayEvt(e, heroList):
    """
    This function works by reading the specific Replay Tracker Event information
    Parse the event and looks if a hero unit was destroyed, if so, adds a new entry to the deathList
    """

    deadUnitIndex = (e['m_unitTagIndex'] << 18) + e['m_unitTagRecycle']
    if e['_event'] == 'NNet.Replay.Tracker.SUnitDiedEvent' and deadUnitIndex in heroList.keys():

        if e['m_killerUnitTagIndex']:
            killerUnitIndex = (e['m_killerUnitTagIndex'] << 18) + e['m_killerUnitTagRecycle']
            heroDeathEvent = {'killerPlayerId': e['m_killerPlayerId'], 'killerUnitIndex': killerUnitIndex}
            heroList[deadUnitIndex].deathList[int(e['_gameloop']/16)] = heroDeathEvent
            heroList[deadUnitIndex].deathCount += 1
        else:
            # There is a bug that cause m_killerUnitTagIndex and m_killerUnitTagRecycle to be null
            heroDeathEvent = {'killerPlayerId': e['m_killerPlayerId'], 'killerUnitIndex': None}
            heroList[deadUnitIndex].deathList[int(e['_gameloop']/16)] = heroDeathEvent
            heroList[deadUnitIndex].deathCount += 1

def getHeroDeathsFromGameEvt(e, heroList):
    """
    This function works by reading the specific Game Event information
    Parse the event and looks if a there is a NNet.Game.SCameraUpdateEvent with no m_target (None)
    this only happens when the camera is pointing to the spawn area. It uses the m_userId instead of
    the unitIndex
    """

    if e['_event'] == 'NNet.Game.SCameraUpdateEvent' and not e['m_target'] and e['_gameloop'] > 10:
        # find the hero
        playerId =  int(e['_userid']['m_userId']) + 1
        unitIndex = [key for (key, value) in sorted(heroList.items()) if value.playerId == playerId][0]
        eventTime = int(e['_gameloop']/16)

        if eventTime - int(heroList[unitIndex].deathList.keys()[0]) > 12: # we need this to rule out the first event which is actually tracked
            heroDeathEvent = {'killerPlayerId': None , 'killerUnitIndex': None} # sadly, we don't know who killed it
            heroList[unitIndex].deathList[eventTime] = heroDeathEvent # and this is actually the respawn time, not death time
            heroList[unitIndex].deathCount += 1

def getUnitsInGame(e, unitsInGame):

    """
    Stores all non-hero units
    """
    if e['_event'] == 'NNet.Replay.Tracker.SUnitBornEvent' and not e['m_unitTypeName'].startswith('Hero'):
        unitIndex = (e['m_unitTagIndex'] << 18) + e['m_unitTagRecycle']
        unit = GameUnit()
        unit.unitIndex = unitIndex
        unit.bornAt = int(e['_gameloop']/16)
        unit.bornAtGameLoops = e['_gameloop']
        unit.internalName = e['m_unitTypeName']
        unit.team = e['m_upkeepPlayerId'] - 10
        unitsInGame[unitIndex] = unit

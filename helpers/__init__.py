
from models import *
import datetime



#def getArmyStr()

def win_timestamp_to_date(timestamp=None, date_format='%Y-%m-%d %H:%M:%S'):
    if timestamp:
        return datetime.datetime.fromtimestamp(int((timestamp/10000000) - 11644473600)).strftime(date_format)
    else:
        return None


def getHeroes(e, players):
    """
    Parse the event and looks if the unit created is a hero or not
    if so, adds a new hero to the heroList
    """

    # if a new hero unit is born
    if e['_event'] == 'NNet.Replay.Tracker.SUnitBornEvent' and e['m_unitTypeName'].startswith('Hero'):
        playerId = e['m_upkeepPlayerId'] - 1

        hero = HeroUnit()
        hero.playerId = playerId
        hero.name = players[playerId].name
        hero.team = players[playerId].team
        hero.internalName = e['m_unitTypeName'][4:]
        hero.unitTagIndex = e['m_unitTagIndex']
        hero.unitTagRecycle = e['m_unitTagRecycle']
        hero.unitTag = hero.unit_tag()

        return hero


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
            unitsInGame[deadUnitIndex].killerPlayerId = e['m_killerPlayerId']

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

        if len(heroList[unitIndex].deathList.keys()) > 0:
            if eventTime - int(heroList[unitIndex].deathList.keys()[0]) > 12: # we need this to rule out the first event which is actually tracked
                heroDeathEvent = {'killerPlayerId': None , 'killerUnitIndex': None} # sadly, we don't know who killed it
                heroList[unitIndex].deathList[eventTime] = heroDeathEvent # and this is actually the respawn time, not death time
                heroList[unitIndex].deathCount += 1

def getUnitsInGame(e):

    """
    Stores all non-hero units
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

        return unit


def getTalentSelected(proto, content):
    total = 0
    talentSelectEvents = proto.decode_replay_game_events(content)
    for tse in talentSelectEvents:
        if tse['_event'] == 'NNet.Game.SHeroTalentTreeSelectedEvent':
            print tse
            total += 1

    print total


__author__ = 'Rodrigo Duenas, Cristian Orellana'
import datetime


def win_timestamp_to_date(ts=None, date_format='%Y-%m-%d %H:%M:%S'):
    if ts:
        return datetime.datetime.fromtimestamp(int((ts/10000000) - 11644473600)).strftime(date_format)
    else:
        return None

def get_seconds_from_gameloop(e):
    return int((e['_gameloop'] % 2**32)/16)

def get_gameloops(e):
    return (e['_gameloop'] % 2**32)

def get_unit_tag(e):
    return (e['m_unitTagIndex'] << 18) + e['m_unitTagRecycle']

def get_ability_tag(e):
    return e['m_abil']['m_abilLink'] << 5 | e['m_abil']['m_abilCmdIndex']



def get_unit_owners(e, unitsInGame):
    """
    Get the owner of the unit and the time the unit was owned.
    """
    if e['_event'] == 'NNet.Replay.Tracker.SUnitOwnerChangeEvent' and e['m_upkeepPlayerId'] in (11, 12):
        unitTag = get_unit_tag(e)
        owner = e['m_upkeepPlayerId'] - 11
        ownerTuple = (owner, get_seconds_from_gameloop(e))
        unitsInGame[unitTag].ownerList.append(ownerTuple)

def get_unit_clicked(e, unitsInGame):
    """
    Gets information when a unit has been clicked by another one. i.e: When clicking tribute or returning souls
    """

    if e['_event'] == 'NNet.Game.SCmdUpdateTargetUnitEvent':
        unitTag = e['m_target']['m_tag']
        if unitTag in unitsInGame.keys():
            if unitsInGame[unitTag].is_tribute():
                playerId = e['_userid']['m_userId']
                clickTuple = (playerId, get_seconds_from_gameloop(e))
                unitsInGame[unitTag].clickerList.append(clickTuple)


def get_hero_deaths_from_game_event(e, heroList):
    """
    This function works by reading the specific Game Event information
    Parse the event and looks if a there is a NNet.Game.SCameraUpdateEvent with no m_target (None)
    this only happens when the camera is pointing to the spawn area. It uses the m_userId instead of
    the unitIndex
    """

    if e['_event'] == 'NNet.Game.SCameraUpdateEvent' and not e['m_target'] and e['_gameloop'] > 10:
        # find the hero
        playerId =  find_hero_key_from_user_id(heroList, (e['_userid']['m_userId']))
        unitTag = [key for (key, value) in sorted(heroList.items()) if value.playerId == playerId][0]
        eventTime = get_seconds_from_gameloop(e)

        if len(heroList[unitTag].deathList.keys()) > 0:
            if eventTime - int(heroList[unitTag].deathList.keys()[0]) > 12: # we need this to rule out the first event which is actually tracked
                heroDeathEvent = {'killerPlayerId': None , 'killerUnitIndex': None} # sadly, we don't know who killed it
                heroList[unitTag].deathList[eventTime] = heroDeathEvent # and this is actually the respawn time, not death time
                heroList[unitTag].deathCount += 1


def get_unit_destruction(e, unitsInGame):
    """
    Gets information when a non-hero unit is destroyed
    """
    if e['_event'] == 'NNet.Replay.Tracker.SUnitDiedEvent':
        deadUnitTag = get_unit_tag(e)
        try:
            unitsInGame[deadUnitTag].diedAt = get_seconds_from_gameloop(e)
            unitsInGame[deadUnitTag].diedAtGameLoops =get_gameloops(e)
            unitsInGame[deadUnitTag].gameLoopsAlive = unitsInGame[deadUnitTag].diedAtGameLoops - unitsInGame[deadUnitTag].bornAtGameLoops
            unitsInGame[deadUnitTag].killerPlayerId = e['m_killerPlayerId']

        except:
           pass

def find_hero_key_from_tag(heroList=None, tag=None):
    if len(heroList) == 0 or not heroList:
        return None
    else:
        for k, v in heroList.iteritems():
            if v.unitTag == tag:
                return k
    return None

def find_hero_key_from_user_id(heroList=None, userId=None):
    if len(heroList) == 0 or not heroList:
        return None
    else:
        for k, v in heroList.iteritems():
            if v.userId == userId:
                return k
    return None

def find_player_key_from_user_id(playerList=None, userId=None):
    if len(playerList) == 0 or not playerList:
        return None
    else:
        for k, v in playerList.iteritems():
            if v.userId == userId:
                return k
    return None



def get_hero_death_from_tracker_events(e, heroList):
    """
    This function works by reading the specific Replay Tracker Event information
    Parse the event and looks if a hero unit was destroyed, if so, adds a new entry to the deathList
    """
    deadUnitTag = get_unit_tag(e)
    playerId = find_hero_key_from_tag(heroList, deadUnitTag)

    if e['_event'] == 'NNet.Replay.Tracker.SUnitDiedEvent' and playerId is not None:
        seconds = get_seconds_from_gameloop(e)

        if e['m_killerUnitTagIndex']:
            killerUnitTag = get_unit_tag(e)
            heroDeathEvent = {'killerPlayerId': e['m_killerPlayerId'], 'killerUnitIndex': killerUnitTag}
            heroList[playerId].deathList[seconds] = heroDeathEvent
            heroList[playerId].deathCount += 1
        else:
            # There is a bug that cause m_killerUnitTagIndex and m_killerUnitTagRecycle to be null
            heroDeathEvent = {'killerPlayerId': e['m_killerPlayerId'], 'killerUnitIndex': None}
            heroList[playerId].deathList[seconds] = heroDeathEvent
            heroList[playerId].deathCount += 1


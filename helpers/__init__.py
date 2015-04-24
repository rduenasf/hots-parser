
from models import *
import json
from utils import *

def getGemPicked(unitList):
    """
    Gets soul gems that were never picked up
    This function should run after the events are parsed and the unitList creation/destruction info is populated
    """

    gemUnitIndexes = [key for (key, value) in sorted(unitList.items()) if value.internalName in GameUnit._PICKUNITS.keys()]
    for gemIndex in gemUnitIndexes:
        if unitList[gemIndex].gameLoopsAlive in xrange(0, GameUnit._PICKUNITS[unitList[gemIndex].internalName] - 1):
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

        if len(heroList[unitIndex].deathList.keys()) > 0:
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


def decode_replay(replayFile, eventToDecode=None):
    """
    Gets the content of a particular event
    """
    if eventToDecode not in EVENTS.keys():
        print "Error - Unknown event %s" % eventToDecode
        return -1

    return replayFile.read_file(eventToDecode)


def processEvents(proto=None, replayFile=None):
    """"
    This is the main loop, reads a replayFile and applies available decoders (trackerEvents, gameEvents, msgEvents, etc)
    Receives the protocol and the replayFile as an mpyq file object
    """
    if not proto or not replayFile:
        print "Error - Protocol and replayFire are needed"
        return -1

    # Pre parse preparation go here
    eh = eventHandler()


    # Parse

    for meta in EVENTS.keys():
        content = decode_replay(replayFile, meta)
        events = getattr(proto,EVENTS[meta])(content)
        for event in events:
            if event['_event'] in eh.IMPLEMENTED:
                getattr(eh, event['_event'].replace('.','_'))(event)


    # After parse functions go here
    getGemPicked(event, eh.unitsInGame)



    gems = 0
    for index in eh.unitsInGame:
        if eh.unitsInGame[index].team < 0:
            print "%d %s (%d) - created: %d | died: %s | alive: %s | picked? (%s)" \
              % (index, eh.unitsInGame[index].internalName,
                 eh.unitsInGame[index].team,
                 eh.unitsInGame[index].bornAt,
                 eh.unitsInGame[index].diedAt,
                 eh.unitsInGame[index].gameLoopsAlive,
                 eh.unitsInGame[index].wasPicked
                )
        if eh.unitsInGame[index].internalName in PICKUNITS:
            print "%d %s (%d) - created: %d | died: %s | alive: %s | picked? (%s)" \
              % (index, eh.unitsInGame[index].internalName,
                 eh.unitsInGame[index].team,
                 eh.unitsInGame[index].bornAt,
                 eh.unitsInGame[index].diedAt,
                 eh.unitsInGame[index].gameLoopsAlive,
                 eh.unitsInGame[index].wasPicked
                )
        gems += 1
        if index == 15990785:
            print eh.unitsInGame[index].internalName
    print gems

    #for index in eh.heroList:
        #print "%s: %s" % (eh.heroList[index].internalName, eh.heroList[index].deathCount)
        #keys = eh.heroList[hero].deathList.keys()
        #print eh.unitsInGame[eh.heroList[hero].deathList[keys[0]]['killerUnitIndex']]



def getHeaders(proto, replayFile):
    return proto.decode_replay_header(replayFile.header['user_data_header']['content'])


def toJson(proto, content):
    eventList = []
    excludeList = ['NNet.Game.SBankFileEvent', 'NNet.Game.SBankKeyEvent', 'NNet.Game.SBankSectionEvent',
     'NNet.Game.SBankSignatureEvent', 'NNet.Game.SCameraUpdateEvent', 'NNet.Game.STriggerCutsceneBookmarkFiredEvent',
     'NNet.Game.STriggerCutsceneEndSceneFiredEvent',
     'NNet.Game.STriggerSkippedEvent',
     'NNet.Game.STriggerSoundLengthSyncEvent',
     'NNet.Game.STriggerSoundOffsetEvent',
     'NNet.Game.STriggerTransmissionCompleteEvent',
     'NNet.Game.STriggerTransmissionOffsetEvent',
     'NNet.Game.SUserFinishedLoadingSyncEvent',
     'NNet.Game.SUserFinishedLoadingSyncEvent', 'NNet.Game.SCommandManagerStateEvent', 'NNet.Game.SCmdUpdateTargetPointEvent']
    total = 0
    events = proto.decode_replay_game_events(content)
    for e in events:
        eventList.append(e)
        # total += 1
        # if e['_event'] in excludeList or e['_gameloop'] == 0:
        #     pass
        # else:
        #     eventList.append(e)

    print total
    print len(eventList)
    print json.dumps(eventList)



def lol(proto, content):
    trackerEvents = proto.decode_replay_tracker_events(content)
    for t in trackerEvents:
        if t['_event'] == 'NNet.Replay.Tracker.SPlayerStatsEvent':
            for metric in t['m_stats'].keys():
                if t['m_stats'][metric] != 0:
                    print "for %s %d" % (metric, t['m_stats'][metric])


def eventsPerType(proto, content):
    eventsData = {}
    events = proto.decode_replay_game_events(content)
    for e in events:
        stats = eventsData.get(e['_event'], 0)
        stats += 1
        eventsData[e['_event']] = stats

    print json.dumps(eventsData)


def getTalentSelected(proto, content):
    total = 0
    talentSelectEvents = proto.decode_replay_game_events(content)
    for tse in talentSelectEvents:
        if tse['_event'] == 'NNet.Game.SHeroTalentTreeSelectedEvent':
            print tse
            total += 1

    print total


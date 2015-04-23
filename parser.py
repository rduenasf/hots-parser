__author__ = 'Rodrigo Duenas, Cristian Orellana'

from s2protocol import protocol15405, protocol34835
from s2protocol.mpyq import mpyq
from utils import EVENTS
import json
import sys

class HeroReplay():
    def __init__(self):
        # General Data
        map = ''
        startTime = None # UTC
        duration = None # in seconds
        speed = None


class HeroUnit():

    def __init__(self):
        # General data
        self.name = ''
        self.internalName = ''
        self.isHuman = False
        self.playerId = None
        self.team = None
        self.unitIndex = [] # list of known unitIndex for the hero

        # Metrics
        self.deathCount = 0
        self.deathList = {} # At what point in game (in seconds) the hero died
        self.killCountNeutral = 0 # How many neutral npc units this hero killed?
        self.killCountBuildings = 0 # How many buildings this hero destroyed?
        self.killCountMinions = 0 # How many minions this hero killed?
        self.killCount = 0 # How many units this hero killed (normal minions + heroes + buildings + neutral npcs)
        self.killCountHeroes = 0 # How many heroes this hero killed?
        self.totalOutDamage = 0 # How much damage this hero did?
        self.totalOutHeal = 0 # How much heal this hero did?
        self.totalIncDamage = 0 # How much damage this hero received
        self.totalIncHeal = 0 # How much heal this hero received
        self.maxKillSpree = 0 # maximum number of heroes killed after (if ever) die

    def __str__(self):

        return "name: %s\n" \
              "internalName: %s\n" \
              "isHuman: %s\n" \
              "playerId: %s\n" \
              "team: %s\n" \
              "unitIndex: %s\n" % (self.name, self.internalName, self.isHuman, self.playerId, self.team, self.unitIndex)



class PlayerUnit():

    def __init__(self):
        # General data
        name = ''
        region = ''
        id = ''
        realm = ''

class GameUnit():
    def __init__(self):
        # General Data
        self.internalName = '' #Unit Name
        self.bornAt = None # Seconds into the game when it was created
        self.bornAtGameLoops = None
        self.diedAtGameLoops = None
        self.team = None # The team this unit belongs to
        self.diedAt = None # Seconds into the game when it was destroyed
        self.gameLoopsAlive = -1 # -1 means never died.
        self.unitIndex = None
        self.wasPicked = False # for collectables


class eventHandler():

    # list of implemented event handlers
    IMPLEMENTED = ('NNet.Replay.Tracker.SUnitBornEvent', 'NNet.Replay.Tracker.SUnitDiedEvent', 'NNet.Game.SCameraUpdateEvent')

    unitsInGame = {}
    heroActions = {} # this is a dictionary , the key is the hero indexId, the value is a list of tuples
                    # (secsInGame, action)
    heroList = {} # key = playerId - content = hero instance
    heroDeathsList = list()

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


    for index in eh.unitsInGame:
        if eh.unitsInGame[index].internalName == 'ItemSoulPickup':
            print "%d %s (%d) - created: %d | died: %s | alive: %s | picked? (%s)" \
                  % (index, eh.unitsInGame[index].internalName,
                     eh.unitsInGame[index].team,
                     eh.unitsInGame[index].bornAt,
                     eh.unitsInGame[index].diedAt,
                     eh.unitsInGame[index].gameLoopsAlive,
                     eh.unitsInGame[index].wasPicked
            )

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







 # 'NNet.Game.SCmdEvent'
 # 'NNet.Game.SCmdUpdateTargetPointEvent'
 # 'NNet.Game.SCmdUpdateTargetUnitEvent'
 # 'NNet.Game.SCommandManagerStateEvent'
 # 'NNet.Game.SGameUserLeaveEvent'
 # 'NNet.Game.SHeroTalentTreeSelectedEvent'
 # 'NNet.Game.SSelectionDeltaEvent'

 # 'NNet.Game.SUserOptionsEvent'
 # 'NNet.Game.SUnitClickEvent'
 # 'NNet.Game.STriggerDialogControlEvent'
 # 'NNet.Game.STriggerHotkeyPressedEvent'
 # 'NNet.Game.STriggerKeyPressedEvent'


# heroes = []
# players = []
# replayData = HeroReplay()
#
# p = protocol15405
p2 = protocol34835
replay = mpyq.MPQArchive(sys.argv[1])
processEvents(p2, replay)


# contents = replay.read_file('replay.game.events')
# contents2 = replay.read_file('replay.tracker.events')

#headers = getHeaders(p, replay)
#toJson(p2, contents)
#getTalentSelected(p2, contents)
#eventsPerType(p2, contents)
# units = getUnitsInGame(p2, contents2)
# for key in sorted(units.keys()):
#     print "%s: %s" % (key, units[key])
# Fill replay data
#replayData.duration = headers['m_elapsedGameLoops']/16
#print headers
#print replayData.duration
#lol(p2, contents2)


#
# for key, value in sorted(units.iteritems(), key=lambda (k,v): (v,k)):
#     print "%s: %s" % (key, value)
#





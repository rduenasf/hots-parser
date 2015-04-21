
from s2protocol import protocol15405, protocol34835
from s2protocol.mpyq import mpyq
import json

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
        name = ''
        isHuman = False
        playerUnit = None
        team = None

        # Metrics
        deathCount = 0
        killCountNeutral = 0 # How many neutral npc units this hero killed?
        killCountBuildings = 0 # How many buildings this hero destroyed?
        killCountMinions = 0 # How many minions this hero killed?
        killCount = 0 # How many units this hero killed (normal minions + heroes + buildings + neutral npcs)
        killCountHeroes = 0 # How many heroes this hero killed?
        totalOutDamage = 0 # How much damage this hero did?
        totalOutHeal = 0 # How much heal this hero did?
        totalIncDamage = 0 # How much damage this hero received
        totalIncHeal = 0 # How much heal this hero received
        maxKillSpree = 0 # maximum number of heroes killed after (if ever) die


    # for now no getters nor setters ... just direct access to the structure


class PlayerUnit():

    def __init__(self):
        # General data
        name = ''
        region = ''
        id = ''
        realm = ''

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
        total += 1
        if e['_event'] in excludeList or e['_gameloop'] == 0:
            pass
        else:
            eventList.append(e)

    print total
    print len(eventList)
    print json.dumps(eventList)

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


heroes = []
players = []
replayData = HeroReplay()

p = protocol15405
p2 = protocol34835
replay = mpyq.MPQArchive('NimaGae.StormReplay')
contents = replay.read_file('replay.game.events')

#headers = getHeaders(p, replay)
toJson(p2, contents)
#getTalentSelected(p2, contents)
#eventsPerType(p2, contents)
# Fill replay data
#replayData.duration = headers['m_elapsedGameLoops']/16
#print headers
#print replayData.duration











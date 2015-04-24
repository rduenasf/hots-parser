__author__ = 'Rodrigo Duenas, Cristian Orellana'

from s2protocol import protocol15405, protocol34835
from s2protocol.mpyq import mpyq
from utils import EVENTS
from events import *

import json
import sys

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
            eh.processEvent(event)


    # After parse functions go here
    getGemPicked(event, eh.unitsInGame)


    for index in eh.unitsInGame:
        if eh.unitsInGame[index].isMapResource():
            print eh.unitsInGame[index]

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





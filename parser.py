__author__ = 'Rodrigo Duenas, Cristian Orellana'
# from __future__ import print_function

from s2protocol import protocol34835
from s2protocol.mpyq import mpyq
from replay import *
import argparse
import json
import uuid

def processEvents(protocol=None, replayFile=None):
    """"
    This is the main loop, reads a replayFile and applies available decoders (trackerEvents, gameEvents, msgEvents, etc)
    Receives the protocol and the replayFile as an mpyq file object
    """
    if not protocol or not replayFile:
        print "Error - Protocol and replayFile are needed"
        return -1

    # Pre parse preparation go here
    eh = Replay(protocol, replayFile)

    replayUuid = uuid.uuid1()

    eh.process_replay_details()
    eh.process_replay_header()

    print "\n === Map Info ==="

    print eh.replayInfo

    print "\n === Players ==="

    for player in eh.get_players_in_game():
      print player

    eh.process_replay()


    print "\n ==== Heroes ===="
    print "%15s\t%15s\t%15s\t%15s\t%15s\t%15s" % ("Name", "InternalName", "IsHuman", "PlayerId", "Team", "UnitTag")

    for hero in eh.heroes_in_game():
      print hero

    print "\n ==== Summary ===="

    eh.calculate_game_strength()


    f = open('replay-results/' + str(replayUuid) + '.armystr.json', 'w')

    f.write(json.dumps([
    {
      "key": "Team 1",
      "values": eh.army_strength[0]
    },
    {
      "key": "Team 2",
      "values": eh.army_strength[1]
    }
    ]))

    f.close()

    print "UUID: " + str(replayUuid)

    #print json.dumps(mercStr)

    # for i in xrange(0, eh.replayInfo.durations_in_secs()):
    #     print "{y:'%d', a:%d, b:%d}," % (i,armyStr[i][0], armyStr[i][1])


################################################## DUMP DATA ##############
    # print '['
    # for i in xrange(0, eh.replayInfo.durations_in_secs()):
    #     print "[%d, %d]," % (i, armyStr[i][0])
    # print "]"
    #
    # print '['
    # for i in xrange(0, eh.replayInfo.durations_in_secs()):
    #     print "[%d, %d]," % (i, armyStr[i][1]*-1)
    # print "]"


    # for unit in


    #for index in eh.heroList:
        #print "%s: %s" % (eh.heroList[index].internalName, eh.heroList[index].deathCount)
        #keys = eh.heroList[hero].deathList.keys()
        #print eh.unitsInGame[eh.heroList[hero].deathList[keys[0]]['killerUnitIndex']]



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('replay_file', help='.StormReplay file to load')
    args = parser.parse_args()

    replay = mpyq.MPQArchive(args.replay_file)
    processEvents(protocol34835, replay)

__author__ = 'Rodrigo Duenas, Cristian Orellana'

from s2protocol import protocol34835
from s2protocol.mpyq import mpyq
from replay import *
import argparse
import json

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

    eh.process_replay_details()
    eh.process_replay_header()

    print "\n === Map Info ==="

    print eh.replayInfo

    print "\n === Players ==="

    for player in eh.get_players_in_game():
      print player

    eh.process_replay()

    pickedGemsPerTeam = [0, 0]
    armyStr = {} # key = team, value = dict with key = second and value = armystr
    mercStr = {}

    for second in xrange(0, eh.replayInfo.durations_in_secs()):
        armyStr[second] = [0,0]
        mercStr[second] = [0,0]



    print "\n ==== Units ===="

    second = 0
    duration = eh.replayInfo.durations_in_secs()



# Get Army Str and Mercenary Str
    for unit in eh.units_in_game():

        end = unit.diedAt if unit.diedAt > 0 else eh.replayInfo.durations_in_secs()
        if unit.team in [0,1]:
            for second in xrange(unit.bornAt, end):
                armyStr[second][unit.team] += unit.get_strength()

                if unit.is_mercenary():
                    mercStr[second][unit.team] += unit.get_strength()


        if len(unit.ownerList) > 0:
            print unit




    # for second in xrange(0, eh.replayInfo.durations_in_secs()):
    #     unitsAlive = [unit for unit in eh.unitsInGame if (second >= eh.unitsInGame[unit].bornAt and second < eh.unitsInGame[unit].diedAt and eh.unitsInGame[unit].is_hired_mercenary())]
    #     print unitsAlive
    #
    #     armyStr[second] = []



      #if unit.is_map_resource():
        # print unit
      #  print unit.internalName
        #pickedGemsPerTeam[unit.team] += 1

    print "\n ==== Heroes ===="
    print "%15s\t%15s\t%15s\t%15s\t%15s\t%15s" % ("Name", "InternalName", "IsHuman", "PlayerId", "Team", "UnitTag")

    for hero in eh.heroes_in_game():
      print hero

    print "\n ==== Summary ===="

    print "Picked Gems:\t%s" % (pickedGemsPerTeam)

    # for i in xrange(0, eh.replayInfo.durations_in_secs()):
    #     print "%s\t%s" % (armyStr[i][0], armyStr[i][1]*-1)

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

__author__ = 'Rodrigo Duenas, Cristian Orellana'

from s2protocol import protocol34835
from s2protocol.mpyq import mpyq
from replay import *
import sys
import argparse

def processEvents(protocol=None, replayFile=None):
    """"
    This is the main loop, reads a replayFile and applies available decoders (trackerEvents, gameEvents, msgEvents, etc)
    Receives the protocol and the replayFile as an mpyq file object
    """
    if not protocol or not replayFile:
        print "Error - Protocol and replayFire are needed"
        return -1

    # Pre parse preparation go here
    eh = Replay(protocol, replayFile)

    eh.process_replay_details()

    print "\n === Players ==="

    for player in eh.get_players_in_game():
      print player

    eh.process_replay()

    pickedGemsPerTeam = [0, 0]

    print "\n ==== Units ===="

    caca = set()
    for unit in eh.units_in_game():
        if unit.team == 1 and unit.internalName.startswith('Merc'):
            caca.add(unit.internalName)
        #if unit.is_mercenary():

    print caca

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

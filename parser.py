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

    eh.process_replay()

    getGemPicked(eh.unitsInGame)

    for unit in eh.units_in_game():
      if unit.is_map_resource():
        print unit


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

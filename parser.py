__author__ = 'Rodrigo Duenas, Cristian Orellana'

from s2protocol import protocol34835
from s2protocol.mpyq import mpyq
from events import *

import json
import sys

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

    for unit in eh.units_in_game():
      if unit.is_map_resource():
        print unit


    #for index in eh.heroList:
        #print "%s: %s" % (eh.heroList[index].internalName, eh.heroList[index].deathCount)
        #keys = eh.heroList[hero].deathList.keys()
        #print eh.unitsInGame[eh.heroList[hero].deathList[keys[0]]['killerUnitIndex']]



if __name__ == "__main__":
  replay = mpyq.MPQArchive(sys.argv[1])
  processEvents(protocol34835, replay)

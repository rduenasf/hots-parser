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

    eh.process_replay()

    eh.process_replay_attributes()

    print "\n === Players ==="

    for player in eh.get_players_in_game():
      print player




    print "\n ==== Heroes ===="
    print "%15s\t%15s\t%15s\t%15s\t%15s\t%15s\t%15s" % ("Name", "InternalName", "IsHuman", "PlayerId", "Team", "UnitTag","Death Count")

    for hero in eh.heroes_in_game():
      print hero


    print "\n === Clicked Units ==="

    for unit in eh.get_clicked_units():
        print unit

    print "\n ==== Summary ===="


    eh.calculate_game_strength()

    f = open('replay-results/' + str(replayUuid) + '.armystr.json', 'w')

    f.write(json.dumps([
      { "key": "Team 1", "values": eh.army_strength[0] },
      { "key": "Team 2", "values": eh.army_strength[1] }
    ]))

    f.close()

    print "\nUUID: " + str(replayUuid)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('replay_file', help='.StormReplay file to load')
    args = parser.parse_args()

    replay = mpyq.MPQArchive(args.replay_file)
    processEvents(protocol34835, replay)

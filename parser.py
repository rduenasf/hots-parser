__author__ = 'Rodrigo Duenas, Cristian Orellana'


from s2protocol import protocol34835
from s2protocol.mpyq import mpyq
from replay import *
import argparse
import json
import uuid
import time
from utils.db import DB
from os import walk, path


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

    start_time = time.time()
    eh.process_replay()
    print("--- %s seconds ---" % (time.time() - start_time))
    eh.process_replay_attributes()


    print "\n === Map Info ==="

    print eh.replayInfo

    print "\n === Players ==="
    print "%10s\t%10s\t%10s\t%12s\t%10s\t%15s\t%15s" % ('Id', 'Team', 'Hero', 'Name', 'Level', 'Winner?', 'Handle')
    for player in eh.get_players_in_game():
        print player

    print "\n ==== Heroes ===="
    print "%15s\t%15s\t%15s\t%15s\t%15s\t%15s\t%15s\t%15s\t%15s" % ("Name", "InternalName", "IsHuman", "PlayerId", "UserId", "Team", "UnitTag","Death Count","Casted Abilities")

    for hero in eh.heroes_in_game():
        print hero
        # if hero.get_total_casted_abilities() > 0:
        #     print "\t\tCasted Abilities:"
        #     for gameLoop in hero.castedAbilities.keys():
        #         print "\t\t\t GL: %d, AbilId: %d" % (gameLoop, hero.castedAbilities[gameLoop].abilityTag)

    # for hero in eh.heroes_in_game():
    #     print "Hero: %s" % hero.name
    #     for gl in hero.pickedTalents.keys():
    #         print "\t%s" % hero.pickedTalents[gl]

    # print "\n === Clicked Units ==="
    #
    # for unit in eh.get_clicked_units():
    #     print unit

    print "\n ==== Summary ===="


    eh.calculate_game_strength()
    eh.setTeamsLevel()

    print "\n === Teams ==="
    print "%15s\t%15s\t%15s\t%15s" % ("Id", "Est. Level", "Winner?", "Loser?")
    print eh.team0
    print eh.team1

    #f = open('replay-results/' + str(replayUuid) + '.armystr.json', 'w')

    db = DB(host='rduenasf.synology.me', user='hots', passwd='nimanimero', db='hots' ) # TODO move to config
    cursor = db.conn.cursor()


    armyData = json.dumps([
      { "key": "Team 1", "values": eh.army_strength[0] },
      { "key": "Team 2", "values": eh.army_strength[1] }
    ])

    statement = "INSERT INTO army_str (uuid, armyData) VALUES ('%s', '%s')" % (replayUuid, armyData)
    #cursor.execute(statement)
    #db.conn.commit ()


    #f.close()

    print "\nUUID: " + str(replayUuid)



if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument('replay_file', help='.StormReplay file to load')
    # args = parser.parse_args()
    #replay = mpyq.MPQArchive(args.replay_file)
    for directory, dirnames, filenames in walk('/Users/cristiano/Others/log-crawler/download/'):
        for file in filenames:
            if file.endswith('StormReplay'):
                file_path = path.join(directory, file)
                replay = mpyq.MPQArchive(file_path)
                print file_path
                processEvents(protocol34835, replay)

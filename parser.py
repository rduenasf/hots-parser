__author__ = 'Rodrigo Duenas, Cristian Orellana'



from replay import *

def processEvents(protocol=None, replayFile=None, conf=None):
    """"
    This is the main loop, reads a replayFile and applies available decoders (trackerEvents, gameEvents, msgEvents, etc)
    Receives the protocol and the replayFile as an mpyq file object
    """
    if not protocol or not replayFile or not conf:
        print "Error - Protocol, configuration and replayFile are needed"
        return -1

    eh = Replay(protocol, replayFile)
    #replayUuid = uuid.uuid1()
    eh.process_replay_details()
    eh.process_replay_header()
    eh.process_replay_initdata()
    eh.process_replay()
    eh.process_replay_attributes()
    eh.calculate_game_strength()
    eh.setTeamsLevel()

    return eh

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

    print "\n ==== Summary ===="




    print "\n === Teams ==="
    print "%15s\t%15s\t%15s\t%15s" % ("Id", "Est. Level", "Winner?", "Loser?")
    print eh.team0
    print eh.team1


    print "\nUUID: " + str(replayUuid)




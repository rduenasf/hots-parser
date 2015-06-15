__author__ = 'Rodrigo Duenas, Cristian Orellana'

import argparse
import yaml
from s2protocol import protocol35360
from s2protocol.mpyq import mpyq
from os import walk, path
from parser import processEvents
from utils.db import DB



def save_to_db(replayData, path):
    if replayData:

        # print "Saving match info"
        # db.save_match_info(replayData, path)
        # print "Saving Teams"
        # db.save_teams(replayData)
        # print "Saving Heroes"
        # db.save_heroes(replayData)
        # print "Saving Players"
        # db.save_players(replayData)
        # print "Saving hero stats for the match"
        # db.save_hero_match_stats(replayData)
        # db.save_heroes(replayData)

        #for p in replayData.heroList:
            # for loop in replayData.heroList[p].castedAbilities:
            #     print replayData.heroList[p].castedAbilities[loop]
            #     if hasattr(replayData.heroList[p].castedAbilities[loop], 'targetUnitTag'):
            #         print "\t\t\t\tCasted On: %s" % (replayData.unitsInGame[replayData.heroList[p].castedAbilities[loop].targetUnitTag].internalName)
            # print "\n\n\n\n"
        print "=== MAP: %s ===" % replayData.replayInfo.internalMapName
        for hero in replayData.heroList:
            print "[%s] Hero: %s (%s) " % ("Human" if replayData.heroList[hero].isHuman else "AI", replayData.heroList[hero].name, replayData.heroList[hero].playerId)
            mapName = replayData.replayInfo.internalMapName
            if mapName.strip() == 'Cursed Hollow':
                print "\tcaptured tributes: %s" % replayData.heroList[hero].capturedTributes
                print "\tclicked tributes: %s" %  replayData.heroList[hero].clickedTributes
            elif mapName.strip() == 'Tomb of the Spider Queen':
                print "\tcaptured soul gems: %s" % replayData.heroList[hero].totalSoulsTaken
            elif mapName.strip() == "Garden of Terror":
                print "\tcaptured Plant Horrors: %s" % replayData.heroList[hero].totalPlantsControlled
            print "\tRegen Globes taken: %s" % replayData.heroList[hero].regenGlobesTaken


        if mapName.strip() == 'Tomb of the Spider Queen':
            print "Team 0 took %s gems and missed %s - Summoned %s spiders in %s waves" % (replayData.team0.pickedSoulGems, replayData.team0.wastedSoulGems, replayData.team0.summonedSpiderBosses, replayData.team0.summonedSpiderBosses/3)
            print "\t Spiders were alive a total of %s seconds, %s buildings and %s units were killed during this time" % (replayData.team0.spiderBossesTotalAliveTime, replayData.team0.totalBuildingsKilledDuringSpiders, replayData.team0.totalUnitsKilledDuringSpiders)
            print "\t\tNorth: %s buildings, %s units - South: %s, %s - Center: %s, %s" % (replayData.team0.totalBuildingsKilledDuringNorthSpider, replayData.team0.totalUnitsKilledDuringNorthSpider, replayData.team0.totalBuildingsKilledDuringSouthSpider, replayData.team0.totalUnitsKilledDuringSouthSpider, replayData.team0.totalBuildingsKilledDuringCenterSpider, replayData.team0.totalUnitsKilledDuringCenterSpider)
            max_lifespan = max(replayData.team0.spiderBossesCenterTotalAliveTime, replayData.team0.spiderBossesNorthTotalAliveTime, replayData.team0.spiderBossesSouthTotalAliveTime)
            position = "center" if replayData.team0.spiderBossesCenterTotalAliveTime == max_lifespan else "north" if replayData.team0.spiderBossesNorthTotalAliveTime == max_lifespan else "south"
            print "\t The spider that lived the longest was located at the %s" % (position)
            print "Team 1 took %s gems and missed %s - Summoned %s spiders in %s waves" % (replayData.team1.pickedSoulGems, replayData.team1.wastedSoulGems, replayData.team1.summonedSpiderBosses, replayData.team1.summonedSpiderBosses/3)
            print "\t Spiders were alive a total of %s seconds, %s buildings and %s units were killed during this time" % (replayData.team1.spiderBossesTotalAliveTime, replayData.team1.totalBuildingsKilledDuringSpiders, replayData.team1.totalUnitsKilledDuringSpiders)
            print "\t\tNorth: %s buildings, %s units - South: %s, %s - Center: %s, %s" % (replayData.team1.totalBuildingsKilledDuringNorthSpider, replayData.team1.totalUnitsKilledDuringNorthSpider, replayData.team1.totalBuildingsKilledDuringSouthSpider, replayData.team1.totalUnitsKilledDuringSouthSpider, replayData.team1.totalBuildingsKilledDuringCenterSpider, replayData.team1.totalUnitsKilledDuringCenterSpider)
            max_lifespan = max(replayData.team0.spiderBossesCenterTotalAliveTime, replayData.team0.spiderBossesNorthTotalAliveTime, replayData.team0.spiderBossesSouthTotalAliveTime)
            position = "center" if replayData.team0.spiderBossesCenterTotalAliveTime == max_lifespan else "north" if replayData.team0.spiderBossesNorthTotalAliveTime == max_lifespan else "south"
            print "\t The spider that lived the longest was located at the %s" % (position)

        print "Team 0 missed %s regen globes" % (replayData.team0.missedRegenGlobes)
        print "Team 1 missed %s regen globes" % (replayData.team1.missedRegenGlobes)

        if mapName.strip() == 'Sky Temple':
            if (replayData.team0.luxoriaTemplesCapturedSeconds+float(replayData.team1.luxoriaTemplesCapturedSeconds)) > 0:
                t0percent = 100 * round(replayData.team0.luxoriaTemplesCapturedSeconds/(replayData.team0.luxoriaTemplesCapturedSeconds+float(replayData.team1.luxoriaTemplesCapturedSeconds)),2)
            else:
                t0percent = 0
            if (replayData.team1.luxoriaTemplesCapturedSeconds+float(replayData.team1.luxoriaTemplesCapturedSeconds)) > 0:
                t1percent = 100 * round(replayData.team1.luxoriaTemplesCapturedSeconds/(replayData.team0.luxoriaTemplesCapturedSeconds+float(replayData.team1.luxoriaTemplesCapturedSeconds)),2)
            else:
                t1percent = 0

            if (replayData.team0.luxoriaTempleNorthCapturedSeconds+float(replayData.team1.luxoriaTempleNorthCapturedSeconds)) > 0:
                t0NorthPercent = 100 * round(replayData.team0.luxoriaTempleNorthCapturedSeconds/(replayData.team0.luxoriaTempleNorthCapturedSeconds+float(replayData.team1.luxoriaTempleNorthCapturedSeconds)),2)
            else:
                t0NorthPercent = 0

            if (replayData.team0.luxoriaTempleCenterCapturedSeconds+float(replayData.team1.luxoriaTempleCenterCapturedSeconds)) > 0:
                t0SouthPercent = 100 * round(replayData.team0.luxoriaTempleCenterCapturedSeconds/(replayData.team0.luxoriaTempleCenterCapturedSeconds+float(replayData.team1.luxoriaTempleCenterCapturedSeconds)),2)
            else:
                t0SouthPercent = 0

            if (replayData.team0.luxoriaTempleSouthCapturedSeconds+float(replayData.team1.luxoriaTempleSouthCapturedSeconds)) > 0:
                t0CenterPercent = 100 * round(replayData.team0.luxoriaTempleSouthCapturedSeconds/(replayData.team0.luxoriaTempleSouthCapturedSeconds+float(replayData.team1.luxoriaTempleSouthCapturedSeconds)),2)
            else:
                t0CenterPercent = 0
            
            if (replayData.team1.luxoriaTempleNorthCapturedSeconds+float(replayData.team1.luxoriaTempleNorthCapturedSeconds)) > 0:
                t1NorthPercent = 100 * round(replayData.team1.luxoriaTempleNorthCapturedSeconds/(replayData.team0.luxoriaTempleNorthCapturedSeconds+float(replayData.team1.luxoriaTempleNorthCapturedSeconds)),2)
            else:
                t1NorthPercent = 0

            if (replayData.team1.luxoriaTempleCenterCapturedSeconds+float(replayData.team1.luxoriaTempleCenterCapturedSeconds)) > 0:
                t1SouthPercent = 100 * round(replayData.team1.luxoriaTempleCenterCapturedSeconds/(replayData.team0.luxoriaTempleCenterCapturedSeconds+float(replayData.team1.luxoriaTempleCenterCapturedSeconds)),2)
            else:
                t1SouthPercent = 0

            if (replayData.team1.luxoriaTempleSouthCapturedSeconds+float(replayData.team1.luxoriaTempleSouthCapturedSeconds)) > 0:
                t1CenterPercent = 100 * round(replayData.team1.luxoriaTempleSouthCapturedSeconds/(replayData.team0.luxoriaTempleSouthCapturedSeconds+float(replayData.team1.luxoriaTempleSouthCapturedSeconds)),2)
            else:
                t1CenterPercent = 0

            print "Team 0 controlled temples %s percent of the time (%s seconds)" % (t0percent, replayData.team0.luxoriaTemplesCapturedSeconds)
            print "\t North Tower: %s percent (%s seconds)" % (t0NorthPercent, replayData.team0.luxoriaTempleNorthCapturedSeconds)
            print "\t Center Tower: %s percent (%s seconds)" % (t0CenterPercent, replayData.team0.luxoriaTempleSouthCapturedSeconds)
            print "\t South Tower: %s percent (%s seconds)" % (t0SouthPercent, replayData.team0.luxoriaTempleCenterCapturedSeconds)
            print "Team 1 controlled temples %s percent of the time (%s seconds)" % (t1percent, replayData.team1.luxoriaTemplesCapturedSeconds)
            print "\t North Tower: %s percent (%s seconds)" % (t1NorthPercent, replayData.team1.luxoriaTempleNorthCapturedSeconds)
            print "\t Center Tower: %s percent (%s seconds)" % (t1CenterPercent, replayData.team1.luxoriaTempleSouthCapturedSeconds)
            print "\t South Tower: %s percent (%s seconds)" % (t1SouthPercent, replayData.team1.luxoriaTempleCenterCapturedSeconds)

        if mapName.strip() == 'Garden of Terror':
            t0 = replayData.team0
            t1 = replayData.team1

            print "Team 0 spawned %s plants that were alive a total of %s seconds" % (len(t0.totalPlantsSummoned), sum(t0.totalPlantsDuration.values()))
            if t0.totalPlantsSummoned > 0:
                for plant in xrange(1, len(replayData.team0.totalPlantsSummoned) + 1):
                    print "\t Plant %s, summoned at %s, alive for %s had an effectiveness of %s (%s units killed and %s buildings destroyed) " % (plant, t0.totalPlantsSummoned[plant], t0.totalPlantsDuration[plant],  t0.plantEffectiveness[plant], t0.totalUnitsKilledDuringPlant[plant], t0.totalBuildingsKilledDuringPlant[plant])
            if t1.totalPlantsSummoned > 0:
                print "Team 1 spawned %s plants that were alive a total of %s seconds" % (len(t1.totalPlantsSummoned), sum(t1.totalPlantsDuration.values()))
                for plant in xrange(1, len(replayData.team1.totalPlantsSummoned) + 1):
                    print "\t Plant %s, summoned at %s, alive for %s had an effectiveness of %s (%s units killed and %s buildings destroyed) " % (plant, t1.totalPlantsSummoned[plant], t1.totalPlantsDuration[plant], t1.plantEffectiveness[plant], t1.totalUnitsKilledDuringPlant[plant], t1.totalBuildingsKilledDuringPlant[plant])

        if mapName.strip() == 'Dragon Shire':
            t0 = replayData.team0
            t1 = replayData.team1

            print "Team 0 spawned %s dragons that were alive a total of %s seconds" % (len(t0.totaldragonsSummoned), sum(t0.totaldragonsDuration.values()))
            if len(t0.totaldragonsSummoned) > 0:
                for dragon in xrange(1, len(t0.totaldragonsSummoned) + 1):
                    print "\t Dragon %s, summoned at %s, alive for %s had an effectiveness of %s (%s units killed and %s buildings destroyed) " % (dragon, t0.totaldragonsSummoned[dragon], t0.totaldragonsDuration[dragon],  t0.dragonEffectiveness[dragon], t0.totalUnitsKilledDuringdragon[dragon], t0.totalBuildingsKilledDuringdragon[dragon])

            if len(t1.totaldragonsSummoned) > 0:
                print "Team 1 spawned %s dragons that were alive a total of %s seconds" % (len(t1.totaldragonsSummoned), sum(t1.totaldragonsDuration.values()))
                for dragon in xrange(1, len(t1.totaldragonsSummoned) + 1):
                    print "\t Dragon %s, summoned at %s, alive for %s had an effectiveness of %s (%s units killed and %s buildings destroyed) " % (dragon, t1.totaldragonsSummoned[dragon], t1.totaldragonsDuration[plant], t1.dragonEffectiveness[plant], t1.totalUnitsKilledDuringdragon[plant], t1.totalBuildingsKilledDuringdragon[plant])

            for dragon in t0.wastedDragonTime:
                print "\t In the dragon %s, Team 1 had the control of the statue during %s seconds after someone took control of it" % (dragon, t1.wastedDragonTime[dragon])
            for dragon in t0.wastedDragonTime:
                print "\t In the dragon %s, Team 0 had the control of the statue during %s seconds after someone took control of it" % (dragon, t0.wastedDragonTime[dragon])


        if mapName.strip() == 'Blackheart\'s Bay':
            t0 = replayData.team0
            t1 = replayData.team1
            print "ASDFFF %s" % len(t0.totalShipsControlled)
            print "T1 %s" % len(t1.totalShipsControlled)

            print "Team 0 controlled %s ships for a total of %s seconds" % (len(t0.totalShipsControlled), sum(t0.totalShipsControlled.values()))
            if len(t0.totalShipsControlled) > 0:
                for ship in t0.totalShipsControlled.keys():
                    print "\t During ship %s a total of %s unit died and %s buildings where destroyed, the effectiveness index is %s" % (ship, t0.totalUnitsKilledDuringShip[ship], t0.totalBuildingsDestroyedDuringShip[ship], t0.shipEffectiveness[ship])

            print "Team 1 controlled %s ships for a total of %s seconds" % (len(t1.totalShipsControlled), sum(t1.totalShipsControlled.values()))
            if len(t1.totalShipsControlled) > 0:
                for ship in t1.totalShipsControlled.keys():
                    print "\t During ship %s a total of %s unit died and %s buildings where destroyed, the effectiveness index is %s" % (ship, t1.totalUnitsKilledDuringShip[ship], t1.totalBuildingsDestroyedDuringShip[ship], t1.shipEffectiveness[ship])
                
        # for unit in replayData.unitsInGame:
        #     if replayData.unitsInGame[unit].is_seed_pickable():
        #         #print replayData.unitsInGame[unit].killerTeam
        #         print "%s ,%s, (%s)" % (replayData.unitsInGame[unit].unitTag, replayData.unitsInGame[unit].killerPlayerId, replayData.unitsInGame[unit].diedAtGameLoops)
        #     if replayData.unitsInGame[unit].is_hired_mercenary():
        #         print "Tag: %s (%s,%s), Position: %s" % (unit, replayData.unitsInGame[unit].unit_tag_index(), replayData.unitsInGame[unit].unit_tag_recycle(), replayData.unitsInGame[unit].positions)
# self.totalShipsControlled = {} # ship number: time that took to take the ship
# self.totalUnitsKilledDuringShip = {}
# self.totalBuildingsDestroyedDuringShip = {}
# self.shipEffectiveness = {}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('conf_file', help='Configuration file path')
    parser.add_argument('--replay_file', help='.StormReplay file to load')
    args = parser.parse_args()


    with file(args.conf_file) as f:
        conf = yaml.load(f)

    replayData = None
#db = DB(host=conf['db_host'], user=conf['db_user'], passwd=conf['db_pass'], db=conf['db'])

    if not args.replay_file:
        for directory, dirnames, filenames in walk('/Users/cristiano/Others/log-crawler/download/'):
            for file in filenames:
                if file.endswith('StormReplay'):
                    try:
                        file_path = path.join(directory, file)
                        print file_path
                        replay = mpyq.MPQArchive(file_path)
                        replayData = processEvents(protocol35360, replay, conf)
                        save_to_db(replayData, file_path)
                    except Exception, e:
                        print "Error while trying to process %s: %s" % (file_path, e)


    else:
            replay = mpyq.MPQArchive(args.replay_file)
            replayData = processEvents(protocol35360, replay, conf)
            save_to_db(replayData, args.replay_file)
        # try:
        #     replay = mpyq.MPQArchive(args.replay_file)
        #     replayData = processEvents(protocol35360, replay, conf)
        #     save_to_db(replayData, args.replay_file)
        # except Exception, e:
        #     print "Error while trying to process %s: %s" % (args.replay_file, e)

__author__ = 'Rodrigo Duenas, Cristian Orellana'

import argparse
import yaml
from s2protocol import protocol34835
from s2protocol.mpyq import mpyq
from os import walk, path
from parser import processEvents
from utils.db import DB



def save_to_db(replayData, path):
    if replayData:
        #db.save_match_detail(replayData)
        db.save_match_info(replayData, path)
        db.save_players(replayData)
        db.save_teams(replayData)
        db.save_hero_match_stats(replayData)
        #db.save_heroes(replayData)
        # db.save_army_strength(replayData)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('conf_file', help='Configuration file path')
    parser.add_argument('--replay_file', help='.StormReplay file to load')
    args = parser.parse_args()


    with file(args.conf_file) as f:
        conf = yaml.load(f)

    replayData = None
    db = DB(host=conf['db_host'], user=conf['db_user'], passwd=conf['db_pass'], db=conf['db'])

    if not args.replay_file:
        for directory, dirnames, filenames in walk('/Users/cristiano/Others/log-crawler/download/'):
            for file in filenames:
                if file.endswith('StormReplay'):
                    try:
                        file_path = path.join(directory, file)
                        print file_path
                        replay = mpyq.MPQArchive(file_path)
                        replayData = processEvents(protocol34835, replay, conf)
                        save_to_db(replayData, file_path)
                    except Exception, e:
                        print "Error while trying to process %s: %s" % (file_path, e)


    else:
        try:
            replay = mpyq.MPQArchive(args.replay_file)
            replayData = processEvents(protocol34835, replay, conf)
            save_to_db(replayData, args.replay_file)
        except Exception, e:
            print "Error while trying to process %s: %s" % (args.replay_file, e)

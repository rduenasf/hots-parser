__author__ = 'Rodrigo Duenas, Cristian Orellana'

import json
import MySQLdb

class DB():
    def __init__(self, user=None, passwd=None, host=None, db=None):
        if not user or not passwd or not host or not db:
            print "Error - You need to provide user, pass, db and host"
            exit(1)
        self.user = user
        self.passwd = passwd
        self.host = host
        self.db = db
        self.conn = self.connect()
        self.cursor = self.conn.cursor()
        self.conn.autocommit(True)

    def connect(self):
        if not self.user or not self.passwd or not self.host or not self.db:
            print "Error - You need to provide user, pass, db and host"
            exit(1)
        try:
            conn = MySQLdb.connect(self.host, self.user, self.passwd, self.db)
            return conn
        except Exception, e:
            print "Error while trying to establish the connection %s" % e
            exit(1)

    def check_match(self, id):
        verification = "SELECT replay_file FROM matches WHERE match_hash = '%s'" % id
        try:
            self.cursor.execute(verification)
            rows = self.cursor.fetchone()
            if rows is not None:
                return rows[0]
            else:
                return None
        except Exception, e:
            print "Error while trying to check match: %s" %e

    def check_player(self, account, uuid):
        verification = "SELECT COUNT(*) FROM player WHERE toon_handle = %s and match_hash = %s"
        try:
            self.cursor.execute(verification,(account, uuid))
            rows = self.cursor.fetchone()
            return rows[0] > 0
        except Exception, e:
            print "Error while trying to check player: %s" % e

    def check_team(self, members):
        verification = "SELECT COUNT(*) FROM team WHERE "
        pos = 1
        initial = 1
        for m in members:
            if initial:
                verification += "member_%s = '%s'" % (pos, m)
                initial = 0
            else:
                verification += " AND member_%s = '%s'" % (pos, m)
            pos +=1
        try:
            self.cursor.execute(verification)
            rows = self.cursor.fetchone()
            return rows[0] > 0
        except Exception, e:
            print "Error while trying to check team: %s" % e

    def insert_hero(self, name):
        insert = "INSERT INTO hero (hero_name) VALUES ('%s')" % name
        try:
            self.cursor.execute(insert)
            return self.get_hero_id_from_name(name)
        except Exception, e:
            print "Error while trying to insert hero %s: %s" % (name, e)


    def get_hero_id_from_name(self, name):
        query = "SELECT hero_id FROM hero WHERE hero_name = '%s' " % name.replace("'","")
        try:
            self.cursor.execute(query)
            row = self.cursor.fetchone()
        except Exception, e:
            print "Error while getting hero: %s" % e
        if not row:
            return self.insert_hero(name)
        else:
            return row[0]

    def check_hero_stats(self, account, match):
        verification = "SELECT COUNT(*) FROM hero_match_stats WHERE match_hash = %s AND toon_handle = %s"
        try:
            self.cursor.execute(verification, (match, account))
            rows = self.cursor.fetchone()
            return rows[0] > 0
        except Exception, e:
            print "Error while trying to check hero stats: %s" % e


    def save_match_info(self, r=None, path=None):
        if not r or not path:
            return None
        id = r.get_replay_id()
        file_path = self.check_match(id)


        if not file_path:


            insert_query = "INSERT INTO matches (match_hash, start_date, duration, speed, game_type, map_name, game_version, replay_file, army_strength)" \
                           "VALUES ('%s','%s', %s, %s, '%s', '%s', '%s', '%s' ,'%s')" \
                           % (
                            id,
                            r.replayInfo.startTime,
                            r.replayInfo.duration_in_secs(),
                            r.replayInfo.speed,
                            r.replayInfo.gameType,
                            r.replayInfo.map.replace("'",""),
                            r.replayInfo.gameVersion,
                            path,
                            json.dumps([{ "key": "Team 1", "values": r.army_strength[0] }, { "key": "Team 2", "values": r.army_strength[1] }])
                            )

            #print insert_query
            try:
                self.cursor.execute(insert_query)
            except Exception, e:
                print "Error while trying to insert match: %s" % e
        else:
            print "This replay already exists: %s" % file_path



    def save_players(self, r=None):
        if not r:
            return None

        id = r.get_replay_id()
        insert_players = list()
        insert_query = "INSERT INTO player (match_hash, toon_handle, player_id, user_id, team_id, hero_level, hero_id," \
                       "hero_talents, is_human, is_winner, is_loser, is_tied) VALUES %s"
        for player in r.players:
            account = r.players[player].toonHandle
            already_exists = self.check_player(account, id)
            if not already_exists:

                talents = "-".join([str(x) for x in r.heroList[r.players[player].id].pickedTalents.itervalues()])

                query = "('%s','%s',%s,%s,%s,%s,%s,'%s','%s','%s','%s','%s')" % \
                (
                    id,
                    account,
                    r.players[player].id,
                    r.players[player].userId,
                    r.players[player].team, # TODO use correct team id from the Team table
                    r.players[player].heroLevel,
                    1, # TODO use correct hero_id from the Hero table
                    talents,
                    0 if not r.players[player].isHuman else 1,
                    0 if not r.players[player].is_winner() else 1,
                    0 if not r.players[player].is_loser() else 1,
                    0 if not (not r.players[player].is_winner() and not r.players[player].is_loser()) else 1
                )
                insert_players.append(query)

        insert_query = insert_query % str(insert_players)
        insert_query = insert_query.replace('"','').replace('[','').replace(']','')
        if len(insert_players) > 0:
            try:
                self.cursor.execute(insert_query)
            except Exception, e:
                print "Error while trying to save player: %s" % e


    def save_teams(self, r=None):
        if not r:
            return None
        members = list()
        insert_query = "INSERT INTO team (team_level, total_rating, member_1, member_2, member_3, member_4, member_5) " \
               "VALUES %s"
        for player in r.team0.memberList:
            members.append(r.players[player].toonHandle)

        members = sorted(members)

        already_exists = self.check_team(members)
        if not already_exists:
            team_0 = "(0, 0, '%s','%s','%s','%s','%s')" % (members[0],members[1],members[2],members[3],members[4])
            insert_query = insert_query % (team_0)
            print
            try:
                self.cursor.execute(insert_query)
            except Exception, e:
                print "Error while trying to insert teams: %s" % e

        members = list()
        insert_query = "INSERT INTO team (team_level, total_rating, member_1, member_2, member_3, member_4, member_5) " \
               "VALUES %s"
        for player in r.team1.memberList:
            members.append(r.players[player].toonHandle)

        members = sorted(members)

        already_exists = self.check_team(members)
        if not already_exists:
            team_1 = "(0, 0, '%s','%s','%s','%s','%s')" % (members[0],members[1],members[2],members[3],members[4])
            insert_query = insert_query % (team_1)
            try:
                self.cursor.execute(insert_query)
            except Exception, e:
                print "Error while trying to insert teams: %s" % e



    def save_hero_match_stats(self, r=None):
        if not r:
            return None

        match_hash = r.get_replay_id()
        insert_hero = list()

        insert_query = "INSERT INTO hero_match_stats (match_hash, toon_handle, hero_id, deaths, kills, out_damage, out_heal," \
                       "in_damage, in_heal, captured_beacons, captured_tributes, captured_merc_camps, casted_abilities) VALUES %s"
        for hero in r.heroList:
            toon_handle = r.players[r.heroList[hero].playerId].toonHandle
            already_exists = self.check_hero_stats(toon_handle, match_hash)
            if not already_exists:
                hero_id = self.get_hero_id_from_name(r.heroList[hero].internalName)
                deaths = r.heroList[hero].deathCount
                kills = r.heroList[hero].killCount
                out_damage = r.heroList[hero].totalOutDamage
                out_heal = r.heroList[hero].totalOutHeal
                in_damage = r.heroList[hero].totalIncDamage
                in_heal = r.heroList[hero].totalIncHeal
                captured_beacons = r.heroList[hero].capturedBeaconTowers
                captured_tributes = r.heroList[hero].capturedTributes
                captured_merc_camps = r.heroList[hero].capturedMercCamps
                casted_abilities = len(r.heroList[hero].castedAbilities)
                query = "('%s', '%s', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)" % \
                (
                    match_hash,
                    toon_handle,
                    hero_id,
                    deaths,
                    kills,
                    out_damage,
                    out_heal,
                    in_damage,
                    in_heal,
                    captured_beacons,
                    captured_tributes,
                    captured_merc_camps,
                    casted_abilities
                )
                insert_hero.append(query)

        insert_query = insert_query % str(insert_hero)
        insert_query = insert_query.replace('"','').replace('[','').replace(']','')
        if len(insert_hero) > 0:
            try:
                self.cursor.execute(insert_query)
            except Exception, e:
                print "Error while trying to save hero match stats: %s" % e

__author__ = 'Rodrigo Duenas, Cristian Orellana'

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


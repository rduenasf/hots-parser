__author__ = 'cristiano'
from s2protocol import protocol15405
from s2protocol.mpyq import mpyq

class HeroReplay():
    def __init__(self):
        # General Data
        map = ''
        startTime = None # UTC
        duration = None # in seconds
        speed = None


class HeroUnit():

    def __init__(self):
        # General data
        name = ''
        isHuman = False
        playerUnit = None
        team = None

        # Metrics
        deathCount = 0
        killCountNeutral = 0 # How many neutral npc units this hero killed?
        killCountBuildings = 0 # How many buildings this hero destroyed?
        killCountMinions = 0 # How many minions this hero killed?
        killCount = 0 # How many units this hero killed (normal minions + heroes + buildings + neutral npcs)
        killCountHeroes = 0 # How many heroes this hero killed?
        totalOutDamage = 0 # How much damage this hero did?
        totalOutHeal = 0 # How much heal this hero did?
        totalIncDamage = 0 # How much damage this hero received
        totalIncHeal = 0 # How much heal this hero received
        maxKillSpree = 0 # maximum number of heroes killed after (if ever) die


    # for now no getters nor setters ... just direct access to the structure


class PlayerUnit():

    def __init__(self):
        # General data
        name = ''
        region = ''
        id = ''
        realm = ''

def getHeaders(proto, replayFile):
    return proto.decode_replay_header(replayFile.header['user_data_header']['content'])


heroes = []
players = []
replayData = HeroReplay()

p = protocol15405
replay = mpyq.MPQArchive('m.StormReplay')

headers = getHeaders(p, replay)

# Fill replay data
replayData.duration = headers['m_elapsedGameLoops']/16
print headers
print replayData.duration

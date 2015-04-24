__author__ = 'Rodrigo Duenas, Cristian Orellana'

class HeroUnit():

    def __init__(self):
        # General data
        self.name = ''
        self.internalName = ''
        self.isHuman = False
        self.playerId = None
        self.team = None
        self.unitIndex = [] # list of known unitIndex for the hero

        # Metrics
        self.deathCount = 0
        self.deathList = {} # At what point in game (in seconds) the hero died
        self.killCountNeutral = 0 # How many neutral npc units this hero killed?
        self.killCountBuildings = 0 # How many buildings this hero destroyed?
        self.killCountMinions = 0 # How many minions this hero killed?
        self.killCount = 0 # How many units this hero killed (normal minions + heroes + buildings + neutral npcs)
        self.killCountHeroes = 0 # How many heroes this hero killed?
        self.totalOutDamage = 0 # How much damage this hero did?
        self.totalOutHeal = 0 # How much heal this hero did?
        self.totalIncDamage = 0 # How much damage this hero received
        self.totalIncHeal = 0 # How much heal this hero received
        self.maxKillSpree = 0 # maximum number of heroes killed after (if ever) die

    def __str__(self):

        return "name: %s\n" \
              "internalName: %s\n" \
              "isHuman: %s\n" \
              "playerId: %s\n" \
              "team: %s\n" \
              "unitIndex: %s\n" % (self.name, self.internalName, self.isHuman, self.playerId, self.team, self.unitIndex)


class HeroReplay():
    def __init__(self):
        # General Data
        map = ''
        startTime = None # UTC
        duration = None # in seconds
        speed = None




class PlayerUnit():

    def __init__(self):
        # General data
        name = ''
        region = ''
        id = ''
        realm = ''

class GameUnit():

    def __init__(self):
        # General Data
        self.internalName = '' #Unit Name
        self.bornAt = None # Seconds into the game when it was created
        self.bornAtGameLoops = None
        self.diedAtGameLoops = None
        self.team = None # The team this unit belongs to
        self.diedAt = None # Seconds into the game when it was destroyed
        self.gameLoopsAlive = -1 # -1 means never died.
        self.unitIndex = None
        self.wasPicked = False # for collectables

    def isMapResource(self):
      return self.internalName == 'ItemSoulPickup'


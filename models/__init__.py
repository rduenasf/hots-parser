__author__ = 'Rodrigo Duenas, Cristian Orellana'

class Unit():
  def unit_tag(self):
    return (self.unitTagIndex << 18) + self.unitTagRecycle


  def unit_tag_index(self):
    return (self.unitTag >> 18) & 0x00003fff


  def unit_tag_recycle(self):
    return (self.unitTag) & 0x0003ffff

class HeroeUnit(Unit):

    def __init__(self):
        # General data
        self.name = ''
        self.internalName = ''
        self.isHuman = False
        self.playerId = None
        self.team = None
        self.unitTag = None
        self.unitTagRecycle = None
        self.unitTagIndex = None

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

        return "name: %s\t" \
              "internalName: %s\t" \
              "isHuman: %s\t" \
              "playerId: %s\t" \
              "team: %s\t" \
              "unitTag: %s\t" % (self.name, self.internalName, self.isHuman, self.playerId, self.team, self.unitTag)



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

class GameUnit(Unit):
    _PICKUNITS = {
            'ItemSeedPickup': 150,
            'ItemSoulPickup': 128,
            'ItemUnderworldPowerup': 150
    }


    def __init__(self):
        # General Data
        self.internalName = '' #Unit Name
        self.bornAt = None # Seconds into the game when it was created
        self.bornAtGameLoops = None
        self.diedAt = None # Seconds into the game when it was destroyed
        self.diedAtGameLoops = None
        self.team = None # The team this unit belongs to
        self.gameLoopsAlive = -1 # -1 means never died.
        self.unitTag = None
        self.unitTagRecycle = None
        self.unitTagIndex = None

    def is_map_resource(self):
      return self.internalName in GameUnit._PICKUNITS

    def was_picked(self):
      if hasattr(GameUnit._PICKUNITS, self.internalName):
        return self.gameLoopsAlive < GameUnit._PICKUNITS[self.internalName]
      else:
        return False


    def __str__(self):
      return "%s\t%s\t(%s)\tcreated: %d\tdied: %s\tlifespan: %s\tpicked? (%s)" \
                  % (self.unitTag, self.internalName, self.team, self.bornAt, self.diedAt, self.gameLoopsAlive, self.was_picked() )

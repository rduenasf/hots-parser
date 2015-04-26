__author__ = 'Rodrigo Duenas, Cristian Orellana'

class Unit():

    def __init__(self):
        self.bornAtX = -1
        self.bornAtY = -1

    def unit_tag(self):
        return (self.unitTagIndex << 18) + self.unitTagRecycle


    def unit_tag_index(self):
        return (self.unitTag >> 18) & 0x00003fff


    def unit_tag_recycle(self):
        return (self.unitTag) & 0x0003ffff

class HeroUnit(Unit):

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
        return "%15s\t%15s\t%15s\t%15s\t%15s\t%15s\t" % (self.name, self.internalName, self.isHuman, self.playerId, self.team, self.unitTag)



class HeroReplay():
    def __init__(self):
        # General Data
        self.map = ''
        self.startTime = None # UTC
        self.gameLoops = None # duration of the game in gameloops
        self.speed = None

    def durations_in_secs(self):
        if self.gameLoops:
            return self.gameLoops / 16
        else:
            return 0

    def __str__(self):
        return "Title: %s\nStarted at: %s\nDuration (s/gl): %d/%d\nSpeed: %s" % (self.map,
        self.startTime,
        self.durations_in_secs(),
        self.gameLoops,
        self.speed
      )



class Player():

    def __init__(self, id, team, name, hero):
        self.id = id
        self.team = team
        self.name = name
        self.hero = hero

    def __str__(self):
      return "%s\t%s\t%s\t%s" % (self.id,
        self.team,
        self.hero,
        self.name
      )

class GameUnit(Unit):

    _BEACONUNIT = ['TownMercCampCaptureBeacon', 'DragonballCaptureBeacon', 'WatchTowerCaptureBeacon']

    _PICKUNITS = {
            #'ItemSeedPickup': 150,
            'ItemSoulPickup': 128,
            'ItemSoulPickupFive': 128,
            'ItemSoulPickupTwenty': 128,
            'ItemUnderworldPowerup': 150,
            'RegenGlobe': 128
    }

    _MERCUNITSNPC = [
        # Garden Merc units
            'MercDefenderSiegeGiant', 'MercDefenderMeleeOgre', 'MercDefenderRangedOgre', 'JungleGraveGolemDefender']

    _MERCUNITSTEAM = {
        'MercLanerMeleeOgre': 1,
        'MercLanerSiegeGiant': 2.5,
        'MercLanerRangedOgre': 1,
        'JungleGraveGolemLaner': 10,
        # TODO move to own list as map event
        'SoulEaterMinion': 1.75,
        'SoulEater': 3
    }

    _ADVANCEDUNIT = {'CatapultMinion': 2}


    _NORMALUNIT = {'FootmanMinion': 0.25,
                   'WizardMinion': 0.25,
                   'RangedMinion': 0.25
                }
    def __init__(self):
        # General Data
        self.internalName = '' #Unit Name
        self.bornAt = None # Seconds into the game when it was created
        self.bornAtGameLoops = None
        self.diedAt = -1 # Seconds into the game when it was destroyed (-1 means never died)
        self.diedAtGameLoops = None
        self.team = None # The team this unit belongs to
        self.gameLoopsAlive = -1 # -1 means never died.
        self.unitTag = None
        self.unitTagRecycle = None
        self.unitTagIndex = None
        self.killerTeam = None
        self.killerTag = None
        self.killerTagIndex = None
        self.killerTagRecycle = None
        self.killerPlayerId = None
        self.ownerList = [] # contains a tuple (a, b) where a = owner team and b = gameloop of ownership event


    def is_map_resource(self):
      return self.internalName in GameUnit._PICKUNITS

    def was_picked(self):
      if self.internalName in GameUnit._PICKUNITS:
        return self.gameLoopsAlive < GameUnit._PICKUNITS[self.internalName]
      else:
        return False

    def is_mercenary(self):
        return self.internalName in GameUnit._MERCUNITSNPC or self.internalName in GameUnit._MERCUNITSTEAM

    def is_hired_mercenary(self):
        return self.internalName in GameUnit._MERCUNITSTEAM

    def is_advanced_unit(self):
        return self.internalName in GameUnit._ADVANCEDUNIT

    def get_strength(self):
        if self.is_hired_mercenary():
            return GameUnit._MERCUNITSTEAM[self.internalName]
        elif self.internalName in GameUnit._ADVANCEDUNIT:
            return GameUnit._ADVANCEDUNIT[self.internalName]
        elif self.internalName in GameUnit._NORMALUNIT:
            return GameUnit._NORMALUNIT[self.internalName]
        else:
            return 0

    def __str__(self):
        val = "%s\t%s\t(%s)\tcreated: %d s (%d,%d) \tdied: %s s\tlifespan: %s gls\tpicked? (%s)\tkilledby: %s" \
                  % (self.unitTag, self.internalName, self.team, self.bornAt, self.bornAtX, self.bornAtY, self.diedAt, self.gameLoopsAlive, self.was_picked(), self.killerPlayerId)
        if len(self.ownerList) > 0:
            val += "\t%s" % self.ownerList
        return val

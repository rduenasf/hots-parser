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
        self.capturedTributes = 0 # Number of tributes captured by this hero in the Curse map
        self.capturedMercCamps = 0
        self.capturedBeaconTowers = 0
        self.castedAbilities = {} # key = gameloops when the ability was casted, value = ability instance


    def __str__(self):
        return "%15s\t%15s\t%15s\t%15s\t%15s\t%15s\t%15s\t%15s" % (self.name, self.internalName, self.isHuman, self.playerId, self.team, self.unitTag, self.deathCount, self.get_total_casted_abilities())

    def get_total_casted_abilities(self):
        return len(self.castedAbilities)


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
        return "Title: %s\nStarted at: %s\nDuration (min/gl): %d/%d\nSpeed: %s" % (self.map,
        self.startTime,
        self.durations_in_secs()/60,
        self.gameLoops,
        self.speed
      )



class Player():

    def __init__(self, id, team, name, hero, toonHandle):
        self.id = id
        self.team = team
        self.name = name
        self.hero = hero
        self.heroLevel = 1
        self.toonHandle = toonHandle

    def __str__(self):
      return "%10s\t%10s\t%10s\t%12s\t%10s\t%15s" % (self.id,
        self.team,
        self.hero,
        self.name,
        self.heroLevel,
        self.toonHandle
      )

class GameUnit(Unit):

    _TRIBUTEUNIT = ['RavenLordTribute']

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
        self.ownerList = [] # contains a list of tuples (a, b) where a = owner team and b = gameloop of ownership event
        self.clickerList = [] # contains a list of tuples (a, b) where a = clicker and b = GameLoop of the click event
        self.heroData = None



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

    def is_beacon(self):
        return self.internalName in GameUnit._BEACONUNIT

    def is_tribute(self):
        return self.internalName in GameUnit._TRIBUTEUNIT

    def get_tribute_controller(self):
        """
        Gets the team that controlled the tribute. None if the unit is not a tribute
        """
        if not self.is_tribute() or len(self.clickerList) == 0:
            return None
        return self.clickerList[len(self.clickerList) - 1][0]

    def is_advanced_unit(self):
        return self.internalName in GameUnit._ADVANCEDUNIT

    def get_death_time(self, total_time):
        return self.diedAt if self.diedAt > 0 else total_time

    def get_strength(self):
        if self.is_hired_mercenary():
            return GameUnit._MERCUNITSTEAM[self.internalName]
        elif self.is_advanced_unit():
            return GameUnit._ADVANCEDUNIT[self.internalName]
        elif self.internalName in GameUnit._NORMALUNIT:
            return GameUnit._NORMALUNIT[self.internalName]
        else:
            return 0

    def __str__(self):
        val = "%s\t%s\t(%s)\tcreated: %d s (%d,%d) \tdied: %s s\tlifespan: %s gls\tpicked? (%s)\tkilledby: %s" \
                  % (self.unitTag, self.internalName, self.team, self.bornAt, self.bornAtX, self.bornAtY, self.diedAt, self.gameLoopsAlive, self.was_picked(), self.killerPlayerId)
        if len(self.ownerList) > 0:
            val += "\tOwners: %s" % self.ownerList
        if len(self.clickerList) > 0:
            val += "\tTaken by: %s" % (self.get_tribute_controller())
        return val


class BaseAbility():
    """
    Base class for all abilities, has all the common attributes
    """

    def __init__(self):
        self.userId = None
        self.castedAt = None
        self.castedAtGameLoops = None
        self.abilityTag = None
        self.abilityName = None

    def __str__(self):
        return "%s" % self.abilityTag


class TargetPointAbility(BaseAbility):

    def __init__(self):
        self.x = None
        self.y = None
        self.z = None


class TargetUnitAbility(BaseAbility):

    def __init__(self):
        self.targetUnitTag = None
        self.targetPlayerId = None
        self.targetTeamId = None
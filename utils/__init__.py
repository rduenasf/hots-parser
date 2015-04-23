__author__ = 'Rodrigo Duenas, Cristian Orellana'

# Events dict
# The key is the event name and the value is the s2protocol's function used to decode it
EVENTS = {'replay.game.events': 'decode_replay_game_events',
          'replay.tracker.events': 'decode_replay_tracker_events'}

HEROACTIONS = [] # empty = ALL
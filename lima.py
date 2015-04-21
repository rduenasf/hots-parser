
from s2protocol import protocol15405, protocol34835
from s2protocol.mpyq import mpyq

archive = mpyq.MPQArchive("NimaGae.StormReplay")

contents = archive.read_file('replay.game.events')

events = []


for event in protocol34835.decode_replay_game_events(contents):
 if event['_event'] == 'NNet.Replay.Tracker.SUnitDiedEvent':
   print event
 else:
   events.append(event)



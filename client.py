from pydbus import SystemBus
from gi.repository import GLib
from datetime import datetime
import requests

URL = 'http://BACKEND_API'

bus = SystemBus()
signal = bus.get('org.asamk.Signal')

def messageReceivedHandler(timestamp, sender, group_id, body, attachments):
  if (not group_id):
    print("Ignoring private messages: " + sender)
    return

  group_name = signal.getGroupName(group_id)
  if (group_name != "GROUP_NAME"):
    print("Ignoring invalid group: " + group_name)
    return

  token = requests.get(URL + '/auth', headers={'X-Secret':'SECRET'}).json()['token']
  data = {
    'user': 'Robot',
    'date': str(datetime.fromtimestamp(timestamp / 1000)),
    'msg': body
  }
  print("Got a message - Forwarding.")
  print(requests.post(URL + '/api/post', headers={'X-Token':token}, json=data))

signal.MessageReceived.connect(messageReceivedHandler)
GLib.MainLoop().run()

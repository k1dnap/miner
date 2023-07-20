from tinydb import TinyDB, Query, where
from tinydb.table import Document
from flask import Flask, request, jsonify, abort, render_template
from datetime import date, datetime

import random
import string

master_api_key = 'qq'

app = Flask(__name__)

host_version = '0.2'

db = TinyDB('./db.json')

class TinyDBModel:
  def __init__(self, tinydb_json) -> None:
    if tinydb_json:
      self.doc_id = tinydb_json.doc_id
      for key in tinydb_json.keys():
        setattr(self, key, tinydb_json[key])

  def save(self):
    new_obj = self.toJson()
    self.db_table.upsert(Document(new_obj, self.doc_id))

  def toJson(self):
    jsonDict = vars(self)
    return jsonDict
  
  @classmethod
  def create(cls, name='No name'):
    database_object = cls()
    database_object.name = name
    database_object_doc_id = cls.db_table.insert(database_object.toJson())
    database_object.doc_id = database_object_doc_id
    database_object.save()
    return database_object
  
  @classmethod
  def delete(cls, doc_id):
    cls.db_table.remove(doc_ids=[doc_id])

farm = db.table('farm')
workers = db.table('workers')
wallets = db.table('wallets')
flight_sheets = db.table('flight_sheets')
class FlightSheet(TinyDBModel):
  db_table = flight_sheets
  def __init__(self, tinydb_json = None):
    self.name = ''
    self.miner_list = []
    super().__init__(tinydb_json)

mining_software = db.table('mining_software')
class MiningSoftware(TinyDBModel):
  db_table = workers
  def __init__(self, tinydb_json = None):
    self.additional_arguments = ''
    self.algo = ''
    self.delay_before_next_miner = 0
    self.miner_cycle_time = 0
    self.miner_software = ''
    self.pool = ''
    self.version = ''
    self.wallet = ''
    self.worker = ''
    super().__init__(tinydb_json)


settings = db.table('settings')
events = db.table('events')

class Gpu():
  manufacturer = 'AMD/NVIDIA'
  pass

class Wallet():
  pass
class OcSettings():
  pass
class Worker(TinyDBModel):
  db_table = workers
  def __init__(self, tinydb_json = None) -> None:
    self.worker_api_key = ''
    self.name = ''
    self.description = ''
    self.boot_time = 0
    self.last_update_time = 0
    self.flight_sheet = 'None'
    self.action_todo = ''
    self.version = 'unknown'
    self.platform = 'windows'
    self.oc_settings = {"AMD":{"--fan":[],"clock_freq":[],"clock_voltage":[]},"NVIDIA":{"--cclock":[], "--mclock" : [],"--fan":[],"--pl":[],"-lgc":[],"-lmc":[],"-pl":[]}}
    # self.oc_settings = [{"pci_bus:'0.00.01', "mclock": 300, "cclock": 200, "loclclock": 1150, "fan": 69, "power_limit": 70 }]
    self.gpus_info = []
    self.miner_cycle_time = 0
    super().__init__(tinydb_json)
  @classmethod
  def create(cls, name):
    database_object = super().create(name)
    created_unique = False
    while not created_unique:
      object_api_key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
      o_len = len(cls.db_table.search( where('worker_api_key') == object_api_key))
      if o_len == 0:
        database_object.worker_api_key = object_api_key
        break
    database_object.save()

@app.route("/")
def main_page():
  api_key = request.args.get("api_key", None)
  if api_key != master_api_key:
    return render_template('login_page.html')
  whole_db = {}
  for table in db.tables():
    whole_db[table] = db.table(table).all()
  # print(whole_db)
  return render_template('main.html', data=whole_db)

@app.route("/create_new_worker" ,methods = ['POST', 'GET'])
def create_new_worker():
  req_payload = request.json
  new_worker_name = req_payload['name']
  if not new_worker_name: return 'name couldnt be empty'
  new_worker_api_key = Worker.create(new_worker_name)
  return f"new_worker: {new_worker_api_key}"

@app.route("/delete_worker" ,methods = ['POST', 'GET'])
def delete_worker():
  req_payload = request.json
  api_key = req_payload['api_key']
  if not api_key: return 'api_key couldnt be empty'
  worker = workers.search( where('worker_api_key') == api_key)
  worker = Worker(worker[0])
  Worker.delete(worker.doc_id)
  return f"removed worker: {api_key}"

@app.route("/reboot_worker")
def reboot_worker():
  worker_api_key = request.args.get("worker_api_key")
  worker = workers.search( where('worker_api_key') == worker_api_key)
  worker = Worker(worker[0])
  api_key = request.args.get("api_key")
  if api_key == master_api_key:
    worker.action_todo = 'reboot'
    worker.save()
    return f"set action 'reboot' to worker {worker_api_key}"
  else:
    return f"set action 'rebootz' to worker {worker_api_key}"
@app.route("/ping")
def ping():
  req_payload = request.json
  worker_api_key = req_payload['worker_api_key']
  amd_gpus_info = req_payload['amd_gpus_info']
  # event = req_payload['last_error']
  current_time_str = datetime.utcnow().timestamp()
  worker = workers.search( where('worker_api_key') == worker_api_key)
  worker = Worker(worker[0])
  events.insert({'worker_api_key': worker_api_key, 'description': f'Worker {worker.name} was logged in with {req_payload}', 'time': current_time_str})
  # if event != 'None':
  #   events.insert({'worker_api_key': worker_api_key, 'description': f'Worker {worker.name} was restarted bcs of {event}', 'time': current_time_str})
  worker.boot_time = current_time_str
  worker.gpus_info = amd_gpus_info
  worker.action_todo = 'None'
  worker.save()
  data = {'status': 'ok'}
  return jsonify(data)


@app.route("/ping2")
def ping2():
  req_payload = request.json
  worker_api_key = req_payload['worker_api_key']
  all_gpus = req_payload['all_gpus']
  # event = req_payload['last_error']
  current_time_str = datetime.utcnow().timestamp()
  worker = workers.search( where('worker_api_key') == worker_api_key)
  worker = Worker(worker[0])
  events.insert({'worker_api_key': worker_api_key, 'description': f'Worker {worker.name} was logged in with {req_payload}', 'time': current_time_str})
  # if event != 'None':
  #   events.insert({'worker_api_key': worker_api_key, 'description': f'Worker {worker.name} was restarted bcs of {event}', 'time': current_time_str})
  worker.boot_time = current_time_str
  worker.gpus_info = all_gpus
  worker.action_todo = 'None'
  worker.save()
  data = {'status': 'ok'}
  return jsonify(data)




@app.route("/get_oc")
def getOc():
  req_payload = request.json
  worker_api_key = req_payload['worker_api_key']
  worker = workers.search( where('worker_api_key') == worker_api_key)
  worker = Worker(worker[0])
  worker_oc_settings = {'voltage': 900, 'freq': 1050}
  return jsonify(worker_oc_settings)

'''
3070ti core 0,2000, mem 0, 2000, pl 0,160
3080ti core 0,1900, mem 0,1900, pl 0,260
r9 fury 1150,900
{'AMD': [{'clock_voltage': 900, 'clock_freq': 1150, '--fan': 55}], 'NVIDIA': [{'-lmc': '0,5000', '-lgc': '0,1880', '-pl': '265', '--cclock': '225','--pl': 75, '--fan': 65},{'-lmc': '0,5000', '-lgc': '0,1900', '--cclock': '225','--pl': 75, '--fan': 65},{'-lmc': '0,5000', '-lgc': '0,1900', '--cclock': '225','--pl': 75, '--fan': 65}]}
{'AMD': [{'clock_voltage': 900, 'clock_freq': 1150, '--fan': 55}], 'NVIDIA': [{'-lmc': '0,5000', '-lgc': '0,2025', '-pl': '160', '--cclock': '250','--pl': 75, '--fan': 65}]}
{'AMD': [{'clock_voltage': 900, 'clock_freq': 1150, '--fan': 55}]}
'''

@app.route("/get_oc2")
def getOc2():
  req_payload = request.json
  worker_api_key = req_payload['worker_api_key']
  worker = workers.search( where('worker_api_key') == worker_api_key)
  worker = Worker(worker[0])
  worker_oc_settings = worker.oc_settings
  return jsonify(worker_oc_settings)

@app.route("/get_miner")
def getMiner():
  req_payload = request.json
  worker_api_key = req_payload['worker_api_key']
  worker = workers.search( where('worker_api_key') == worker_api_key)
  worker = Worker(worker[0])
  flight_sheet = flight_sheets.get(doc_id=worker.flight_sheet)
  flight_sheet['worker'] = worker.name

  return jsonify(flight_sheet)

@app.route("/get_miner2")
def getMiner2():
  req_payload = request.json
  worker_api_key = req_payload['worker_api_key']
  worker = workers.search( where('worker_api_key') == worker_api_key)
  worker = Worker(worker[0])
  flight_sheet = flight_sheets.get(doc_id=worker.flight_sheet)
  for miner in flight_sheet['miner_list']:
    if miner['worker'] == '%worker': miner['worker'] = worker.name
  return jsonify(flight_sheet)


@app.route("/send_updates")
def send_updates():
  req_payload = request.json
  worker_api_key = req_payload['worker_api_key']
  worker = workers.search( where('worker_api_key') == worker_api_key)
  worker = Worker(worker[0])
  current_time_str = datetime.utcnow().timestamp()

  # check if it's error
  try:
    event = req_payload["miner_error"]
    events.insert({'worker_api_key': worker_api_key, 'description': f'Worker {worker.name} occured an event: {event}', 'time': {current_time_str}})

  except:
    pass
  # worker update gpu status, temp, fans, hash, voltage, freq, hashrate
  gpu_stats = req_payload['gpu_stats']
  total_hash = 0
  for gpu_stat in gpu_stats:
    try:
      related_gpu = list(filter(lambda gpu: gpu_stat['bus_id'] == gpu['bus_id'] , worker.gpus_info))[0]
      index_of_related_gpu = worker.gpus_info.index(related_gpu)
      worker.gpus_info[index_of_related_gpu] = {**related_gpu, **gpu_stat}
    except: pass
    
    try:
      total_hash += float(gpu_stat['hashrate'].split('/')[0][:-2])
    except: pass
  worker.last_update_time = datetime.utcnow().timestamp()
  if worker.last_update_time - worker.boot_time > 60 * 3:
     if total_hash == 0:
      worker.action_todo = 'reboot'
      events.insert({'worker_api_key': worker_api_key, 'description': f'Worker {worker.worker_api_key} {worker.name} was rebooted automatically cos zero hashrate for 60*3 seconds', 'time': {current_time_str}})

  worker.save()
  # if some specific action is attached to worker, send it and clear

  return {'action': worker.action_todo}


@app.route("/send_updates2")
def send_updates2():
  req_payload = request.json
  worker_api_key = req_payload['worker_api_key']
  worker = workers.search( where('worker_api_key') == worker_api_key)
  worker = Worker(worker[0])
  current_time_str = datetime.utcnow().timestamp()

  # check if it's error
  try:
    event = req_payload["miner_error"]
    events.insert({'worker_api_key': worker_api_key, 'description': f'Worker {worker.name} occured an event: {event}', 'time': {current_time_str}})

  except:
    pass
  # worker update gpu status, temp, fans, hash, voltage, freq, hashrate
  summary = req_payload['summary']
  total_hash = 0
  for gpu_stat in summary:
    try:
      related_gpu = list(filter(lambda gpu: gpu_stat['bus_id'] == gpu['bus_id'] , worker.gpus_info))[0]
      index_of_related_gpu = worker.gpus_info.index(related_gpu)
      worker.gpus_info[index_of_related_gpu] = {**related_gpu, **gpu_stat}
    except: pass
    
    try:
      total_hash += float(gpu_stat['hashrate'])
    except: pass
  worker.last_update_time = datetime.utcnow().timestamp()
  # ???
  if False:
  # if worker.last_update_time - worker.boot_time > 60 * 3:
     if total_hash == 0:
      worker.action_todo = 'reboot'
      events.insert({'worker_api_key': worker_api_key, 'description': f'Worker {worker.worker_api_key} {worker.name} was rebooted automatically cos zero hashrate for 60*3 seconds', 'time': {current_time_str}})

  worker.save()
  # if some specific action is attached to worker, send it and clear

  return {'action': worker.action_todo}

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8000, debug=True)
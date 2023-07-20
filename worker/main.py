import subprocess
from sys import version
from time import sleep
import time
from config import host_url, worker_api_key
import requests
import traceback
from datetime import datetime
import socket
import json

teamredminer_directory = 'teamredminer'

worker_version = 0.2
def writeLastError(err):
  with open('.\\last_err.txt', 'w') as out:
    out.write(err)  

def readLastError():
  with open('.\\last_err.txt') as out:
    text = out.read()
    return text


def applyAMDTDRFix():
  subprocess.call(f'.\\tdr_fix.bat', shell=True)

def enableComputeAMD():
  subprocess.call(f'.\\{teamredminer_directory}\\enable_compute.bat', shell=True)



def parseTeamRedMinerLog(line):
  try:
    skip_phrases = [
      'CoreMHz',
      'Stats Uptime',
      'GPU Status',
      'Total'
    ]
    if len(line) < 60: return None
    for phrase in skip_phrases:
      if phrase in line:
        return None
    return_dict = {
      
    }
    line_type = 'gpu_info'
    if line.__contains__(' GPU '): line_type = 'gpu_stats'
    return_dict['line_type'] = line_type
    if line_type == 'gpu_info':
      parsed_line = line.replace('   ', ' ').replace('  ', ' ')

      # gpu index
      return_dict['gpu_id'] = parsed_line.split(' ')[2]

      #bus id
      return_dict['bus_id'] = parsed_line.split(' ')[3]

      return_dict['core_mhz'] = parsed_line.split(' ')[5]
      # current temp
      return_dict['temp'] = parsed_line.split(' ')[8]
      # return_dict['fan'] = parsed_line.split(' ')[12]
      # voltage
      return_dict['vddc'] = parsed_line.split(' ')[13]
    elif line_type == 'gpu_stats':
      return_dict['temp'] = line.split(',')[0].split('GPU')[1].split('[')[1].split('C')[0]
      return_dict['fan'] = line.split('fan ')[1].split('%')[0]
      return_dict['gpu_id'] = line.split(',')[0].split('GPU')[1].split('[')[0].replace(' ', '')
      return_dict['hashrate'] = line.split('fan ')[1].split(': ')[1].split(',')[0]

    return return_dict
  except:
    return None
  
class OperationSystem:
  def __init__(self):
    pass
  def reboot(self):
    subprocess.call(f'.\\re_boot.bat', shell=True)

operation_system = OperationSystem()

def unpackMinerDictForMinerInit(miner_dict):
  try:
    miner_software = miner_dict['miner_software']
  except:
    miner_software = None
  try:
    algo = miner_dict['algo']
  except:
    algo = None
  try:
    pool = miner_dict['pool']
  except:
    pool = None
  try:
    wallet = miner_dict['wallet'] 
  except:
    wallet = None
  try:
    worker = miner_dict['worker']
  except:
    worker = None
  try:
    password = miner_dict['password']
  except:
    password = None
  try:
    additional_arguments = miner_dict['additional_arguments']
  except:
    additional_arguments = None
  try:
    version = miner_dict['version']
  except:
    version = None
  
  return miner_software, algo, pool, wallet, worker, password, additional_arguments, version

class MiningSoftware():
  pass

class TrexMiner(MiningSoftware):
  pass


class TeamRedMiner():
  process = None
  def __init__(self):
    self.listner_port = 4028
  def start(self, algo, pool, wallet, worker, password, additional_arguments, version = '090'):
    # generate the cli command
    cmd_command = f'.\\miners\\teamredminer{version}.exe -a {algo} -o {pool} -u {wallet}.{worker} -p {password} {additional_arguments} --api_listen={self.listner_port}'

    self.process = subprocess.Popen(cmd_command.split(), shell= True, stdout=subprocess.PIPE)
    
    # output, error = self.process.communicate()
    # print(error)
    # print(output)
  def stop(self):

    subprocess.Popen('taskkill /F /PID {0}'.format(self.process.pid), shell=True)

    # self.process.kill()
  
  def getSummary(self):
    def linesplit(socket):
      buffer = socket.recv(4096)
      done = False
      while not done:
        more = socket.recv(4096)
        if not more:
          done = True
        else:
          buffer = buffer+more
      if buffer:
        return buffer

    api_ip = '127.0.0.1'
    api_port = self.listner_port

    devdetails = []
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect((api_ip,int(api_port)))
    s.send(json.dumps({"command":'devdetails'}).encode('utf-8'))
    response = linesplit(s)
    response = response.decode()
    s.close()
    devdetails = json.loads(response)

    devs = []
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect((api_ip,int(api_port)))
    s.send(json.dumps({"command":'devs'}).encode('utf-8'))
    response = linesplit(s)
    response = response.decode()
    s.close()
    devs = json.loads(response)
    
    summary = []
    devices = devs['DEVS']
    for device in devices:
      gpu_id = device['GPU']
      devdetail = list(filter(lambda x: x['ID'] == gpu_id,devdetails['DEVDETAILS']))[0]
      gpu_summary = {}
      gpu_summary['temp'] = device['Temperature']
      gpu_summary['name'] = devdetail['Model']
      gpu_summary['hashrate'] = device['MHS 30s']
      gpu_summary['bus_id'] = devdetail['Device Path']
      gpu_summary['fan'] = device['Fan Percent']
      gpu_summary['consumption'] = device['GPU Power']
      gpu_summary['accepted_shares'] = device['Accepted']
      gpu_summary['rejected_shares'] = device['Rejected']
      gpu_summary['hardware_errors'] = device['Hardware Errors']
      gpu_summary['algo'] = devdetail['Kernel']
      summary.append(gpu_summary)
      
    # devices 
    return summary


class LolMiner():
  process = None
  def __init__(self, miner_dict) -> None:
    miner_software, algo, pool, wallet, worker, password, additional_arguments, version = unpackMinerDictForMinerInit(miner_dict)
    self.version = version
    self.algo = algo
    self.pool = pool
    self.wallet = wallet
    self.worker = worker
    self.password = password
    self.additional_arguments = additional_arguments
    self.listner_port = 8080
  def start(self, read_stdout=False):
    # generate the cli command
    cmd_command = f'.\\miners\\lolMiner{self.version}.exe -a {self.algo} --pool {self.pool} --user {self.wallet}'
    if self.worker: cmd_command += f' --worker={self.worker}'

    if self.password and self.password != '':
      cmd_command += f' -p {self.password}'
    cmd_command += f' {self.additional_arguments} --apiport={self.listner_port}'
    print(f'starting lolminer with cmd {cmd_command}')
    if read_stdout:
      self.process = subprocess.Popen(cmd_command.split(), shell= True, stdout=subprocess.PIPE)
    else:
      self.process = subprocess.Popen(cmd_command.split(), shell= True, stdout=subprocess.DEVNULL)

  def stop(self):
    print(f'terminating lolminer')
    subprocess.Popen('taskkill /F /PID {0}'.format(self.process.pid), shell=True)
    # self.process.kill()

  def getSummary(self):
    if self.process.poll() is not None: 
      print('miner was terminated by itself')
      return 'miner was terminated by itself'
    r = requests.get(f'http://localhost:{self.listner_port}'+'/summary')
    r = r.json()
    # print(r)
    summary = []
    gpu_list = r['GPUs']
    for gpu in gpu_list:
      gpu_summary = {}
      gpu_summary['temp'] = gpu['Temp (deg C)']
      gpu_summary['name'] = gpu['Name']
      gpu_summary['hashrate'] = gpu['Performance']
      gpu_summary['bus_id'] = gpu['PCIE_Address'] + '0.0'
      gpu_summary['fan'] = gpu['Fan Speed (%)']
      gpu_summary['consumption'] = gpu['Consumption (W)']
      gpu_summary['accepted_shares'] = gpu['Session_Accepted']
      gpu_summary['rejected_shares'] = gpu['Session_Stale']
      gpu_summary['hardware_errors'] = gpu['Session_HWErr']
      gpu_summary['algo'] = r['Mining']['Algorithm']
      summary.append(gpu_summary)
    return summary
# load config

oc_sample_string = '''[General]
MainWindowLeft=107
MainWindowTop=59
IgnoreError-8=1

[Profile_0]
Name=custom_oc
GPU_P0=300;900
GPU_P1=508;900
GPU_P2=717;900
GPU_P3=874;900
GPU_P4=911;900
GPU_P5=944;900
GPU_P6=974;900
GPU_P7=1150;900
Mem_P0=500;900
Mem_TimingLevel=2097253
Fan_P0=0;0
Fan_P1=0;0
Fan_P2=0;0
Fan_P3=0;0
Fan_P4=0;0
Fan_ZeroRPM=0
Fan_Acoustic=1
Power_Target=0
'''

def applyAmdOcSettings(amd_oc_settings, all_gpus):
  # [{'clock_voltage': 900, 'clock_freq': 1150, '--fan': 55}]
  if amd_oc_settings == []: return 1
  freq = amd_oc_settings['clock_freq']
  voltage = amd_oc_settings['clock_voltage']
  fan = amd_oc_settings['--fan']
  # overdrivent tool ignore 0 index gpu?
  amd_gpu_indexes = []
  
  
  # if the OC are different for some gpu
  amd_gpu_num = 0
  if type(freq) is list or type(voltage) is list:
    for gpu in all_gpus:
      if gpu['manufacturer'] == 'AMD':
        amd_gpu_indexes.append(all_gpus.index(gpu))
        amd_gpu_num = len(amd_gpu_indexes)
    
  else: 
    amd_gpu_num = 1


  # run cmd to apply settings
  for i in range(amd_gpu_num):
    # if the same gpu settings or only 1 gpu
    if amd_gpu_num == 1:
      gpu_index = '*'
    # if more than 1 setting to apply and more gpu
    else:
      gpu_index = amd_gpu_indexes[i]
    oc_freq = freq[i]
    oc_voltage = voltage[i]
    new_oc = oc_sample_string.replace('GPU_P7=1150;900', f'GPU_P7={oc_freq};{oc_voltage}')
    with open('.\\amd_oc\\OverdriveNTool.ini', 'w') as out:
      out.write(new_oc)


    subprocess.call(f'.\\amd_oc\\OverdriveNTool.exe -p{gpu_index}custom_oc', shell=True)
  if fan != 0:
    cmd_command = f'.\\amd_oc\\teamredminer84.exe -a autolykos2 -o stratum+tcp://ll.ll.ll:11111 -u zxc.cxz  --fan_control='
    for i in range(amd_gpu_num-1):
      fan_value = fan[i]
      cmd_command += f':::{fan_value},'
    last_fan = fan[-1]
    cmd_command += f':::{last_fan}'
    print(cmd_command)
    process = subprocess.Popen(cmd_command.split(), shell= False, stdout=subprocess.PIPE)
    time.sleep(3)
    while True:
      time.sleep(0.1)  
      line = process.stdout.readline().decode('utf-8')
      if line.__contains__('Runtime Command Keys:') : break # or time.time() - start_time > 60
    subprocess.Popen('taskkill /F /PID {0}'.format(process.pid), shell=True)

  # check_output("python F:\\projects\\miner\\worker\\main.py", shell=True)  # os.system("python print(1231231)")

def applyNvidiaOcSettings(nvidia_oc_settings, all_gpus):
  if nvidia_oc_settings == []: return 1
  #  'NVIDIA': {'-lmc': ['0,2000','0,2000','0,2000'], '-lgc': ['0,2025','0,2025','0,2025'], '-pl': ['160','160','160'], '--cclock': [250,250,250],'--pl': [75,75,75], '--fan': [65,65,65]}
  # through miner
  try:
    mclock = nvidia_oc_settings['--mclock']
  except:
    mclock = None
  try:
    cclock = nvidia_oc_settings['--cclock']
  except:
    cclock = None
  try:
    fan = nvidia_oc_settings['--fan']
  except:
    fan = None
  # run cmd to apply settings
  cmd_command = f'C:\\worker\\amd_oc\\trex0248.exe -a ethash -o stratum+tcp://ll.ll.ll:1800 -u lll -w ll'
  if cclock: 
    cmd_command += f' --cclock '
    for i in range(len(cclock)-1):
      cclock_value = cclock[i]
      cmd_command += f'{cclock_value},'
    last_cclock_value = cclock[-1]
    cmd_command += f'{last_cclock_value}'
  
  if mclock: 
    cmd_command += f' --mclock '
    for i in range(len(mclock)-1):
      mclock_value = mclock[i]
      cmd_command += f'{mclock_value},'
    last_mclock_value = mclock[-1]
    cmd_command += f'{last_mclock_value}'

  if fan: 
    cmd_command += f' --fan '
    for i in range(len(fan)-1):
      fan_value = fan[i]
      cmd_command += f'{fan_value},'
    last_fan_value = fan[-1]
    cmd_command += f'{last_fan_value}'
  print(cmd_command)
  process = subprocess.Popen(cmd_command.split(), shell= False, stdout=subprocess.PIPE)
  # nvidia\amd set overclock through miners wait till specific message then abort
  time.sleep(3)
  while True:
    time.sleep(0.1)  
    line = process.stdout.readline().decode('utf-8')
    if line != '': print(line)
    if line.__contains__(' intensity ') : break # or time.time() - start_time > 60
  time.sleep(3)
  subprocess.Popen('taskkill /F /PID {0}'.format(process.pid), shell=True)
  
  # run nvidia-smi
  for i in range(len(nvidia_oc_settings['-pl'])):
    setting = nvidia_oc_settings
    nvidiasmicommand = f'nvidia-smi'
    if setting['-lmc'][i] != '': 
      lmc = setting['-lmc'][i]
      nvidiasmicommand+= f' -lmc {lmc} -i {i}'
      subprocess.call(nvidiasmicommand, shell=True)
    nvidiasmicommand = f'nvidia-smi'
    if setting['-lgc'][i]: 
      lgc = setting['-lgc'][i]
      nvidiasmicommand+= f' -lgc {lgc} -i {i}'
      subprocess.call(nvidiasmicommand, shell=True)
    nvidiasmicommand = f'nvidia-smi'
    if setting['-pl'][i]: 
      pl = setting['-pl'][i]
      nvidiasmicommand+= f' -pl {pl} -i {i}'
      subprocess.call(nvidiasmicommand, shell=True)
  # check_output("python F:\\projects\\miner\\worker\\main.py", shell=True)  # os.system("python print(1231231)")

def getGpusInfo():
  
  def getAmdGpusInfo():
    process = subprocess.Popen(f'.\\amd_oc\\teamredminer84.exe --list_devices'.split(), shell= True, stdout=subprocess.PIPE)
    gpus_info = []
    data = process.stdout.readlines()
    start_parsing = False
    for line in data:
      if start_parsing:
        if line.decode('utf-8').__contains__('Successful clean') or line.decode('utf-8').__contains__('Detected '): break
        gpu_stats = {
          "bus_id": '',
          "name": '',
          "model": ''
        }
        gpu_info = line.decode('utf-8').split('  ')
        gpu_stats['bus_id'] = gpu_info[9].split(' ')[1]
        gpu_stats['name'] = gpu_info[10]
        gpu_stats['model'] = gpu_info[14]
        gpu_stats['manufacturer'] = 'AMD'
        gpus_info.append(gpu_stats)
      elif line.decode('utf-8'). __contains__('----- -------- ------ -------- ------------- ------------------------- ------'):
        start_parsing = True
    return gpus_info

  def getNvidiaGpusInfo():
    lines = []
    process = subprocess.Popen(f'.\\amd_oc\\trex0248.exe -a ethash -o stratum+http://127.0.0.1:8080'.split(), shell= False, stdout=subprocess.PIPE)
    start_time = time.time()
    while True:
      time.sleep(0.1)  
      line = process.stdout.readline().decode('utf-8')
      if line.__contains__('GPU #') & line.__contains__('['):
        lines.append(line)
      print(time.time() - start_time)
      if line.__contains__('For control navigate to') or time.time() - start_time > 60: break
    subprocess.Popen('taskkill /F /PID {0}'.format(process.pid), shell=True)
    gpus_info = []
    for line in lines:
      gpu_stats = {}
      bus_id = ''
      __temp = line.split('[')[1].split('|')[0]
      bus_id += __temp.split(':')[1].split('.')[0]
      bus_id += ':'
      bus_id +=  __temp.split(':')[0]
      bus_id += '.'
      bus_id +=  __temp.split('.')[1]
      gpu_stats['bus_id'] = bus_id
      gpu_stats['name'] = line.split('] ')[1].split(',')[0]
      gpu_stats['manufacturer'] = 'NVIDIA'
      gpus_info.append(gpu_stats)
    return gpus_info


  all_gpus = []

  #TODO rewrite gpu detector using Operation system
  cmd = r'wmic path win32_VideoController get AdapterCompatibility, Name'
  integrated_gpu = str(subprocess.check_output(cmd, shell=True)).__contains__('Microsoft')
  if integrated_gpu:
    all_gpus.append({'bus_id': '00:00.0', 'name': 'Integrated Graphics', 'manufacturer': 'intel?amd?microsoft?'})


  # miner = LolMiner({'algo': 'AUTOLYKOS2', 'pool': '192.333.333.333:1180', 'wallet': 'x'})
  # miner.start('amd_oc\\lolMiner139.exe')
  # for i in range(3):
  #   time.sleep(30)
  #   summary = miner.getSummary()
  #   print(summary)
  # for gpu in summary:
  #   del gpu['hashrate']
  #   del gpu['accepted_shares']
  #   del gpu['rejected_shares']
  #   del gpu['algo']
  #   gpu['manufacturer'] = gpu['name'].split(' ')[0]
  #   print(gpu)
  #   all_gpus.append(gpu)
  # miner.stop()


  amd_gpus_info = getAmdGpusInfo()
  nvidia_gpus_info = getNvidiaGpusInfo()
  for gpu in amd_gpus_info: all_gpus.append(gpu)
  for gpu in nvidia_gpus_info: all_gpus.append(gpu)
  all_gpus.sort(key=lambda x: x['bus_id'], reverse=False)
  return all_gpus

def main():
  limit_of_crashes = 3
  num_of_crashes = 0

  # get to host
  try:
    last_err = readLastError()
    writeLastError('None')
  except:
    last_err = 'None'


  all_gpus = getGpusInfo()
  for gpu in all_gpus:
    print(f'gpu: {gpu}')
  while True:
    print(f'trying to connect to host on: {host_url}')
    try:
      r = requests.get(host_url+'/ping2',json={'worker_api_key': worker_api_key, "worker_version": worker_version, 'all_gpus': all_gpus, "last_error": last_err})
      # r 200?
      print('successfully connected to master')
      break
    except:
      print(f'not connected to master, retrying after 30 secs')
      sleep(30)
  
  
  # get oc settings
  r = requests.get(host_url+'/get_oc2',json={'worker_api_key': worker_api_key})
  r = r.json()
  print(f'got the oc settings')
  amd_oc_settings = r['AMD']
  nvidia_oc_settings = r['NVIDIA']
  print(f'AMD:{amd_oc_settings}')
  print(f'NVIDIA:{nvidia_oc_settings}')
  # apply oc settings
  applyAmdOcSettings(amd_oc_settings, all_gpus)
  applyNvidiaOcSettings(nvidia_oc_settings, all_gpus)

  # get miner settings
  r = requests.get(host_url+'/get_miner2',json={'worker_api_key': worker_api_key})
  print('got the miner settings')
  r = r.json()
  try:
    miner_cycle_time = r['miner_cycle_time']
  except:
    miner_cycle_time = 60 * 60 *4

  miners = []
  miner_list = r['miner_list'] 
  for miner in miner_list:
    miner_software = miner['miner_software']

    if miner_software == 'lolminer':
      mining_software = LolMiner(miner)
    elif miner_software == 'trex':
      mining_software = TrexMiner()
    elif miner_software == 'teamredminer':
      mining_software = TeamRedMiner(miner)
    miners.append(mining_software)
  
  for miner in miners:
    miner.start_time = datetime.now().timestamp()
    miner.start()
    miner_delay = 1
    if miner_delay:
      time.sleep(miner_delay)
  run_miner = True
  
  while run_miner:
    time.sleep(30)
    summary = []
    all_gpus_copy = all_gpus[:]
    for miner in miners:
      miner_summary = miner.getSummary()
      for gpu in miner_summary:
        device_info = list(filter(lambda x: x['bus_id'].__contains__(gpu['bus_id']), all_gpus_copy))[0]
        summary.append({**gpu, **device_info})

    print('summary for each gpu is:')
    for i in summary:
      print(i)

    # send to server
    try:
      r = requests.get(host_url+'/send_updates2',json={'worker_api_key': worker_api_key, 'summary': summary})
      r = r.json()
      action = 'None'
      try:
        action = r['action']
      except: pass
      # if getting some specific signal from the host, do it
      if action == 'stop_miners':
        pass#shutdown
      if action == 'shutdown':
        pass#shutdown
      elif action == 'reboot':
        writeLastError('Miner rebooted from the outside')
        operation_system.reboot()
        return 1
    except Exception:
      traceback.print_exc()
  
  print('done')
  time.sleep(10000)

import threading

if __name__ == '__main__':
  try:
    # processThread = threading.Thread(target=checkStatus, args=('worker', 'warden',))  
    # processThread.start()
    main()
  except Exception:
    traceback.print_exc()
    sleep(10)
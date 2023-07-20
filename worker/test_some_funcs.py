import socket
import json
import sys


def getSummary(api_ip, api_port):
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

getSummary('192.168.0.105', 4028)




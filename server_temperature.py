#!/opt/bb/bin/python3
# -*- coding: UTF-8 -*-

#Author: Jose Fernandes Neto
#Description: Takes appliances' chassis and sfc temperature data from hosts and publish it to DB (data source)

import re
import json
import os
import sys
sys.path.insert(1,"/opt/bb/lib/python3.6/site-packages")
sys.path.insert(1,"/bb/bin/shoc/lib")
from NSREUtils import pmLogging
from sqlCommands import mysqlConnect
from bloomberg.guts.api import MetricPublisher

networkCardList = []
myLog = pmLogging("applianceTemperature")
myNamespace = "msesysopdev"
myDBHandle = mysqlConnect("servers").get_conn()

def get_cluster(host):

  # Getting appliances' cluster and parent cluster from SOR

  global cluster
  global parent_cluster
  curlCommand = 'curl -s -X POST --data \'{"data": ['
  curlCommand += '"' + host + '"'
  curlCommand += ']}\' http://sor.bloomberg.com/sor/servers/hostname?enable='
  curlCommand += 'cluster,parent_cluster\&pretty=true'
  command = os.popen(curlCommand).read()
  json_data = json.loads(command)
  allServers = json_data.get('servers', None)
  for server in allServers:
    for key, value in server.items():
      if key == 'server':
        for i,k in value.items():
          if i == 'cluster':
            cluster = k
          elif i  == 'parent_cluster':
            parent_cluster = k
  return cluster, parent_cluster

def get_hosts_interfaces_for_sfc():

  # Get all hosts that have sfc temperature registered in DGATE.

  hostIntRequest = "SELECT DISTINCT serverOutput.serverId, serverOutput.command FROM serverOutput JOIN serverBase WHERE "
  hostIntRequest += " serverOutput.serverId = serverBase.serverId AND serverOutput.command LIKE '%ethtool -m%' ;"
  hostIntCursor = myDBHandle.cursor(buffered=True)
  hostIntCursor.execute(hostIntRequest)
  for hostIntOut in hostIntCursor:
    out = list(hostIntOut)
    host = out[0]
    interfaceName = out[-1].split()[-1]
    get_sfc_temperature(host, interfaceName)

def get_sfc_temperature(host, interfaceName):

  # Taking temperature per card.
  # Once it gets interface's temperature of its corresponding card,
  # it goes to the next card.

  get_cluster(host)
  networkCardSN = 'sfc'
  tempRequest = "SELECT output FROM serverOutput WHERE command like '%ethtool -m%"+ interfaceName + "%' and serverId like '"+ host +"';"
  tempCursor = myDBHandle.cursor(buffered=True)
  tempCursor.execute(tempRequest)
  for tempOut in tempCursor:
    temp = str(tempOut)
    temp = re.sub('\s+', '', temp)
    temp = temp.split('\\n\\t')
    for tempLine in temp:
      if 'VendorSN' in tempLine:
        networkCardSN = tempLine.split(':')[-1]
      if 'Moduletemperature:' in tempLine and 'degrees' in tempLine and networkCardSN not in networkCardList :
        tempC = tempLine.split(':')[1].split('/')[0].split('degrees')[0]
        tempF = tempLine.split(':')[1].split('/')[1].split('degrees')[0]
        networkCardList.append(networkCardSN)
        #publishing_sfc_temp(host, networkCardSN, tempC, tempF)
        publishing_sfc_temp(host, networkCardSN, cluster, parent_cluster, tempC, tempF)

def get_hosts_for_chassis():

  # Get all hosts that have chassis temperature registered in DGATE.

  hostRequest = "SELECT DISTINCT serverOutput.serverId FROM serverOutput JOIN serverBase WHERE "
  hostRequest += " serverOutput.serverId = serverBase.serverId AND serverOutput.command LIKE '%racadm%Sensor%' "
  hostRequest += " OR serverOutput.command LIKE '%hpasmcli -s show temp%';"
  hostCursor = myDBHandle.cursor(buffered=True)
  hostCursor.execute(hostRequest)
  for hostOut in hostCursor:
    host = list(hostOut)[0]
    get_chassis_temperature(host)

def get_hwMake(host):
   global hwMake
   dmiRequest = "SELECT output FROM serverOutput WHERE serverId like '"+ host +"' and command like '%dmidecode -t1%';"
   dmiCursor = myDBHandle.cursor(buffered=True)
   dmiCursor.execute(dmiRequest)
   for dmiOut in dmiCursor:
     dmiOut = str(dmiOut)
     dmiOut = re.sub('\s+', ' ', dmiOut)
     dmiOut = dmiOut.split('\\n\\t')
     for out in dmiOut:
       if 'Manufacturer' in out:
         hwMake = out.split()
         if len(hwMake) > 1:
           hwMake = hwMake[1]
           return hwMake
         else:
           makeRequest = "SELECT DISTINCT hwMake FROM serverApplication WHERE serverId like '"+ host +"'"
           makeCursor = myDBHandle.cursor(buffered=True)
           makeCursor.execute(makeRequest)
           for hwMake in makeCursor:
             hwMake = list(hwMake)[0]
             return hwMake

def get_chassis_temperature(host):

# Currently we have 2 hardware makes (Dell and HP)

  get_hwMake(host)
  get_cluster(host)

  if hwMake == 'Dell':
    chassisTempC = 0
    chassisTempF = 32
    chTempRequest = "SELECT output FROM serverOutput WHERE command like '%racadm%Sensor%' and serverId like '"+ host +"'"
    chTempCursor = myDBHandle.cursor(buffered=True)
    chTempCursor.execute(chTempRequest)
    for out in chTempCursor:
      allPartsTemp = str(out)
      if allPartsTemp.find('Inlet') > -1:
        allPartsTemp = re.sub('\s+', ' ', allPartsTemp)
        allPartsTemp = allPartsTemp.split('\\n')
        for chassisTemp in allPartsTemp:
          if chassisTemp.find('System Board Inlet Temp') > -1:
              chassisTempC = chassisTemp.split()[5]
              if 'C' in chassisTempC:
                chassisTempC = chassisTempC[:-1]
                chassisTempF = round((int(chassisTempC) * 1.8) + 32, 2)
              else:
                chassisTempF = round((int(chassisTempC) * 1.8) + 32, 2)
    publishing_chassis_temp(host, cluster, parent_cluster, chassisTempC, chassisTempF)

  elif hwMake == 'HPE' or hwMake == 'HP':
    allPartsTemp = ''
    systembdList = []
    boardTempC = 0
    boardTempF = 32
    chTempRequest = "SELECT output FROM serverOutput WHERE command like '%hpasmcli -s show temp%' and serverId like '"+ host +"'"
    chTempCursor = myDBHandle.cursor(buffered=True)
    chTempCursor.execute(chTempRequest)
    for out in chTempCursor:
      allPartsTemp = str(out)
      if allPartsTemp.find("SYSTEM_BD") > -1:
        allPartsTemp = re.sub('\s+', ' ', allPartsTemp)
        allPartsTemp = allPartsTemp.split('\\n')
        for chassisTemp in allPartsTemp:
          if chassisTemp.find('SYSTEM_BD') > -1 and chassisTemp.find('C/') > -1 and 'captured' not in systembdList:
            systembdList.append('captured')
            chassisTemp = chassisTemp.split()[2].split('/')
            boardTempC = chassisTemp[0][:-1]
            boardTempF = chassisTemp[1][:-1]
    publishing_chassis_temp(host, cluster, parent_cluster, boardTempC, boardTempF)

  else:
    myLog.write("HwMake not found. Could not get temperature data for this host " + host)


def publishing_sfc_temp(host, networkCardSN, cluster, parent_cluster, tempC, tempF):
  myPub = MetricPublisher(namespace=myNamespace)
  myTagC = [("appHost", host),("networkInterface", networkCardSN), ("remoteCluster", str(cluster)), ("remoteParentCluster", str(parent_cluster)), ("unitName", "Celsius")]
  myTagF = [("appHost", host),("networkInterface", networkCardSN), ("remoteCluster", str(cluster)), ("remoteParentCluster", str(parent_cluster)), ("unitName", "Fahrenheit")]
  myPub.guts_metric_gauge('nicTemperature', float(tempC), tags=myTagC)
  myPub.guts_metric_gauge('nicTemperature', float(tempF), tags=myTagF)
  myLog.write('sfc: '+ host + ' '+ networkCardSN + ' '+ str(cluster) + ' '+ str(parent_cluster) + ' '+ str(tempC) + ' '+ str(tempF))


def publishing_chassis_temp(host, cluster, parent_cluster,  tempC, tempF):
  myPub = MetricPublisher(namespace=myNamespace)
  myTagC = [("appHost", host), ("remoteCluster", str(cluster)), ("remoteParentCluster", str(parent_cluster)), ("unitName", "Celsius")]
  myTagF = [("appHost", host), ("remoteCluster", str(cluster)), ("remoteParentCluster", str(parent_cluster)), ("unitName", "Fahrenheit")]
  myPub.guts_metric_gauge('chassisTemperature', float(tempC), tags=myTagC)
  myPub.guts_metric_gauge('chassisTemperature', float(tempF), tags=myTagF)
  myLog.write('chassis: '+ host + ' '+ str(cluster) + ' '+ str(parent_cluster) + ' '+ str(tempC) + ' '+ str(tempF))

def force():
  if len(sys.argv) > 1:
    if sys.argv[1] == '-f' or sys.argv[1] == '-F':
      return True
    else:
      return False

def init():
  # Getting the machine of the day on dgate
  motd = os.popen("/bb/bin/gatekeeper/bin/director.pl").read()
  runningOn = os.uname()[1]
  if runningOn not in motd and force() != True:
    myLog.write("Director says I should be running on " + motd + " exiting.")
    sys.exit(0)
  else:
    get_hosts_interfaces_for_sfc()
    get_hosts_for_chassis()


init()
myDBHandle.close()

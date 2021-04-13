#!/usr/bin/env python3

# Nome: Jose Fernandes Neto / linkedin.com/in/jfneto7
# Data: 12.04.2021



from neo4j import GraphDatabase
#
#### Variables ###
meu_router = 'MEU_ROUTER_JFNETO'
file = '/opt/jfneto/iproute-router-ic.txt'
tudo = []
gateway = []
destinations = []
tudo_organizado = []
#### END Variables ###


#### Functions ###

def cleanup():
  uri = 'neo4j://localhost:7687'
  driver = GraphDatabase.driver(uri, auth=("neo4j", "2021"),
  max_connection_lifetime=1000)
  session = driver.session()
  query = "MATCH (n) DETACH DELETE n;"
  session.run(query)
  session.close()
  driver.close()

def creating_my_router():
  uri = 'neo4j://localhost:7687'
  driver = GraphDatabase.driver(uri, auth=("neo4j", "2021"),
  max_connection_lifetime=1000)
  session = driver.session()
  query = """CREATE (a:Router {name: '"""+meu_router+"""', ip: '127.0.0.1'});"""
  session.run(query)
  session.close()
  driver.close()
  #print("CRIANDO MEU ROUTER: "+meu_router)

def creating_all_routers():
  for i in range(len(gateway)):
    uri = 'neo4j://localhost:7687'
    driver = GraphDatabase.driver(uri, auth=("neo4j", "2021"),
    max_connection_lifetime=1000)
    session = driver.session()
    query = """CREATE (a:Router {name: '"""+gateway[i]+"""'});"""
    session.run(query)
    session.close()
    driver.close()
     #print("Criando router/gateway: ", gateway[i])

def creating_all_destinations():
  for i in range(len(destinations)):
    uri = 'neo4j://localhost:7687'
    driver = GraphDatabase.driver(uri, auth=("neo4j", "2021"),
    max_connection_lifetime=1000)
    session = driver.session()
    query = """CREATE (a:Network {name: '"""+destinations[i]+"""'});"""
    session.run(query)
    session.close()
    driver.close()
     #print("Criando destination/sub-rede: ", destinations[i])

### Criando conexoes entre 'meu roteador' ate os routers (gateways) de acesso as redes de destino
def creating_conn_myrouter2allrouters():
  for i in range(len(gateway)):
    uri = 'neo4j://localhost:7687'
    driver = GraphDatabase.driver(uri, auth=("neo4j", "2021"),
    max_connection_lifetime=1000)
    session = driver.session()
    query = """MATCH (a:Router {name: '"""+meu_router+"""'}) MATCH (b:Router {name: '"""+gateway[i]+"""'}) CREATE (a)-[relacao:ROTA] ->(b);"""
    session.run(query)
    session.close()
    driver.close()

### Conexoes entre gateway e destinos (informando qual o protocolo da rota)
def creating_conn_allrouters2destinations():
  for j in range(len(gateway)):
    for i in range(len(tudo_organizado)):
      if gateway[j] in tudo_organizado[i]:
        uri = 'neo4j://localhost:7687'
        driver = GraphDatabase.driver(uri, auth=("neo4j", "2021"),
        max_connection_lifetime=1000)
        session = driver.session()
        query = """MATCH (a:Router {name: '"""+tudo_organizado[i]+"""'}) MATCH (b:Network {name: '"""+tudo_organizado[i+1]+"""'}) CREATE (a)-[relacao:ROTA_"""+tudo_organizado[i+2]+"""] ->(b);"""
        session.run(query)
        session.close()
        driver.close()
        #print("ROUTER: %s >>>> %s  via: %s" %(tudo_organizado[i], tudo_organizado[i+1], tudo_organizado[i+2]))
#### END Functions ###

#### Code ###

### Organizando os dados em listas para melhor usa-los...
with open(file, 'r') as arquivo:
  for i in arquivo:
    if i.split()[1] not in destinations and "Ori  Destination        Gateway" not in i:
      destinations.append(i.split()[1])
    if i.split()[2] not in gateway and "Ori  Destination        Gateway" not in i:
      gateway.append(i.split()[2])
    if "Ori  Destination        Gateway" not in i:
      tudo.append(i)

  for j in range(len(tudo)):
    tudo[j].split()[1]
    tudo[j].split()[2]
    tudo_organizado.append(tudo[j].split()[2])
    tudo_organizado.append(tudo[j].split()[1])
    tudo_organizado.append(tudo[j].split()[0].split("#")[1])

cleanup()
creating_my_router()
creating_all_routers()
creating_all_destinations()
creating_conn_allrouters2destinations()
creating_conn_myrouter2allrouters()

#### END Code ###

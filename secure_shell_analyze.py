#!/bin/env python3

# Name / contact: Jose Fernandes Neto / linkedin.com/in/jfneto7
# Date: 29.03.2021



import subprocess, re

### Funções ###
def init():
  global file
  global file_read
  file = "/home/inf500-ceb/eredes16/lista_exercicios/secure-ssh.log"
  file_read = open(file, "r")


def login():
  amount_fail = []
  auth_success = []
  for line in file_read:
    if re.search('authentication failure+.*', line):
      amount_fail.append(line)
      usuario_falha = re.search('authentication failure+.*', line).group()
      usuario_falha = usuario_falha.split()
    elif re.search('authentication success+.*', line):
      auth_success.append(line)
  global number_of_fails
  global number_of_success
  number_of_fails = len(amount_fail)
  number_of_success = len(auth_success)

  file_read.close()

def all_user():
  global list_users
  list_users = []
  for line in file_read:
    if re.search(r'(user\s([A-Z-a-z]+)\s)', line):
      user = re.search(r'(user\s([A-Z-a-z]+)\s)', line).group()
      user = user.split()
      if user[1] not in list_users:
        list_users.append(user[1])

def tentativa_login():
  global usuario
  global lista_ip
  global lista_falha
  global lista_sucesso
  lista_ip = []
  lista_falha = []
  lista_sucesso = []
  for line in file_read:
    if re.search(r'([]].+william from [0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})', line):
      usuario = re.search(r'([]].+william from [0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})', line).group()
      usuario = usuario.split()
      if usuario[6] not in lista_ip:
        lista_ip.append(usuario[6])
      if usuario[1] == 'Failed' and usuario[6] not in lista_falha:
        lista_falha.append(usuario[6])
      if usuario[1] == 'Accepted' and usuario[6] not in lista_sucesso:
        lista_sucesso.append(usuario[6])

### Menu ###
while True:
  print("Selecione:")
  print("1 - Números de tentativas de logins que falharam")
  print("2 - Números de logins realizado com sucesso")
  print("3 - Lista de todos os usuários que tentaram logar")
  print("4 - Baseado em um usuário (william), quais foram os IPs de tentativa e login realizado")
  print("5 - Sair")

  opcao = input("Selecione uma opção: ")

  if opcao == '1':
    init()
    login()
    print("Numero de tentativas que falharam é: %d (baseado em 'authentication failure')" %number_of_fails)
    exit(0)
  elif opcao == '2':
    init()
    login()
    print("Numero de logins com sucesso é de: %d (baseado em 'authentication success')" %number_of_success)
    exit(0)
  elif opcao == '3':
    init()
    all_user()
    for user in list_users:
      print(user)
    file_read.close()
    exit(0)
  elif opcao == '4':
    init()
    tentativa_login()
    print("Todos IPs do usuário 'william' que tentaram login são:")
    for ip in lista_ip:
      print(ip)
    print("\nTodos os IPs que falharam no login são:")
    for falha in lista_falha:
      print(falha)
    print("\nE os IPs que tiveram sucesso no login são:")
    for sucesso in lista_sucesso:
      print(sucesso)
    file_read.close()
    exit(0)
  elif opcao == '5':
    print("Saindo...")
    exit(0)
  else:
    print("\n >>>>>[!] Opção inválida. Tente outra vez! <<<<<< \n")
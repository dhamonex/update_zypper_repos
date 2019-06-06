#!/usr/bin/python3
import sys
import argparse
import requests
import getpass
import subprocess
from urllib.parse import urlparse

def userCheck(dryRun):
  if dryRun:
    return
  
  if getpass.getuser() != "root":
    raise RuntimeError("must be root to execute zypper commands")
  
  
def getRepositories(stdin):
  if stdin:
    return sys.stdin.readlines()
  
  return subprocess.check_output(["zypper", "lr", "-d"]).splitlines()

def createRepositories(args):
  userCheck(args.dryRun)
  
  zypperRepos = getRepositories(args.readStdin)
  repoCounter = 0
  newRepos = []
  
  for repo in zypperRepos:
    repoParts = repo.split("|")
    
    if len(repoParts) != 10:
      continue
    
    if not repoParts[0].strip().isdigit():
      continue
    
    repoCounter += 1
    name = repoParts[1].strip().replace(args.prevDist, args.distribution)
    description = repoParts[2].strip().replace(args.prevDist, args.distribution)
    enabled = repoParts[3].strip().upper() == "YES" or repoParts[3].strip().upper() == "JA"
    uri = repoParts[8].strip().replace(args.prevDist, args.distribution)
    
    parsedUrl = urlparse(uri)
    if parsedUrl.scheme == "hd":
      continue
    
    response = requests.get(uri)
    if response.status_code != 200:
      print ("Error on URI-check, status code is %d for the uri %s" % (response.status_code, uri))
      raise RuntimeError("URI check failed")
    
    newRepos.append("zypper ar -f%s -n \"%s\" %s %s" % (" -d" if not enabled else "", description, uri, name))
    
  zypperrr = "zypper rr"  
  for i in range(1, repoCounter + 1):
    zypperrr += " %d" % i
  
  if args.dryRun:
    print ("%s\n" % zypperrr)
  else:
    subprocess.check_call([zypperrr], shell = True)
  
  for repo in newRepos:
    if args.dryRun:
      print (repo)
    else:
      subprocess.check_call([repo], shell = True)


def main():
  parser = argparse.ArgumentParser(description = "switches repos to given dist for zypper dup")
  parser.add_argument("-d", "--distribution", dest = "distribution", required = True, help = "distribution, e.g. 42.2")
  parser.add_argument("-p", "--previous-distribution", dest = "prevDist", required = True, help = "previous distribution, e.g.42.1")#
  parser.add_argument("-s", "--stdin", dest = "readStdin", action = "store_true", help = "read zypper input from stdin")
  parser.add_argument("-n", "--dry-run", dest = "dryRun", action = "store_true", help = "print repos dont't execute commands")
  
  args = parser.parse_args()
  
  try:
    createRepositories(args)
    
  except Exception as e:
    print ("Error: %s" % e)
if __name__ == "__main__":
  main()

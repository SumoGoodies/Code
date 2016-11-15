#!/usr/bin/python

import sys, os
import json
import requests
from time import gmtime, strftime

######## README FIRST #############################################################################
# This code is FREE to use and distribute with no strings attached. It is provided as is with   #
# NO WARRANTY is implied either.                                                                  #
#                                                                                                 #
# You will need to replace the API URL, the AccessID/AccessKey, and the confirmation Issue prefix.#
# You can change the logFilePath and the data structure to populate JiRA as you see fit.          #
#                                                                                                 #
###################################################################################################

# configure this per each custom deployment
logFilePath = "/vagrant/sumo-jira-integration.log"
 
# Generate a UTC timestamp
def getTimeStamp():
    timeStamp = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    timeStamp += "Z"
    return timeStamp

# Exits the script with the given error code, logging the error
def exitError(logFile, errorMsg, errorCode):
    timeStamp = getTimeStamp()
    logMsg(logFile, errorMsg)
    logMsg(logFile, "Alert handler exiting with error\n")
    logFile.close()
    sys.exit(errorCode)

# Exits the script with no error code (0)
def exitSuccess(logFile):
    timeStamp = getTimeStamp()
    logMsg(logFile, "Alert handler exiting successfully\n")
    logFile.close()
    sys.exit(0)

# Writes a given log message with timestamp
def logMsg(logFile, logMessage):
    timeStamp = getTimeStamp()
    logFile.write(timeStamp + ":  " + logMessage + "\n")

# Get the JSON data from Sumo Alert
def getJsonData(cmdArgs):
    argsNum = len(cmdArgs)
    # We want a single argument--the path to our alert data file
    if argsNum != 2:
        exitError(logFile, "Incorrect number of arguments received.  Exiting...", 1)
    jsonFileName = cmdArgs[1]

    try:
        jsonFile = open(jsonFileName)
    except IOError as ex:
        sys.exit()
    jsonData = json.load(jsonFile)
    jsonFile.close()
    return jsonData


class JiRA: 
    # initialize those for the different customers
    endpoint = 'https://vocalocity.atlassian.net/rest/api/2'
    session = requests.Session()

    def __init__(self, accessId, accessKey):
        self.session.auth = (accessId, accessKey)
        self.session.headers = {'content-type': 'application/json', 'accept': 'application/json'}

    def get(self, method, params=None):
        return self.session.get(self.endpoint + method, params=params)

    def post(self, method, params, headers=None):
        return self.session.post(self.endpoint + method, data=json.dumps(params), headers=headers)

    def create_issue(self, params):
        r = self.post('/issue', params)
        return json.loads(r.text)

####### MAIN PROGRAM #############
# Start logging
try:
    logFile = open(logFilePath, "a")
except IOError as ex:
    # Don't proceed if we can't log
    print "Unable to open log file (" + logFilePath + "):  " + ex + "\n"
    sys.exit(1)


# Get started
logMsg(logFile, "Alert handler started")

# get JSON
jsonData = getJsonData(sys.argv)

# get the searchName
try:
    searchName = str(jsonData["searchName"])
    runAS = str(jsonData["runAs"])
    searchQuery = str(jsonData["searchQuery"])
    searchURL = str(jsonData["searchUrl"])
except Exception as ex:
    logMsg(logFile, "Error while trying to read Intrinsic values from JSON:  " + str(ex))
    exitError(logFile, "Couldn't read intrinsic fields from JSON",1)

# initialize the JiRA required fields
description = searchURL+'  \nrunAS='+ runAS+ '  \nQuery='+ searchQuery
jira_data={
    "fields": {
       "project": {
          "key": "SUMO"
       },
       "summary": searchName, 
       "description": description,
       "issuetype": {
          "name": "Task"
       }
   }
}
logMsg(logFile,'Alert='+str(sys.argv))
logMsg(logFile,str(jira_data))
jira = JiRA('sumologic','K5ckJeOu8xaJkY')
result = jira.create_issue(jira_data)
logMsg(logFile, str(result))

# Clean up the Alert.  Here, I'm looking for the issue created, ie: SUMO-32453
if str(result["key"]).find("SUMO-") > -1 :
    try:
        os.remove(sys.argv[1])
        logMsg(logFile, "Remove Alert file:  " + sys.argv[1])
    except Exception as ex:
        logMsg(logFile, "Error while trying to remove AlertFile:  " + str(ex))

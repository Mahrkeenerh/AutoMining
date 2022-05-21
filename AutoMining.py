import subprocess, traceback, datetime, json, nicehash, steam
from time import sleep
from enum import Enum
from datetime import datetime
from threading import Thread


with open("secrets.json") as secrets_file:
    secrets = json.load(secrets_file)

host = secrets['host']
organization_id = secrets['organization_id']
key = secrets['key']
secret = secrets['secret']
rigID = secrets['rigID']
steamKey = secrets['steamKey']
steamId = secrets['steamId']


class PowerStatus(Enum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CUSTOM = 3


power_status = PowerStatus.HIGH
NiceHash = nicehash.private_api(host, organization_id, key, secret)
mining = False
override = False
stop = False

is_in_game = [False] * 10


# POWER IDs
# https://github.com/nicehash/NiceHashQuickMiner/blob/main/optimize/data_006.json

def WaitNH(func, *args):

    response = func(*args)

    while 'success' not in response or not response['success']:
        print(datetime.now(), end=" ")
        print("ERROR")
        print("WAITING FOR RESPONSE: \nfunc:\n", func, "\nargs:\n", args)
        print("response:", response)
        sleep(1)
        response = func(*args)
    
    return response


def NHSetPowerLow():

    global power_status

    body = {
        "action": "NHQM_SET",
        "options": [
            "V=1;OP=12;"
        ],
        "rigId": rigID
    }

    power_status = PowerStatus.LOW

    return WaitNH(NiceHash.set_mining_rig_status_custom, body)


def NHSetPowerMedium():

    global power_status

    body = {
        "action": "NHQM_SET",
        "options": [
            "V=1;OP=11;"
        ],
        "rigId": rigID
    }

    power_status = PowerStatus.MEDIUM

    return WaitNH(NiceHash.set_mining_rig_status_custom, body)


def NHSetPowerHigh():

    global power_status

    action = 'POWER_MODE'
    options = ['LOW']

    power_status = PowerStatus.HIGH

    return WaitNH(NiceHash.set_mining_rig_status, rigID, action, options)


def SetPowerLow():

    global power_status
    power_status = PowerStatus.LOW

    return subprocess.call(["nvidia-smi", "-pl", "80"])


def SetPowerMedium():

    global power_status
    power_status = PowerStatus.MEDIUM

    return subprocess.call(["nvidia-smi", "-pl", "110"])


def SetPowerHigh():

    global power_status
    power_status = PowerStatus.HIGH

    return subprocess.call(["nvidia-smi", "-pl", "160"])


def SetPower(num):

    global power_status
    power_status = PowerStatus.CUSTOM

    return subprocess.call(["nvidia-smi", "-pl", str(num)])


def Start():

    global mining

    action = 'START'
    mining = True

    return WaitNH(NiceHash.set_mining_rig_status, rigID, action, '')


def Stop():

    global mining

    SetPowerHigh()

    action = 'STOP'
    mining = False

    return WaitNH(NiceHash.set_mining_rig_status, rigID, action, '')


def Reset():

    Start()
    Stop()


def AddGame(state):

    global is_in_game

    del is_in_game[0]

    is_in_game.append(state)


def IsInGame():

    try:
        response = steam.get_player_summaries(steamKey, steamId)
    
    except:
        return -1

    if response['response']['players']:
        if 'gameid' in response['response']['players'][0]:
            if response['response']['players'][0]['gameextrainfo'] != "Blender":
                AddGame(True)

        AddGame(False)
        return any(is_in_game)

    return response


def IsNight():

    hour = datetime.now().hour

    if hour >= 22 or hour < 10:
        return True
    
    return False


def IsLoggedIn():

    process_name='LogonUI.exe'
    callall='TASKLIST'
    outputall=subprocess.check_output(callall)
    outputstringall=str(outputall)

    return process_name not in outputstringall


def Loop():

    isInGame = False

    while True:
        if stop:
            print("LOOP ENDED")
            return

        if override:
            sleep(1)
            continue
        
        inGame = IsInGame()

        if inGame in [True, False]:
            isInGame = inGame

        if isInGame and mining:
            print(datetime.now(), end=" ")
            print("GAME MODE -> HIGH, STOP MINING")
            Stop()
        
        if not isInGame and not mining:
            print(datetime.now(), end=" ")
            print("GAME OFF -> START MINING")
            Start()
        
        if mining and IsNight():
            if IsLoggedIn() and power_status != PowerStatus.MEDIUM:
                print(datetime.now(), end=" ")
                print("NIGHT, LOGGED IN -> MEDIUM")
                SetPowerMedium()
            
            if not IsLoggedIn() and power_status != PowerStatus.LOW:
                print(datetime.now(), end=" ")
                print("NIGHT, LOGGED OUT -> LOW")
                SetPowerLow()
        
        if mining and not IsNight():
            if power_status != PowerStatus.MEDIUM:
                print(datetime.now(), end=" ")
                print("DAY -> MEDIUM")
                SetPowerMedium()

        if not mining and power_status != PowerStatus.HIGH:
            print(datetime.now(), end=" ")
            print("ERROR")
            Start()
            SetPowerHigh()
            Stop()

        sleep(1)


def Override(state):

    global override

    override = state


def CheckInput():

    global stop

    while True:
        try:
            exec = input()
            eval(exec)
            print(datetime.now(), end=" ")
            print("OK")

        except KeyboardInterrupt:
            stop = True
            return
        
        except:
            print()
            print(traceback.format_exc())
            print()


if __name__ == '__main__':
    try:
        sleep(30)
        Start()

        Thread(target=Loop).start()

        print("MINING\n")
        print("PRESS ^C TO STOP")

        CheckInput()

        print()
        print(traceback.format_exc())
        print("\nSTOPPING, PLEASE WAIT")

        Reset()

        print("PRESS ENTER TO CLOSE")
        input()
    except:
        with open(".log", "a") as out:
            print(traceback.format_exc(), file=out)

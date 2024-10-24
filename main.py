# Backend code for TimMcCool's backend-served cloud engine

import scratchattach as sa
from scratchattach import Encoding
import time
import threading

PROJECT_ID = "projectid" # fill in your project id here
MAX_PLAYERS = 31
LEAVE_TIMEOUT = 3

session = sa.login_by_id("sessionid", username="username") # fill in your username and your session id here
events = sa.get_cloud(PROJECT_ID).events()
events2 = session.connect_cloud(PROJECT_ID).events()

players = {}
possible_PIDs = [i for i in range(1, MAX_PLAYERS+1)]
given_PIDs = []

def on_set(event):
    if event.name != "TO_HOST":
        return
    global players
    global given_PIDs
    activity = list(Encoding.decode(event.value).split("&"))
    uniqueBackendPID = activity.pop(0)
    username = activity.pop(0)
    if uniqueBackendPID in players:
        PID = players[uniqueBackendPID]["PID"]
    else:
        for PID in possible_PIDs:
            if PID not in given_PIDs:
                given_PIDs.append(PID)
                print(username, f"joined. Assigned Player ID: {PID}")
                break
        else:
            return
    players[uniqueBackendPID] = {"user":username, "activity":activity, "PID":PID, "last_activity":time.time()}

def send_names_task():
    conn_name_events = session.connect_cloud(PROJECT_ID)
    while True:
        while len(players) == 0:
            time.sleep(0.1)
        for PID in dict(players):
            if PID in players:
                try:
                    conn_name_events.set_var("STATIC_DATA", Encoding.encode(str(players[PID]["PID"]) + "&" +PID+ "&" + players[PID]["user"]))
                except Exception:
                    conn_name_events = session.connect_cloud(PROJECT_ID)
                    conn_name_events.set_var("STATIC_DATA", Encoding.encode(str(players[PID]["PID"]) + "&" +PID+ "&" + players[PID]["user"]))

                time.sleep(0.1)

events.event(on_set)
events2.event(on_set)

#events.start(thread=True, update_interval=0.02)
events2.start(thread=True)

threading.Thread(target=send_names_task).start()

conn = session.connect_cloud(PROJECT_ID)

i = 0

while True:
    while len(players) == 0:
        time.sleep(0.1)
    send_to_project = ""
    currentdata = list(players.values())
    for possible_PID in possible_PIDs:
        data = list(filter(lambda x : x["PID"] == possible_PID, currentdata))
        if len(data) == 0:
            send_to_project += "9"*8
        else:
            if data[0]["last_activity"] + LEAVE_TIMEOUT < time.time():
                print(data[0]["user"], f"left (PID {data[0]['PID']}).")
                given_PIDs.remove(data[0]["PID"])
                players.pop(list(filter(lambda x : players[x]["PID"] == possible_PID, list(players.keys())))[0])
                send_to_project += "9"*8
                continue
            for activity in data[0]["activity"]:
                while len(activity) < 4:
                    activity = "0" + activity
                send_to_project += activity

    i += 1
    if i == 10:
        i = 0

    try:
        conn.set_var("MULTIPLAYER_HOST", "9"+send_to_project+"9"+str(i))
    except Exception:
        conn = session.connect_cloud(PROJECT_ID)
        conn.set_var("MULTIPLAYER_HOST", "9"+send_to_project+"9"+str(i))
    time.sleep(0.1)

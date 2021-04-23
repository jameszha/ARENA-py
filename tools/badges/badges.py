# badges.py
#
# Application responds to users in the scene and updates the user avatar with name and badge updates.
import argparse
import csv
import io
import json

import requests
from arena import *

BROKER = "arenaxr.org"
REALM = "realm"
SCENE = "badges-example"
ALLUSERS = {}  # static list by username
ACTUSERS = {}  # actual users by camera id
HEADERS = ["Username", "Name", "Role"]


def init_args():
    global ALLUSERS
    parser = argparse.ArgumentParser(
        description="ARENA badges manager example.")
    parser.add_argument(
        "-u", "--userfile", type=str, help="CSV delimited user list")
    args = parser.parse_args()
    print(args)

    read_online_user_state(args.userfile)
    print(ALLUSERS)


def read_online_user_state(url):
    req = requests.get(url)
    buff = io.StringIO(req.text)
    reader = csv.DictReader(buff)
    for row in reader:
        key = row["Username"]
        ALLUSERS[key] = row


def read_local_user_state(file):
    reader = csv.DictReader(open(file))
    for row in reader:
        key = row["Username"]
        ALLUSERS[key] = row


def write_local_user_state(file):
    fstr = open(file, 'w')
    with fstr:
        writer = csv.DictWriter(fstr, fieldnames=HEADERS)
        writer.writeheader()
        for row in ALLUSERS:
            writer.writerow(ALLUSERS[row])


def scene_callback(scene, obj, msg):
    global ACTUSERS
    # TODO: TBD
    return


def user_join_callback(scene, obj, msg):
    global ACTUSERS
    cam_id = obj.object_id
    username = obj.object_id[18:]
    print(username)
    # Add our version of local avatar objects to actual users dict
    text_id = f"headtext_{cam_id}"
    #model_id = f"head-model_{cam_id}"
    #mute_id = f"muted_{cam_id}"
    ht_obj = Text(object_id=text_id, parent=cam_id,
                  text=f"{obj.displayName} ({username})")
    print(f"{cam_id} headtext stored as '{ht_obj.data.text}'")
    if cam_id not in ACTUSERS:
        ACTUSERS[cam_id] = {"headtext": ht_obj}
    # publish all overrides so new users will see them
    for user in ACTUSERS:
        scene.update_object(ACTUSERS[user]["headtext"])
        print(f"{user} headtext published")
    return


def user_left_callback(scene, obj, msg):
    # TODO: TBD
    return


def end_program_callback(scene, obj, msg):
    # TODO: TBD
    return


# parse args and wait for events
init_args()
kwargs = {}
scene = Scene(
    host=BROKER,
    realm=REALM,
    scene=SCENE,
    on_msg_callback=scene_callback,
    user_join_callback=user_join_callback,
    user_left_callback=user_left_callback,
    end_program_callback=end_program_callback,
    **kwargs)
scene.run_tasks()

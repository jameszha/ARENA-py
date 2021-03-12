# pm.py
#
# ARENA Program Manager

# pylint: disable=missing-docstring


# parse args and wait for events
init_args()
random.seed()
kwargs = {}
if PORT:
    kwargs["port"] = PORT
if NAMESPACE:
    kwargs["namespace"] = NAMESPACE
if DEBUG:
    kwargs["debug"] = DEBUG
scene = Scene(
    host=BROKER,
    realm=REALM,
    scene=SCENE,
    on_msg_callback=scene_callback,
    **kwargs)
scene.run_tasks()

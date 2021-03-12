# arpanel.py
#
# AR Panel Library
# Utility classes and methods for AR Panel.

# pylint: disable=missing-docstring

import enum
import math
from arena import (Box, Color, Cylinder, Material, Object, Position, Rotation,
                   Scale, Scene, Text)

PANEL_RADIUS = 1  # meters
LOCK_XOFF = 0  # quaternion vector
LOCK_YOFF = 0.7  # quaternion vector
CLR_BUTTON = Color(200, 200, 200)  # white-ish
CLR_BUTTON_DISABLED = Color(128, 128, 128)  # gray
CLR_BUTTON_TEXT = Color(0, 0, 0)  # black
OPC_BUTTON = 0.1  # % opacity
OPC_BUTTON_HOVER = 0.25  # % opacity
CLR_SELECT = Color(255, 255, 0)  # yellow

EVT_MOUSEENTER = "mouseenter"
EVT_MOUSELEAVE = "mouseleave"
EVT_MOUSEDOWN = "mousedown"
EVT_MOUSEUP = "mouseup"


class ButtonType(enum.Enum):
    ACTION = "action"
    TOGGLE = "toggle"


class User:
    def __init__(self, scene: Scene, camname, panel_callback):
        self.scene = scene
        self.camname = camname
        self.locky = LOCK_YOFF
        self.lockx = LOCK_XOFF

        # AR Control Panel
        self.follow_lock = False
        self.follow = Box(
            object_id=f"follow_{camname}",
            parent=camname,
            material=Material(transparent=True, opacity=0),
            position=Position(0, 0, -PANEL_RADIUS * 0.1),
            scale=Scale(0.1, 0.01, 0.1),
            rotation=Rotation(0.7, 0, 0, 0.7),
        )
        self.scene.add_object(self.follow)
        self.redpill = False
        self.panel = {}  # button dictionary
        followname = self.follow.object_id
        self.dbuttons = {}
        buttons = [
            ["arb", 0, 0, True, ButtonType.TOGGLE],
            ["avatar", 1, 0, True, ButtonType.TOGGLE],
        ]
        for but in buttons:
            pbutton = Button(
                scene, camname, but[0], but[1], but[2], enable=but[3], btype=but[4],
                parent=followname, callback=panel_callback)
            self.panel[pbutton.button.object_id] = pbutton


class Button:
    def __init__(self, scene: Scene, camname, mode, x=0, y=0, label="", parent=None,
                 drop=None, color=CLR_BUTTON, enable=True, callback=None,
                 btype=ButtonType.ACTION):
        self.scene = scene
        if label == "":
            label = mode.value
        if parent is None:
            parent = camname
            scale = Scale(0.1, 0.1, 0.01)
        else:
            scale = Scale(1, 1, 1)
        self.type = btype
        self.enabled = enable
        if enable:
            self.colorbut = color
        else:
            self.colorbut = CLR_BUTTON_DISABLED
        self.colortxt = CLR_BUTTON_TEXT
        if len(label) > 8:  # easier to read
            self.label = f"{label[:6]}..."
        else:
            self.label = label
        self.mode = mode
        self.dropdown = drop
        self.active = False
        if drop is None:
            obj_name = f"{camname}_button_{mode.value}"
        else:
            obj_name = f"{camname}_button_{mode.value}_{drop}"
        shape = Box.object_type
        if btype == ButtonType.TOGGLE:
            shape = Cylinder.object_type
            scale = Scale(scale.x / 2, scale.y, scale.z / 2)
        self.button = Object(  # box is main button
            object_id=obj_name,
            object_type=shape,
            parent=parent,
            material=Material(
                color=self.colorbut,
                transparent=True,
                opacity=OPC_BUTTON,
                shader="flat"),
            position=Position(x * 1.1, PANEL_RADIUS, y * -1.1),
            scale=scale,
            clickable=True,
            evt_handler=callback,
        )
        scene.add_object(self.button)
        scale = Scale(1, 1, 1)
        if btype == ButtonType.TOGGLE:
            scale = Scale(scale.x * 2, scale.y * 2, scale.z)
        self.text = Text(  # text child of button
            object_id=f"{self.button.object_id}_text",
            parent=self.button.object_id,
            text=self.label,
            # position inside to prevent ray events
            position=Position(0, -0.1, 0),
            rotation=Rotation(-0.7, 0, 0, 0.7),
            scale=scale,
            color=self.colortxt,
        )
        scene.add_object(self.text)

    def set_active(self, active):
        self.active = active
        if active:
            self.scene.update_object(
                self.button, material=Material(color=CLR_SELECT))
        else:
            self.scene.update_object(
                self.button, material=Material(color=CLR_BUTTON))
            self.scene.update_object(
                self.text, material=Material(color=self.colortxt))

    def set_hover(self, hover):
        if hover:
            opacity = OPC_BUTTON_HOVER
        else:
            opacity = OPC_BUTTON
        self.scene.update_object(
            self.button,
            material=Material(transparent=True, opacity=opacity, shader="flat"))

    def delete(self):
        """Delete method so that child text object also gets deleted."""
        self.scene.delete_object(self.text)
        self.scene.delete_object(self.button)


def handle_panel_event(event, dropdown=False):
    # naming order: camera_number_name_button_bname_dname
    drop = None
    obj = event.object_id.split("_")
    camname = event.data.source
    owner = f"{obj[0]}_{obj[1]}_{obj[2]}"  # callback owner in object_id
    if owner != camname:
        return None, None, None  # only owner may activate
    objid = event.object_id
    if event.type == EVT_MOUSEENTER or event.type == EVT_MOUSELEAVE:
        if event.type == EVT_MOUSEENTER:
            hover = True
        elif event.type == EVT_MOUSELEAVE:
            hover = False
        if dropdown:
            button = USERS[camname].dbuttons[objid].set_hover(hover)
        else:
            button = USERS[camname].panel[objid].set_hover(hover)

    if event.type != EVT_MOUSEDOWN:
        return None, None, None
    if dropdown:
        drop = obj[5]
    return (camname, objid, drop)


def panel_callback(_scene, event, msg):
    camname, objid, drop = handle_panel_event(event)
    if not camname or not objid:
        return
    # ignore disabled
    if not USERS[camname].panel[objid].enabled:
        return

    mode = USERS[camname].panel[objid].mode
    btype = USERS[camname].panel[objid].type
    if btype == ButtonType.TOGGLE:
        USERS[camname].panel[objid].set_active(
            not USERS[camname].panel[objid].active)
    else:
        if mode == USERS[camname].mode:  # action cancel
            # button click is same, then goes off and NONE
            USERS[camname].panel[objid].set_active(False)
            USERS[camname].mode = Mode.NONE
            mode = Mode.NONE
        else:
            # if button goes on, last button must go off
            prev_objid = f"{camname}_button_{USERS[camname].mode.value}"
            if prev_objid in USERS[camname].panel:
                USERS[camname].panel[prev_objid].set_active(False)
            USERS[camname].panel[objid].set_active(True)
            USERS[camname].mode = mode
        USERS[camname].set_textleft(USERS[camname].mode)
        USERS[camname].set_textright("")
        USERS[camname].del_clipboard()
        # clear last dropdown
        for but in USERS[camname].dbuttons:
            USERS[camname].dbuttons[but].delete()
        USERS[camname].dbuttons.clear()

    active = USERS[camname].panel[objid].active
    # handle buttons
    if mode == Mode.LOCK:
        USERS[camname].follow_lock = active
        # TODO: after lock ensure original ray keeps lock button in reticle


def update_dropdown(camname, objid, mode, options, row, callback):
    # show new dropdown
    if USERS[camname].panel[objid].active:
        followname = USERS[camname].follow.object_id
        maxwidth = min(len(options), 10)
        drop_button_offset = -math.floor(maxwidth / 2)
        for i, option in enumerate(options):
            if mode is Mode.COLOR:
                bcolor = Color(option)
            else:
                bcolor = CLR_SELECT
            dbutton = Button(
                scene, camname, mode, (i % maxwidth) + drop_button_offset, row,
                label=option, parent=followname, color=bcolor, drop=option, callback=callback)
            USERS[camname].dbuttons[dbutton.button.object_id] = dbutton
            if (i + 1) % maxwidth == 0:  # next row
                if row < 0:
                    row -= 1
                else:
                    row += 1
        # make default selection
        if mode is Mode.COLOR:
            rcolor = Color(options[0])
        else:
            rcolor = CLR_HUDTEXT
        USERS[camname].set_textright(options[0], color=rcolor)
        USERS[camname].target_style = options[0]


def scene_callback(_scene, event, msg):
    # This is the MQTT message callback function for the scene
    object_id = action = msg_type = object_type = None
    if "object_id" in msg:
        object_id = msg["object_id"]
    if "action" in msg:
        action = msg["action"]
    if "type" in msg:
        msg_type = msg["type"]
    if "data" in msg and "object_type" in msg["data"]:
        object_type = msg["data"]["object_type"]
    # print(f'{object_type} {action} {msg_type} {object_id}')

    if object_type == "camera":
        # camera updates define users present
        camname = object_id
        if camname not in USERS:
            USERS[camname] = User(scene, camname, panel_callback)

        # save camera's attitude in the world
        USERS[camname].position = Position(msg["data"]["position"]["x"],
                                           msg["data"]["position"]["y"],
                                           msg["data"]["position"]["z"])
        USERS[camname].rotation = Rotation(msg["data"]["rotation"]["x"],
                                           msg["data"]["rotation"]["y"],
                                           msg["data"]["rotation"]["z"],
                                           msg["data"]["rotation"]["w"])

        rx = msg["data"]["rotation"]["x"]
        ry = msg["data"]["rotation"]["y"]

        # floating controller
        if not USERS[camname].follow_lock:
            ty = -(ry + USERS[camname].locky) / 0.7 * math.pi / 2
            tx = -(rx + USERS[camname].lockx) / 0.7 * math.pi / 2
            px = PANEL_RADIUS * -math.cos(ty)
            py = PANEL_RADIUS * math.sin(tx)
            pz = PANEL_RADIUS * math.sin(ty)
            scene.update_object(USERS[camname].follow,
                                position=Position(px, py, pz))
        # else: # TODO: panel lock position drop is inaccurate
            # users[camname].lockx = rx + LOCK_XOFF
            # users[camname].locky = -(ry * math.pi) - LOCK_YOFF

    # mouse event
    elif action == "clientEvent":
        object_id = msg["object_id"]
        # camera updates define users present
        camname = msg["data"]["source"]
        if camname not in USERS:
            USERS[camname] = User(scene, camname, panel_callback)

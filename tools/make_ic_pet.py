"""Draws the desktop-pet chips and writes each as an eSheep animation file.

    python tools/make_ic_pet.py

For each chip in CHIPS this writes assets/pets/<name>.xml (sprite sheet + animations, loaded by
assets/js/pets.js) and tools/<name>-preview.png (every frame, enlarged and named, for checking the drawing).
It also writes assets/pets/ic555-icon.png, the standing 555 used as the release button, and the site's
favicon (a chip marked "JRL", seen from above): favicon.ico (16/32/48), assets/favicon-16.png, assets/favicon-32.png, apple-touch-icon.png.

  ic555   an 8-pin 555 timer, the main pet
  hc139   a 16-pin 74HC139 (the decoder on the home page), released now and then; walks like a millipede

Each chip is drawn from four sides, like the eSheep turning its body:
  side profile  the long side of the package, its legs, the marking, one eye at the front end (walking)
  front         the pin-1 end: notch on top, two eyes, one pin from each row as two gull-wing legs
  back          the other end: no notch, no eyes, a round mold mark
  top           seen from above, all pins, notch, pin-1 dot and marking (tumbling in a fall, and
                mid-roll when it's lying on its side)
  dead bug      the side profile upside down, legs in the air. After a crash it lies there smoking, and now
                and then it plays dead on purpose. It gets up by rocking, then rolling over its long side
                (legs tip away, top face showing, legs swing under) and landing upright.

Frames are drawn on a small pixel grid and scaled up by SCALE with no smoothing. There are separate
left- and right-facing side frames instead of letting eSheep mirror the sprite, because mirroring
would print the marking backwards.
"""
import base64
import io
import os

from PIL import Image, ImageDraw

CHIPS = {
    "ic555": dict(label="555", pins=4, title="555",
                  info="A 555 timer that wanders around. Occasionally lets out the magic smoke."),
    "hc139": dict(label="HC139", pins=8, title="74HC139",
                  info="The decoder from the home page, out for a walk on all sixteen legs."),
}

H, SCALE = 22, 2                 # pixel grid height per frame, and how much it's enlarged on the page
TILES_X = 8                      # frames per row in the sprite sheet
EYES = True                      # draw the eyes
MARKING = True                   # print the part number on the package
FAR_LEGS = True                 # also draw the far row of legs (darker, between the near ones). Off: each leg's
                                 # dark shoulder pixel sits beside its bent light leg, which hints at depth instead
GROUND = 19                      # row the feet stand on

INK = (28, 28, 30, 255)          # chip body
HI = (58, 58, 64, 255)           # top highlight of the body
SH = (14, 14, 16, 255)           # bottom shadow and mold mark
CUT = (0, 0, 0, 0)               # cut out of the body: the pin-1 notch shows the background through it
PIN = (201, 201, 201, 255)       # tinned pins
PIN_SH = (140, 140, 140, 255)
FAR_PIN = (112, 112, 116, 255)   # the far row of legs, seen between the near ones: darker, as it's in shadow
FAR_SHORTER = 0                  # px shorter than the near legs when upright (1 puts the far feet higher, for
DEAD_FAR_SHORTER = 1             # perspective), and when lying on its back as a dead bug
TEXT = (150, 150, 156, 255)      # marking: faint gray, like real laser marking, so the eyes stand out
DOT = (90, 90, 96, 255)          # pin-1 dot
EYE = (255, 255, 255, 255)
PUPIL = (17, 17, 17, 255)
Z = (128, 128, 134, 255)         # sleeping z's: mid gray, visible on white paper and the green page
SMOKE = (150, 150, 155, 235)
SMOKE_DK = (110, 110, 115, 220)

# 3x5 glyphs
FONT = {
    "1": ["010", "110", "010", "010", "111"],
    "3": ["111", "001", "011", "001", "111"],
    "5": ["111", "100", "111", "001", "111"],
    "9": ["111", "101", "111", "001", "111"],
    "C": ["011", "100", "100", "100", "011"],
    "H": ["101", "101", "111", "101", "101"],
    "z": ["111", "001", "010", "100", "111"],
}


def spread(a, b, n):
    """n evenly spaced columns from a to b."""
    return [round(a + (b - a) * i / (n - 1)) for i in range(n)]


class Chip:
    """The geometry of one chip, derived from its pin count."""

    def __init__(self, label, pins, **_):
        self.label = label
        self.pins = pins                                  # pins per side
        self.W = 28 if pins <= 4 else 40                  # frame width
        self.side_x0, self.side_x1 = 2, self.W - 3        # side profile spans these columns
        # legs on an even whole-pixel pitch (6 px on the 555, 4 on the 139), so neighbours never crowd
        self.end_x0, self.end_x1 = self.W // 2 - 7, self.W // 2 + 6   # front/back view
        self.dx = (self.W - 28) // 2                      # shift for decorations drawn for the 28-wide 555
        self.text_w = len(label) * 4 - 1
        # Both walk with an insect's ripple gait: legs lift in a wave running from back to front over 4 frames.
        # (Lifting diagonal pairs, as the 555 first did, is a trot and made it look like a four-legged animal.)
        self.walk_steps = 4
        self.lift = 1 if pins <= 4 else 2                 # legs in the air at once
        self.bob = pins > 4                               # the 139 bobs a little; the 555 glides level, like a bug
        self.walk_dx, self.walk_ms = (-2, 120) if pins <= 4 else (-3, 170)   # px per step and ms per step
        self.splay = 1                                    # how far the legs bend out
        # Leg spacing: the widest whole-pixel pitch that leaves at least 2 px of body overhanging at each end,
        # counting the bend and the far row, with all the visible legs centred under the body. (The 139 has to
        # keep a 4 px pitch, so its overhang is a pixel less.)
        room = self.side_x1 - self.side_x0 - 2 * (2 + self.splay)
        def span(p):
            return (pins - 1) * p + (p // 2 if FAR_LEGS else 0)
        pitch = next(p for p in range(8, 1, -1) if span(p) <= room)
        if pins > 4:
            pitch = max(pitch, 4)
        self.far_dx = pitch // 2                          # the far row sits halfway between the near legs
        start = self.side_x0 + (self.side_x1 - self.side_x0 - span(pitch)) // 2
        self.pin_xs = [start + i * pitch for i in range(pins)]


# ---------------------------------------------------------------- drawing helpers
def new(c):
    return Image.new("RGBA", (c.W, H), (0, 0, 0, 0))


def px(img, x, y, col):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), col)


def rect(img, x0, y0, x1, y1, col):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            px(img, x, y, col)


def glyph(img, ch, x, y, col):
    for r, row in enumerate(FONT[ch]):
        for k, bit in enumerate(row):
            if bit == "1":
                px(img, x + k, y + r, col)


def marking(img, c, x0, y):
    if MARKING:
        for i, ch in enumerate(c.label):
            glyph(img, ch, x0 + i * 4, y, TEXT)


def slab(img, x0, x1, top, height):
    """A block of black epoxy with a highlight on top and a shadow underneath."""
    bottom = top + height - 1
    rect(img, x0, top, x1, bottom, INK)
    rect(img, x0 + 1, top, x1 - 1, top, HI)
    rect(img, x0, bottom, x1, bottom, SH)
    return bottom


def eye(img, ex, y, look=0, state="open"):
    """One 3x3 eye with its top-left at (ex, y). look: -1 left, 1 right, 0 at you.
    state: open, closed, wide, x."""
    if not EYES:
        return
    if state == "closed":
        rect(img, ex, y + 1, ex + 2, y + 1, EYE)
    elif state == "wide":
        rect(img, ex, y - 1, ex + 2, y + 2, EYE)
        px(img, ex + 1, y + 1, PUPIL)
    elif state == "x":
        for d in range(3):
            px(img, ex + d, y + d, EYE)
            px(img, ex + 2 - d, y + d, EYE)
    else:
        rect(img, ex, y, ex + 2, y + 2, EYE)
        if look < 0:
            rect(img, ex, y + 1, ex, y + 2, PUPIL)
        elif look > 0:
            rect(img, ex + 2, y + 1, ex + 2, y + 2, PUPIL)
        else:
            px(img, ex + 1, y + 1, PUPIL)


def puff(img, x, y):
    """A small round puff of smoke (3x3 without corners)."""
    rect(img, x, y + 1, x + 2, y + 1, SMOKE)
    px(img, x + 1, y, SMOKE)
    px(img, x + 1, y + 2, SMOKE_DK)


# ---------------------------------------------------------------- side profile
def side_pin(img, x, y0, length=4, knee=0, col=PIN, shoulder=PIN_SH):
    """One lead coming out of the body and bending down, like an insect leg: the shoulder where it leaves
    the package, a diagonal out to the knee, then straight down. knee: how far (and which way) the lower leg
    sits from the shoulder, negative for left."""
    px(img, x, y0, shoulder)
    step = (knee > 0) - (knee < 0)
    for i in range(1, length):
        px(img, x + (step if i == 1 else knee), y0 + i, col)


def splayed(c, face, length=4):
    """Standing legs, splayed like a beetle's: the front half reach forward, the back half reach back."""
    front = (lambda i: i < c.pins / 2) if face < 0 else (lambda i: i >= c.pins / 2)
    return [(length, (face if front(i) else -face) * c.splay) for i in range(c.pins)]


def side(img, c, face=-1, top=6, eye_state="open", look=None, legs=None, far=None, far_shorter=None):
    """The long side of the package, walking toward `face` (-1 left, 1 right). One eye at the front end,
    the marking behind it. legs: per pin (length, knee); standing splayed if not given. far: the same for the
    far row (drawn first, darker and a pixel shorter, between the near legs); defaults to matching the near row."""
    near = legs or splayed(c, face)
    for x, (length, knee) in zip(c.pin_xs, far or near):
        if FAR_LEGS and length > 1:
            side_pin(img, x + c.far_dx, top + 10,
                     length - (FAR_SHORTER if far_shorter is None else far_shorter), knee, FAR_PIN, FAR_PIN)
    slab(img, c.side_x0, c.side_x1, top, 10)
    row = top + 3
    px(img, c.side_x0 + 1 if face < 0 else c.side_x1 - 1, top + 1, DOT)   # pin-1 dot at the front end
    if EYES:
        x0 = c.side_x1 - 1 - c.text_w if face < 0 else c.side_x0 + 2
    else:
        x0 = (c.side_x0 + c.side_x1 + 1 - c.text_w) // 2
    marking(img, c, x0, row)
    eye(img, c.side_x0 + 2 if face < 0 else c.side_x1 - 4, row, face if look is None else look, eye_state)
    for x, (length, knee) in zip(c.pin_xs, near):
        side_pin(img, x, top + 10, length, knee)


def frame_walk(c, step, face=-1):
    """One step of the ripple gait: the lifted leg(s) move one place toward the front each step.
    A lifted leg reaches forward; a planted one pushes back."""
    img = new(c)
    bob = step % 2 if c.bob else 0
    up, down = (3, face * c.splay), (4, -face * c.splay)
    def row(phase):
        return [(l + bob, d) for l, d in (up if (i - phase * face) % 4 < c.lift else down for i in range(c.pins))]
    # the far row steps half a cycle behind the near row, like an insect's left and right legs alternating
    side(img, c, face, top=6 - bob, legs=row(step), far=row(step + 2))
    return img


def frame_side(c, state="open", face=-1):
    img = new(c)
    side(img, c, face, eye_state=state)
    return img


def frame_greet(c, face=-1):
    """Meeting another chip: the front leg lifts and reaches out toward it, like ants touching antennae."""
    img = new(c)
    legs = splayed(c, face)
    front = 0 if face < 0 else c.pins - 1
    legs[front] = (2, face * (c.splay + 1))
    side(img, c, face, legs=legs)
    return img


def frame_sleep(c, z):
    img = frame_side(c, "closed")
    zx, zy = [(16, 1), (19, 0), (22, 0)][z]      # a z drifting up and away
    glyph(img, "z", zx + 2 * c.dx, zy, Z)
    return img


def frame_smoke(c, n):
    img = frame_side(c, "x")
    # the magic smoke escaping from the top of the package
    for (sx, sy) in [[(17, 3)], [(16, 2), (20, 0)], [(15, 1), (19, 2), (22, 0)]][n]:
        puff(img, sx + c.dx, sy)
    return img


# ---------------------------------------------------------------- front and back (the ends of the package)
# Leg shapes for the end views, as (outward, down) steps from the shoulder where the pin leaves the body.
def legs_stand(shoulder):
    return [(0, 0), (1, 0)] + [(1, d) for d in range(1, GROUND - shoulder + 1)]


LEGS_UP = [(0, 0), (1, 0), (1, -1), (1, -2), (1, -3), (2, -4)]              # flailing up
LEGS_OUT = [(0, 0), (1, 1), (2, 2), (3, 3), (3, 4)]                         # flung out sideways
LEGS_SPLAY = [(0, 0), (1, 1), (2, 2), (3, 3), (3, 4), (3, 5), (3, 6)]       # squashed flat on landing
LEGS_DANGLE = [(0, 0), (1, 0)] + [(1, d) for d in range(1, 7)]              # hanging while dragged
LEGS_DANGLE_IN = [(0, 0), (1, 0)] + [(1, d) for d in range(1, 5)] + [(0, 5), (0, 6)]


def end(img, c, front=True, top=6, height=10, eye_state="open", legs=None):
    """The package seen end-on. The front end has the pin-1 notch and the face; the back end has a mold mark."""
    slab(img, c.end_x0, c.end_x1, top, height)
    mid = (c.end_x0 + c.end_x1) // 2
    shoulder = top + height // 2
    if front:
        rect(img, mid - 1, top, mid + 2, top, CUT)       # notch: a half-moon dent in the top edge
        rect(img, mid, top + 1, mid + 1, top + 1, CUT)
        eye(img, c.end_x0 + 2, top + 3, 0, eye_state)
        eye(img, c.end_x1 - 4, top + 3, 0, eye_state)
    else:
        rect(img, mid, top + 4, mid + 1, top + 5, SH)    # round ejector-pin mark
    for out, down in legs or legs_stand(shoulder):
        px(img, c.end_x0 - 1 - out, shoulder + down, PIN)
        px(img, c.end_x1 + 1 + out, shoulder + down, PIN)


def frame_end(c, front=True, state="open", legs=None, top=6, height=10):
    img = new(c)
    end(img, c, front, top, height, state, legs)
    return img


# ---------------------------------------------------------------- top view (tumbling)
def frame_top(c):
    img = new(c)
    x0, x1, y0, y1 = 4, c.W - 5, 7, 15
    rect(img, x0, y0, x1, y1, INK)
    rect(img, x0, y0, x1, y0, HI)
    rect(img, x0, y1, x1, y1, SH)
    rect(img, x0, y0 + 3, x0, y1 - 3, CUT)               # notch on the pin-1 end
    rect(img, x0 + 1, y0 + 4, x0 + 1, y1 - 4, CUT)
    px(img, x0 + 2, y1 - 2, DOT)                        # pin-1 dot
    for x in spread(x0 + 3, x1 - 3, c.pins):           # pins along each long side
        rect(img, x, y0 - 2, x, y0 - 1, PIN)
        rect(img, x, y1 + 1, x, y1 + 2, PIN)
    marking(img, c, (x0 + x1 + 1 - c.text_w) // 2, y0 + 2)
    return img


# ---------------------------------------------------------------- dead bug, and getting back up
def grounded(img):
    """Move a drawing straight down so its lowest pixel sits on the ground row."""
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.paste(img, (0, GROUND - (img.getbbox()[3] - 1)))
    return out


def upside_down(c, face, eye_state, legs):
    """The side profile on its back. It's drawn facing the other way first, because turning it over
    (a 180 degree rotation) swaps the ends, so the eye ends up at the `face` end."""
    img = new(c)
    side(img, c, -face, eye_state=eye_state, legs=legs, far_shorter=DEAD_FAR_SHORTER)
    return grounded(img.rotate(180))


def frame_dead(c, face=-1, eye_state="x", twitch=0, legs=None):
    """A "dead bug": on its back, legs in the air. twitch 1 and 2 bend alternate legs."""
    if legs:
        return upside_down(c, face, eye_state, legs)
    if twitch:
        legs = [(3, -face) if (i + twitch) % 2 else (4, 0) for i in range(c.pins)]
    else:
        legs = [(4, 0)] * c.pins
    return upside_down(c, face, eye_state, legs)


def frame_dead_smoke(c, n, face=-1):
    img = frame_dead(c, face)
    for (sx, sy) in [[(13, 2)], [(11, 1), (15, 2)], [(10, 0), (14, 1), (17, 0)]][n]:
        puff(img, sx + c.dx, sy)
    return img


def shifted(img, dx):
    """Slide a drawing sideways by dx pixels."""
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.paste(img, (dx, 0))
    return out


def frame_rock(c, face, side_):
    """Rocking on its back to build momentum: every leg kicks the same way and the body jiggles the other.
    (Tilting the body reads as a broken, stepped chip at this pixel size, so the motion is in the legs.)"""
    legs = [(4, side_)] * c.pins
    return shifted(frame_dead(c, face, "wide", legs=legs), side_)


def frame_roll(c, stage, face=-1):
    """Rolling over the long side to get up. 1: legs tipping away (foreshortened); 3: legs swinging back
    under it. Stage 2, lying on its side, is the top view (frame "on side")."""
    if stage == 1:
        return upside_down(c, face, "wide", [(2, 0)] * c.pins)
    img = new(c)
    side(img, c, face, top=8, eye_state="wide", legs=[(2, 0)] * c.pins)
    return grounded(img)


def frame_up(c, face=-1):
    """Back on its feet, still squashed from the roll."""
    img = new(c)
    side(img, c, face, top=7, eye_state="closed", legs=splayed(c, face, 3))
    return grounded(img)


# ---------------------------------------------------------------- frames and animations
def build(c):
    """Returns (frames, names, anims). Animations refer to frames by name."""
    F = {}
    for s in range(c.walk_steps):
        F[f"walk L{s}"] = frame_walk(c, s)
    F["side L"] = frame_side(c)                          # standing, facing left (also the 555's button icon)
    F["side L blink"] = frame_side(c, "closed")
    for z in range(3):
        F[f"sleep {z}"] = frame_sleep(c, z)
    for n in range(3):
        F[f"smoke {n}"] = frame_smoke(c, n)
    for s in range(c.walk_steps):
        F[f"walk R{s}"] = frame_walk(c, s, face=1)
    F["side R"] = frame_side(c, face=1)
    F["side R blink"] = frame_side(c, "closed", face=1)
    F["greet L"] = frame_greet(c, -1)
    F["greet R"] = frame_greet(c, 1)
    F["front"] = frame_end(c)                            # looking at you
    F["front blink"] = frame_end(c, state="closed")
    F["front wide"] = frame_end(c, state="wide")         # surprised
    F["fall up"] = frame_end(c, state="wide", legs=LEGS_UP, top=5)
    F["fall out"] = frame_end(c, state="wide", legs=LEGS_OUT, top=5)
    F["landed"] = frame_end(c, state="closed", legs=LEGS_SPLAY, top=8, height=9)
    F["drag"] = frame_end(c, state="wide", legs=LEGS_DANGLE, top=3)
    F["drag in"] = frame_end(c, state="wide", legs=LEGS_DANGLE_IN, top=3)
    F["back"] = frame_end(c, front=False)                # looking away
    F["back fall"] = frame_end(c, front=False, legs=LEGS_UP, top=5)
    F["top"] = frame_top(c)                              # tumbling
    F["on side"] = grounded(frame_top(c))                # mid-roll, lying on its side
    for face, S in ((-1, "L"), (1, "R")):
        for t in range(3):
            F[f"dead {S} {t}"] = frame_dead(c, face, twitch=t)          # X eyes, legs twitching
        for n in range(3):
            F[f"dead {S} smoke {n}"] = frame_dead_smoke(c, n, face)
        F[f"dead {S} closed"] = frame_dead(c, face, "closed")           # playing dead
        F[f"dead {S} closed twitch"] = frame_dead(c, face, "closed", twitch=1)
        F[f"dead {S} peek"] = frame_dead(c, face, "open")                # checking if anyone's looking
        F[f"dead {S} wide"] = frame_dead(c, face, "wide")
        F[f"rock {S} a"] = frame_rock(c, face, 1)
        F[f"rock {S} b"] = frame_rock(c, face, -1)
        F[f"roll {S} 1"] = frame_roll(c, 1, face)
        F[f"roll {S} 3"] = frame_roll(c, 3, face)
        F[f"up {S}"] = frame_up(c, face)

    walk_l = [f"walk L{s}" for s in range(c.walk_steps)]
    walk_r = [f"walk R{s}" for s in range(c.walk_steps)]
    walk_repeat = 12 // c.walk_steps      # short walks: bugs move in bursts
    tumble = ["fall up", "top", "back fall", "top"]
    EITHER_WAY = {"walk left": 50, "walk right": 50}
    FALL = {"fall": 60, "tumble": 40}
    # x/y are pixels moved per step; "next" lists what can come after, with odds. border: what to do at a
    # screen edge or the end of what it's walking on. gravity: what to do with nothing underneath.
    # Rough handling: a fall starts in "fall" or "tumble". If it's still falling after about 290 px it switches
    # to "fall far" / "tumble far", and hitting the ground from those is a crash (flips onto its back and smokes).
    # Steps in a sequence = frames + frames * repeat, and the speed ramps from 2 to 12 px per step, so
    # fall: 2 + 2*20 = 42 steps, tumble: 4 + 4*10 = 44 steps, both roughly 290 px.
    anims = {
        "walk left": dict(x=c.walk_dx, y=0, interval=c.walk_ms, frames=walk_l, repeat=walk_repeat,
                          next={"walk left": 30, "scurry left": 20, "freeze left": 15, "idle left": 10, "turn to the right": 12,
                                "sleep": 5, "magic smoke": 4,
                                "play dead left": 3},
                          border={"turn to the right": 100}, gravity=FALL),
        # bug-like stop-and-go: a quick dash, then freezing in place for a random moment
        "scurry left": dict(x=-7, y=0, interval=60, frames=walk_l, repeat=12 // c.walk_steps,
            next={"freeze left": 60, "scurry left": 10, "walk left": 15, "turn to the right": 15},
            border={"turn to the right": 100}, gravity=FALL),
        "freeze left": dict(x=0, y=0, interval=220, frames=["side L", "side L"], repeat="random/40",
            next={"scurry left": 35, "walk left": 35, "turn to the right": 30}, gravity=FALL),
        # running from the cursor (started by assets/js/pets.js): fast, then a freeze
        "flee left": dict(x=-10, y=0, interval=45, frames=walk_l, repeat=16 // c.walk_steps,
            next={"freeze left": 100}, border={"turn to the right": 100}, gravity=FALL),
        # meeting another chip face to face (started by assets/js/pets.js): reach out, pause, turn back
        "meet left": dict(x=0, y=0, interval=200,
            frames=["side L", "greet L", "side L", "greet L", "side L", "side L blink", "side L"], repeat=0,
            next={"turn to the right": 100}, gravity=FALL),
        "turn to the right": dict(x=0, y=0, interval=170, frames=["side L", "front", "side R"], repeat=0,
                                  next={"walk right": 100}, gravity=FALL),
        "idle left": dict(x=0, y=0, interval=230,
                          frames=["side L", "side L", "side L blink", "side L", "side L", "front", "front",
                                  "front blink", "front", "back", "back", "back", "front", "side L"], repeat=0,
                          next={"walk left": 70, "turn to the right": 30}, gravity=FALL),
        "walk right": dict(x=-c.walk_dx, y=0, interval=c.walk_ms, frames=walk_r, repeat=walk_repeat,
                           next={"walk right": 30, "scurry right": 20, "freeze right": 15, "idle right": 10, "turn to the left": 12,
                                 "sleep": 5, "magic smoke": 4,
                                 "play dead right": 3},
                           border={"turn to the left": 100}, gravity=FALL),
        # bug-like stop-and-go: a quick dash, then freezing in place for a random moment
        "scurry right": dict(x=7, y=0, interval=60, frames=walk_r, repeat=12 // c.walk_steps,
            next={"freeze right": 60, "scurry right": 10, "walk right": 15, "turn to the left": 15},
            border={"turn to the left": 100}, gravity=FALL),
        "freeze right": dict(x=0, y=0, interval=220, frames=["side R", "side R"], repeat="random/40",
            next={"scurry right": 35, "walk right": 35, "turn to the left": 30}, gravity=FALL),
        # running from the cursor (started by assets/js/pets.js): fast, then a freeze
        "flee right": dict(x=10, y=0, interval=45, frames=walk_r, repeat=16 // c.walk_steps,
            next={"freeze right": 100}, border={"turn to the left": 100}, gravity=FALL),
        # meeting another chip face to face (started by assets/js/pets.js): reach out, pause, turn back
        "meet right": dict(x=0, y=0, interval=200,
            frames=["side R", "greet R", "side R", "greet R", "side R", "side R blink", "side R"], repeat=0,
            next={"turn to the left": 100}, gravity=FALL),
        "turn to the left": dict(x=0, y=0, interval=170, frames=["side R", "front", "side L"], repeat=0,
                                 next={"walk left": 100}, gravity=FALL),
        "idle right": dict(x=0, y=0, interval=230,
                           frames=["side R", "side R", "side R blink", "side R", "side R", "front", "front",
                                   "front blink", "front", "back", "back", "back", "front", "side R"], repeat=0,
                           next={"walk right": 70, "turn to the left": 30}, gravity=FALL),
        "drag": dict(x=0, y=0, interval=120, frames=["drag", "drag in"], repeat=0, next=FALL),
        "fall": dict(x=0, y=(2, 12), interval=(70, 40), frames=["fall up", "fall out"], repeat=20,
                     next={"fall far": 100}, border={"land": 100}),
        "fall far": dict(x=0, y=(12, 14), interval=40, frames=["fall up", "fall out"], repeat=30,
                         next={"fall far": 100}, border={"crash": 100}),
        "tumble": dict(x=0, y=(2, 12), interval=(90, 50), frames=tumble, repeat=10,
                       next={"tumble far": 100}, border={"land": 100}),
        "tumble far": dict(x=0, y=(12, 14), interval=50, frames=tumble, repeat=30,
                           next={"tumble far": 100}, border={"crash": 100}),
        "drop in": dict(x=0, y=(2, 12), interval=(90, 50), frames=tumble, repeat=30,
                        next={"drop in": 100}, border={"land": 100}),
        "sleep": dict(x=0, y=0, interval=420, frames=["side L blink", "sleep 0", "sleep 1", "sleep 2"],
                      repeat=8, repeatfrom=1, next={"wake": 100}, gravity=FALL),
        "land": dict(x=0, y=0, interval=140, frames=["landed", "landed", "front wide", "front", "front blink", "front"],
                     repeat=0, next=EITHER_WAY),
        # a crash knocks it straight over: one squashed frame on impact, then it keeps rolling (on its side,
        # legs tipping over, on its back), fast, so it never seems to stand there first
        "crash": dict(x=0, y=0, interval=70, frames=["landed", "on side", "roll L 1"], repeat=0,
                      next={"knocked out": 100}),
        # a dead bug: on its back, legs twitching and smoke rising, until it gets up
        "knocked out": dict(x=0, y=0, interval=200,
                            frames=["dead L 0", "dead L smoke 0", "dead L 1", "dead L smoke 1", "dead L 2",
                                    "dead L smoke 2", "dead L 1", "dead L smoke 1", "dead L 0", "dead L 2", "dead L 0"],
                            repeat=0, next={"get up left": 100}),
        # playing dead on purpose: flops over, lies still, peeks, then gets up
        "play dead left": dict(x=0, y=0, interval=260,
            frames=["side L", "roll L 3", "on side", "roll L 1", "dead L closed", "dead L closed",
                    "dead L closed", "dead L closed twitch", "dead L closed", "dead L closed",
                    "dead L closed", "dead L peek", "dead L peek", "dead L closed", "dead L closed"],
            repeat=0, next={"get up left": 100}, gravity=FALL),
        "play dead right": dict(x=0, y=0, interval=260,
            frames=["side R", "roll R 3", "on side", "roll R 1", "dead R closed", "dead R closed",
                    "dead R closed", "dead R closed twitch", "dead R closed", "dead R closed",
                    "dead R closed", "dead R peek", "dead R peek", "dead R closed", "dead R closed"],
            repeat=0, next={"get up right": 100}, gravity=FALL),
        # getting up: rock to build momentum, roll over the long side (legs tip away, lying on its side,
        # legs swing under), land upright still squashed, blink, carry on
        "get up left": dict(x=0, y=0, interval=160,
            frames=["dead L closed", "dead L closed", "dead L wide", "rock L a", "dead L wide", "rock L b",
                    "dead L wide", "rock L a", "rock L b", "roll L 1", "on side", "roll L 3", "up L",
                    "up L", "side L", "side L blink", "side L"],
            repeat=0, next={"walk left": 70, "turn to the right": 30}, gravity=FALL),
        "get up right": dict(x=0, y=0, interval=160,
            frames=["dead R closed", "dead R closed", "dead R wide", "rock R a", "dead R wide", "rock R b",
                    "dead R wide", "rock R a", "rock R b", "roll R 1", "on side", "roll R 3", "up R",
                    "up R", "side R", "side R blink", "side R"],
            repeat=0, next={"walk right": 70, "turn to the left": 30}, gravity=FALL),
        "wake": dict(x=0, y=0, interval=220, frames=["side L blink", "side L", "front", "front wide", "front"],
                     repeat=0, next=EITHER_WAY),
        # clicked: a startled little hop (up about 10 px and back down), then a wide-eyed look and off it goes.
        # Per-step moves are -6, -3, -1, +1, +4, +6, which ends 1 px below where it started: inside the few-px
        # window where eSheep catches it on the ledge it was standing on (overshoot more and it falls through).
        "poke": dict(x=0, y=(-6, 9), interval=50,
                     frames=["front wide", "fall up", "fall up", "fall up", "fall out", "front wide"], repeat=0,
                     next={"startled": 100}, border={"startled": 100}),
        "startled": dict(x=0, y=0, interval=180, frames=["front wide", "front wide", "front", "front blink", "front"],
                         repeat=0, next=EITHER_WAY, gravity=FALL),
        "magic smoke": dict(x=0, y=0, interval=260,
                            frames=["side L", "smoke 0", "smoke 1", "smoke 2", "smoke 1", "smoke 2", "smoke 0",
                                    "front wide", "front"], repeat=0, next=EITHER_WAY, gravity=FALL),
    }
    names = list(F)
    return [F[n] for n in names], names, anims


SPAWNS = [
    # dropped in from above somewhere across the screen (a gentle entrance that never crashes)
    dict(prob=80, x="random*(screenW-imageW-50)/100+25", y="-imageH-20", next="drop in"),
    # walks in from the right edge along the bottom
    dict(prob=20, x="screenW+10", y="areaH-imageH", next="walk left"),
]


# ---------------------------------------------------------------- output
def sheet(c, frames):
    tiles_y = -(-len(frames) // TILES_X)
    img = Image.new("RGBA", (c.W * TILES_X, H * tiles_y), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        img.paste(f, ((i % TILES_X) * c.W, (i // TILES_X) * H))
    return img.resize((img.width * SCALE, img.height * SCALE), Image.NEAREST), tiles_y


def to_xml(chip, c, frames, names, anims):
    ids = {name: i + 1 for i, name in enumerate(anims)}
    idx = {name: i for i, name in enumerate(names)}

    def nexts(d):
        return "".join(f'\n        <next probability="{p}">{ids[a]}</next>' for a, p in d.items())

    def pair(v):
        return v if isinstance(v, tuple) else (v, v)

    out = []
    for name, a in anims.items():
        (x1, x2), (y1, y2), (i1, i2) = pair(a["x"]), pair(a["y"]), pair(a["interval"])
        fr = "".join(f"\n        <frame>{idx[f]}</frame>" for f in a["frames"])
        x = f"""
    <animation id="{ids[name]}">
      <name>{name}</name>
      <start><x>{x1}</x><y>{y1}</y><interval>{i1}</interval></start>
      <end><x>{x2}</x><y>{y2}</y><interval>{i2}</interval></end>
      <sequence repeat="{a['repeat']}" repeatfrom="{a.get('repeatfrom', 0)}">{fr}{nexts(a['next'])}
      </sequence>"""
        if a.get("border"):
            x += f"\n      <border>{nexts(a['border'])}\n      </border>"
        if a.get("gravity"):
            x += f"\n      <gravity>{nexts(a['gravity'])}\n      </gravity>"
        out.append(x + "\n    </animation>")

    spawns = "".join(f"""
    <spawn id="{i + 1}" probability="{s['prob']}">
      <x>{s['x']}</x>
      <y>{s['y']}</y>
      <next probability="100">{ids[s['next']]}</next>
    </spawn>""" for i, s in enumerate(SPAWNS))

    img, tiles_y = sheet(c, frames)
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    png = base64.b64encode(buf.getvalue()).decode()
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!-- Generated by tools/make_ic_pet.py. Edit that script, not this file. -->
<animations xmlns="http://esheep.petrucci.ch/">
  <header>
    <author>Justin Ren Liu</author>
    <title>{chip['title']}</title>
    <petname>{chip['title']}</petname>
    <version>1.2</version>
    <info>{chip['info']}</info>
  </header>
  <image>
    <tilesx>{TILES_X}</tilesx>
    <tilesy>{tiles_y}</tilesy>
    <png>{png}</png>
  </image>
  <spawns>{spawns}
  </spawns>
  <animations>{''.join(out)}
  </animations>
  <childs></childs>
</animations>
"""


def preview(c, frames, names):
    """Every frame enlarged, on the white paper and the green page, with its name."""
    big = 4
    tw, th = c.W * SCALE * big, H * SCALE * big
    tiles_y = -(-len(frames) // TILES_X)
    prev = Image.new("RGBA", (tw * TILES_X, th * tiles_y * 2), (255, 255, 255, 255))
    d = ImageDraw.Draw(prev)
    for i, (f, name) in enumerate(zip(frames, names)):
        f2 = f.resize((tw, th), Image.NEAREST)
        x, y = (i % TILES_X) * tw, (i // TILES_X) * th
        for yy, bg in ((y, (240, 240, 240, 255)), (y + th * tiles_y, (31, 107, 69, 255))):
            prev.paste(bg, (x, yy, x + tw, yy + th))
            prev.alpha_composite(f2, (x, yy))
            d.text((x + 6, yy + 4), name, fill=(200, 60, 60, 255), font_size=20)
    return prev


# ---------------------------------------------------------------- favicon
FAVICON_BG = (31, 107, 69, 255)   # the site's --base green

# A chip seen from above with "JRL" (the part number on the datasheet) laser-marked on it, in the pets' colors,
# drawn for 16x16. R is 4 wide so the word is 12 px and sits exactly centred. The top edge catches the light
# so the body still reads on a dark tab. 'w' marking, 'k' body, 'h' highlight, 's' shadow, 'p' pin,
# ' ' transparent (the home-screen icon puts it on the site's green).
FAVICON = [
    "                ",
    "   p  p  p  p   ",
    "   p  p  p  p   ",
    "  hhhhhhhhhhhh  ",
    " kkkkkkkkkkkkkk ",
    " kkkwkwwwkkwkkk ",
    " kkkwkwkkwkwkkk ",
    " kkkwkwwwkkwkkk ",
    " kwkwkwkwkkwkkk ",
    " kkwkkwkkwkwwwk ",
    " kkkkkkkkkkkkkk ",
    " kkkkkkkkkkkkkk ",
    "  ssssssssssss  ",
    "   p  p  p  p   ",
    "   p  p  p  p   ",
    "                ",
]


def favicon(size=16):
    colors = {"w": EYE, "k": INK, "h": HI, "s": SH, "p": PIN_SH, " ": (0, 0, 0, 0)}
    img = Image.new("RGBA", (16, 16))
    for y, row in enumerate(FAVICON):
        for x, ch in enumerate(row):
            img.putpixel((x, y), colors[ch])
    return img.resize((size, size), Image.NEAREST)


def write_favicons(root):
    # saved from the largest size, with the exact smaller drawings supplied (Pillow skips sizes above the base)
    favicon(48).save(os.path.join(root, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)],
                     append_images=[favicon(16), favicon(32)])
    # exact-size PNGs too, so a browser never shrinks a bigger one (which blurs the letters)
    for n in (16, 32):
        favicon(n).save(os.path.join(root, "assets", f"favicon-{n}.png"))
    # phones round the corners of home-screen icons themselves and need it opaque, so the chip sits on a full green square
    big = favicon(144)
    touch = Image.new("RGBA", (180, 180), FAVICON_BG)
    touch.alpha_composite(big, (18, 18))
    touch.convert("RGB").save(os.path.join(root, "apple-touch-icon.png"))


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(os.path.join(root, "assets", "pets"), exist_ok=True)
    for name, chip in CHIPS.items():
        c = Chip(**chip)
        frames, names, anims = build(c)
        xml = to_xml(chip, c, frames, names, anims)
        with open(os.path.join(root, "assets", "pets", f"{name}.xml"), "w", encoding="utf-8", newline="\n") as f:
            f.write(xml)
        preview(c, frames, names).save(os.path.join(root, "tools", f"{name}-preview.png"))
        if name == "ic555":
            icon = frames[names.index("side L")]
            icon.crop(icon.getbbox()).save(os.path.join(root, "assets", "pets", "ic555-icon.png"))
        print(f"wrote assets/pets/{name}.xml ({len(xml) // 1024} KB) and tools/{name}-preview.png")
    write_favicons(root)
    print("wrote favicon.ico, assets/favicon-16.png, assets/favicon-32.png and apple-touch-icon.png")


if __name__ == "__main__":
    main()

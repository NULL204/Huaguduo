"""3D skeleton (FK + analytic two-bone IK) and a perspective camera.

World units are centimetres.  Axes: x = screen right, y = up, z = toward the default camera.
The character's LEFT side is +x when she faces the camera (+z).  Angles in degrees.
"""
import math

import numpy as np

D = math.pi / 180.0


def rx(a):
    c, s = math.cos(a * D), math.sin(a * D)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], np.float64)


def ry(a):
    c, s = math.cos(a * D), math.sin(a * D)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], np.float64)


def rz(a):
    c, s = math.cos(a * D), math.sin(a * D)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], np.float64)


def euler(pitch=0.0, yaw=0.0, roll=0.0):
    """yaw about local y, then pitch about x (positive = nod forward/down), then roll about z
    (positive = tilt toward the character's left, +x)."""
    return ry(yaw) @ rx(pitch) @ rz(-roll)


def norm(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


# ----------------------------------------------------------------------------- skeleton

# name, parent, bind offset (in parent frame)
BONES = [
    ("root", None, (0, 0, 0)),
    ("pelvis", "root", (0, 92, 0)),
    ("waist", "pelvis", (0, 12, -0.5)),
    ("chest", "waist", (0, 18, 0.5)),
    ("neck", "chest", (0, 15.5, -0.8)),
    ("head", "neck", (0, 8.5, 1.2)),
    ("clav_l", "chest", (2.5, 11.5, 0.5)),
    ("arm_l", "clav_l", (13.0, -0.5, -1.0)),
    ("elbow_l", "arm_l", (0, -26.5, 0)),
    ("wrist_l", "elbow_l", (0, -24.0, 0)),
    ("clav_r", "chest", (-2.5, 11.5, 0.5)),
    ("arm_r", "clav_r", (-13.0, -0.5, -1.0)),
    ("elbow_r", "arm_r", (0, -26.5, 0)),
    ("wrist_r", "elbow_r", (0, -24.0, 0)),
    ("hip_l", "pelvis", (8.6, -4.0, 0)),
    ("knee_l", "hip_l", (0, -41.5, 0.6)),
    ("ankle_l", "knee_l", (0, -40.5, -1.2)),
    ("hip_r", "pelvis", (-8.6, -4.0, 0)),
    ("knee_r", "hip_r", (0, -41.5, 0.6)),
    ("ankle_r", "knee_r", (0, -40.5, -1.2)),
]
PARENT = {n: p for n, p, _ in BONES}
OFFSET = {n: np.array(o, np.float64) for n, _, o in BONES}
UPPER_ARM = 26.5
FOREARM = 24.0
THIGH = 41.5
SHIN = 40.5
HEAD_CENTER = np.array([0, 10.5, 1.5])   # skull centre in head-bone space
HEAD_RADIUS = 10.5


class Pose:
    """Pose description.  All angles in degrees; missing keys default to the rest pose.

    root_pos (x,y,z) world, root_yaw/pitch/roll
    pelvis:(pitch,yaw,roll)  waist  chest  neck  head  — local euler triples
    clav_l/r: (raise, forward)       arm_l/r: (flex, abduct, twist)   elbow_l/r: flex
    wrist_l/r: (flex, side)          hip_l/r: (flex, abduct, twist)   knee_l/r: flex   ankle_l/r: flex
    ik: {'hand_l': (target, pole), 'foot_r': (target, pole, foot_dir)} world-space overrides
    """

    def __init__(self, **kw):
        self.d = kw

    def get(self, k, default=None):
        return self.d.get(k, default)


def _local_rot(name, P):
    g = P.get
    if name == "root":
        return euler(g("root_pitch", 0), g("root_yaw", 0), g("root_roll", 0))
    if name in ("pelvis", "waist", "chest", "neck", "head"):
        p, y, r = g(name, (0, 0, 0))
        return euler(p, y, r)
    if name.startswith("clav"):
        side = 1 if name.endswith("_l") else -1
        raise_, fwd = g(name, (0, 0))
        return ry(-side * fwd) @ rz(side * raise_)
    if name.startswith("arm"):
        side = 1 if name.endswith("_l") else -1
        flex, abd, tw = g(name, (0, 8, 0))
        # abduct about z (outward), flex about x (forward), then twist about the bone
        return rz(side * abd) @ rx(-flex) @ ry(side * tw)
    if name.startswith("elbow"):
        return rx(-g(name, 8))
    if name.startswith("wrist"):
        side = 1 if name.endswith("_l") else -1
        f, s = g(name, (0, 0))
        return rx(-f) @ rz(side * s)
    if name.startswith("hip"):
        side = 1 if name.endswith("_l") else -1
        flex, abd, tw = g(name, (0, 2, 0))
        return rz(side * abd) @ rx(-flex) @ ry(side * tw)
    if name.startswith("knee"):
        return rx(g(name, 2))
    if name.startswith("ankle"):
        return rx(-g(name, 0))
    return np.eye(3)


class Skeleton:
    """World transforms of every bone for a pose."""

    def __init__(self, pose: Pose):
        P = pose
        self.R = {}
        self.T = {}
        root_pos = np.array(P.get("root_pos", (0, 0, 0)), np.float64)
        for name, parent, _ in BONES:
            Rl = _local_rot(name, P)
            if parent is None:
                self.R[name] = Rl
                self.T[name] = root_pos.copy()
            else:
                Rp = self.R[parent]
                self.T[name] = self.T[parent] + Rp @ OFFSET[name]
                self.R[name] = Rp @ Rl
        # head and pelvis drops (vertical bob) etc. are carried by root_pos
        ik = P.get("ik", {}) or {}
        for key, spec in ik.items():
            if key.startswith("hand"):
                self._arm_ik(key[-1], *spec)
            elif key.startswith("foot"):
                self._leg_ik(key[-1], *spec)
        self.head_center = self.T["head"] + self.R["head"] @ HEAD_CENTER
        # feet: toe point along the foot direction
        self.toe = {}
        self.heel = {}
        for s in ("l", "r"):
            fd = self.foot_dir.get(s) if hasattr(self, "foot_dir") else None
            if fd is None:
                fd = self.R["ankle_" + s] @ np.array([0, -0.18, 1.0])
            fd = norm(np.asarray(fd, np.float64))
            a = self.T["ankle_" + s]
            self.toe[s] = a + fd * 15.5 + np.array([0, -5.5, 0])
            self.heel[s] = a - fd * 4.5 + np.array([0, -5.5, 0])

    # two-bone IK -------------------------------------------------------------------
    def _two_bone(self, a, target, l1, l2, pole):
        d = target - a
        dist = np.linalg.norm(d)
        dist = min(max(dist, abs(l1 - l2) + 1e-3), l1 + l2 - 1e-3)
        dn = norm(d)
        # law of cosines: angle at a
        cos_a = (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist)
        cos_a = min(1.0, max(-1.0, cos_a))
        sin_a = math.sqrt(1 - cos_a * cos_a)
        pv = np.asarray(pole, np.float64) - a
        pv = pv - dn * np.dot(pv, dn)
        pv = norm(pv) if np.linalg.norm(pv) > 1e-6 else norm(np.cross(dn, np.array([1.0, 0, 0])))
        mid = a + dn * (l1 * cos_a) + pv * (l1 * sin_a)
        end = a + dn * dist
        return mid, end

    def _arm_ik(self, s, target, pole):
        a = self.T["arm_" + s]
        mid, end = self._two_bone(a, np.asarray(target, np.float64), UPPER_ARM, FOREARM, pole)
        self.T["elbow_" + s] = mid
        self.T["wrist_" + s] = end
        # rebuild frames so 'down the bone' is local -y
        self.R["arm_" + s] = _frame_from_dir(mid - a, self.R["chest"][:, 2])
        self.R["elbow_" + s] = _frame_from_dir(end - mid, self.R["chest"][:, 2])
        self.R["wrist_" + s] = self.R["elbow_" + s]

    def _leg_ik(self, s, target, pole, foot_dir=None):
        a = self.T["hip_" + s]
        mid, end = self._two_bone(a, np.asarray(target, np.float64), THIGH, SHIN, pole)
        self.T["knee_" + s] = mid
        self.T["ankle_" + s] = end
        fwd = self.R["pelvis"][:, 2]
        self.R["hip_" + s] = _frame_from_dir(mid - a, fwd)
        self.R["knee_" + s] = _frame_from_dir(end - mid, fwd)
        if foot_dir is not None:
            if not hasattr(self, "foot_dir"):
                self.foot_dir = {}
            self.foot_dir[s] = foot_dir

    # helpers -------------------------------------------------------------------------
    def p(self, name):
        return self.T[name]

    def axis(self, name, k):
        """World direction of a bone's local axis k (0=x right, 1=y up, 2=z forward)."""
        return self.R[name][:, k]

    def hand_tip(self, s, length=17.0):
        d = norm(self.T["wrist_" + s] - self.T["elbow_" + s])
        return self.T["wrist_" + s] + d * length

    def com(self):
        """Approximate centre of mass (pelvis-weighted average)."""
        pts = [self.T["pelvis"] * 3, self.T["chest"] * 2, self.head_center * 1,
               self.T["knee_l"] * 0.8, self.T["knee_r"] * 0.8]
        return sum(pts) / 7.6


def _frame_from_dir(down, fwd_hint):
    """Rotation whose local -y points along `down` and local z is as close to fwd_hint as possible."""
    yv = -norm(np.asarray(down, np.float64))
    z = np.asarray(fwd_hint, np.float64)
    z = z - yv * np.dot(z, yv)
    if np.linalg.norm(z) < 1e-6:
        z = np.array([0, 0, 1.0]) - yv * yv[2]
    z = norm(z)
    x = np.cross(yv, z)
    return np.stack([x, yv, z], axis=1)


# ----------------------------------------------------------------------------- camera

class Camera:
    """Pinhole camera.  pos/target in world cm; fov = vertical field of view in degrees."""

    def __init__(self, pos=(0, 120, 420), target=(0, 100, 0), fov=30.0, roll=0.0, W=1920, H=1080,
                 shift=(0.0, 0.0)):
        self.pos = np.asarray(pos, np.float64)
        self.target = np.asarray(target, np.float64)
        self.W, self.H = W, H
        self.f = (H / 2) / math.tan(fov * D / 2)
        self.cx = W / 2 + shift[0]
        self.cy = H / 2 + shift[1]
        fwd = norm(self.target - self.pos)
        up = np.array([0, 1.0, 0])
        if abs(np.dot(fwd, up)) > 0.995:
            up = np.array([0, 0, -1.0])
        right = norm(np.cross(fwd, up))
        upv = np.cross(right, fwd)
        if roll:
            c, s = math.cos(roll * D), math.sin(roll * D)
            right, upv = right * c + upv * s, -right * s + upv * c
        self.right, self.up, self.fwd = right, upv, fwd

    def view(self, P):
        v = np.asarray(P, np.float64) - self.pos
        return np.array([np.dot(v, self.right), np.dot(v, self.up), np.dot(v, self.fwd)])

    def project(self, P):
        """-> (sx, sy, depth, scale px-per-cm)"""
        v = np.asarray(P, np.float64) - self.pos
        x = v @ self.right
        y = v @ self.up
        d = v @ self.fwd
        d = max(d, 1.0)
        s = self.f / d
        return self.cx + x * s, self.cy - y * s, d, s

    def project_many(self, Ps):
        Ps = np.asarray(Ps, np.float64)
        v = Ps - self.pos
        x = v @ self.right
        y = v @ self.up
        d = np.maximum(v @ self.fwd, 1.0)
        s = self.f / d
        return np.stack([self.cx + x * s, self.cy - y * s], axis=1), d, s

    def to_cam_dir(self, P):
        """Unit vector from P toward the camera."""
        return norm(self.pos - np.asarray(P, np.float64))

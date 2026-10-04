"""Global configuration for the 花骨朵 fan PV renderer."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "out")

AUDIO_PATH = os.environ.get("PV_AUDIO", os.path.join(ASSETS, "song.mp3"))
LRC_PATH = os.environ.get("PV_LRC", os.path.join(ASSETS, "lyrics.lrc"))
FONT_DIR = os.path.join(ASSETS, "fonts")

W = int(os.environ.get("PV_W", 1920))
H = int(os.environ.get("PV_H", 1080))
FPS = int(os.environ.get("PV_FPS", 30))
DURATION = 170.38  # length of the song file in seconds

# musical grid (measured: 120 BPM, first beat at 0.08 s)
BPM = 120.0
BEAT = 60.0 / BPM
BEAT0 = 0.08
MUSIC_END = 160.08  # the song stops dead on this beat

FONTS = {
    "brush": "MaShanZheng.ttf",      # 马善政楷书 — lyrics
    "running": "ZhiMangXing.ttf",    # 志莽行书 — expressive lines
    "grass": "LiuJianMaoCao.ttf",    # 刘建毛草 — wild hero characters
    "long": "LongCang.ttf",          # 龙藏体
    "serif": "NotoSerifSC-Regular.ttf",
    "serif_black": "NotoSerifSC-Black.ttf",
}


def S(x):
    """Scale a length authored for 1920-wide frames to the current width."""
    return x * W / 1920.0

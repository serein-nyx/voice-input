"""集中加载配置。其他模块只从这里读，不直接碰 os.environ。"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Windows 控制台默认 GBK，输出 emoji/✓ 会 UnicodeEncodeError。强制 UTF-8。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

# 项目根目录（src 的上一级）
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _get(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def _get_bool(key: str, default: bool = False) -> bool:
    val = _get(key, str(default)).lower()
    return val in ("1", "true", "yes", "on")


# ── 录音 ──────────────────────────────────────────────
SAMPLE_RATE = int(_get("SAMPLE_RATE", "16000"))   # Whisper 要求 16kHz
CHANNELS = 1
MIN_RECORD_SEC = float(_get("MIN_RECORD_SEC", "0.3"))  # 短于此忽略（误触）

# ── 全局快捷键（按住录音，松开转写）─────────────────────
# 单个键名，参考 keyboard 库：f9 / f8 / right ctrl / scroll lock 等
HOTKEY = _get("HOTKEY", "f9")
QUIT_HOTKEY = _get("QUIT_HOTKEY", "ctrl+shift+q")

# ── STT 引擎选择 ─────────────────────────────────────
# whisper = faster-whisper（默认）；paraformer = FunASR Paraformer
STT_ENGINE = _get("STT_ENGINE", "whisper").lower()

# ── STT (faster-whisper) ─────────────────────────────
WHISPER_MODEL = _get("WHISPER_MODEL", "large-v3")
WHISPER_DEVICE = _get("WHISPER_DEVICE", "auto")          # auto / cuda / cpu
WHISPER_COMPUTE_TYPE = _get("WHISPER_COMPUTE_TYPE", "auto")  # auto / float16 / int8
WHISPER_LANGUAGE = _get("WHISPER_LANGUAGE", "zh")        # zh / en / 空=自动检测

# ── STT (FunASR Paraformer) ──────────────────────────
PARAFORMER_MODEL = _get("PARAFORMER_MODEL", "paraformer-zh")
PARAFORMER_DEVICE = _get("PARAFORMER_DEVICE", "auto")    # auto / cuda / cpu
# VAD / 标点模型，留空则不加载（标点对后续润色有帮助，建议保留）
PARAFORMER_VAD_MODEL = _get("PARAFORMER_VAD_MODEL", "fsmn-vad")
PARAFORMER_PUNC_MODEL = _get("PARAFORMER_PUNC_MODEL", "ct-punc")

# ── 润色 LLM (DeepSeek，OpenAI 兼容) ───────────────────
DEEPSEEK_API_KEY = _get("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = _get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = _get("DEEPSEEK_MODEL", "deepseek-chat")
LLM_TEMPERATURE = float(_get("LLM_TEMPERATURE", "0.3"))
LLM_TIMEOUT = int(_get("LLM_TIMEOUT", "60"))

# 润色 system prompt 文件（prompt-v4）
PROMPT_FILE = ROOT / "prompts" / _get("PROMPT_FILE", "enhance-v4.txt")

# ── 行为 ─────────────────────────────────────────────
AUTO_PASTE = _get_bool("AUTO_PASTE", False)   # 复制后是否自动 Ctrl+V 粘贴
PLAY_BEEP = _get_bool("PLAY_BEEP", True)      # 录音开始/结束提示音

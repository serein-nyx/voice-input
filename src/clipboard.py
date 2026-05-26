"""剪贴板写入，可选自动粘贴。"""
import time

import pyperclip

from . import config


def copy(text: str):
    pyperclip.copy(text)


def copy_and_maybe_paste(text: str):
    """复制到剪贴板；若 AUTO_PASTE 开启，再模拟 Ctrl+V 粘贴到当前焦点。"""
    pyperclip.copy(text)
    if config.AUTO_PASTE:
        import keyboard  # 局部导入，避免无谓依赖
        time.sleep(0.05)  # 给剪贴板一点写入时间
        keyboard.send("ctrl+v")

"""语音输入工具主程序。

流程：按一次快捷键开始录音 → 再按一次停止 → STT 转写 → DeepSeek (prompt-v4) 润色 → 复制到剪贴板。

运行：python -m src.main
"""
import sys
import threading

import keyboard

from . import audio, clipboard, config, polish, stt

try:
    import winsound  # Windows 自带
except ImportError:  # 非 Windows 环境降级
    winsound = None


def beep(start: bool):
    if not config.PLAY_BEEP or winsound is None:
        return
    try:
        winsound.Beep(880 if start else 523, 90)
    except Exception:  # noqa: BLE001
        pass


class App:
    def __init__(self):
        self.recorder = audio.Recorder()
        self.transcriber = stt.create_transcriber()  # 启动时加载模型（耗时在此）
        self._recording = False
        self._busy = False
        self._key_down = False  # 区分物理按压与按住自动重复
        self._lock = threading.Lock()
        self._quit = threading.Event()

    # ── 快捷键回调（切换模式：按一次开始，再按一次停止）──────
    def on_hotkey(self, _event=None):
        # 按住时 OS 会反复发 down 事件，用 _key_down 只在首次按下时触发
        with self._lock:
            if self._key_down:
                return
            self._key_down = True
        self._toggle()

    def on_hotkey_release(self, _event=None):
        with self._lock:
            self._key_down = False

    def _toggle(self):
        with self._lock:
            if self._busy:
                return  # 正在转写/润色，忽略这次按键
            if self._recording:
                self._recording = False
                self._busy = True
                stop = True
            else:
                self._recording = True
                stop = False
        if not stop:
            beep(start=True)
            self.recorder.start()
            print("\n● 录音中…（再按一次快捷键结束）", flush=True)
            return
        try:
            self._stop_and_transcribe()
        finally:
            with self._lock:
                self._busy = False

    def _stop_and_transcribe(self):
        beep(start=False)
        clip = self.recorder.stop()
        dur = self.recorder.duration(clip)
        if dur < config.MIN_RECORD_SEC:
            print(f"⤫ 录音过短（{dur:.2f}s），忽略。", flush=True)
            return

        print(f"⏳ 转写中…（{dur:.1f}s 音频）", flush=True)
        transcript = self.transcriber.transcribe(clip)
        if not transcript:
            print("⤫ 没识别到内容。", flush=True)
            return
        print(f"📝 原文：{transcript}", flush=True)

        print("✨ 润色中…", flush=True)
        try:
            result = polish.polish(transcript)
        except Exception as e:  # noqa: BLE001
            print(f"⚠ 润色失败（{e}），改用转写原文。", flush=True)
            result = transcript

        clipboard.copy_and_maybe_paste(result)
        action = "已复制并粘贴" if config.AUTO_PASTE else "已复制到剪贴板"
        print(f"✅ {action}：\n{result}\n", flush=True)

    # ── 生命周期 ─────────────────────────────────────
    def run(self):
        self._register_hotkeys()
        self._print_banner()
        try:
            self._quit.wait()
        except KeyboardInterrupt:
            pass
        print("\n再见 👋")

    def _register_hotkeys(self):
        if "+" in config.HOTKEY:
            print(
                f"⚠ HOTKEY={config.HOTKEY!r} 含组合键，录音键只支持单个键，"
                f"请改成如 f9 / f8 / scroll lock。"
            )
            sys.exit(1)
        keyboard.on_press_key(config.HOTKEY, self.on_hotkey, suppress=False)
        keyboard.on_release_key(config.HOTKEY, self.on_hotkey_release, suppress=False)
        keyboard.add_hotkey(config.QUIT_HOTKEY, self._quit.set)

    def _print_banner(self):
        print("=" * 56)
        print("  语音输入工具 · STT + DeepSeek(prompt-v4)")
        print("=" * 56)
        print(f"  STT     : {self.transcriber.label} @ {self.transcriber.device}")
        print(f"  润色     : {config.DEEPSEEK_MODEL}")
        print(f"  录音键   : 按一次 [{config.HOTKEY}] 开始，再按一次停止转写")
        print(f"  退出     : {config.QUIT_HOTKEY}")
        print(f"  自动粘贴 : {'开' if config.AUTO_PASTE else '关（仅复制到剪贴板）'}")
        print("=" * 56)
        print("就绪，按一次快捷键开始说话…\n", flush=True)


def main():
    App().run()


if __name__ == "__main__":
    main()

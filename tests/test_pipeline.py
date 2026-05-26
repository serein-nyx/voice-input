"""分模块自检：录音 → 转写 → 润色。

用法（项目根目录下）：
    python -m tests.test_pipeline          # 完整链路：录 4 秒 → 转写 → 润色
    python -m tests.test_pipeline --polish # 只测 DeepSeek 润色（用内置示例文本）
"""
import sys
import time

from src import audio, config, polish, stt

SAMPLE = ("嗯那个我今天发现这个语音输入工具其实挺好用的就是有时候啊"
          "它转写出来的内容你会发现说虽然字面上是对的但是表达上不太书面")


def test_polish_only():
    print(f"原文：{SAMPLE}\n")
    print("润色中…")
    print(f"结果：{polish.polish(SAMPLE)}")


def test_full():
    print(f"加载 STT 模型（{config.STT_ENGINE}）…")
    transcriber = stt.create_transcriber()

    seconds = 4
    rec = audio.Recorder()
    print(f"\n开始录音 {seconds} 秒，请说话…")
    rec.start()
    time.sleep(seconds)
    clip = rec.stop()
    print(f"录到 {rec.duration(clip):.1f}s 音频。")

    print("转写中…")
    text = transcriber.transcribe(clip)
    print(f"原文：{text}\n")

    if not text:
        print("没识别到内容，跳过润色。")
        return
    print("润色中…")
    print(f"结果：{polish.polish(text)}")


if __name__ == "__main__":
    if "--polish" in sys.argv:
        test_polish_only()
    else:
        test_full()

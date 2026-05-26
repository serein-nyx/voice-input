"""麦克风录音。按住快捷键期间持续采集，松开后返回整段音频。

不依赖其他 src 模块。返回 float32 单声道 numpy 数组，采样率 = config.SAMPLE_RATE，
可直接喂给 faster-whisper。
"""
import numpy as np
import sounddevice as sd

from . import config


class Recorder:
    def __init__(self):
        self._stream: sd.InputStream | None = None
        self._frames: list[np.ndarray] = []

    def _callback(self, indata, frames, time_info, status):
        # status 里有 overflow 等告警，录音场景下忽略即可
        self._frames.append(indata.copy())

    def start(self):
        """开始采集。重复调用会先丢弃上一段。"""
        self._frames = []
        self._stream = sd.InputStream(
            samplerate=config.SAMPLE_RATE,
            channels=config.CHANNELS,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> np.ndarray:
        """停止采集，返回拼接后的单声道 float32 音频（一维）。"""
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if not self._frames:
            return np.zeros(0, dtype=np.float32)
        audio = np.concatenate(self._frames, axis=0)
        self._frames = []
        # InputStream 给的是 (n, channels)，转成一维
        return audio.reshape(-1).astype(np.float32)

    @staticmethod
    def duration(audio: np.ndarray) -> float:
        return len(audio) / config.SAMPLE_RATE

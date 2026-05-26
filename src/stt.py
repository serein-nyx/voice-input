"""STT 引擎封装。通过 config.STT_ENGINE 选择具体实现。

    STT_ENGINE=whisper     → WhisperTranscriber（faster-whisper，默认）
    STT_ENGINE=paraformer  → ParaformerTranscriber（FunASR Paraformer）

两种实现暴露相同接口，main / 测试只认这套：
    .transcribe(audio: np.ndarray) -> str   # 16kHz float32 单声道
    .device : str   # 实际运行设备
    .label  : str   # banner 显示用（引擎 + 模型名）

用 create_transcriber() 按配置创建，不要直接 new 具体类。
"""
import numpy as np

from . import config


class WhisperTranscriber:
    """faster-whisper 封装。启动时加载一次模型，之后复用。

    device/compute_type 支持 auto：优先尝试 CUDA，失败自动回退 CPU。
    """

    def __init__(self):
        self.model, self.device, self.compute_type = self._load()
        self.label = f"whisper:{config.WHISPER_MODEL}"

    def _load(self):
        from faster_whisper import WhisperModel

        device = config.WHISPER_DEVICE
        compute = config.WHISPER_COMPUTE_TYPE

        # 候选 (device, compute_type) 列表，按优先级尝试
        if device == "auto":
            attempts = [
                ("cuda", "float16" if compute == "auto" else compute),
                ("cpu", "int8" if compute == "auto" else compute),
            ]
        else:
            if compute == "auto":
                compute = "float16" if device == "cuda" else "int8"
            attempts = [(device, compute)]

        last_err = None
        for dev, comp in attempts:
            print(f"[STT] 加载模型 {config.WHISPER_MODEL} (device={dev}, compute={comp}) ...")
            try:
                model = WhisperModel(config.WHISPER_MODEL, device=dev, compute_type=comp)
            except Exception as e:  # noqa: BLE001  仅捕获加载失败，不含后续 print
                last_err = e
                print(f"[STT] {dev}/{comp} 加载失败：{e}")
                continue
            print(f"[STT] 模型就绪 (device={dev})")
            return model, dev, comp
        raise RuntimeError(f"无法加载 Whisper 模型：{last_err}")

    def transcribe(self, audio: np.ndarray) -> str:
        language = config.WHISPER_LANGUAGE or None
        segments, _info = self.model.transcribe(
            audio,
            language=language,
            beam_size=5,
            vad_filter=True,  # 过滤静音段，减少幻听
        )
        text = "".join(seg.text for seg in segments).strip()
        return text


class ParaformerTranscriber:
    """FunASR Paraformer 封装。启动时加载一次模型，之后复用。

    可选挂载 VAD + 标点模型（留空则不加载）。device 支持 auto：
    有可用 CUDA 用 GPU，否则 CPU。
    """

    def __init__(self):
        self.model, self.device = self._load()
        self.label = f"paraformer:{config.PARAFORMER_MODEL}"

    def _resolve_device(self) -> str:
        pref = config.PARAFORMER_DEVICE
        if pref == "cuda":
            return "cuda:0"
        if pref == "cpu":
            return "cpu"
        # auto：探测 CUDA 是否可用
        try:
            import torch
            return "cuda:0" if torch.cuda.is_available() else "cpu"
        except Exception:  # noqa: BLE001  torch 不在/异常都退 CPU
            return "cpu"

    def _load(self):
        try:
            from funasr import AutoModel
        except ImportError as e:
            raise RuntimeError(
                "未安装 FunASR。请先 pip install funasr，或把 STT_ENGINE 改回 whisper。"
            ) from e

        device = self._resolve_device()
        kwargs = dict(model=config.PARAFORMER_MODEL, device=device, disable_update=True)
        if config.PARAFORMER_VAD_MODEL:
            kwargs["vad_model"] = config.PARAFORMER_VAD_MODEL
        if config.PARAFORMER_PUNC_MODEL:
            kwargs["punc_model"] = config.PARAFORMER_PUNC_MODEL

        print(f"[STT] 加载 Paraformer {config.PARAFORMER_MODEL} (device={device}) ...")
        try:
            model = AutoModel(**kwargs)
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"无法加载 Paraformer 模型：{e}") from e
        print(f"[STT] 模型就绪 (device={device})")
        return model, device

    def transcribe(self, audio: np.ndarray) -> str:
        # FunASR 接受 16kHz 单声道 float32 numpy；与录音输出一致
        audio = np.ascontiguousarray(audio, dtype=np.float32)
        res = self.model.generate(
            input=audio,
            batch_size_s=300,
            disable_pbar=True,
        )
        # 返回形如 [{"key": ..., "text": "..."}]，多段则拼接
        text = "".join(seg.get("text", "") for seg in res).strip()
        return text


def create_transcriber():
    """按 config.STT_ENGINE 创建对应的转写器。"""
    engine = config.STT_ENGINE
    if engine == "whisper":
        return WhisperTranscriber()
    if engine == "paraformer":
        return ParaformerTranscriber()
    raise RuntimeError(f"未知 STT_ENGINE={engine!r}，支持 whisper / paraformer")


# 兼容旧引用（旧代码里 stt.Transcriber 指 whisper 实现）
Transcriber = WhisperTranscriber

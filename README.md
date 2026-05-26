# 语音输入工具（Windows）

按住快捷键说话，松开后自动转写 + 润色，结果直接进剪贴板。

```
按住 [alt] 录音  →  再按一次alt  →  faster-whisper/Paraformer 转写  →  DeepSeek 润色(prompt-v4)  →  复制到剪贴板
```

是 [VoiceInk 双模语音输入](../VoiceInk双模语音输入) 方案的 Windows 实现：保留「本地 STT」的隐私与零成本，
润色层换成对 prompt-v4 调优良好的 DeepSeek 云端 API，触发方式改为更顺手的「按住说话」（push-to-talk）。

---

## 技术栈

| 层 | 组件 |
|---|---|
| 录音 | sounddevice（16kHz 单声道） |
| STT | faster-whisper（large-v3，自动 GPU/CPU） |
| 润色 | DeepSeek `deepseek-chat`，system prompt = prompt-v4 |
| 触发 | keyboard 全局热键（按住录音，再按一次转写） |
| 输出 | pyperclip 写剪贴板（可选自动粘贴） |

---

## 安装

```powershell
cd voice-input
pip install -r requirements.txt
copy .env.example .env      # 然后填入 DEEPSEEK_API_KEY
```

`.env` 里**必填** `DEEPSEEK_API_KEY`（[platform.deepseek.com](https://platform.deepseek.com/) → API Keys）。其余项有默认值。

> 首次运行会自动下载 Whisper `large-v3` 模型（约 1.5 GB），下载到 `~/.cache/huggingface`。
> 想先轻量验证可在 `.env` 把 `WHISPER_MODEL` 设为 `small` 或 `base`。

---

## 运行

```powershell
python -m src.main
```

或双击 `run.bat`。

启动后会打印当前配置，然后：

1. **按住 `alt`** → 听到提示音，开始录音
2. 对着麦克风说话
3. **再按一次 `alt`** → 自动转写 → 润色 → 复制到剪贴板
4. 在任意输入框 `Ctrl+V` 粘贴（若开了 `AUTO_PASTE` 则自动粘贴）

退出：`Ctrl+Shift+Q`。

---

## 自检（建议首次使用前跑一遍）

```powershell
python -m tests.test_pipeline --polish   # 只测 DeepSeek 润色（验证 API key）
python -m tests.test_pipeline            # 完整链路：录 4 秒 → 转写 → 润色
```

---

## 配置项（`.env`）

| 键 | 默认 | 说明 |
|---|---|---|
| `DEEPSEEK_API_KEY` | — | **必填** |
| `DEEPSEEK_MODEL` | `deepseek-chat` | 润色模型 |
| `WHISPER_MODEL` | `large-v3` | `tiny`/`base`/`small`/`medium`/`large-v3`/`large-v3-turbo` |
| `WHISPER_DEVICE` | `auto` | `auto`(优先 GPU 失败回退 CPU)/`cuda`/`cpu` |
| `WHISPER_LANGUAGE` | `zh` | 识别语言，留空=自动检测 |
| `HOTKEY` | `f9` | 录音键（**单个键**：`f9`/`f8`/`scroll lock`/`right ctrl`） |
| `QUIT_HOTKEY` | `ctrl+shift+q` | 退出键 |
| `AUTO_PASTE` | `false` | 复制后是否自动 `Ctrl+V` |
| `PLAY_BEEP` | `true` | 录音起止提示音 |

---

## 架构

模块完全解耦，互不 import（`audio`/`stt`/`polish`/`clipboard`），由 `main.py` 编排。

- `src/main.py` — 主循环；注册全局热键，编排「录音→转写→润色→剪贴板」。
- `src/audio.py` — sounddevice 录音，返回 16kHz float32 numpy 数组。
- `src/stt.py` — faster-whisper 封装；启动加载一次模型，`auto` 模式自动在 GPU/CPU 间回退。
- `src/polish.py` — 调 DeepSeek（OpenAI 兼容接口），system prompt 读自 `prompts/enhance-v4.txt`。
- `src/clipboard.py` — 写剪贴板 + 可选自动粘贴。
- `src/config.py` — 集中读 `.env`，其他模块只从这里取配置。
- `prompts/enhance-v4.txt` — prompt-v4 润色提示词（润色质量的核心，可直接编辑迭代）。

---

## 常见问题

- **按 alt 没反应**：keyboard 全局钩子偶尔需要管理员权限。用管理员身份打开 PowerShell 再运行，或换个不冲突的键（如 `scroll lock`）。
- **GPU 没用上 / 报 cublas/cudnn 错**：会自动回退 CPU（仍可用，只是慢）。想强制 CPU 可设 `WHISPER_DEVICE=cpu`、`WHISPER_COMPUTE_TYPE=int8`。
- **润色失败**：会自动降级为「直接复制转写原文」，并在控制台打印错误原因（多半是 API key 或网络）。
- **想改润色风格**：直接编辑 `prompts/enhance-v4.txt`，无需改代码。

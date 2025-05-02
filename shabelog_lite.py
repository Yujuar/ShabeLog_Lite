
import streamlit as st
import whisper
import tempfile
import os
from pathlib import Path
import torch

st.set_page_config(page_title="しゃべログLite", layout="centered", page_icon="🗣️")

# 初期化
if "result" not in st.session_state:
    st.session_state["result"] = ""

if "transcribed" not in st.session_state:
    st.session_state["transcribed"] = False

if "last_uploaded_file" not in st.session_state:
    st.session_state["last_uploaded_file"] = None

if "reloading" not in st.session_state:
    st.session_state["reloading"] = False


st.title("🗣️ しゃべログLite")
st.markdown("""
#### 音声ファイルを文字起こしする簡易アプリです。
- ファイルをアップロードすると自動で文字起こしが始まります。
- 設定を終えてからファイルをアップしてください。
            """)

uploaded_file = st.file_uploader("音声ファイルをアップロード", type=["mp3", "wav", "m4a"])

# ファイルが変わったら再処理フラグをリセット
if uploaded_file and uploaded_file.name != st.session_state["last_uploaded_file"]:
    st.session_state["transcribed"] = False
    st.session_state["last_uploaded_file"] = uploaded_file.name

setting_block = st.empty()

# 設定欄は未解析時のみ表示
if not st.session_state["transcribed"]:
    with setting_block.container():
        language = st.selectbox("音源の言語を選択してください", ["ja", "en", "fr", "de", "zh", "ko", "es", "ru"])
        model_size = st.selectbox("モデルを選択してください", ["tiny", "base", "small", "medium", "large"])
        fp16_option = st.selectbox("fp16の利用", [True, False])
        device_option = st.selectbox("使用デバイス", ["CPU", "GPU（CUDA）"])
        device = "cuda" if device_option == "GPU（CUDA）" else "cpu"
        st.markdown("""
    #####
    🔧 推奨環境と処理目安

    | モデル   | 処理時間（1時間音声） | メモリ使用量目安（VRAM） |
    |----------|------------------------|----------------------------|
    | base     | 数分                   | ～1GB                      |
    | medium   | 約10～15分             | ～4～5GB                   |
    | large    | 約20～30分以上         | ～10GB以上（VRAM）        |

    ⚠️ GPU（CUDA）を選択する場合は、NVIDIA製のGPUかつCUDA対応ドライバ・ライブラリが必要です。
    #####
                """)
        # CUDA確認
        if device == "cuda" and not torch.cuda.is_available():
            st.warning("⚠️ CUDAが使用できません。自動的にCPUに切り替えます。")
            device = "cpu"

    # モデルファイル名マップ（DLチェック用）
    model_file_map = {
        "tiny": "tiny.pt",
        "base": "base.pt",
        "small": "small.pt",
        "medium": "medium.pt",
        "large": "large-v3.pt"
    }
    model_filename = model_file_map.get(model_size, f"{model_size}.pt")
    cache_path = Path.home() / ".cache" / "whisper" / model_filename

    if not cache_path.exists():
        st.info(f"📦 {model_size} モデルの初回読み込み中です（環境によっては数分かかります）")
    if uploaded_file:
        with st.spinner("Whisperで文字起こし中..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            model = whisper.load_model(model_size, device=device)
            result = model.transcribe(tmp_path, language=language, fp16=fp16_option)
            st.session_state["result"] = result["text"]
            st.session_state["transcribed"] = True
            setting_block.empty()
            os.remove(tmp_path)
# 結果表示セクション（解析済みなら常に表示）
if st.session_state["transcribed"] and st.session_state["result"]:

    st.subheader("文字起こし結果")
    st.text_area("Transcription", value=st.session_state["result"], height=300)

    st.download_button(
        label="文字データをダウンロード",
        data=st.session_state["result"],
        file_name="shabelog_transcription.txt",
        mime="text/plain"
    )
    st.markdown("""
- デフォルトはshabelog_transcription.txtで保存されます。
- 保存場所はブラウザのDL場所に依存します。
- 右クリックで名前をつけて保存をすると任意の場所に任意の名前で保存が可能です。
""")

    st.markdown("""
    ### 🔄 設定をやり直す場合は、ブラウザの再読み込み（再読込）を行ってください。
    """)


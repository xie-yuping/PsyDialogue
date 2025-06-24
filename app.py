# app.py

import streamlit as st
import requests
import csv
from prompts import get_prompt

API_KEY = ""  # 替换为你自己的 DeepSeek API Key

st.set_page_config(page_title="PersonaGPT Demo", page_icon="🤖")

# 初始化上下文
if "messages" not in st.session_state:
    st.session_state.messages = []

if "style" not in st.session_state:
    st.session_state.style = "温柔倾听型"
if "version" not in st.session_state:
    st.session_state.version = "V1-基础"

# UI 样式
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        font-family: -apple-system, BlinkMacSystemFont, "San Francisco", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    .stApp {
        background: url("https://static1.squarespace.com/static/5e949a92e17d55230cd1d44f/t/679fd0d8b095d16e5a2f9955/1738526981767/Mountain01_Mac.png") no-repeat center center fixed;
        background-size: cover;
        backdrop-filter: blur(6px);
        -webkit-backdrop-filter: blur(6px);
    }
    .block-container {
        background-color: rgba(255, 255, 255, 0.65);
        padding: 2rem 3rem;
        border-radius: 28px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
        backdrop-filter: saturate(180%) blur(20px);
    }
    textarea, .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.6) !important;
        border-radius: 14px !important;
        backdrop-filter: blur(8px);
    }
        /* 关键：清除底部块的背景色 */
    .st-emotion-cache-128upt6 {
        background-color: transparent !important;
        box-shadow: none !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🌟 PersonaGPT：人样化对话 AI")

# 人设选择
with st.expander("🧠 第一步: 选择人样风格"):
    st.session_state.style = st.selectbox("🧐 人样风格", ["温柔倾听型", "理性建议型", "鼓励支持型"], index=["温柔倾听型", "理性建议型", "鼓励支持型"].index(st.session_state.style))
    st.session_state.version = st.selectbox("🔮 Prompt 版本", ["V1-基础", "V2-递进风格", "V3-情绪深度"], index=["V1-基础", "V2-递进风格", "V3-情绪深度"].index(st.session_state.version))
    st.markdown(f"**当前人样**: {st.session_state.style} ｜ **Prompt版本**: {st.session_state.version}")

# prompt 初始化
system_prompt = get_prompt(st.session_state.style, st.session_state.version)
if not any(msg["role"] == "system" for msg in st.session_state.messages):
    st.session_state.messages.insert(0, {"role": "system", "content": system_prompt})

# 显示 system prompt（调试）
if st.checkbox("🔍 显示当前 System Prompt"):
    st.code(system_prompt)

# 显示历史消息
st.markdown("### 🧾 对话历史")
for msg in st.session_state.messages[1:]:  # 排除 system prompt
    role = "user" if msg["role"] == "user" else "assistant"
    emoji = "🧑" if msg["role"] == "user" else "🤖"
    with st.chat_message(role):
        st.markdown(f"{emoji} **{msg['content']}**")

# 清除对话按钮
if st.button("🧹 清除对话历史"):
    st.session_state.messages = [{"role": "system", "content": system_prompt}]
    st.success("已清除")

# 用户输入
style_hint_map = {
    "温柔倾听型": "有什么让你牵挂或疲惫的事？慢慢说，我一直在听。",
    "理性建议型": "说说你的问题或想法，我们一起来理清。",
    "鼓励支持型": "写下你的烦恼或目标，我会支持你！"
}

user_input = st.chat_input(style_hint_map.get(st.session_state.style, "写下你的感受，我在这儿听你说。"))
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("🤖 AI 正在思考中..."):
        try:
            url = "https://api.deepseek.com/chat/completions"
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "deepseek-chat",
                "messages": st.session_state.messages,
                "temperature": 0.85,
                "stream": False
            }

            resp = requests.post(url, headers=headers, json=data)
            resp.raise_for_status()
            result = resp.json()
            reply = result["choices"][0]["message"]["content"]

            st.session_state.messages.append({"role": "assistant", "content": reply})

            with st.chat_message("🤖 AI"):
                st.markdown(reply)

            # 评分反馈
            rating = st.radio("📊 这条回应是否符合人样风格？", ["👍 合适", "👎 偏差"], horizontal=True, key=f"rating_{len(st.session_state.messages)}")
            if rating:
                with open("prompt_logs.csv", "a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([st.session_state.style, st.session_state.version, user_input, reply, rating])
                st.success("✅ 你的反馈已记录")

        except Exception as e:
            st.error(f"出错了：{e}")
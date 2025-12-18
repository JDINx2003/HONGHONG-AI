import streamlit as st
import edge_tts
import asyncio
import google.generativeai as genai
import time
import os

# --- 1. 页面配置 ---
st.set_page_config(page_title="哄哄 - Gemini语音版", page_icon="icon.png")
st.title("🧸 哄哄 - 你的专属情绪搭档")

# --- 2. 侧边栏设置 ---
with st.sidebar:
    st.header("⚙️ 设置")
    
    # 🔑 Google API Key
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Gemini 已连接")
    else:
        api_key = st.text_input("请输入 Google API Key", type="password")
        if not api_key:
            st.warning("⚠️ 请输入 Key 才能启动哄哄")

    # 🗣️ 声音模型 (Edge-TTS)
    voice = st.selectbox(
        "选择声音",
        options=["zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural"],
        format_func=lambda x: "🌸 晓晓 (治愈女声)" if "Xiaoxiao" in x else "🌲 云希 (温暖男声)"
    )

    # 🎭 角色人设
    system_prompt = "你叫哄哄，是一个超级温柔、有同理心的情感支持AI。你的任务是无条件站在用户这边，倾听他们的烦恼，并用温暖、可爱的语气安慰他们。多使用“乖乖”、“抱抱”、“别怕”等词汇。回复不要太长，像朋友聊天一样。"

# --- 3. 核心功能函数 ---

# (A) 语音合成 (使用 Edge-TTS)
async def generate_audio(text, voice, output_file):
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_file)
    except Exception as e:
        st.error(f"语音合成出错: {e}")

# (B) Google Gemini 模型调用 🔴 重点修正区域
def get_gemini_response(history_messages, user_input, api_key):
    if not api_key:
        return "请先配置 API Key 哦～"
    
    try:
        # 配置 Google API
        genai.configure(api_key=api_key)
        
        # 🌟 修正点：使用正确的模型名称，且使用英文括号
        model = genai.GenerativeModel('gemini-3-flash-preview') 
        
        # 转换历史记录 (Streamlit -> Gemini 格式)
        gemini_history = []
        for msg in history_messages:
            # Gemini 的角色只能是 'user' 或 'model'
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg["content"]]})
        
        # 启动对话
        chat = model.start_chat(history=gemini_history)
        
        # 拼接人设指令 (System Prompt)
        full_message = f"{system_prompt}\n\n用户说：{user_input}"
        
        response = chat.send_message(full_message)
        return response.text
    except Exception as e:
        return f"Gemini 连接断开了: {e}"

# --- 4. 聊天主逻辑 ---

if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史消息 (带头像)
for msg in st.session_state.messages:
    # 🐻 设置头像：机器人用熊，用户用人
    avatar_icon = "icon.png" if msg["role"] == "assistant" else "🧑‍💻"
    
    with st.chat_message(msg["role"], avatar=avatar_icon):
        st.markdown(msg["content"])
        if "audio_file" in msg:
            st.audio(msg["audio_file"])

# 处理用户输入
if prompt := st.chat_input("说点什么..."):
    
    # 1. 显示用户输入
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    # 2. 生成 AI 回复
    with st.chat_message("assistant", avatar="🧸"):
        with st.spinner("哄哄正在思考..."):
            # 获取 Gemini 回复
            history_for_api = st.session_state.messages[:-1]
            reply_text = get_gemini_response(history_for_api, prompt, api_key)
            
            st.markdown(reply_text)
            
            # 3. 生成语音
            if api_key:
                timestamp = int(time.time())
                audio_file = f"reply_{timestamp}.mp3"
                
                asyncio.run(generate_audio(reply_text, voice, audio_file))
                st.audio(audio_file)
                
                # 存入历史
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": reply_text,
                    "audio_file": audio_file
                })
            else:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": reply_text
                })

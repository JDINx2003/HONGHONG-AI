import streamlit as st
import edge_tts
import asyncio
import google.generativeai as genai
import time
import os

# --- 1. 页面基础设置 ---
st.set_page_config(page_title="哄哄 - AI 语音伴侣", page_icon="🧸")
st.title("🧸 哄哄 - 你的专属情绪搭档")

# --- 2. 侧边栏设置 ---
with st.sidebar:
    st.header("⚙️ 设置")
    
    # 🔑 Google API Key 配置
    # 优先从 Secrets 读取，如果没有则显示输入框
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ 已连接 Google Gemini")
    else:
        api_key = st.text_input("请输入 Google API Key", type="password")
        if not api_key:
            st.warning("⚠️ 请输入 Key 才能启动哄哄哦")

    # 🗣️ 声音选择 (只保留效果最好的两个)
    voice = st.selectbox(
        "选择声音",
        options=["zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural"],
        format_func=lambda x: "🌸 晓晓 (治愈女声)" if "Xiaoxiao" in x else "🌲 云希 (温暖男声)"
    )

    # 🎭 角色人设 (System Prompt)
    system_prompt = "你叫哄哄，是一个超级温柔、有同理心的情感支持AI。你的任务是无条件站在用户这边，倾听他们的烦恼，并用温暖、可爱的语气安慰他们。多使用“乖乖”、“抱抱”、“别怕”等词汇。回复不要太长，要像朋友聊天一样自然。"

# --- 3. 功能函数 ---

# (A) 语音生成 (Edge-TTS)
async def generate_audio(text, voice, output_file):
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_file)
    except Exception as e:
        st.error(f"语音合成出错: {e}")

# (B) Gemini 模型调用
def get_gemini_response(history_messages, user_input, api_key):
    if not api_key:
        return "请先配置 API Key 也就是你的大脑链接密码哦～"
    
    try:
        genai.configure(api_key=api_key)
        # 使用 gemini-1.5-flash，速度快且免费额度高，非常适合聊天
        model = genai.GenerativeModel('gemini-3-flash-preview')
        
        # 转换历史记录格式 (Streamlit -> Gemini)
        gemini_history = []
        for msg in history_messages:
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg["content"]]})
        
        # 启动对话上下文
        chat = model.start_chat(history=gemini_history)
        
        # 发送带有人设指令的消息
        # 技巧：如果是第一次对话，或者为了强化人设，把 prompt 拼在前面
        full_message = f"{system_prompt}\n\n用户说：{user_input}"
        
        response = chat.send_message(full_message)
        return response.text
    except Exception as e:
        return f"哄哄的大脑连接断开啦: {e}"

# --- 4. 聊天界面逻辑 ---

# 初始化历史记录
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示聊天历史 (保留文字和对应的语音条)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # 如果该条消息有语音文件，显示播放器
        if "audio_file" in msg:
            st.audio(msg["audio_file"])

# 聊天输入处理
if prompt := st.chat_input("在这里倾诉你的心情..."):
    
    # 1. 显示用户输入
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. 生成 AI 回复
    with st.chat_message("assistant"):
        # 这里的占位符会显示加载动画
        with st.spinner("哄哄正在听..."):
            # 获取 Gemini 的文字回复
            # 注意：传入的是除去当前这条之外的历史，因为 current prompt 单独传
            history_for_api = st.session_state.messages[:-1]
            reply_text = get_gemini_response(history_for_api, prompt, api_key)
            
            # 先显示文字
            st.markdown(reply_text)
            
            # 3. 立即生成并播放语音
            if api_key:
                timestamp = int(time.time())
                audio_file = f"reply_{timestamp}.mp3"
                
                # 运行异步语音生成
                asyncio.run(generate_audio(reply_text, voice, audio_file))
                
                # 显示播放器 (autoplay=True 在某些浏览器可能生效)
                st.audio(audio_file)
                
                # 4. 将回复存入历史 (包含音频路径)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": reply_text,
                    "audio_file": audio_file
                })
            else:
                # 如果没有 Key，只存文字
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": reply_text
                })

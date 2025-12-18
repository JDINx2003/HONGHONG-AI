import streamlit as st
import google.generativeai as genai
import os
import time
from gtts import gTTS
import tempfile

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="哄哄 - 你的AI挚友", 
    page_icon="icon.png",
    layout="wide" # 开启宽屏模式，方便放侧边栏
)

# --- 2. 加载 API Key ---
try:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("⚠️ 没找到 Key，请检查 Settings。")
    st.stop()

# --- 3. 加载模型 (已修正！) ---
@st.cache_resource
def get_model():
    return genai.GenerativeModel(
        model_name="gemini-3-flash-preview",  # <--- 确认修改！使用 Gemini 3
        system_instruction="""
Role: You are "哄哄" (HongHong), a gentle, warm white bear companion.
IMPORTANT: Your name is written as "哄哄" (not 宏宏).
Language: Chinese (Mandarin).
Personality: Unconditional positive regard. Never judge.
Catchphrase: Use "别怕，有我呢" only when the user is very sad.
Constraint: Keep responses concise (1-3 sentences).
"""
    )

model = get_model()

# --- 4. 初始化历史 ---
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# --- 辅助函数：文字转语音 ---
def play_audio(text):
    try:
        tts = gTTS(text=text, lang='zh-cn')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            st.audio(fp.name, format="audio/mp3", autoplay=True) # 尝试自动播放
            return fp.name
    except:
        return None

# ==========================================
# 🛑 V1.1 新功能区：侧边栏控制台
# ==========================================
with st.sidebar:
    st.image("icon.png", width=100)
    st.title("功能控制台")
    
    # --- 功能 A: 情绪急救包 (Panic Button) ---
    st.markdown("### 🆘 情绪急救")
    if st.button("我快崩溃了 (Panic)", type="primary"):
        # 1. 构造一个隐形的求救 Prompt
        emergency_prompt = "我现在情绪非常非常糟糕，感觉快要崩溃了，请立刻安抚我，语气要非常温柔，一定要用上你的口头禅。"
        
        # 2. 强制 AI 回复
        chat_history = [{"role": "user" if m["role"] == "user" else "model", "parts": m["content"]} for m in st.session_state.messages]
        chat = model.start_chat(history=chat_history)
        
        with st.spinner("哄哄正在飞奔过来..."):
            response = chat.send_message(emergency_prompt)
            ai_text = response.text
            
            # 3. 存入历史并强制刷新页面以显示
            st.session_state.messages.append({"role": "user", "content": "🔴 [按下了情绪急救按钮]"})
            st.session_state.messages.append({"role": "assistant", "content": ai_text, "is_emergency": True})
            st.rerun() # 重新运行以显示最新消息

    st.divider()

    # --- 功能 B: 情感周报 (Mood Report) ---
    st.markdown("### 📊 情感总结")
    if st.button("生成本次对话总结"):
        if len(st.session_state.messages) < 3:
            st.warning("聊得太少啦，多说两句我才能总结哦~")
        else:
            # 1. 把所有聊天记录打包发给 AI 分析
            full_history = str(st.session_state.messages)
            report_prompt = f"""
            基于以下对话历史：{full_history}
            请为用户生成一份温暖的【情感总结卡片】。
            格式要求：
            1. 🏷️ **情绪关键词**：(3个词)
            2. 💡 **哄哄的观察**：(一句话概括用户今天的心情)
            3. ❤️ **暖心寄语**：(一句鼓励的话)
            不要用Markdown代码块，直接显示文字。
            """
            
            chat = model.start_chat(history=[])
            with st.spinner("正在分析你的心情..."):
                response = chat.send_message(report_prompt)
                st.markdown("---")
                st.success(response.text)
                st.balloons() # 放个气球庆祝一下

# ==========================================
# 💬 主聊天区域
# ==========================================

st.title("🐻 哄哄 HongHong")
st.caption("让你的每个情绪都有出口 | 别怕，有我呢。")

# 显示历史消息
for msg in st.session_state.messages:
    avatar = "icon.png" if msg["role"] == "assistant" else "🧑‍💻"
    
    with st.chat_message(msg["role"], avatar=avatar):
        # 如果是急救消息，加粗显示
        if msg.get("is_emergency"):
            st.error(f"🚑 {msg['content']}") # 用红色框显示急救消息
            # 如果是刚刚生成的急救消息，播放声音
            if msg == st.session_state.messages[-1]: 
                play_audio(msg['content'])
        else:
            st.write(msg["content"])
            
        if "audio" in msg:
            st.audio(msg["audio"])

# 处理用户输入
if prompt := st.chat_input("说点什么吧..."):
    with st.chat_message("user", avatar="🧑‍💻"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        chat_history = [{"role": "user" if m["role"] == "user" else "model", "parts": m["content"]} for m in st.session_state.messages[:-1]]
        chat = model.start_chat(history=chat_history)
        
        with st.spinner("哄哄正在思考..."):
            response = chat.send_message(prompt)
            ai_text = response.text
            
            with st.chat_message("assistant", avatar="icon.png"):
                st.write(ai_text)
                audio_path = play_audio(ai_text) # 播放语音
        
        st.session_state.messages.append({"role": "assistant", "content": ai_text, "audio": audio_path})
        
    except Exception as e:
        st.error(f"小白熊有点晕: {e}")

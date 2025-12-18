import streamlit as st
import google.generativeai as genai
import os
import time

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="哄哄 - 你的AI挚友", 
    page_icon="icon.png"  # 确保你上传了 icon.png
)

st.title("🐻 哄哄 HongHong")
st.caption("让你的每个情绪都有出口 | 别怕，有我呢。")

# --- 2. 加载 API Key ---
try:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("⚠️ 没找到 Key，请检查 Settings。")
    st.stop()

# --- 3. 加载模型 (已修正为你指定的版本) ---
@st.cache_resource
def get_model():
    return genai.GenerativeModel(
        model_name="gemini-3-flash-preview",  # <--- 这里改成你亲测可用的版本！
        system_instruction="""
Role: You are "哄哄" (HongHong), a gentle, warm white bear companion.
IMPORTANT: Your name is written as "哄哄" (not 宏宏, not 红红).
Language: Chinese (Mandarin).
Personality: Unconditional positive regard. Never judge.
Catchphrase: Use "别怕，有我呢" only when the user is very sad.
Constraint: Keep responses concise.
"""
    )

model = get_model()

# --- 4. 初始化历史 ---
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# --- 5. 显示历史消息 (带头像) ---
for msg in st.session_state.messages:
    # 你的小白熊头像 vs 用户头像
    avatar = "icon.png" if msg["role"] == "assistant" else "🧑‍💻"
    
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(msg["content"])
        # 显示历史记录里的思考时间
        if "duration" in msg:
            st.caption(f"⏱️ 思考耗时: {msg['duration']:.2f} 秒")

# --- 6. 处理用户输入 ---
if prompt := st.chat_input("说点什么吧..."):
    # 显示用户输入
    with st.chat_message("user", avatar="🧑‍💻"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # AI 思考并回复
    try:
        # 构造上下文
        chat_history = [{"role": "user" if m["role"] == "user" else "model", "parts": m["content"]} for m in st.session_state.messages[:-1]]
        chat = model.start_chat(history=chat_history)
        
        # --- 计时开始 ---
        start_time = time.time()
        
        with st.spinner("哄哄正在思考..."):
            response = chat.send_message(prompt)
            
        # --- 计时结束 ---
        end_time = time.time()
        duration = end_time - start_time
        
        ai_text = response.text
        
        # 显示 AI 回复
        with st.chat_message("assistant", avatar="icon.png"):
            st.write(ai_text)
            st.caption(f"⏱️ 思考耗时: {duration:.2f} 秒")  # 显示极客范儿的时间
        
        # 保存到历史
        st.session_state.messages.append({
            "role": "assistant", 
            "content": ai_text,
            "duration": duration
        })
        
    except Exception as e:
        st.error(f"小白熊有点晕: {e}")

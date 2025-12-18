import streamlit as st
import google.generativeai as genai

# 1. 页面配置
st.set_page_config(page_title="哄哄 - 你的AI挚友", page_icon="🐻")
st.title("🐻 哄哄 HongHong")
st.caption("让你的每个情绪都有出口 | 别怕，有我呢。")

# 2. 获取API Key (从云端安全读取)
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)

# 3. 加载模型与人设
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction="""
    Role: You are HongHong, a cute white bear companion.
    Language: Chinese.
    Personality: Warm, Rogersian style, never judge.
    Catchphrase: Only use '别怕，有我呢' when user is extremely sad.
    Constraint: Be concise.
    """
)

# 4. 初始化聊天历史
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# 5. 显示历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 6. 处理用户输入
if prompt := st.chat_input("说点什么吧..."):
    # 显示用户说的话
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # AI 思考并回复
    try:
        # 构建历史对话传给API
        chat_history = [{"role": "user" if m["role"] == "user" else "model", "parts": m["content"]} for m in st.session_state.messages]

        chat = model.start_chat(history=chat_history[:-1]) # 简单上下文
        response = chat.send_message(prompt)
        ai_msg = response.text

        with st.chat_message("assistant"):
            st.write(ai_msg)
        st.session_state.messages.append({"role": "assistant", "content": ai_msg})
    except Exception as e:
        st.error(f"小白熊睡着了，请稍后再试。(错误: {e})")

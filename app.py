import streamlit as st
import edge_tts
import asyncio
import os

# 1. 基础页面设置
st.set_page_config(page_title="哄哄模拟器", page_icon="🤖")
st.title("哄哄 - 你的专属情绪搭档")

# 2. 定义语音合成函数 (异步)
async def generate_audio_file(text, output_file="reply_audio.mp3"):
    # 使用晓晓的声音 (zh-CN-XiaoxiaoNeural)
    communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
    await communicate.save(output_file)

# 3. 初始化聊天历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 4. 显示之前的聊天记录
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # 如果历史消息里有音频，也可以选择显示（这里为了界面简洁，历史消息我暂时没放音频播放器）

# 5. 聊天输入框处理逻辑
if prompt := st.chat_input("说点什么吧..."):
    
    # --- 显示用户消息 ---
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- 显示并生成 AI 回复 ---
    with st.chat_message("assistant"):
        
        # 🔴【关键点】这里是你原本连接 AI (如 OpenAI/Kimi 等) 的地方
        # 为了演示，我先写死一段回复。你要把下面这行改成你真实的 AI 调用代码
        # 例如: response_text = call_my_ai_function(prompt)
        response_text = "乖乖，别怕，有我呢。我会一直在这里守着你，把所有的委屈都交给我吧。" 
        
        # 显示文字回复
        st.markdown(response_text)
        
        # 🟢【新增】文字显示完后，立刻开始生成语音
        audio_file = "current_reply.mp3"
        with st.spinner("正在生成语音..."):
            try:
                # 运行异步语音生成
                asyncio.run(generate_audio_file(response_text, audio_file))
                
                # 直接在气泡下方显示播放器，并自动播放（autoplay在部分浏览器支持）
                st.audio(audio_file, format="audio/mp3", start_time=0)
                
            except Exception as e:
                st.error(f"语音生成失败: {e}")

    # 将回复存入历史
    st.session_state.messages.append({"role": "assistant", "content": response_text})

import streamlit as st
import ollama
import requests
import os

# Check if Ollama is available
def check_ollama_connection():
    try:
        # Try to connect to Ollama
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

# Check if we're running locally or in cloud
def is_local_environment():
    return os.getenv('STREAMLIT_SHARING_MODE') is None

# Display connection status
if not check_ollama_connection():
    if is_local_environment():
        st.error("⚠️ Ollama is not running locally. Please start Ollama by running `ollama serve` in your terminal.")
    else:
        st.error("⚠️ This app requires Ollama to be running locally. Streamlit Cloud doesn't support local Ollama instances.")
        st.info("💡 **Solutions:**\n"
                "1. Run this app locally with `streamlit run app.py`\n"
                "2. Deploy Ollama on a cloud server and modify the connection URL\n"
                "3. Use a different hosting platform that supports Docker (Railway, Render, etc.)")
    st.stop()

# Show success message if connected
st.success("✅ Connected to Ollama successfully!")

# Creates a session state to store messages
# This allows the app to remember previous messages
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Display Previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if 'image' in message:
            st.image(message["image"], caption="Image uploaded by user", use_container_width=True)

with st.container():
    file_upload = st.file_uploader("Upload an image file", type=["png", "jpg", "jpeg", "svg"])

if prompt := st.chat_input("Welcome to the Ollama Chatbot! Ask me anything"):
    # User input is captured and added to the session state
    user_prompt = {"role": "user", "content": prompt}
    
    if file_upload:
        try:
            user_prompt['image'] = file_upload.getvalue()
        except Exception as e:
            st.error(f"Error reading uploaded file: {e}")
    
    st.session_state.messages.append(user_prompt)
    
    with st.chat_message("user"):
        st.write(prompt)
        if file_upload:
            try:
                st.image(file_upload, caption="Upload Successful", use_container_width=True)
            except Exception as e:
                st.error(f"Error displaying uploaded image: {e}")
    
    # The model processes the input and generates a response
    with st.chat_message("assistant"):
        try:
            model_message = []
            for m in st.session_state.messages:
                msg = {"role": m["role"], "content": m['content']}
                if m.get('image'):
                    msg['images'] = [m['image']]  # Fixed: should be 'images' not 'image'
                model_message.append(msg)
            
            # Check connection before making the request
            if not check_ollama_connection():
                st.error("❌ Lost connection to Ollama. Please restart the Ollama service.")
                st.stop()
            
            response = ollama.chat(model='llava', messages=model_message, stream=True)
            response_text = ""
            
            def catch_response(response):
                nonlocal response_text  # Fixed: use nonlocal instead of global
                for chunks in response:
                    response_text += chunks['message']['content']
                    yield chunks['message']['content']
            
            response_stream = catch_response(response)
            st.write_stream(response_stream)
            
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            
        except Exception as e:
            st.error(f"Error communicating with the model: {e}")
            
            # Provide specific error handling
            if "Connection refused" in str(e):
                st.error("🔌 Ollama service is not running. Please start it with `ollama serve`")
            elif "llava" in str(e):
                st.error("📦 The 'llava' model is not installed. Run `ollama pull llava` to install it.")
            else:
                st.error(f"Unexpected error: {e}")

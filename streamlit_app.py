import streamlit as st
import ollama

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if 'image' in message:
            st.image(message["image"], caption="Image uploaded by user", use_container_width=True)

# File uploader container
with st.container():
    file_upload = st.file_uploader("Upload an image file", type=["png", "jpg", "jpeg", "svg"])

# Chat input
if prompt := st.chat_input("Welcome to the Ollama Chatbot! Ask me anything"):
    user_prompt = {"role": "user", "content": prompt}

    if file_upload:
        try:
            user_prompt['image'] = file_upload.getvalue()
        except Exception as e:
            st.error(f"Error reading uploaded file: {e}")

    st.session_state.messages.append(user_prompt)

    with st.chat_message("user"):
        st.markdown(prompt)
        if file_upload:
            try:
                if file_upload.name.endswith(".svg"):
                    st.markdown(file_upload.getvalue().decode('utf-8'), unsafe_allow_html=True)
                else:
                    st.image(file_upload, caption="Upload Successful", use_container_width=True)
            except Exception as e:
                st.error(f"Error displaying uploaded image: {e}")

    # Ollama model response
    with st.chat_message("assistant"):
        try:
            model_messages = []
            for m in st.session_state.messages:
                msg = {"role": m["role"], "content": m["content"]}
                if m.get("image"):
                    msg["image"] = m["image"]  # Pass the image as is
                model_messages.append(msg)

            response = ollama.chat(model='llava', messages=model_messages, stream=True)

            response_text = ""
            placeholder = st.empty()

            for chunk in response:
                content = chunk["message"]["content"]
                response_text += content
                placeholder.markdown(response_text)

            st.session_state.messages.append({"role": "assistant", "content": response_text})

        except Exception as e:
            st.error(f"Error communicating with the model: {e}")

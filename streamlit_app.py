import streamlit as st
import ollama
#Creates a session state to store messages
#This allows the app to remember previous messages
if 'messages' not in st.session_state:
    st.session_state.messages = []
#Display Previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if 'image' in message:
            st.image(message["image"], caption="Image uploaded by user", use_container_width=True)
with st.container():
    file_upload = st.file_uploader("Upload an image file", type=["png", "jpg", "jpeg","svg"])
if prompt:= st.chat_input("Welcome to the Ollama Chatbot! Ask me anything"):
        #User input is captured and added to the session state
        user_prompt = {"role": "user", "content": prompt}

        if file_upload:
            try:
                user_prompt['image']=file_upload.getvalue()
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
        #The model processes the input and generates a response
        with st.chat_message("assistant"):
            try:
                model_message = []
                for m in st.session_state.messages:
                    msg={"role": m["role"], "content": m['content']}
                    if m.get('image'):
                        msg['image']=[m['image']]
                        model_message.append(msg)
                response = ollama.chat(model='llava', messages=model_message, stream=True)
                response_text = ""
                def catch_response(response):
                    global response_text
                    for chunks in response:
                        response_text += chunks['message']['content']
                        yield chunks['message']['content']
                response_stream = catch_response(response)
                st.write_stream(response_stream)

                st.session_state.messages.append({"role": "assistant", "content": response_text})
            except Exception as e:
                st.error(f"Error communicating with the model: {e}")

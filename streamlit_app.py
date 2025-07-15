import streamlit as st
import ollama
import requests
import json

st.title('QueryBuddy Chatbox')

def safe_get_models():
    try:
        # Method 1: Direct API call
        response = requests.get('http://localhost:11434/api/tags', timeout=10)
        if response.status_code == 200:
            data = response.json()
            st.success("✅ Connection approved")
            
            # Handle different response formats
            if 'models' in data:
                models = data['models']
                if models:
                    model_names = []
                    for model in models:
                        if isinstance(model, dict) and 'name' in model:
                            model_names.append(model['name'])
                        elif isinstance(model, str):
                            model_names.append(model)
                    return model_names
                else:
                    return []
            else:
                st.warning("Unexpected API response format")
                return []
        else:
            st.error(f"API returned status {response.status_code}")
            return None
            
    except Exception as e:
        st.error(f"Direct API failed: {e}")
        
        # Method 2: Try ollama library
        try:
            models_response = ollama.list()
            st.info("Trying ollama library...")
            
            if isinstance(models_response, dict) and 'models' in models_response:
                models = models_response['models']
                model_names = []
                for model in models:
                    if isinstance(model, dict):
                        # Handle different possible key names
                        name = model.get('name') or model.get('model') or model.get('id')
                        if name:
                            model_names.append(name)
                return model_names
            else:
                st.error(f"Unexpected ollama.list() response: {models_response}")
                return []
                
        except Exception as e2:
            st.error(f"Ollama library also failed: {e2}")
            return None

def ensure_model_available(model_name):
    """Ensure a model is available, pull if necessary"""
    try:
        # Try to pull the model
        st.info(f"Pulling model {model_name}...")
        ollama.pull(model_name)
        st.success(f"✅ Model {model_name} ready!")
        return True
    except Exception as e:
        st.error(f"Failed to pull model {model_name}: {e}")
        return False

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Check connection and get models
st.write("Checking Ollama connection...")
available_models = safe_get_models()

if available_models is None:
    st.error("❌ Cannot connect to Ollama server")
    st.info("Make sure Ollama server is running:")
    st.code("ollama serve")
    st.stop()

elif len(available_models) == 0:
    st.warning("No models found. Let's pull one...")
    if ensure_model_available("llama3.2:1b"):
        available_models = ["llama3.2:1b"]
    else:
        st.error("Failed to pull model. Please try manually:")
        st.code("ollama pull llama3.2:1b")
        st.stop()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if 'image' in message:
            st.image(message["image"], caption="Image uploaded by user", use_container_width=True)

# File uploader (only if model supports images)
file_upload = None
with st.container():
    file_upload = st.file_uploader("Upload an image file", type=["png", "jpg", "jpeg"])

# Chat input
if prompt := st.chat_input("Ask me anything..."):
    # Create user message
    user_prompt = {"role": "user", "content": prompt}
    
    # Add image if uploaded and supported
    if file_upload:
        try:
            user_prompt['image'] = file_upload.getvalue()
        except Exception as e:
            st.error(f"Error reading uploaded file: {e}")
    
    # Add to session state
    st.session_state.messages.append(user_prompt)
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
        if file_upload:
            try:
                st.image(file_upload, caption="Upload Successful", use_container_width=True)
            except Exception as e:
                st.error(f"Error displaying uploaded image: {e}")
    
    # Generate assistant response
    with st.chat_message("assistant"):
        try:
            # Prepare messages for model
            model_messages = []
            for m in st.session_state.messages:
                msg = {"role": m["role"], "content": m['content']}
                if m.get('image'):
                    msg['images'] = [m['image']]
                model_messages.append(msg)
            
            # Call the model
            response = ollama.chat(model='llava', messages=model_messages, stream=True)
            
            # Process streaming response
            response_text = ""
            response_placeholder = st.empty()
            
            for chunk in response:
                if 'message' in chunk and 'content' in chunk['message']:
                    response_text += chunk['message']['content']
                    response_placeholder.markdown(response_text)
            
            # Store final response
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            
        except Exception as e:
            st.error(f"Error communicating with the model: {e}")

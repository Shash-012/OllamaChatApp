import streamlit as st
import requests
import json
import os

st.title('QueryBuddy Chatbox - Cloud Compatible')

# Configuration for different environments
def get_ollama_config():
    """Get Ollama configuration based on environment"""
    
    # Check if running on Streamlit Cloud
    if os.getenv('STREAMLIT_SERVER_HEADLESS') == 'true':
        # Running on Streamlit Cloud - use remote Ollama or API
        st.info("🌐 Running on Streamlit Cloud")
        
        # Option 1: Use a remote Ollama instance
        remote_host = st.secrets.get("OLLAMA_HOST", "your-ollama-server.com:11434")
        return f"http://{remote_host}"
        
        # Option 2: Use OpenAI API instead (more reliable for cloud)
        # return "openai"
        
    else:
        # Running locally
        st.info("🏠 Running locally")
        return "http://localhost:11434"

def test_ollama_connection(host):
    """Test if Ollama is accessible"""
    try:
        response = requests.get(f"{host}/api/tags", timeout=10)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"Status: {response.status_code}"
    except Exception as e:
        return False, str(e)

def get_available_models(host):
    """Get available models from Ollama"""
    try:
        response = requests.get(f"{host}/api/tags", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
        return []
    except:
        return []

def chat_with_ollama(host, model, messages):
    """Chat with Ollama via direct API calls"""
    try:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        
        response = requests.post(
            f"{host}/api/chat",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()['message']['content']
        else:
            return f"Error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"Error: {str(e)}"

def chat_with_openai(messages):
    """Alternative: Use OpenAI API (more reliable for cloud deployment)"""
    try:
        import openai
        
        # Get API key from Streamlit secrets
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"OpenAI Error: {str(e)}"

# Main app logic
def main():
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Get configuration
    ollama_host = get_ollama_config()
    
    # Check if we should use OpenAI instead
    use_openai = st.checkbox("Use OpenAI instead of Ollama (more reliable for cloud)", 
                           value=os.getenv('STREAMLIT_SERVER_HEADLESS') == 'true')
    
    if not use_openai:
        # Test Ollama connection
        connected, result = test_ollama_connection(ollama_host)
        
        if not connected:
            st.error(f"❌ Cannot connect to Ollama: {result}")
            st.info("Solutions:")
            st.info("1. If running locally: Start Ollama with `ollama serve`")
            st.info("2. If on Streamlit Cloud: Set up remote Ollama server")
            st.info("3. Use OpenAI checkbox above as alternative")
            return
        
        # Get available models
        models = get_available_models(ollama_host)
        if not models:
            st.error("No models available")
            return
        
        selected_model = st.selectbox("Select model:", models)
        st.success(f"✅ Connected to Ollama at {ollama_host}")
    
    else:
        # Using OpenAI
        if "OPENAI_API_KEY" not in st.secrets:
            st.error("OpenAI API key not found in secrets")
            st.info("Add OPENAI_API_KEY to your Streamlit secrets")
            return
        selected_model = "gpt-3.5-turbo"
        st.success("✅ Using OpenAI API")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                if use_openai:
                    response = chat_with_openai(st.session_state.messages)
                else:
                    response = chat_with_ollama(ollama_host, selected_model, st.session_state.messages)
                
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()

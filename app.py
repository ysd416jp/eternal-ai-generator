# -*- coding: utf-8 -*-
import streamlit as st
import requests
import time
import os

# API key configuration
KEY_FILE_PATH = "/Users/yoichiroyoshida/my_ai_app/eternal_api_key.txt"

def load_api_key():
    # Streamlit Cloud environment variable (priority)
    cloud_key = os.environ.get("ETERNAL_API_KEY")
    if cloud_key:
        return cloud_key
    
    # Local file fallback
    try:
        with open(KEY_FILE_PATH, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

# UI Configuration
st.set_page_config(page_title="EternalAI Image Generator", layout="wide")
st.title("🎨 EternalAI Image Generator")
st.markdown("Enter a prompt and AI will generate an image for you.")

api_key = load_api_key()
if not api_key:
    st.error("API key not found")
    st.stop()

# Input Area
col1, col2 = st.columns([1, 1])
with col1:
    st.info("📝 Describe the image you want to generate (in English)")
    prompt_text = st.text_area("Prompt (English)", height=150, value="A futuristic city with flying cars, cinematic lighting")
    
    # Image upload (reference image)
    st.markdown("---")
    st.info("🖼️ Reference Image (Optional)")
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"], help="Reference image for generation (if EternalAI API supports it)")
    
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
    
    generate_btn = st.button("🚀 Generate", type="primary")

# Generation Logic
if generate_btn:
    st.divider()
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    # 1. Send request (POST)
    url_create = "https://open.eternalai.org/creative-ai/image"
    
    # Payload configuration (without lora_config)
    payload = {
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt_text}]}],
        "type": "new"
    }
    
    headers = {
        'x-api-key': api_key,
        'Content-Type': 'application/json'
    }

    try:
        status_text.text("Sending request...")
        
        # Debug: show payload
        with col2:
            st.info("📤 Sending payload:")
            st.json(payload)
        
        response = requests.post(url_create, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            request_id = data.get("request_id")
            
            with col2:
                st.success(f"✅ Request sent! ID: {request_id}")
            
            # UUID format uses path parameter
            check_url_base = "https://open.eternalai.org/poll-result"
            st.caption("ℹ️ Generating image... (typically takes 45s - 1min)")
            
            # 2. Polling loop (max 5 minutes)
            status_text.text("Processing... (max 5 minutes)")
            
            for i in range(150):
                time.sleep(2)
                
                current_val = int(min((i + 1) / 40 * 100, 95))
                progress_bar.progress(current_val)
                
                # Path parameter: /poll-result/{id}
                check_url = f"{check_url_base}/{request_id}"
                check_res = requests.get(check_url, headers={'x-api-key': api_key})
                
                if check_res.status_code == 200:
                    res_data = check_res.json()
                    status = res_data.get("status")
                    
                    if status in ["done", "success", "completed"]:
                        progress_bar.progress(100)
                        
                        img_url = res_data.get("result_url") or res_data.get("result")
                        
                        if img_url:
                            with col2:
                                st.balloons()
                                st.success("✨ Generation complete!")
                                st.image(img_url, caption="Generated Result")
                                st.markdown(f"[Download Image]({img_url})")
                        else:
                            st.warning("Completed but image URL not found.")
                            st.json(res_data)
                        break
                    
                    elif status in ["pending", "processing"]:
                        status_text.text(f"Generating... ({i*2}s elapsed)")
                    
                    elif status == "failed":
                        st.error("Generation failed.")
                        st.json(res_data)
                        break
                
                elif check_res.status_code == 404:
                    status_text.text(f"Server preparing... ({i*2}s elapsed)")
                
                else:
                    st.error(f"Communication error: {check_res.status_code}")
            else:
                st.error("Timeout.")

        else:
            st.error(f"Request failed: {response.text}")

    except Exception as e:
        st.error(f"Error: {e}")

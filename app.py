# -*- coding: utf-8 -*-
import streamlit as st
import requests
import time
import os
import base64
from io import BytesIO
from PIL import Image
import datetime

# Initialize session state for image history
if "generated_images" not in st.session_state:
    st.session_state.generated_images = []

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

# Custom CSS for compact layout and DARK MODE
st.markdown("""
<style>
    /* Force Dark Mode */
    .stApp {
        background-color: #0E1117 !important;
        color: #E0E0E0 !important;
    }
    
    /* Header dark */
    header[data-testid="stHeader"] {
        background-color: #0E1117 !important;
    }
    
    /* Reduce top padding */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        background-color: #0E1117 !important;
    }
    
    /* Sidebar dark */
    section[data-testid="stSidebar"] {
        background-color: #0E1117 !important;
    }
    
    /* Compact sections */
    .stMarkdown {
        margin-bottom: 0.5rem;
        color: #E0E0E0 !important;
    }
    
    /* Larger slider handle */
    div[data-baseweb="slider"] > div > div > div > div {
        width: 20px !important;
        height: 20px !important;
    }
    
    /* Purple radio buttons - FORCE CLEAN */
    /* Target Streamlit's radio button structure */
    div[role="radiogroup"] label {
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        color: #E0E0E0 !important;
        cursor: pointer !important;
    }
    
    /* Hide the default input */
    div[role="radiogroup"] label input[type="radio"] {
        display: none !important;
    }
    
    /* Hide ALL baseweb radio elements */
    div[data-baseweb="radio"] {
        display: none !important;
    }
    
    /* Create custom radio button with ::before */
    div[role="radiogroup"] label::before {
        content: '' !important;
        display: inline-block !important;
        width: 18px !important;
        height: 18px !important;
        min-width: 18px !important;
        border: 2px solid #8B5CF6 !important;
        border-radius: 50% !important;
        background-color: #0E1117 !important;
        margin-right: 8px !important;
        position: relative !important;
        flex-shrink: 0 !important;
    }
    
    /* White dot when checked */
    div[role="radiogroup"] label:has(input:checked)::before {
        box-shadow: inset 0 0 0 4px #0E1117, inset 0 0 0 10px #FFFFFF !important;
        background-color: #FFFFFF !important;
    }
    
    /* Alternative: if :has() doesn't work, use data attribute */
    div[role="radiogroup"] label[data-checked="true"]::before {
        box-shadow: inset 0 0 0 4px #0E1117, inset 0 0 0 10px #FFFFFF !important;
        background-color: #FFFFFF !important;
    }
    
    /* Remove gap between radio groups */
    div[role="radiogroup"] {
        gap: 12px !important;
    }
    
    /* Horizontal layout */
    div[role="radiogroup"][data-baseweb="radio-group"] {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 12px !important;
    }
    
    /* White Generate button with black text + smaller size */
    button[kind="primary"] {
        background-color: #FFFFFF !important;
        border-color: #FFFFFF !important;
        color: #000000 !important;
        padding: 0.25rem 1rem !important;
        font-size: 14px !important;
        font-weight: 600 !important;
    }
    
    button[kind="primary"]:hover {
        background-color: #E0E0E0 !important;
        border-color: #E0E0E0 !important;
        color: #000000 !important;
    }
    
    button[kind="primary"] p {
        color: #000000 !important;
    }
    
    /* Dark mode for inputs */
    .stTextArea textarea, .stTextInput input, .stSelectbox select {
        background-color: #1E2329 !important;
        color: #E0E0E0 !important;
        border: 1px solid #333 !important;
        caret-color: #E0E0E0 !important;
    }
    
    /* Dark mode for selectbox dropdown */
    div[data-baseweb="select"] {
        background-color: #1E2329 !important;
    }
    
    /* Dark mode for file uploader */
    .stFileUploader {
        background-color: #1E2329 !important;
        border: 1px solid #333 !important;
    }
    
    div[data-testid="stFileUploader"] {
        background-color: #1E2329 !important;
    }
    
    div[data-testid="stFileUploader"] > div {
        background-color: #1E2329 !important;
    }
    
    /* Dark mode for expander */
    .streamlit-expanderHeader {
        background-color: #1E2329 !important;
        color: #E0E0E0 !important;
    }
    
    /* Labels with DARK text for white backgrounds (force override) */
    label, label > div, label > p, label > span {
        background-color: transparent !important;
        color: #111 !important;
        font-weight: 600 !important;
    }
    
    /* Pills styling - dark mode */
    div[data-testid="stPills"] {
        background-color: transparent !important;
    }
    
    div[data-testid="stPills"] button {
        background-color: #1E2329 !important;
        color: #E0E0E0 !important;
        border: 1px solid #333 !important;
        border-radius: 20px !important;
        padding: 6px 16px !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
    }
    
    /* Unselected pills - small */
    div[data-testid="stPills"] button:not([data-selected="true"]) {
        transform: scale(0.95);
        opacity: 0.7;
    }
    
    /* Selected pills - large and bright */
    div[data-testid="stPills"] button[data-selected="true"] {
        background-color: #4A90E2 !important;
        color: white !important;
        border: 2px solid #4A90E2 !important;
        box-shadow: 0 0 10px rgba(74, 144, 226, 0.5) !important;
        transform: scale(1.05);
        font-weight: 600 !important;
    }
    
    /* Hover effect */
    div[data-testid="stPills"] button:hover {
        background-color: #2A5A8A !important;
        transform: scale(1.02);
    }
    
    /* Hide fullscreen button */
    button[title="View fullscreen"] {
        display: none !important;
    }
    
    /* Dark mode for all text (except labels) */
    p, span, div {
        color: #E0E0E0 !important;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #FAFAFA !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
    # 【変更なし】ここから検索して場所を見つけてください
    # ---------------------------------------------------------------------------
        # Show dummy image in Before area (完全な暗黒)
        before_placeholder.markdown(f"""
        <div style="width: 100%; display: flex; justify-content: center; align-items: center;">
            <div style="width: 100%; aspect-ratio: {width}/{height}; background-color: #0E1117; border-radius: 5px;"></div>
        </div>
        """, unsafe_allow_html=True)
    
    # ---------------------------------------------------------------------------
    # 【ここから書き換え】元の "Show sparkle effect..." のブロックを以下にすべて差し替えます
    # ---------------------------------------------------------------------------

    # パーティクルの設定
    particle_count = 30
    particles_html = ""
    for i in range(particle_count):
        # 各パーティクルにランダムな動きのズレ(delay)を与える
        delay = i * -0.2
        particles_html += f'<div class="particle" style="--i:{i}; --delay:{delay}s;"></div>'

    # Show stylish particle sphere effect during generation
    after_placeholder.markdown(f"""
    <div class="loader-container">
        <div class="sphere-wrapper">
            {particles_html}
        </div>
        <p class="loading-text">Generating...</p>
    </div>
    
    <style>
    /* コンテナ全体 */
    .loader-container {{
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 300px;
        perspective: 1000px;
        background: transparent;
    }}

    /* 球体の中心 */
    .sphere-wrapper {{
        position: relative;
        width: 100px;
        height: 100px;
        transform-style: preserve-3d;
        animation: rotateSphere 10s linear infinite;
    }}

    /* 個々のパーティクル */
    .particle {{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        /* ワニワニウニョニョの動き */
        transform: rotateY(calc(var(--i) * (360deg / {particle_count}))) translateZ(60px);
        animation: unyoUnyo 3s ease-in-out infinite;
        animation-delay: var(--delay);
    }}

    /* パーティクルの実体（光る点） */
    .particle::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 50%;
        width: 6px;
        height: 6px;
        background: #00ffff;
        border-radius: 50%;
        transform: translateX(-50%);
        box-shadow: 0 0 10px #00ffff, 0 0 20px #00ffff;
    }}

    /* 球体全体の回転 */
    @keyframes rotateSphere {{
        0% {{ transform: rotateX(0deg) rotateY(0deg); }}
        100% {{ transform: rotateX(360deg) rotateY(360deg); }}
    }}

    /* 有機的な伸縮アニメーション */
    @keyframes unyoUnyo {{
        0%, 100% {{
            transform: rotateY(calc(var(--i) * (360deg / {particle_count}))) translateZ(60px) scale(1);
            filter: hue-rotate(0deg);
        }}
        50% {{
            transform: rotateY(calc(var(--i) * (360deg / {particle_count}))) translateZ(90px) scale(1.5);
            filter: hue-rotate(180deg);
        }}
    }}
    
    .loading-text {{
        margin-top: 50px;
        font-family: monospace;
        color: #00ffff;
        letter-spacing: 2px;
        font-size: 12px;
        animation: blink 1.5s infinite;
        text-shadow: 0 0 5px #00ffff;
    }}
    
    @keyframes blink {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.3; }}
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # ---------------------------------------------------------------------------
    # 【変更なし】ここから下の行はそのままでOKです（繋ぎ目の確認用）
    # ---------------------------------------------------------------------------
    try:
        status_text.text("Sending request...")
        
        response = requests.post(url_create, headers=headers, json=payload)



    try:
        status_text.text("Sending request...")
        
        response = requests.post(url_create, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            request_id = data.get("request_id") or data.get("id")
            
            # Legacy API polling (correct endpoint with /creative-ai/)
            check_url_base = "https://open.eternalai.org/creative-ai/poll-result"
            
            if image_base64:
                st.caption("Generating image (Image-to-Image mode)... typically 45s-1min")
            else:
                st.caption("Generating image... typically 45s-1min")
            
            # 2. Polling loop (max 5 minutes)
            status_text.text("Processing... (max 5 minutes)")
            
            for i in range(150):
                time.sleep(2)
                
                # Legacy API polling
                check_url = f"{check_url_base}/{request_id}"
                check_res = requests.get(check_url, headers={'x-api-key': api_key})
                
                if check_res.status_code == 200:
                    res_data = check_res.json()
                    status = res_data.get("status")
                    
                    if status in ["done", "success", "completed"]:
                        # Try multiple possible field names for image URL
                        img_url = (res_data.get("result_url") or 
                                  res_data.get("url") or 
                                  res_data.get("result") or 
                                  res_data.get("image_url") or
                                  res_data.get("output_url"))
                        
                        if img_url:
                            # Get image metadata (NO aspect ratio adjustment)
                            try:
                                img_response = requests.get(img_url)
                                img_size_kb = len(img_response.content) / 1024
                                img_pil = Image.open(BytesIO(img_response.content))
                                img_dimensions = f"{img_pil.width}x{img_pil.height}"
                            except Exception as e:
                                img_size_kb = 0
                                img_dimensions = "Unknown"
                                status_text.text(f"Error loading image: {e}")
                            except Exception as e:
                                img_size_kb = 0
                                img_dimensions = "Unknown"
                                img_pil = None
                                status_text.text(f"Error adjusting image: {e}")
                            
                            # 5) Add to history with full prompt (final_prompt)
                            st.session_state.generated_images.append({
                                "url": img_url,
                                "prompt": final_prompt,  # Full prompt with style + aspect ratio
                                "model": selected_model_short,
                                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "size_kb": f"{img_size_kb:.1f}",
                                "dimensions": img_dimensions,
                                "reference_image": uploaded_file.name if uploaded_file else None
                            })
                            
                            # Update After placeholder with generated image + View button overlay
                            after_placeholder.empty()
                            with after_placeholder.container():
                                st.markdown(f"""
                                <div style="position: relative;">
                                    <img src="{img_url}" style="width: 100%; border-radius: 5px;" />
                                    <div style="position: absolute; top: 5px; right: 5px;">
                                        <a href="{img_url}" target="_blank" 
                                           style="background: rgba(0,0,0,0.8); color: white; padding: 4px 8px; border-radius: 3px; text-decoration: none; font-size: 11px;">
                                           View
                                        </a>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # Balloons for Text-to-Image only
                            if uploaded_file is None:
                                st.balloons()
                            
                            # Caption with size and resolution (no download button)
                            with col2:
                                st.caption(f"Size: {img_size_kb:.1f} KB | Resolution: {img_dimensions}")
                                
                                # Debug info at the bottom (collapsible)
                                with st.expander("Debug Info (Click to expand)", expanded=False):
                                    st.info("Final Prompt:")
                                    st.text_area("", value=final_prompt, height=100, disabled=True)
                                    st.info("Request Details:")
                                    st.json({"request_id": request_id, "model": selected_model_short, "aspect_ratio": selected_aspect_value})
                                    st.info("Response:")
                                    st.json(res_data)
                        else:
                            st.warning("Completed but image URL not found.")
                            st.caption("Received data:")
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

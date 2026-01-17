# -*- coding: utf-8 -*-
import streamlit as st
import requests
import time
import os
import base64
from io import BytesIO
from PIL import Image
import datetime
import streamlit.components.v1 as components

# ---------------------------------------------------------
# 1. Session State Initialization
# ---------------------------------------------------------
if "generated_images" not in st.session_state:
    st.session_state.generated_images = []

# API key configuration
KEY_FILE_PATH = "/Users/yoichiroyoshida/my_ai_app/eternal_api_key.txt"

def load_api_key():
    cloud_key = os.environ.get("ETERNAL_API_KEY")
    if cloud_key: return cloud_key
    try:
        with open(KEY_FILE_PATH, "r") as f: return f.read().strip()
    except FileNotFoundError: return None

# ---------------------------------------------------------
# 2. UI Configuration & CSS
# ---------------------------------------------------------
st.set_page_config(page_title="EternalAI Image Generator", layout="wide")

st.markdown("""
<style>
    /* Force Dark Mode */
    .stApp { background-color: #0E1117 !important; color: #E0E0E0 !important; }
    header[data-testid="stHeader"] { background-color: #0E1117 !important; }
    .block-container { padding-top: 1rem; padding-bottom: 0rem; background-color: #0E1117 !important; }
    section[data-testid="stSidebar"] { background-color: #0E1117 !important; }
    .stMarkdown { margin-bottom: 0.5rem; color: #E0E0E0 !important; }
    
    /* Input Styling */
    .stTextArea textarea, .stTextInput input, .stSelectbox select {
        background-color: #1E2329 !important;
        color: #E0E0E0 !important;
        border: 1px solid #333 !important;
    }
    div[data-baseweb="select"] { background-color: #1E2329 !important; }
    .stFileUploader { background-color: #1E2329 !important; border: 1px solid #333 !important; }
    
    /* Generate Button */
    button[kind="primary"] {
        background-color: #FFFFFF !important;
        border-color: #FFFFFF !important;
        color: #000000 !important;
        font-weight: 600 !important;
    }
    button[kind="primary"]:hover { background-color: #E0E0E0 !important; }
    
    /* Pills (Radio) */
    div[data-testid="stPills"] button[data-selected="true"] {
        background-color: #4A90E2 !important;
        color: white !important;
        border: 2px solid #4A90E2 !important;
    }
    
    /* Custom Slider CSS for Comparison Dialog */
    .img-comp-container { position: relative; height: 400px; width: 100%; overflow: hidden; border-radius: 8px; background-color: #000; }
    .img-comp-img { position: absolute; width: 100%; height: 100%; overflow: hidden; }
    .img-comp-img img { display: block; width: 100%; height: 100%; object-fit: contain; }
    .img-comp-slider {
        position: absolute; z-index: 9; cursor: col-resize; width: 40px; height: 40px;
        background-color: #2196F3; border-radius: 50%; opacity: 0.9;
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 0 10px rgba(0,0,0,0.5); top: 50%; left: 50%; transform: translate(-50%, -50%);
    }
    .slider-line { position: absolute; z-index: 8; top: 0; bottom: 0; width: 2px; background-color: #2196F3; left: 50%; pointer-events: none; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. Helper Functions (Comparison HTML)
# ---------------------------------------------------------
def get_comparison_html(before_src, after_src):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ margin: 0; padding: 0; background-color: #0E1117; }}
        .img-comp-container {{ position: relative; height: 450px; width: 100%; overflow: hidden; border-radius: 8px; }}
        .img-comp-img {{ position: absolute; width: 100%; height: 100%; overflow: hidden; }}
        .img-comp-img img {{ display: block; width: 100%; height: 100%; object-fit: contain; }}
        .img-comp-slider {{
            position: absolute; z-index: 9; cursor: col-resize; width: 40px; height: 40px;
            background-color: #2196F3; border-radius: 50%; opacity: 0.8;
            display: flex; align-items: center; justify-content: center; color: white;
            top: 50%; left: 50%; transform: translate(-50%, -50%);
        }}
        .slider-line {{ position: absolute; z-index: 8; top: 0; bottom: 0; width: 2px; background-color: #2196F3; left: 50%; pointer-events: none; }}
    </style>
    </head>
    <body>
    <div class="img-comp-container" id="container">
        <div class="img-comp-img"><img src="{after_src}"></div>
        <div class="img-comp-img img-comp-overlay" id="overlay"><img src="{before_src}"></div>
        <div class="slider-line" id="slider-line"></div>
        <div class="img-comp-slider" id="slider">↔</div>
    </div>
    <script>
        initComparisons();
        function initComparisons() {{
            var overlay = document.getElementById("overlay");
            var slider = document.getElementById("slider");
            var line = document.getElementById("slider-line");
            var container = document.getElementById("container");
            var clicked = 0;
            var w = container.offsetWidth;
            overlay.style.width = (w / 2) + "px";
            
            slider.addEventListener("mousedown", slideReady);
            window.addEventListener("mouseup", slideFinish);
            slider.addEventListener("touchstart", slideReady);
            window.addEventListener("touchend", slideFinish);
            
            function slideReady(e) {{ e.preventDefault(); clicked = 1; window.addEventListener("mousemove", slideMove); window.addEventListener("touchmove", slideMove); }}
            function slideFinish() {{ clicked = 0; }}
            function slideMove(e) {{
                if (clicked == 0) return false;
                var rect = container.getBoundingClientRect();
                var x = (e.changedTouches ? e.changedTouches[0].pageX : e.pageX) - rect.left - window.pageXOffset;
                if (x < 0) x = 0; if (x > w) x = w;
                overlay.style.width = x + "px";
                slider.style.left = x + "px";
                line.style.left = x + "px";
            }}
        }}
    </script>
    </body>
    </html>
    """

@st.dialog("Before / After Comparison", width="large")
def show_comparison_dialog(before_b64, after_url):
    components.html(get_comparison_html(before_b64, after_url), height=460)
    c1, c2 = st.columns(2)
    c1.caption("Before")
    c2.caption("After")

# ---------------------------------------------------------
# 4. Main App Logic
# ---------------------------------------------------------
st.markdown("<p style='text-align: center; color: #888; font-size: 12px; margin: 0; padding: 0;'>EternalAI Image Generator</p>", unsafe_allow_html=True)

api_key = load_api_key()
if not api_key:
    st.error("API key not found")
    st.stop()

# --- Sidebar ---
with st.sidebar:
    st.markdown(f"<p style='font-size:14px;'>History ({len(st.session_state.generated_images)})</p>", unsafe_allow_html=True)
    if st.session_state.generated_images:
        st.markdown("<hr style='margin:3px 0;'>", unsafe_allow_html=True)
        for img_data in reversed(st.session_state.generated_images[-20:]):
            st.markdown(f"""
            <div style="position: relative; margin-bottom: 5px;">
                <a href="{img_data['url']}" target="_blank"><img src="{img_data['url']}" style="width: 100%; border-radius: 5px;" /></a>
            </div>
            <p style='font-size:8px; color: #888;'>{img_data['model']} | {img_data['dimensions']}</p>
            <hr style='margin:3px 0; opacity:0.2;'>
            """, unsafe_allow_html=True)

# --- Layout ---
col1, col2 = st.columns([1, 1])

# --- Input Section (Col 1) ---
with col1:
    uploaded_file = st.file_uploader("Reference Image (Optional)", type=["jpg", "png", "webp"])
    
    STYLE_PRESETS = {"None (Custom)": "", "Realistic Portrait": "photorealistic, 8k", "Cinematic": "cinematic, dramatic lighting", "Anime": "anime style, vibrant"}
    selected_style = st.selectbox("Style Preset", options=list(STYLE_PRESETS.keys()))
    style_prompt = st.text_area("Style Details", value=STYLE_PRESETS[selected_style], height=60) if selected_style != "None (Custom)" else ""
    
    url_prompt = st.query_params.get("prompt", "")
    prompt_text = st.text_area("Prompt (English)", height=80, value=url_prompt if url_prompt else "A beautiful Japanese woman in her 20s working in an office.")
    
    model_options = {"Qwen": "Qwen-Image-Edit-2509", "NB Pro": "gemini-3-pro-image-preview", "NB": "gemini-2.5-flash-image", "SD4.5": "seedream-4-5-251128", "Flux": "flux-2-pro"}
    selected_model_short = st.pills("Model", options=list(model_options.keys()), default="Qwen")
    
    aspect_ratio_options = {"Auto": "auto", "21:9": "21:9", "16:9": "16:9", "4:3": "4:3", "1:1": "1:1", "9:16": "9:16"}
    selected_aspect_ratio = st.pills("Aspect Ratio", options=list(aspect_ratio_options.keys()), default="Auto")
    
    denoising_strength = st.slider("Denoising Strength", 0.1, 0.9, 0.6, 0.1)
    
    generate_btn = st.button("Generate", type="primary")

# --- Output Section (Col 2) ---
with col2:
    st.markdown("<p style='font-size:12px; color:#E0E0E0;'>Result</p>", unsafe_allow_html=True)
    result_placeholder = st.empty()

    # ---------------------------------------------------------
    # GENERATION LOGIC
    # ---------------------------------------------------------
    if generate_btn:
        # 1. Animation
        particle_count = 30
        particles_html = "".join([f'<div class="particle" style="--i:{i}; --delay:{i*-0.2}s;"></div>' for i in range(particle_count)])
        result_placeholder.markdown(f"""
        <div class="loader-container"><div class="sphere-wrapper">{particles_html}</div><p class="loading-text">Generating...</p></div>
        <style>
        .loader-container {{ display: flex; flex-direction: column; align-items: center; height: 300px; perspective: 1000px; }}
        .sphere-wrapper {{ position: relative; width: 100px; height: 100px; transform-style: preserve-3d; animation: rotateSphere 10s linear infinite; }}
        .particle {{ position: absolute; width: 100%; height: 100%; border-radius: 50%; transform: rotateY(calc(var(--i) * (360deg / {particle_count}))) translateZ(60px); animation: unyoUnyo 3s ease-in-out infinite; animation-delay: var(--delay); }}
        .particle::before {{ content: ''; position: absolute; left: 50%; width: 6px; height: 6px; background: #00ffff; border-radius: 50%; box-shadow: 0 0 10px #00ffff; }}
        @keyframes rotateSphere {{ to {{ transform: rotateX(360deg) rotateY(360deg); }} }}
        @keyframes unyoUnyo {{ 0%,100% {{ transform: rotateY(calc(var(--i) * (360deg / {particle_count}))) translateZ(60px) scale(1); filter: hue-rotate(0deg); }} 50% {{ transform: rotateY(calc(var(--i) * (360deg / {particle_count}))) translateZ(90px) scale(1.5); filter: hue-rotate(180deg); }} }}
        .loading-text {{ margin-top: 50px; font-family: monospace; color: #00ffff; animation: blink 1.5s infinite; }}
        @keyframes blink {{ 50% {{ opacity: 0.3; }} }}
        </style>
        """, unsafe_allow_html=True)
        
        # 2. Process Inputs
        final_prompt = prompt_text
        if style_prompt: final_prompt += f", {style_prompt}"
        if selected_aspect_ratio != "Auto": final_prompt += f", aspect ratio {selected_aspect_ratio}"
        
        image_base64 = None
        if uploaded_file:
            img = Image.open(uploaded_file)
            img.thumbnail((1024, 1024))
            buf = BytesIO()
            img.save(buf, format="PNG")
            image_base64 = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
        
        # 3. API Call
        try:
            content = [{"type": "text", "text": final_prompt}]
            if image_base64: content.append({"type": "image_url", "image_url": {"url": image_base64}})
            
            res = requests.post("https://open.eternalai.org/creative-ai/image", 
                                headers={'x-api-key': api_key}, 
                                json={"messages": [{"role": "user", "content": content}], 
                                      "type": "edit" if image_base64 else "new", 
                                      "model_id": model_options[selected_model_short]})
            
            if res.status_code == 200:
                req_id = res.json().get("request_id") or res.json().get("id")
                # Polling
                for _ in range(150):
                    time.sleep(2)
                    check = requests.get(f"https://open.eternalai.org/creative-ai/poll-result/{req_id}", headers={'x-api-key': api_key})
                    if check.status_code == 200:
                        data = check.json()
                        if data.get("status") in ["done", "success", "completed"]:
                            img_url = data.get("result_url") or data.get("url") or data.get("result")
                            if img_url:
                                # Fetch for Download/Metadata
                                r_img = requests.get(img_url)
                                pil_img = Image.open(BytesIO(r_img.content))
                                b64_dl = base64.b64encode(r_img.content).decode()
                                
                                # SAVE TO HISTORY
                                st.session_state.generated_images.append({
                                    "url": img_url,
                                    "prompt": final_prompt,
                                    "model": selected_model_short,
                                    "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                                    "size_kb": f"{len(r_img.content)/1024:.1f}",
                                    "dimensions": f"{pil_img.width}x{pil_img.height}",
                                    "before_b64": image_base64,
                                    "dl_data": f"data:image/png;base64,{b64_dl}",
                                    "dl_name": f"eternal_{int(time.time())}.png"
                                })
                                st.rerun() # FORCE REFRESH TO SHOW RESULT
                            break
                        elif data.get("status") == "failed":
                            st.error("Generation failed")
                            break
            else:
                st.error(f"API Error: {res.text}")
        except Exception as e:
            st.error(f"Error: {e}")

    # ---------------------------------------------------------
    # DISPLAY LOGIC (Always Runs)
    # ---------------------------------------------------------
    if st.session_state.generated_images:
        last_img = st.session_state.generated_images[-1]
        
        # 1. Render Image with Overlay Buttons
        btns_html = f"""
        <div style="position: absolute; top: 10px; right: 10px; display: flex; gap: 8px; z-index: 10;">
            <a href="{last_img['url']}" target="_blank" style="background: rgba(0,0,0,0.7); color: white; padding: 5px 12px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold;">View</a>
            <a href="{last_img['dl_data']}" download="{last_img['dl_name']}" style="background: rgba(0,0,0,0.7); color: white; padding: 5px 12px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold;">Save</a>
        </div>
        """
        result_placeholder.markdown(f"""
        <div style="position: relative; width: 100%;">
            <img src="{last_img['url']}" style="width: 100%; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
            {btns_html}
        </div>
        """, unsafe_allow_html=True)
        
        # 2. Compare Button (Outside Image)
        if last_img.get("before_b64"):
            st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)
            if st.button("↔️ Compare Slider", use_container_width=True):
                show_comparison_dialog(last_img["before_b64"], last_img["url"])
                
        # 3. Info
        with st.expander("Debug Info"):
            st.json(last_img)
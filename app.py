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

# Compact title (small and humble)
st.markdown("<p style='text-align: center; color: #888; font-size: 12px; margin: 0; padding: 0;'>EternalAI Image Generator</p>", unsafe_allow_html=True)

# Get prompt from URL parameter (from translation site)
query_params = st.query_params
url_prompt = query_params.get("prompt", None)

if url_prompt:
    pass  # プロンプト入力済みで分かるので通知不要

api_key = load_api_key()
if not api_key:
    st.error("API key not found")
    st.stop()

# Sidebar: Image Gallery (Ultra Compact with overlay buttons)
with st.sidebar:
    st.markdown("<p style='font-size:14px; margin:0; padding:2px 0;'>History ({0})</p>".format(len(st.session_state.generated_images)), unsafe_allow_html=True)
    
    if len(st.session_state.generated_images) > 0:
        st.markdown("<hr style='margin:3px 0;'>", unsafe_allow_html=True)
        # Show last 20 images - ultra compact with overlay
        for idx, img_data in enumerate(reversed(st.session_state.generated_images[-20:])):
            # Unique ID for each image
            unique_id = f"img_{idx}_{img_data['timestamp'].replace(' ', '_').replace(':', '_')}"
            
            # Image with overlay button (View only)
            st.markdown(f"""
            <div style="position: relative; margin-bottom: 5px;">
                <a href="{img_data['url']}" target="_blank">
                    <img src="{img_data['url']}" style="width: 100%; border-radius: 5px; cursor: pointer;" />
                </a>
                <div style="position: absolute; top: 5px; right: 5px;">
                    <a href="{img_data['url']}" target="_blank" 
                       style="background: rgba(0,0,0,0.8); color: white; padding: 2px 6px; border-radius: 3px; text-decoration: none; font-size: 9px;">
                       View
                    </a>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Ultra compact info directly below image
            st.markdown(f"<p style='font-size:8px; margin:1px 0; color: #888;'>{img_data['model']} | {img_data['size_kb']}KB | {img_data['dimensions']}</p>", unsafe_allow_html=True)
            
            st.markdown("<hr style='margin:3px 0; opacity:0.2;'>", unsafe_allow_html=True)
    else:
        st.info("No images yet")

# Style Presets (English only, no icons)
STYLE_PRESETS = {
    "None (Custom)": "",
    "Realistic Portrait": "photorealistic, professional portrait photography, natural lighting, shot on Canon EOS R5, 85mm f/1.2, natural skin texture, realistic features, shallow depth of field, soft studio lighting, lifelike",
    "Cinematic": "cinematic photography, film grain, anamorphic lens, natural color grading, shot on ARRI Alexa, dramatic lighting, movie still, cinematic composition",
    "Street Photography": "candid street photography, natural lighting, realistic atmosphere, documentary style, shot on Leica M10, 35mm lens, photojournalism, authentic moment",
    "Commercial": "commercial photography, professional studio lighting, high resolution, sharp focus, advertising quality, clean background, product photography style",
    "Landscape": "landscape photography, golden hour lighting, natural colors, shot on Sony A7R IV, 24mm lens, vivid details, realistic scenery, high dynamic range",
    "Art Photography": "fine art photography, creative lighting, artistic composition, professional color grading, gallery quality, expressive mood"
}

# Input Area
col1, col2 = st.columns([1, 1])
with col1:
    # 6) Browse Files at the top (決定的な態度)
    uploaded_file = st.file_uploader(
        "Reference Image (Optional)", 
        type=["jpg", "jpeg", "png", "webp"],
        help="Upload a reference image for Image-to-Image generation (Max 5MB)"
    )
    
    # Style preset selector
    selected_style = st.selectbox(
        "Style Preset",
        options=list(STYLE_PRESETS.keys())
    )
    
    # Show selected style description (editable)
    if selected_style != "None (Custom)":
        style_prompt = st.text_area(
            "Style Details (Editable)",
            value=STYLE_PRESETS[selected_style],
            height=60
        )
    else:
        style_prompt = ""
    
    prompt_text = st.text_area(
        "Prompt (English)", 
        height=80,
        value=url_prompt if url_prompt else "A beautiful Japanese woman in her 20s working in an office. Full body shot."
    )
    
    model_options = {
        "Qwen": "Qwen-Image-Edit-2509",
        "NB Pro": "gemini-3-pro-image-preview",
        "NB": "gemini-2.5-flash-image",
        "SD4.5": "seedream-4-5-251128",
        "Flux": "flux-2-pro"
    }
    
    model_full_names = {
        "Qwen": "Qwen Image Edit (最も柔軟・最安・18+)",
        "NB Pro": "Nano Banana Pro (最高品質・高速)",
        "NB": "Nano Banana (高品質)",
        "SD4.5": "Seedream 4.5 (新モデル)",
        "Flux": "Flux 2 Pro (プロ品質)"
    }
    
    # Model selection with st.pills() - modern button style
    selected_model_short = st.pills(
        "Model",
        options=list(model_options.keys()),
        default="Qwen",
        label_visibility="collapsed"
    )
    
    selected_model_id = model_options[selected_model_short]
    
    # Aspect Ratio selection with st.pills() - modern button style
    aspect_ratio_options = {
        "Auto": "auto",
        "21:9": "21:9",
        "16:9": "16:9",
        "4:3": "4:3",
        "1:1": "1:1",
        "9:16": "9:16"
    }
    
    selected_aspect_ratio = st.pills(
        "Aspect Ratio",
        options=list(aspect_ratio_options.keys()),
        default="Auto",
        label_visibility="collapsed"
    )
    
    selected_aspect_value = aspect_ratio_options[selected_aspect_ratio]
    
    # Denoising strength slider with larger handle (always show)
    denoising_strength = st.slider(
        "Denoising Strength",
        min_value=0.1,
        max_value=0.9,
        value=0.6,
        step=0.1,
        help="Lower: subtle changes, Higher: dramatic changes"
    )
    
    generate_btn = st.button("Generate", type="primary")

with col2:
    # Always show Before & After structure (unified layout)
    compare_cols = st.columns(2)
    with compare_cols[0]:
        st.markdown("<p style='font-size:12px; margin:0; color:#E0E0E0;'>Before</p>", unsafe_allow_html=True)
        before_placeholder = st.empty()
        if uploaded_file is not None:
            # Image-to-Image: Show uploaded image
            before_placeholder.image(uploaded_file, use_column_width=True)
        # else: Text-to-Image will show dummy black image when Generate is clicked
    
    with compare_cols[1]:
        st.markdown("<p style='font-size:12px; margin:0; color:#E0E0E0;'>After</p>", unsafe_allow_html=True)
        after_placeholder = st.empty()

# Generation Logic
if generate_btn:
    # Move debug info to bottom
    debug_placeholder = st.empty()
    
    status_text = st.empty()
    
    # 1. Send request (POST)
    # Legacy API supports both Text-to-Image and Image-to-Image
    url_create = "https://open.eternalai.org/creative-ai/image"
    use_v1_api = False
    
    # Combine prompt with style preset (use editable style_prompt)
    final_prompt = prompt_text
    if selected_style != "None (Custom)" and style_prompt:
        final_prompt = f"{prompt_text}, {style_prompt}"
    
    # Add aspect ratio to prompt (if not Auto) - stronger emphasis for NB Pro
    if selected_aspect_value != "auto":
        # Determine orientation description
        if selected_aspect_value in ["9:16", "3:4"]:
            orientation_desc = "vertical portrait orientation"
        elif selected_aspect_value in ["21:9", "16:9", "4:3"]:
            orientation_desc = "horizontal landscape orientation"
        else:  # 1:1
            orientation_desc = "square format"
        
        # Extra strong emphasis for NB Pro with image-to-image
        if selected_model_short == "NB Pro" and uploaded_file is not None:
            final_prompt = f"{final_prompt}, MUST be {orientation_desc}, MUST maintain {selected_aspect_value} aspect ratio, {selected_aspect_value} format, ignore reference image aspect ratio, output must be {selected_aspect_value}"
        else:
            final_prompt = f"{final_prompt}, {orientation_desc}, aspect ratio {selected_aspect_value}, {selected_aspect_value} format"
    
    # No debug info here - moved to bottom
    
    # Convert uploaded image to Base64 (if exists)
    image_base64 = None
    if uploaded_file is not None:
        try:
            # Read image
            image = Image.open(uploaded_file)
            
            # Resize if too large (max 5MB after compression)
            max_size = (1024, 1024)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert to Base64
            buffered = BytesIO()
            image_format = image.format if image.format else 'PNG'
            image.save(buffered, format=image_format, quality=85)
            img_bytes = buffered.getvalue()
            image_base64 = f"data:image/{image_format.lower()};base64,{base64.b64encode(img_bytes).decode()}"
            
            status_text.text(f"Image converted ({len(img_bytes) / 1024:.2f} KB)")
        except Exception as e:
            st.error(f"Failed to load image: {e}")
            st.stop()
    
    # Payload configuration (Legacy API format)
    # Build content array
    content_items = [
        {
            "type": "text",
            "text": final_prompt
        }
    ]
    
    # Add image to content array for Image-to-Image mode (following official docs)
    if image_base64:
        content_items.append({
            "type": "image_url",
            "image_url": {
                "url": image_base64,
                "filename": "input.jpg"
            }
        })
    
    payload = {
        "messages": [{
            "role": "user",
            "content": content_items
        }],
        "type": "edit" if image_base64 else "new",
        "model_id": selected_model_id  # Always include model_id
    }
    
    headers = {
        'x-api-key': api_key,
        'Content-Type': 'application/json'
    }

    if uploaded_file is None:
        # Calculate aspect ratio dimensions
        aspect_map = {
            "21:9": (420, 180),
            "16:9": (320, 180),
            "4:3": (240, 180),
            "1:1": (180, 180),
            "9:16": (180, 320),
            "auto": (180, 180)
        }
        width, height = aspect_map.get(selected_aspect_value, (180, 180))
        
        # Show dummy image in Before area (完全な暗黒)
        before_placeholder.markdown(f"""
        <div style="width: 100%; display: flex; justify-content: center; align-items: center;">
            <div style="width: 100%; aspect-ratio: {width}/{height}; background-color: #0E1117; border-radius: 5px;"></div>
        </div>
        """, unsafe_allow_html=True)

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
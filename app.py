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

# Compact title (small and humble)
st.markdown("<p style='text-align: center; color: #888; font-size: 14px; margin: 5px 0;'>🎨 EternalAI Image Generator</p>", unsafe_allow_html=True)

# Get prompt from URL parameter (from translation site)
query_params = st.query_params
url_prompt = query_params.get("prompt", None)

if url_prompt:
    st.success("✅ 翻訳サイトからプロンプトを受け取りました！")

api_key = load_api_key()
if not api_key:
    st.error("API key not found")
    st.stop()

# Sidebar: Image Gallery (Ultra Compact for maximum density)
with st.sidebar:
    st.markdown("<p style='font-size:16px; margin:0;'>📸 履歴 ({0})</p>".format(len(st.session_state.generated_images)), unsafe_allow_html=True)
    
    if len(st.session_state.generated_images) > 0:
        st.markdown("<hr style='margin:5px 0;'>", unsafe_allow_html=True)
        # Show last 20 images - ultra compact
        for idx, img_data in enumerate(reversed(st.session_state.generated_images[-20:])):
            # Tiny thumbnail (100px width)
            st.image(img_data["url"], width=100)
            
            # Ultra compact info
            st.markdown(f"<p style='font-size:9px; margin:2px 0;'>{img_data['model']} | {img_data['size_kb']}KB</p>", unsafe_allow_html=True)
            
            # Tiny buttons
            cols = st.columns([1, 1])
            with cols[0]:
                if st.button("📝", key=f"p_{idx}", help="Prompt"):
                    st.caption(img_data["prompt"][:80])
            with cols[1]:
                st.markdown(f"<a href='{img_data['url']}' download style='font-size:10px;'>📥</a>", unsafe_allow_html=True)
            
            st.markdown("<hr style='margin:3px 0; opacity:0.3;'>", unsafe_allow_html=True)
    else:
        st.info("未生成")

# Style Presets
STYLE_PRESETS = {
    "None (カスタムのみ)": "",
    "📸 実写・ポートレート": "photorealistic, professional portrait photography, natural lighting, shot on Canon EOS R5, 85mm f/1.2, natural skin texture, realistic features, shallow depth of field, soft studio lighting, lifelike",
    "🎬 映画風": "cinematic photography, film grain, anamorphic lens, natural color grading, shot on ARRI Alexa, dramatic lighting, movie still, cinematic composition",
    "📷 ストリート写真": "candid street photography, natural lighting, realistic atmosphere, documentary style, shot on Leica M10, 35mm lens, photojournalism, authentic moment",
    "💼 商業写真": "commercial photography, professional studio lighting, high resolution, sharp focus, advertising quality, clean background, product photography style",
    "🌆 風景写真": "landscape photography, golden hour lighting, natural colors, shot on Sony A7R IV, 24mm lens, vivid details, realistic scenery, high dynamic range",
    "🎨 アート写真": "fine art photography, creative lighting, artistic composition, professional color grading, gallery quality, expressive mood"
}

# Input Area
col1, col2 = st.columns([1, 1])
with col1:
    # Style preset selector
    selected_style = st.selectbox(
        "🎨 スタイルプリセット",
        options=list(STYLE_PRESETS.keys())
    )
    
    # Show selected style description (compact)
    if selected_style != "None (カスタムのみ)":
        with st.expander("ℹ️ スタイル詳細"):
            st.caption(STYLE_PRESETS[selected_style])
    
    prompt_text = st.text_area(
        "📝 Prompt (English)", 
        height=100,
        value=url_prompt if url_prompt else "A beautiful Japanese woman in her 30s, wearing a white coat"
    )
    
    # 🤖 Model selection (Compact horizontal radio)
    st.markdown("🤖 **モデル**")
    
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
    
    selected_model_short = st.radio(
        "label",
        options=list(model_options.keys()),
        horizontal=True,
        index=0,
        label_visibility="collapsed"
    )
    
    selected_model_id = model_options[selected_model_short]
    st.caption(f"📝 {model_full_names[selected_model_short]}")
    
    # Image upload (reference image) - Image-to-Image mode
    mode_tabs = st.tabs(["📝 Text-to-Image", "🖼️ Image-to-Image"])
    
    with mode_tabs[0]:
        st.caption("参照画像なしでゼロから生成します")
    
    with mode_tabs[1]:
        uploaded_file = st.file_uploader(
            "参照画像をアップロード", 
            type=["jpg", "jpeg", "png", "webp"]
        )
        
        if uploaded_file is not None:
            # Denoising strength slider (compact)
            denoising_strength = st.slider(
                "🎚️ 変更度",
                min_value=0.1,
                max_value=0.9,
                value=0.5,
                step=0.1
            )
        else:
            denoising_strength = 0.5
    
    generate_btn = st.button("🚀 Generate", type="primary")

# Generation Logic
if generate_btn:
    st.divider()
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    # 1. Send request (POST)
    # Legacy API supports both Text-to-Image and Image-to-Image
    url_create = "https://open.eternalai.org/creative-ai/image"
    use_v1_api = False
    
    # Combine prompt with style preset
    final_prompt = prompt_text
    if selected_style != "None (カスタムのみ)":
        final_prompt = f"{prompt_text}, {STYLE_PRESETS[selected_style]}"
    
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
            
            status_text.text(f"画像を変換しました ({len(img_bytes) / 1024:.2f} KB)")
        except Exception as e:
            st.error(f"画像の読み込みに失敗しました: {e}")
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

    try:
        status_text.text("Sending request...")
        
        # Debug: show payload (collapsible)
        with col2:
            with st.expander("🔍 デバッグ情報（クリックで展開）", expanded=False):
                st.info("📤 Sending payload:")
                st.json(payload)
        
        response = requests.post(url_create, headers=headers, json=payload)
        
        # Show response for debugging (collapsible)
        with col2:
            with st.expander("🔍 デバッグ情報（クリックで展開）", expanded=False):
                st.info(f"📡 Response Status: {response.status_code}")
                if response.status_code != 200:
                    st.error(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            request_id = data.get("request_id") or data.get("id")
            
            with col2:
                with st.expander("🔍 デバッグ情報（クリックで展開）", expanded=False):
                    st.success(f"✅ Request sent! ID: {request_id}")
                    st.json(data)  # Show full response
            
            # Legacy API polling (correct endpoint with /creative-ai/)
            check_url_base = "https://open.eternalai.org/creative-ai/poll-result"
            
            if image_base64:
                st.caption("ℹ️ Generating image (Image-to-Image mode)... (typically takes 45s - 1min)")
            else:
                st.caption("ℹ️ Generating image... (typically takes 45s - 1min)")
            
            # 2. Polling loop (max 5 minutes)
            status_text.text("Processing... (max 5 minutes)")
            
            for i in range(150):
                time.sleep(2)
                
                current_val = int(min((i + 1) / 40 * 100, 95))
                progress_bar.progress(current_val)
                
                # Legacy API polling
                check_url = f"{check_url_base}/{request_id}"
                check_res = requests.get(check_url, headers={'x-api-key': api_key})
                
                if check_res.status_code == 200:
                    res_data = check_res.json()
                    status = res_data.get("status")
                    
                    # Debug: show polling response every 10 iterations (collapsible)
                    if i % 10 == 0:
                        with col2:
                            with st.expander("🔍 デピバッグ情報（クリックで展開）", expanded=False):
                                st.caption(f"Polling {i}: {status}")
                                st.json(res_data)
                    
                    if status in ["done", "success", "completed"]:
                        progress_bar.progress(100)
                        
                        # Try multiple possible field names for image URL
                        img_url = (res_data.get("result_url") or 
                                  res_data.get("url") or 
                                  res_data.get("result") or 
                                  res_data.get("image_url") or
                                  res_data.get("output_url"))
                        
                        if img_url:
                            # Get image metadata
                            try:
                                img_response = requests.get(img_url)
                                img_size_kb = len(img_response.content) / 1024
                                img_pil = Image.open(BytesIO(img_response.content))
                                img_dimensions = f"{img_pil.width}x{img_pil.height}"
                            except:
                                img_size_kb = 0
                                img_dimensions = "Unknown"
                            
                            # Add to history with metadata
                            st.session_state.generated_images.append({
                                "url": img_url,
                                "prompt": prompt_text,
                                "model": selected_model_short,
                                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "size_kb": f"{img_size_kb:.1f}",
                                "dimensions": img_dimensions,
                                "reference_image": uploaded_file.name if uploaded_file else None
                            })
                            
                            with col2:
                                st.balloons()
                                st.success("✨ Generation complete!")
                                
                                # Show reference image and generated image side by side for Image-to-Image
                                if uploaded_file is not None:
                                    st.markdown("### 🔄 Before & After")
                                    compare_cols = st.columns(2)
                                    with compare_cols[0]:
                                        st.image(uploaded_file, caption="📥 参照画像", use_column_width=True)
                                    with compare_cols[1]:
                                        st.image(img_url, caption="✨ 生成画像", use_column_width=True)
                                else:
                                    st.image(img_url, caption="✨ Generated Result", use_column_width=True)
                                
                                st.markdown(f"[📥 Download Image]({img_url})")
                                st.caption(f"📊 サイズ: {img_size_kb:.1f} KB | 📎 解像度: {img_dimensions}")
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

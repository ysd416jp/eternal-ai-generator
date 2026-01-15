# -*- coding: utf-8 -*-
import streamlit as st
import requests
import time
import os
import base64
from io import BytesIO
from PIL import Image

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

# Get prompt from URL parameter (from translation site)
query_params = st.query_params
url_prompt = query_params.get("prompt", None)

if url_prompt:
    st.success("✅ 翻訳サイトからプロンプトを受け取りました！")

api_key = load_api_key()
if not api_key:
    st.error("API key not found")
    st.stop()

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
    st.info("📝 Describe the image you want to generate (in English)")
    
    # Style preset selector
    selected_style = st.selectbox(
        "🎨 スタイルプリセット",
        options=list(STYLE_PRESETS.keys()),
        help="写真スタイルを選択してください。自動的にプロンプトに追加されます。"
    )
    
    # Show selected style description
    if selected_style != "None (カスタムのみ)":
        with st.expander("ℹ️ 選択中のスタイル詳細"):
            st.code(STYLE_PRESETS[selected_style])
    
    prompt_text = st.text_area(
        "Prompt (English)", 
        height=150, 
        value=url_prompt if url_prompt else "A beautiful Japanese woman in her 30s, wearing a white coat",
        help="基本的なプロンプトを入力してください。スタイルプリセットは自動的に追加されます。"
    )
    
    # Image upload (reference image) - Image-to-Image mode
    st.markdown("---")
    st.info("🖼️ Reference Image (Image-to-Image)")
    
    mode_tabs = st.tabs(["📝 Text-to-Image", "🖼️ Image-to-Image"])
    
    with mode_tabs[0]:
        st.markdown("**プロンプトのみで画像生成**")
        st.caption("参照画像なしでゼロから生成します")
    
    with mode_tabs[1]:
        st.markdown("**参照画像 + プロンプトで画像生成**")
        uploaded_file = st.file_uploader(
            "画像をアップロード", 
            type=["jpg", "jpeg", "png", "webp"],
            help="最大5MB。アップロードした画像をベースに、プロンプトで指示した内容に変更します。"
        )
        
        if uploaded_file is not None:
            st.image(uploaded_file, caption="参照画像", use_column_width=True)
            
            # Denoising strength slider
            denoising_strength = st.slider(
                "🎚️ 変更度（Denoising Strength）",
                min_value=0.1,
                max_value=0.9,
                value=0.5,
                step=0.1,
                help="0.1 = 微調整（元画像に近い）、0.9 = 大幅変更（プロンプト重視）"
            )
            
            st.caption(f"現在の設定: {denoising_strength} ({'微調整' if denoising_strength < 0.4 else '大幅変更' if denoising_strength > 0.6 else 'バランス'})")
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
    
    # Show final prompt
    with col2:
        st.info("📝 最終プロンプト:")
        st.text_area("Combined Prompt", value=final_prompt, height=150, disabled=True)
        
        # Show Image-to-Image info if image uploaded
        if uploaded_file is not None:
            st.info("🖼️ Image-to-Image モード")
            st.caption(f"変更度: {denoising_strength}")
            st.caption(f"ファイル名: {uploaded_file.name}")
            st.caption(f"ファイルサイズ: {uploaded_file.size / 1024:.2f} KB")
    
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
    payload = {
        "messages": [{"role": "user", "content": [{"type": "text", "text": final_prompt}]}],
    }
    
    # Add image fields for Image-to-Image mode
    if image_base64:
        payload["type"] = "edit"  # Change to "edit" mode for Image-to-Image
        payload["image"] = image_base64
        payload["strength"] = denoising_strength
    else:
        payload["type"] = "new"  # "new" for Text-to-Image
    
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
        
        # Show response for debugging
        with col2:
            st.info(f"📡 Response Status: {response.status_code}")
            if response.status_code != 200:
                st.error(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            request_id = data.get("request_id") or data.get("id")
            
            with col2:
                st.success(f"✅ Request sent! ID: {request_id}")
                st.json(data)  # Show full response
            
            # Legacy API polling
            check_url_base = "https://open.eternalai.org/poll-result"
            
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
                    
                    # Debug: show polling response every 10 iterations
                    if i % 10 == 0:
                        with col2:
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
                            with col2:
                                st.balloons()
                                st.success("✨ Generation complete!")
                                st.image(img_url, caption="Generated Result")
                                st.markdown(f"[Download Image]({img_url})")
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

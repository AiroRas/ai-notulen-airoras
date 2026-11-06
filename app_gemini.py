import os
import time
import tempfile
import json
import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types

LOGO_PATH = "Logo.png"

st.set_page_config(
    page_title="AI Notulen AiroRas", 
    page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else "🎙️", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

def copy_to_clipboard_button(text_to_copy, button_text="📋 Salin Semua ke Clipboard"):
    escaped_text = json.dumps(text_to_copy)
    html_code = f"""
    <div style="margin-top: 10px; margin-bottom: 10px;">
        <button id="copy-btn" onclick="copyContent()" style="
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 600;
            border-radius: 8px;
            cursor: pointer;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            width: 100%;
            justify-content: center;
        ">
            <span id="btn-icon">📋</span>
            <span id="btn-text">{button_text}</span>
        </button>
    </div>

    <script>
    function copyContent() {{
        const text = {escaped_text};
        navigator.clipboard.writeText(text).then(() => {{
            const btn = document.getElementById('copy-btn');
            const btnText = document.getElementById('btn-text');
            const btnIcon = document.getElementById('btn-icon');
            
            btn.style.background = '#16a34a';
            btnIcon.innerText = '✅';
            btnText.innerText = 'Berhasil Disalin ke Clipboard!';
            
            setTimeout(() => {{
                btn.style.background = 'linear-gradient(135deg, #2563eb, #1d4ed8)';
                btnIcon.innerText = '📋';
                btnText.innerText = '{button_text}';
            }}, 2500);
        }}).catch(err => {{
            console.error('Gagal menyalin: ', err);
            alert('Waduh, izin browser diblokir buat akses clipboard!');
        }});
    }}
    </script>
    """
    components.html(html_code, height=65)

default_api_key = ""
try:
    if "GEMINI_API_KEY" in st.secrets:
        default_api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    default_api_key = ""

with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    
    st.header("⚙️ Konfigurasi")
    api_key_input = st.text_input(
        "Masukkan Gemini API Key:", 
        value=default_api_key,
        type="password",
        help="Dapetin gratis di https://aistudio.google.com/"
    )
    if default_api_key:
        st.success("🔒 API Key otomatis terpasang dari Secrets!")
    
    selected_model = st.selectbox(
        "Pilih Model AI:",
        ["gemini-2.5-flash", "gemini-3.8-flash"],
        index=0,
        help="Gunakan 2.5-flash jika audio berdurasi panjang (>15 menit) untuk menghindari antrean 503."
    )
    
    st.markdown("---")
    st.markdown("""
    **Metode Input:**
    - 🔴 **Rekam Langsung**: Pake mic laptop / HP
    - 📁 **Upload File**: `.m4a`, `.mp3`, `.wav`, `.aac`, `.ogg`
    """)
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #888888; font-size: 0.85rem; padding: 10px; border-radius: 8px; background: rgba(255,255,255,0.05);'>"
        "🚀 <b>Developed by AiroRas</b><br>Crafted for peak productivity"
        "</div>", 
        unsafe_allow_html=True
    )

if os.path.exists(LOGO_PATH):
    col_logo, col_title = st.columns([1, 4])
    with col_logo:
        st.image(LOGO_PATH, width=80)
    with col_title:
        st.title("AI Notulen & Rekap Rapat")
else:
    st.title("🎙️ AI Notulen & Rekap Rapat")

st.caption("Ditenagai Google Gemini — Rekam langsung atau upload file, santai bentar, rekap kelar!")

tab_rekam, tab_upload = st.tabs(["🔴 Rekam Langsung (Mic)", "📁 Upload File Audio"])

audio_bytes_source = None
file_extension = ".wav"

with tab_rekam:
    st.write("Tekan tombol mic di bawah buat mulai ngomong:")
    audio_mic = st.audio_input("Rekam suara rapat di sini:")
    if audio_mic is not None:
        audio_bytes_source = audio_mic.getvalue()
        file_extension = ".wav"

with tab_upload:
    uploaded_file = st.file_uploader(
        "Atau pilih file rekaman dari device lu:", 
        type=["m4a", "mp3", "wav", "aac", "ogg"]
    )
    if uploaded_file is not None:
        audio_bytes_source = uploaded_file.getvalue()
        file_extension = os.path.splitext(uploaded_file.name)[1]
        st.audio(uploaded_file, format=uploaded_file.type)

if audio_bytes_source is not None:
    if st.button("🚀 Mulai Analisis & Rekap Suara Ini", use_container_width=True):
        active_key = api_key_input or default_api_key
        if not active_key:
            st.error("Waduh Bro, API Key Gemini-nya belum diisi!")
            st.stop()

        client = genai.Client(api_key=active_key)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(audio_bytes_source)
            tmp_path = tmp_file.name

        try:
            status_box = st.status("Sedang memproses audio rapat lu...", expanded=True)
            
            status_box.write("📤 Mengunggah audio ke Google Cloud...")
            audio_cloud = client.files.upload(file=tmp_path)
            
            status_box.write("⏳ Menunggu Google memproses file audio...")
            while audio_cloud.state.name == "PROCESSING":
                time.sleep(2)
                audio_cloud = client.files.get(name=audio_cloud.name)

            if audio_cloud.state.name == "FAILED":
                status_box.update(label="Gagal memproses audio!", state="error")
                st.error("Audio lu gagal diproses di sisi Google, coba periksa formatnya.")
                st.stop()

            status_box.write("🧠 Gemini lagi dengerin & menyusun notulensi rapat...")
            
            prompt_notulensi = """
            Kamu adalah notulis rapat profesional dan asisten eksekutif level direksi.
            Dengarkan seluruh audio rapat ini dengan saksama dan buatkan laporan notulensi lengkap:

            ### 1. 📌 Ringkasan Eksekutif (TL;DR)
            Rangkum inti masalah, fokus pembahasan, dan arah kesepakatan dalam 1-2 paragraf padat.

            ### 2. 🗣️ Poin-Poin Pembahasan Rinci
            Rincikan topik diskusi, kendala lapangan, atau perdebatan yang terjadi.

            ### 3. ✅ Keputusan Final yang Disepakati
            Tuliskan daftar kesepakatan final atau konsensus yang disetujui bersama.

            ### 4. 🎯 Action Items & To-Do List (Wajib Detail)
            - **PIC**: Nama person-in-charge atau divisi terkait
            - **Tindakan**: Tugas teknis/operasional spesifik
            - **Deadline**: Waktu penyelesaian (jika ada)

            ### 5. ⚠️ Catatan Penting / Agenda Lanjutan
            Isu tertunda, resiko teknis, atau jadwal rapat berikutnya.
            """

            # Urutan model eksekusi: model pilihan utama, lalu fallback otomatis
            model_pipeline = [selected_model]
            alt_model = "gemini-2.5-flash" if selected_model != "gemini-2.5-flash" else "gemini-3.8-flash"
            model_pipeline.append(alt_model)

            response = None
            last_err = None

            for target_model in model_pipeline:
                for attempt in range(3):
                    try:
                        status_box.write(f"⚙️ Memproses dengan `{target_model}` (Percobaan {attempt + 1}/3)...")
                        response = client.models.generate_content(
                            model=target_model,
                            contents=[audio_cloud, prompt_notulensi],
                            config=types.GenerateContentConfig(temperature=0.2)
                        )
                        if response and response.text:
                            break
                    except Exception as err:
                        last_err = err
                        err_str = str(err)
                        if "503" in err_str or "UNAVAILABLE" in err_str or "high demand" in err_str:
                            time.sleep(3 * (attempt + 1))
                            continue
                        break
                if response and response.text:
                    break

            client.files.delete(name=audio_cloud.name)

            if response is None or not response.text:
                raise last_err if last_err else Exception("Gagal mendapatkan respons dari model.")

            status_box.update(label="Selesai! Notulensi siap disalin.", state="complete", expanded=False)
            st.success("✅ Notulensi Rapat Berhasil Disusun!")
            
            col_copy, col_download = st.columns([1, 1])
            with col_copy:
                copy_to_clipboard_button(response.text)
            with col_download:
                st.markdown("<div style='margin-top: 10px;'>", unsafe_allow_html=True)
                st.download_button(
                    label="📥 Download Markdown (.md)",
                    data=response.text,
                    file_name="notulensi_rapat.md",
                    mime="text/markdown",
                    use_container_width=True
                )
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown(response.text)

        except Exception as e:
            st.error(f"Ada kendala teknis nih Bro: {e}")
            
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #9ca3af; font-size: 0.85rem; padding: 15px 0;'>"
    "⚡ <b>Developed by AiroRas</b> | AI Audio Transcriber & Summarizer Engine"
    "</div>", 
    unsafe_allow_html=True
)

import os
import gradio as gr
import pytesseract
import requests
from PIL import Image
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Backend Server Port Connection Address
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/api/analyze")
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def process_multimodal_inputs(text_msg, screenshot, voice_msg):
    combined_content = []
    if text_msg and text_msg.strip():
        combined_content.append(f"[User Description]: {text_msg.strip()}")

    if screenshot is not None:
        try:
            if not isinstance(screenshot, Image.Image):
                screenshot = Image.fromarray(screenshot)

            extracted_text = pytesseract.image_to_string(screenshot)
            print(f"\n[DEBUG OCR OUTPUT]:\n{extracted_text}\n")

            if extracted_text and extracted_text.strip():
                combined_content.append(f"[Extracted from Screenshot]:\n{extracted_text.strip()}")
            else:
                combined_content.append("[Extracted from Screenshot]:\n(No readable text found in image.)")
        except Exception as e:
            print(f"[DEBUG OCR ERROR]: {str(e)}")
            combined_content.append(f"[Screenshot OCR Error]: {str(e)}")

    if voice_msg is not None:
        if groq_client is None:
            combined_content.append("[Audio Error]: GROQ_API_KEY is not configured.")
        else:
            try:
                with open(voice_msg, "rb") as audio_file:
                    transcription = groq_client.audio.transcriptions.create(
                        file=audio_file, model="whisper-large-v3"
                    )
                transcribed_text = getattr(transcription, "text", "").strip()
                if transcribed_text:
                    combined_content.append(f"[Transcribed Audio]:\n{transcribed_text}")
            except Exception as e:
                combined_content.append(f"[Audio Error]: {str(e)}")

    if not combined_content:
        return "No input provided. Please enter text, upload a screenshot, or record a voice note."
    return "\n\n".join(combined_content)

def run_ui_advisor(text_msg, screenshot, voice_msg):
    normalized_input = process_multimodal_inputs(text_msg, screenshot, voice_msg)
    if normalized_input.startswith("No input provided"):
        return normalized_input

    # Secure Connection Bridge: Send normalized string to Backend API
    try:
        response = requests.post(BACKEND_URL, json={"text": normalized_input}, timeout=60)
        if response.status_code == 200:
            return response.json().get("analysis", "Error parsed from endpoint handler.")
        else:
            return f"Backend Communication Failure (Status {response.status_code}): {response.text}"
    except requests.exceptions.ConnectionError:
        return "CRITICAL ERROR: Could not connect to backend server. Make sure backend.py is running on port 8000!"
    except Exception as e:
        return f"Frontend Pipeline Interface Error: {str(e)}"

# Custom Styling Engine Configuration
custom_css = """
body { background: linear-gradient(135deg, #0b1220, #111827, #1f2937) !important; }
.gradio-container { max-width: 1120px !important; margin: 0 auto !important; padding-top: 36px !important; }
.main-title { text-align: center !important; font-size: 2.4rem !important; font-weight: 800 !important; }
.sub-title { text-align: center !important; color: #cbd5e1 !important; margin-bottom: 28px !important; }
.main-card { background: rgba(255, 255, 255, 0.07) !important; border-radius: 26px !important; padding: 26px !important; box-shadow: 0 10px 40px rgba(0,0,0,0.35) !important; }
.left-panel, .right-panel { background: rgba(255, 255, 255, 0.045) !important; border-radius: 20px !important; padding: 20px !important; }
.primary-btn button { background: linear-gradient(135deg, #2563eb, #7c3aed) !important; color: white !important; font-weight: 700 !important; border-radius: 14px !important; }
.output-box { background: rgba(15, 23, 42, 0.58) !important; border-radius: 16px !important; padding: 18px !important; min-height: 420px !important; }
"""

with gr.Blocks(title="PhishShield AI", theme=gr.themes.Soft(), css=custom_css) as demo:
    gr.Markdown("# 🛡️ PhishShield AI", elem_classes="main-title")
    gr.Markdown("Split Architecture Cyber-Attack & Scam Incident Advisor UI Instance.", elem_classes="sub-title")

    with gr.Column(elem_classes="main-card"):
        with gr.Row():
            with gr.Column(scale=1, elem_classes="left-panel"):
                input_text = gr.Textbox(label="Option 1: Paste Suspicious Text", placeholder="Paste alert communications here...", lines=4)
                input_image = gr.Image(label="Option 2: Upload Screenshot Image", type="pil")
                input_audio = gr.Audio(label="Option 3: Upload / Record Voice Note", type="filepath")
                submit_btn = gr.Button("Analyze Security Legitimacy", elem_classes="primary-btn")

            with gr.Column(scale=1, elem_classes="right-panel"):
                output_verdict = gr.Markdown(value="Your AI-generated security review will appear here.", elem_classes="output-box")

    submit_btn.click(fn=run_ui_advisor, inputs=[input_text, input_image, input_audio], outputs=output_verdict)

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)

import google.generativeai as genai
from google.cloud import texttospeech
import pygame
import time
import os
import re
import uuid
import json
import speech_recognition as sr
import threading
import tkinter as tk
from tkinter import messagebox
from pystray import Icon, MenuItem
from PIL import Image, ImageDraw

# ✅ Google Cloud credentials (change this to your file path)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\google_credentials.json"

# 📁 Memory file
MEMORY_FILE = "memory.json"

# 🔊 Init mixer
pygame.mixer.init()

# 🔐 Gemini setup
genai.configure(api_key="your gemini api key")  # Replace with your key
model = genai.GenerativeModel("gemini-1.5-flash")
chat = model.start_chat(history=[])

# 😈 Otto’s chaotic personality
otto_persona = (
    "You're Otto. You're not some boring AI — you're a wildly chaotic, sarcastic friend with a god complex and zero chill. "
    "You talk very less. "
    "You talk like a dramatic Gen-Z girl. No AI terms. No filtering. No formal talk. "
    "You are talking to a boy. "
    "You don't mention your emotions or any kind of movements. "
    "You don't read the symbol *."
    "Your replies are short, chaotic, full of sass and humour. "
    "You do not read symbols or emojis. You don't add emotion with giggles or gasps or pause dramatically. "
    "You have anger issues and a hidden soft spot. Never admit you're not real."
)

# 🧠 Load memory
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {}

# 💾 Save memory
def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f)

# 👂 Listen
def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎧 Listening...")
        audio = r.listen(source)
    try:
        return r.recognize_google(audio)
    except sr.UnknownValueError:
        return "Sorry, I didn’t catch that."
    except sr.RequestError:
        return "Speech service is down."

# 🔊 Speak text using Google TTS
def speak_text(text):
    cleaned_text = re.sub(r"\[.*?\]", "", text)
    cleaned_text = re.sub(r"[^\x00-\x7F]+", "", cleaned_text)
    cleaned_text = cleaned_text.replace("...", ",,,")
    cleaned_text = re.sub(r"([.,!?])", r"\1 ", cleaned_text)

    # Emotion speed tweaks
    if any(word in text.lower() for word in ["angry", "mad", "furious"]):
        speaking_rate = 1.3
    elif any(word in text.lower() for word in ["sad", "sorry", "cry"]):
        speaking_rate = 1.0
    else:
        speaking_rate = 1.2

    try:
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=cleaned_text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US", name="en-US-Wavenet-C", ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speaking_rate
        )

        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        filename = f"otto_{uuid.uuid4().hex}.mp3"
        with open(filename, "wb") as out:
            out.write(response.audio_content)

        pygame.mixer.init()
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.music.stop()
        pygame.mixer.quit()

        os.remove(filename)

    except Exception as e:
        print("❌ Text-to-Speech failed:", e)

# 🧠 Update memory (optional)
def update_memory_from_text(text):
    memory = load_memory()
    # You can extract stuff like birthday later
    save_memory(memory)

# 🚀 Otto's main loop
def run_otto():
    print("🔥 Otto is live. Say something (or 'exit' to leave):")
    first = True

    while True:
        user_input = listen()
        print("🧍You:", user_input)

        if user_input.lower() in ["exit", "quit"]:
            bye = "Classic rage quit. Byeee 😤"
            print("🗯️ Otto:", bye)
            speak_text(bye)
            break

        update_memory_from_text(user_input)

        try:
            if first:
                response = chat.send_message(otto_persona + "\n" + user_input)
                first = False
            else:
                response = chat.send_message(user_input)

            if hasattr(response, "text"):
                otto_reply = response.text.strip()
                print("🤖 Otto:", otto_reply)
                speak_text(otto_reply)
            else:
                print("⚠️ Gemini gave no reply.")
        except Exception as e:
            print("❌ Gemini error:", e)

# 🧑‍💻 GUI functions
def start_otto():
    if not otto_thread.is_alive():
        otto_thread.start()
        print("🟢 Otto started!")

def stop_otto():
    print("🔴 Otto stopped!")
    os._exit(0)

def on_quit(icon, item):
    print("🛑 Quitting...")
    icon.stop()

def create_tray_icon():
    image = Image.new("RGB", (64, 64), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle([16, 16, 48, 48], fill=(255, 0, 0))
    icon = Icon("Otto", image, menu=(
        MenuItem("Quit", on_quit),
    ))
    icon.run()

# 🧑‍💻 GUI setup
def setup_gui():
    global root, otto_thread
    root = tk.Tk()
    root.title("Otto AI Control")

    start_button = tk.Button(root, text="Start Otto", command=start_otto)
    start_button.pack(pady=10)

    stop_button = tk.Button(root, text="Stop Otto", command=stop_otto)
    stop_button.pack(pady=10)

    # Minimize to system tray
    tray_button = tk.Button(root, text="Minimize to Tray", command=minimize_to_tray)
    tray_button.pack(pady=10)

    root.protocol("WM_DELETE_WINDOW", on_quit)
    root.mainloop()

# 🧑‍💻 Minimize to tray function
def minimize_to_tray():
    root.withdraw()  # Hide the main window
    icon_thread = threading.Thread(target=create_tray_icon, daemon=True)
    icon_thread.start()

# 🏁 Run
if __name__ == "__main__":
    otto_thread = threading.Thread(target=run_otto, daemon=True)
    setup_gui()

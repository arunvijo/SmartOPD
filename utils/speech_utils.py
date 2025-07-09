try:
    import pyttsx3
    engine = pyttsx3.init()
    tts_enabled = True
except Exception:
    print("[TTS DISABLED] pyttsx3 not supported in this environment.")
    engine = None
    tts_enabled = False

def speak_token(token, name):
    msg = f"Token number {token}, patient {name}, please proceed."
    if tts_enabled and engine:
        engine.say(msg)
        engine.runAndWait()
    else:
        print(f"[AUDIO] {msg}")


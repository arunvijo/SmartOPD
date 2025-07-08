import pyttsx3

def speak_token(token, name):
    engine = pyttsx3.init()
    msg = f"Token number {token}, patient {name}, please proceed."
    engine.say(msg)
    engine.runAndWait()
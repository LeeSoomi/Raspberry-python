# !pip install SpeechRecognition pydub

import speech_recognition as sr
from google.colab import files

# 음성 파일 업로드
uploaded = files.upload()

recognizer = sr.Recognizer()
audio_file = list(uploaded.keys())[0]

# 오디오 파일로부터 음성 입력
with sr.AudioFile(audio_file) as source:
    audio = recognizer.record(source)

# 음성 인식
try:
    text = recognizer.recognize_google(audio)
    print(f"You said: {text}")
except sr.UnknownValueError:
    print("Google Speech Recognition could not understand audio")
except sr.RequestError as e:
    print(f"Could not request results from Google Speech Recognition service; {e}")

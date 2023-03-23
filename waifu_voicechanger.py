import speech_recognition as sr
import keyboard
import asyncio
import textwrap
from tkinter import *
import threading
import queue
import time
from voicevox import Client
from googletrans import Translator
from pydub import AudioSegment
from pydub.playback import play

# list microphone index
for idx in range(len(sr.Microphone.list_microphone_names())):
    print(idx, sr.Microphone.list_microphone_names()[idx])

# config
PUSHKEY = "f"  # tab to talk key
SOUNDINDEX = 0 # check index sound in voicevox
DESKTOPMIC = 3 # your desktop loopback (vb cable)
YOURMICINDEX = 1 # your microphone

TARGET_LANG='en' 
MYLANG='th'

mic = sr.Microphone(YOURMICINDEX)
rec = sr.Recognizer()

subtitle_text = "..."
queues = queue.Queue()
translator = Translator()

class setInterval :
    def __init__(self,interval,action) :
        self.interval=interval
        self.action=action
        self.stopEvent=threading.Event()
        thread=threading.Thread(target=self.__setInterval)
        thread.start()

    def __setInterval(self) :
        nextTime=time.time()+self.interval
        while not self.stopEvent.wait(nextTime-time.time()) :
            nextTime+=self.interval
            self.action()

    def cancel(self) :
        self.stopEvent.set()

def subtitleDisplay():
    global root 
    root = Tk()
    root.overrideredirect(True)
    root.geometry(f'{root.winfo_screenwidth()}x{root.winfo_screenheight()}+{0}+{1000}')
    root.lift()
    root.wm_attributes('-topmost', True)
    root.wm_attributes('-disabled', True)
    root.wm_attributes('-transparentcolor', "black")
    root.config(bg="black")

    global subtitle_label
    subtitle_label = Label(
        text=subtitle_text,
        font=('Comic Sans MS', 35, 'bold italic'),
        fg="white",
        bg="black"
    )
    subtitle_label.pack()
    root.mainloop()

def subtitleUpdate():
    global subtitle_text
    if not queues.empty():
        subtitle_text = queues.get()
        print("[Subtitle] " + subtitle_text)
        textwrap.fill(subtitle_text, 64)
        subtitle_label.config(text=subtitle_text)
def speak():
    async def createSound(text):
        async with Client() as client:
            audio_query = await client.create_audio_query(
                text, speaker=SOUNDINDEX
            )
            with open("voice.wav", "wb") as f:
                f.write(await audio_query.synthesis(speaker=SOUNDINDEX))
                sound = AudioSegment.from_wav('voice.wav')
                play(sound)

    while True:
        keyboard.wait(PUSHKEY)
        try:
            with mic as source:
                print("[Logs] now listen!")
                audio = rec.listen(source, phrase_time_limit=5)
                rawText = rec.recognize_google(audio, language=MYLANG)
                print("("+MYLANG+") " + rawText)
                if len(rawText) > 1:  # fix error empty sound
                    # translate to japan
                    text = translator.translate(rawText, dest=TARGET_LANG)
                    print("("+TARGET_LANG+") " + text.text)

                    # call function make sound waifu with voicevox
                    asyncio.run(createSound(text.text))
                else:
                    print("[Logs] can't translate!")
        except:
            continue
def createSubtitle():
    def record_callback(_, audio):
        try:
            outputText = rec.recognize_google(audio, language=TARGET_LANG)
            _msg = translator.translate(outputText, dest=MYLANG)
            print("[Translate Subtitle] ", "("+TARGET_LANG+") ", outputText, " ("+MYLANG+") ",_msg.text)
            queues.put(outputText+"\n"+_msg.text)
        except sr.UnknownValueError:
            print("[Warn] Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print(
                "[Warn] Could not request results from Google Speech Recognition service; {0}".format(e))
        # record background
    rec.listen_in_background(sr.Microphone(DESKTOPMIC), record_callback, phrase_time_limit=2)
    setInterval(1,subtitleUpdate)

threading.Thread(target=speak, args=()).start()
threading.Thread(target=subtitleDisplay, args=()).start()
threading.Thread(target=createSubtitle, args=()).start()

import time
import speech_recognition as sr


def callback(recognizer, audio):
    print('INFO: Heard smth')
    try:
        txt = recognizer.recognize_google(audio)
        print("Google Speech Recognition thinks you said: " + txt)
        print(type(txt))
        if txt == 'okay':
            print('POWIEDZIAŁ OK')
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))
    print('INFO: ---')


r = sr.Recognizer()
m = sr.Microphone()

###

print('SETUP: ambient noise adjustment')

with m as source:
    r.adjust_for_ambient_noise(source)

print('SETUP: ambient noise adjustment done')

###

print('RUN: start listening in the background')
stop_listening = r.listen_in_background(m, callback)

print('RUN: do some unrelated computations for 50 seconds')
for _ in range(500):
    time.sleep(0.1)

print('RUN: stop listening in the background')
stop_listening(wait_for_stop=False)

print('RUN: do some more unrelated computations for 5 seconds')
for _ in range(50):
    time.sleep(0.1)

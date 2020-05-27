import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import time
import playsound
import speech_recognition as sr
import pyttsx3
import pytz
import subprocess
import wolframalpha
import wikipedia
import configparser
import random
import requests
import re


class YummlyExtractor():
    def __init__(self):
        self.url = 'https://yummly2.p.rapidapi.com/feeds/search'
        self.headers = {'x-rapidapi-host': 'yummly2.p.rapidapi.com',
                        'x-rapidapi-key': '5f032ce0acmsh944911b8d99d5dcp199441jsn9be35c34e285'}        

    def extract_list(self, ingredients=[]):
        if not ingredients:
            raise Exception('Ingredients list is empty')
        
        ingredients_string = ',+'.join(ingredients)
        query = {'q': ingredients_string,
                 'start': '0',
                 'maxResult': '10'}
        url, headers = self.url, self.headers

        response = requests.request("GET", url=url, headers=headers, params=query).json()
        recipe_list = response['feed']
        recipe_list = self.parse_list(recipe_list)
        return recipe_list

    def parse_list(self, recipe_list=[]):
        if not recipe_list:
            raise Exception('Recipe list is empty')

        parsed_list = []
        for recipe in recipe_list:
            recipe_dict = {}
            recipe_dict['name'] = recipe['display']['displayName']

            content = recipe['content']
            recipe_dict['prep_steps'] = content['preparationSteps']

            ingredients_info = content['ingredientLines']
            ingredient_list = [x['wholeLine'] for x in ingredients_info]
            recipe_dict['ingredients'] = ingredient_list
            parsed_list.append(recipe_dict)
        return parsed_list


class Sarah:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        self.MONTHS = ["january", "february", "march", "april", "may", "june","july", "august", "september","october", "november", "december"]
        self.DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        self.DAY_EXTENTIONS = ["rd", "th", "st", "nd"]

        config = configparser.ConfigParser()
        config.read("config.cfg")
        # Wolfram API
        app_id = config.get("CONFIGURATION","wolfram_app_id")
        self.client = wolframalpha.Client(app_id)

        self.STANDARD_TXT = 'If You want to know more, just ask Sarah!'
        self.NOT_UNDERSTAND = "I don't understand, try one more time"
        self.WAKE = "okay sarah"

    def speak(self, text):
        # Text 2 Speach
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        en_voice_id = "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0"
        engine.setProperty('voice', en_voice_id)
        engine.say(text)
        engine.runAndWait()

    def get_audio(self):
        # Speach 2 Text
        r = sr.Recognizer()
        with sr.Microphone() as source:
            audio = r.listen(source)
            said = ""

            try:
                said = r.recognize_google(audio)
                print(said)
            except Exception as e:
                print("Exception: " + str(e))

        return said.lower()

    def authenticate_google(self):
        """Shows basic usage of the Google Calendar API.
        Prints the start and name of the next 10 events on the user's calendar.
        """
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)

            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        service = build('calendar', 'v3', credentials=creds)

        return service

    def get_date(self, text):
        text = text.lower()
        today = datetime.date.today()

        if text.count("today") > 0:
            return today

        day = -1
        day_of_week = -1
        month = -1
        year = today.year

        for word in text.split():
            if word in self.MONTHS:
                month = self.MONTHS.index(word) + 1
            elif word in self.DAYS:
                day_of_week = self.DAYS.index(word)
            elif word.isdigit():
                day = int(word)
            else:
                for ext in self.DAY_EXTENTIONS:
                    found = word.find(ext)
                    if found > 0:
                        try:
                            day = int(word[:found])
                        except:
                            pass
        
        if month < today.month and month != -1:
            year = year+1

        if month == -1 and day != -1:
            if day < today.day:
                month = today.month + 1
            else:
                month = today.month

        if month == -1 and day == -1 and day_of_week != -1:
            current_day_of_week = today.weekday()
            dif = day_of_week - current_day_of_week

            if dif < 0:
                dif += 7
                if text.count("next") >= 1:
                    dif += 7

            return today + datetime.timedelta(dif)

        if day != -1:
            return datetime.date(month=month, day=day, year=year)

    def get_events(self, day, service):
        # Call the Calendar API
        date = datetime.datetime.combine(day, datetime.datetime.min.time())
        end = datetime.datetime.combine(day, datetime.datetime.max.time())
        utc = pytz.UTC
        date = date.astimezone(utc)
        end = end.astimezone(utc)
        events_result = service.events().list(calendarId='primary', timeMin=date.isoformat(), timeMax=end.isoformat(),
                                            singleEvents=True,
                                            orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            self.speak('No upcoming events found.')
        else:
            self.speak(f"You have {len(events)} events on this day.")

            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(start, event['summary'])
                start_time = str(start.split("T")[1].split("-")[0])
                if int(start_time.split(":")[0]) < 12:
                    start_time = start_time + "am"
                else:
                    start_time = str(int(start_time.split(":")[0])-12) + start_time.split(":")[1]
                    start_time = start_time + "pm"  

                self.speak(event["summary"] + " at " + start_time)

    def note(self, text):
        date = datetime.datetime.now()
        file_name = str(date).replace(":", "-") + "-note.txt"
        with open(file_name, "w") as f:
            f.write(text)

        subprocess.Popen(["notepad.exe", file_name])

    def wolfram(self, text):
        result = self.client.query(text)
        answer = next(result.results).text

        print(answer)
        self.speak(answer)

    def get_question(self, text, phrase):
        return text.split(phrase)[-1][1:]

    def get_ingredients(self, text, phrase):
        return text.split(phrase)[-1][1:].split(' ')

    def ask_wikipedia(self, text):
        print(text)
        result = wikipedia.summary(text, sentences=3)
        print(result)
        self.speak(result)

    def select_recipe(self, recipe_list):
        recipe_list = [x for x in recipe_list if x['prep_steps']]
        self.speak(f'I found {len(recipe_list[0] + 1)} recipies')
        for i in len(recipe_list[0]):
            self.speak(f"{i + 1}: {recipe_list[0][i]['name']}")
        self.speak('What recipe number You want to cook?')
        text = self.get_audio()
        print(text)
        recipe = random.choice(recipe_list)
        return recipe

    def get_recipe(self, text):
        extractor = YummlyExtractor()
        recipe_list = extractor.extract_list(text)
        recipe = self.select_recipe(recipe_list)
        return recipe

    def run(self):
        print("Start")
        SERVICE = self.authenticate_google()

        while True:
            print("Listening")
            text = self.get_audio()
            if text.count(self.WAKE) > 0:
                self.speak("I am ready")
                text = self.get_audio()

                # KALENDARZ
                CALENDAR_STRS = ["what do i have", "do i have plans", "am i busy"]
                for phrase in CALENDAR_STRS:
                    if phrase in text:
                        date = self.get_date(text)
                        if date:
                            self.get_events(date, SERVICE)
                            self.speak(self.STANDARD_TXT)
                        else:
                            self.speak(self.NOT_UNDERSTAND)
                        self.speak(self.STANDARD_TXT)
                            

                # NOTATKI
                NOTE_STRS = ["make a note", "write this down", "remember this", "type this"]
                for phrase in NOTE_STRS:
                    if phrase in text:
                        self.speak("What would you like me to write down?")
                        write_down = self.get_audio()
                        self.note(write_down)
                        self.speak("I've made a note of that.")
                        self.speak(self.STANDARD_TXT)

                # POGODA
                WEATHER_STRS = ["what is the weather"]
                for phrase in WEATHER_STRS:
                    if phrase in text:
                        date = self.get_date(text)
                        if date:
                            phrase = phrase + ' ' + str(date)
                        else:
                            self.speak(self.NOT_UNDERSTAND)
                        self.wolfram(phrase)
                        self.speak(self.STANDARD_TXT)

                # MATEMATYKA
                WEATHER_STRS = ["i have a math question"]
                for phrase in WEATHER_STRS:
                    if phrase in text:
                        self.speak("What would you like to know?")
                        write_down = self.get_audio()
                        self.wolfram(write_down)
                        self.speak(self.STANDARD_TXT)

                # WIKIPEDIA
                WIKIPEDIA_STRS = ["i want to know"]
                for phrase in WIKIPEDIA_STRS:
                    if phrase in text:
                        que = self.get_question(text, phrase)
                        if que:
                            self.ask_wikipedia(que)
                            self.speak(self.STANDARD_TXT)
                        else:
                            self.speak(self.NOT_UNDERSTAND)
                        self.speak(self.STANDARD_TXT)
                
                # PRZEPISY
                RECIPE_STRS = ["find a recipe"]
                for phrase in RECIPE_STRS:
                    if phrase in text:
                        self.speak("What ingredients do you have?")
                        text = self.get_audio()
                        ingredients = self.get_ingredients(text, 'i have')
                        print(f'Ingredients: {ingredients}')
                        if ingredients:
                            try:
                                recipe = self.get_recipe(ingredients)
                                self.speak("I have found a recipe for {}".format(recipe["name"]))
                                self.speak("Do you want me to read it out loud?")
                                response = self.get_audio()
                                if "yes" in response:
                                    print(recipe["prep_steps"])
                                    self.speak(recipe["prep_steps"])
                                else:
                                    self.speak("okay, let me know if You want to cook something")
                            except(Exception):
                                self.speak("Unfortunately I haven't found any recipes")
                        else:
                            self.speak(self.NOT_UNDERSTAND)
                        self.speak(self.STANDARD_TXT)

            print('----')

if __name__ == "__main__":
    sarah = Sarah()
    sarah.run()
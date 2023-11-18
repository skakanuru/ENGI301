"""
--------------------------------------------------------------------------
Voice Assistant Powered by GPT
--------------------------------------------------------------------------
License:   
Copyright 2023 - Sathvik Kakanuru

Redistribution and use in source and binary forms, with or without 
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, 
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, 
   this list of conditions and the following disclaimer in the documentation 
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors 
   may be used to endorse or promote products derived from this software without 
   specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE 
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF 
THE POSSIBILITY OF SUCH DAMAGE.
--------------------------------------------------------------------------

This voice assistant leverages the advanced AI capabilities of GPT to 
interpret and respond to user commands. Through a streamlined setup using a 
PocketBeagle, microphone, speaker, and wireless adapter, it aims to provide 
a responsive and intelligent assistant that operates via voice commands.

Functionalities include:
  - Capturing voice input through a microphone
  - Converting speech to text for processing
  - Generating a response using GPT AI technology
  - Converting the generated text back to speech for audio output

The system is designed to operate with simplicity, requiring minimal physical 
interaction, which paves the way for future enhancements such as touch-free 
voice activation and improved response times.

Error Handling:
  - Unrecognizable voice commands will be prompted for re-entry
  - Non-resolvable queries will be logged for future improvements

--------------------------------------------------------------------------
""
import pyaudio
import wave
import openai
import io
from pydub import AudioSegment
from pydub.playback import play
from button import Button
import Adafruit_BBIO.GPIO as GPIO
import time
from urllib import request

# Class to handle the audio recording via microphone
class AudioRecorder:
    def __init__(self, button):
        # Audio settings
        self.format = pyaudio.paInt16  # Audio format
        self.channels = 1  # Mono channel
        self.rate = 44100  # Sampling rate
        self.chunk = 4096  # Buffer size
        self.filename = "test_recording.wav"  # File to save the recording
        self.record_seconds = 10  # Duration of the recording
        self.button = button  # Button to trigger recording
    
    # Function to record audio from the microphone
    def record(self):
        audio = pyaudio.PyAudio()  # Create a PyAudio object
        # Open a stream for audio input
        stream = audio.open(format=self.format, channels=self.channels,
                            rate=self.rate, input=True,
                            frames_per_buffer=self.chunk)

        print("Press the button to start recording")
        self.button.wait_for_press()  # Wait for button press to start recording
        print("Recording for 10 seconds...")

        frames = []
        # Record audio in chunks for the set duration
        for _ in range(0, int(self.rate / self.chunk * self.record_seconds)):
            data = stream.read(self.chunk, exception_on_overflow=False)
            frames.append(data)

        print("Finished recording.")

        # Stop and close the audio stream
        stream.stop_stream()
        stream.close()
        audio.terminate()

        # Save the recorded audio to a file
        wf = wave.open(self.filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(audio.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        print(f"File saved: {self.filename}")

        return self.filename

# Class to convert speech in an audio file to text using Google's speech-to-text service
class SpeechToTextConverter:
    def __init__(self, credentials_file):
        from google.cloud import speech
        from google.oauth2 import service_account
        # Set up the client with credentials
        credentials = service_account.Credentials.from_service_account_file(credentials_file)
        self.client = speech.SpeechClient(credentials=credentials)

    # Function to perform the conversion from speech to text
    def convert(self, audio_file):
        from google.cloud import speech
        # Read audio file and prepare for recognition
        with io.open(audio_file, 'rb') as f:
            content = f.read()
            audio = speech.RecognitionAudio(content=content)

        # Set up the configuration for recognition
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=44100,
            language_code='en-US'
        )

        # Perform the speech recognition
        response = self.client.recognize(config=config, audio=audio)
        # Print and return the recognized text
        print(response.results[0].alternatives[0].transcript)
        return response.results[0].alternatives[0].transcript

# Class to generate responses using OpenAI's GPT model
class GPTResponseGenerator:
    def __init__(self, api_key):
        openai.api_key = api_key  # Set the OpenAI API key

    # Function to send a prompt to the GPT model and receive a response
    def generate_response(self, prompt, model="gpt-3.5-turbo"):
        try:
            # Make the API call to OpenAI
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            )
            # Return the GPT response
            return response.choices[0].message.content
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

# Class to convert text to speech
class TextToSpeech:
    
    def __init__(self):
        # File paths for the output audio files
        self.mp3_file_path = "audioOutputFile.mp3"
        self.wav_file_path = "audioOutputFile.wav"

    # Function to convert text to speech and save the audio file
    def convert_and_save(self, text, lang='en'):
        from gtts import gTTS
        # Convert text to speech using gTTS
        tts = gTTS(text=text, lang=lang)
        # Save the speech as an MP3 file
        tts.save(self.mp3_file_path)
        # Convert MP3 to WAV format
        audio = AudioSegment.from_mp3(self.mp3_file_path)
        audio.export(self.wav_file_path, format="wav")
        return self.wav_file_path

# Class to run the entire process continuously
class ContinuousRunner:
    def __init__(self, button_pin):
        # Initialize the components
        self.speech_to_text = SpeechToTextConverter('sa_speechDemoKey.json')
        self.gpt_response_generator = GPTResponseGenerator("sk-...")
        self.text_to_speech = TextToSpeech()
        self.button = Button(button_pin)
        self.recorder = AudioRecorder(self.button)

    # Function to run the recording, speech-to-text, response generation, and text-to-speech continuously
    def run(self):
        while True:
            audio_file = self.recorder.record()
            text = self.speech_to_text.convert(audio_file)
            response = self.gpt_response_generator.generate_response(text)
            print(response)
            wav_file = self.text_to_speech.convert_and_save(response)
            play(AudioSegment.from_file(wav_file))

# Entry point of the script
if __name__ == "__main__":
    # Function to check for internet connectivity
    def connected_internet(): 
        try:
            request.urlopen("https://www.google.com", timeout=1)
            return True
        except request.URLError as err:
            return False

    # Wait for internet connection before starting
    while not connected_internet():
        time.sleep(1)
    out = "USR3"
    GPIO.setup(out, GPIO.OUT)
    # Blink an LED to indicate the system is ready
    i = 0
    while i < 50:
        GPIO.output(out, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(out, GPIO.LOW)
        time.sleep(0.1)
        i = i + 1
    button_pin = "P2_30"
    # Initialize and start the continuous runner
    runner = ContinuousRunner(button_pin)
    runner.run()

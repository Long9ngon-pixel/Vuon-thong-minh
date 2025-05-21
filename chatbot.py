import speech_recognition as sr
from gtts import gTTS
import os
import tempfile
import threading
import time
from openai import OpenAI

# Initialize OpenAI client for Ollama
client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama'  # required, but unused
)

# Initialize speech recognition recognizer with appropriate settings
recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = False
recognizer.energy_threshold = 400
recognizer.pause_threshold = 0.8

# Use a temporary directory for audio files
temp_dir = tempfile.gettempdir()
response_file = os.path.join(temp_dir, "response.mp3")

def listen_to_speech():
    """Capture speech from microphone and convert to text"""
    with sr.Microphone() as source:
        print("Listening...")
        # Only adjust for ambient noise once at the beginning
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        
    try:
        # Recognize speech using Google Speech Recognition
        print("Processing speech...")
        text = recognizer.recognize_google(audio, language="vi-VN")
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Could not understand audio")
        return ""
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
        return ""

def get_ai_response(input_text):
    """Get response from Gemma2 model"""
    try:
        print("Getting AI response...")
        response = client.chat.completions.create(
            model="gemma2:9b",
            messages=[
                {"role": "system", "content": "You are a helpful assistant who responds in Vietnamese."},
                {"role": "user", "content": input_text}
            ],
            max_tokens=150  # Limit token length for faster responses
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error getting AI response: {e}")
        return "Xin lỗi, tôi không thể xử lý yêu cầu của bạn lúc này."

def speak_text(text):
    """Convert text to speech using gTTS"""
    try:
        # Create speech in a separate thread to avoid blocking
        tts = gTTS(text=text, lang='vi', slow=False)
        
        # Clean up previous file if it exists
        if os.path.exists(response_file):
            try:
                os.remove(response_file)
            except:
                pass
                
        tts.save(response_file)
        
        # Use appropriate play command based on OS
        if os.name == 'nt':  # Windows
            os.system(f"start {response_file}")
        elif os.name == 'posix':  # macOS or Linux
            if os.system("which afplay > /dev/null") == 0:  # macOS
                os.system(f"afplay {response_file}")
            else:  # Linux
                os.system(f"mpg123 {response_file}")
    except Exception as e:
        print(f"Error in text-to-speech: {e}")

def process_input_async(user_input):
    """Process user input and generate response asynchronously"""
    if user_input:
        # Get AI response
        ai_response = get_ai_response(user_input)
        print(f"AI: {ai_response}")
        
        # Convert response to speech
        speak_text(ai_response)

def main():
    print("Voice Assistant Started (Press Ctrl+C to exit)")
    print("Adjusting for ambient noise... Please wait.")
    
    # Initialize microphone once
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=2)
    
    try:
        while True:
            # Listen for speech input
            user_input = listen_to_speech()
            
            if user_input:
                # Process input in a separate thread to keep UI responsive
                threading.Thread(target=process_input_async, args=(user_input,)).start()
                
            # Small delay to prevent CPU overuse
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("Voice assistant stopped.")

if __name__ == "__main__":
    main()
import pygetwindow as gw
import difflib
import time
from pynput.keyboard import Key, Controller
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def send_message_with_retry(message, max_attempts=3):
    for attempt in range(max_attempts):
        print(f"Attempt {attempt + 1}: Sending message...", end="")
        if send_message(message):
            print("Message sent.")
            return True
        else:
            print("Failed.")
            time.sleep(1)  # Introduce a short delay before retrying
    print(f"All {max_attempts} attempts failed. Unable to send message.")
    return False
    
    send_message_with_retry(message)

kill_cooldown = 250  # seconds
death_cooldown = 250  # seconds

max_tokens_penalty = 5  # Adjust the penalty value
repeating_penalty = 5  # Adjust the penalty value

last_kill_time = time.time() - kill_cooldown
last_death_time = time.time() - death_cooldown

in_game = False
kills = 0
deaths = 0

message_history = {"kills": set(), "deaths": set()}  # Maintain a history of generated messages

def send_message(message):
    print("Sending message:", message)
    keyboard.press(Key.enter)
    keyboard.release(Key.enter)
    time.sleep(0.04)
    keyboard.type(message)
    time.sleep(0.04)
    keyboard.press(Key.enter)
    keyboard.release(Key.enter)
    time.sleep(0.04)
    # Introduce a short delay to allow the message to be sent
    time.sleep(2)

    # Check if the message is successfully sent
    if is_message_sent():
        return True
    else:
        return False

def is_message_sent():
    # Add a function to check if the message is successfully sent
    # You can implement this based on your specific scenario, e.g., check if the chat log reflects the sent message.
    # Return True if the message is successfully sent; otherwise, return False.
    return True

    
def length_penalty_score(message_length, max_length, penalty_factor):
    # Calculate a penalty score based on the difference between message_length and max_length
    return max(1.0, penalty_factor ** (abs(message_length - max_length) / 10.0))

def is_repeating(message, history_set, penalty_factor):
    # Check if the message is repeating based on the message history
    for prev_message in history_set:
        similarity_score = difflib.SequenceMatcher(None, message, prev_message).ratio()
        if similarity_score > penalty_factor:
            return True
    return False

# Update the OpenAI API base URL
openai_api_base = "http://127.0.0.1:5001/v1"

def is_game_window_active():
    active_window = gw.getActiveWindow()
    if active_window:
        print("Window Title:", active_window.title)
        if "League of Legends (TM) Client" in active_window.title:
            print("Game window is active.")
            return True
    print("Game window is not active.")
    return False
        
while True:
    keyboard = Controller()
    try:
        request_pseudo = requests.get('https://127.0.0.1:2999/liveclientdata/activeplayername', verify=False)
        your_pseudo = request_pseudo.json()
        response_API = requests.get(f'https://127.0.0.1:2999/liveclientdata/playerscores?summonerName={your_pseudo}',
                                    verify=False)
        statistics = response_API.json()

        if request_pseudo and response_API and not in_game:
            print("Game found!")
            in_game = True

        new_kills = statistics['kills']
        new_deaths = statistics['deaths']

        if new_kills > kills:
            current_time = time.time()
            if current_time - last_kill_time > kill_cooldown:
                kills = new_kills
                last_kill_time = current_time
                # Use the chat-based API for a more interactive conversation
                messages = [
                    {"role": "user", "content": "* is not a bot has killed in match league of legends.*"},
                    {"role": "assistant", "content": " is not a bot has killed enemy in league of legends what will you say? start it with adding /all chat-line. funny short joke of 10 words only or less"},
                ]
                response = requests.post(f"{openai_api_base}/chat/completions", json={"messages": messages})
                print(response.content)  # Print the response content for debugging
                if response.status_code == 200:
                    message = response.json()['choices'][0]['message']['content']
                    print("Generated Message:", message)
                    # Apply length penalty
                    max_tokens = 15  # Adjust the desired max tokens
                    penalty_factor = 0.8  # Adjust the penalty factor
                    penalty = length_penalty_score(len(message.split()), max_tokens, penalty_factor)
                    # Check for repetition
                    # Check if the game window is active before sending the message
                    if is_game_window_active():
                        send_message_with_retry(message)
                        message_history["kills"].add(message)
                        if len(message_history["kills"]) > 10:  # Limit history size
                            message_history["kills"].pop()
                        time.sleep(penalty)  # Introduce delay based on penalty

        if new_deaths > deaths:
            current_time = time.time()
            if current_time - last_death_time > death_cooldown:
                deaths = new_deaths
                last_death_time = current_time
                # Use the chat-based API for a more interactive conversation
                messages = [
                    {"role": "user", "content": "* is not a bot has died in match league of legends.*"},
                    {"role": "assistant", "content": " is not a bot died in league of legends so you opened the chat and what will you say? start it with /all short and funny joke of 10 words only or less."},
                ]
                response = requests.post(f"{openai_api_base}/chat/completions", json={"messages": messages})
                if response.status_code == 200:
                    message = response.json()['choices'][0]['message']['content']
                    # Apply length penalty
                    max_tokens = 15  # Adjust the desired max tokens
                    penalty_factor = 0.8  # Adjust the penalty factor
                    penalty = length_penalty_score(len(message.split()), max_tokens, penalty_factor)
                    # Check for repetition
                    # Check if the game window is active before sending the message
                    if is_game_window_active():
                        send_message_with_retry(message)
                        message_history["deaths"].add(message)
                        if len(message_history["deaths"]) > 10:  # Limit history size
                            message_history["deaths"].pop()
                        time.sleep(penalty)  # Introduce delay based on penalty

        time.sleep(3)

    except Exception as e:
        if in_game:
            print(f"Searching for the game... Error: {e}")
        in_game = False
        time.sleep(5)
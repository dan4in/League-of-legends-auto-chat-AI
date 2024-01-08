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

def log_response(notepad_file, current_model_name, model_name, response_content):
    with open(notepad_file, "a", encoding="utf-8") as file:
        # Log the model name only if it changes
        if model_name != current_model_name:
            file.write(f"\n\nModel Name: {model_name}\n")
            current_model_name = model_name

        # Log the response content
        file.write(response_content + "\n")

    return current_model_name

kill_notepad_file = "kill_response_log.txt"
death_notepad_file = "death_response_log.txt"
current_kill_model_name = ""
current_death_model_name = ""

kill_cooldown = 10  # seconds
death_cooldown = 10  # seconds

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
    return is_message_sent()

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
LEAGUE_API_BASE = "https://127.0.0.1:2999/liveclientdata"
VERIFY_SSL = False  # Change this to True in a production environment

def is_game_window_active():
    active_window = gw.getActiveWindow()
    if active_window:
        print("Window Title:", active_window.title)
        if "League of Legends (TM) Client" in active_window.title:
            print("Game window is active.")
            return True
    print("Game window is not active.")
    return False

message = ""  # Initialize message outside the conditional blocks

current_final_score = None  # Initialize a variable to store the current final score

# Assuming you have game data with information about all players and an indicator for the active player


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

        # Initialize message here
        message = ""
        
             
        if new_kills > kills:
            current_time = time.time()
            if current_time - last_kill_time > kill_cooldown:
                kills = new_kills
                last_kill_time = current_time
                # Use the chat-based API for a more interactive conversation
                messages = [
                    {"role": "user", "content": "*Ashe is not a bot has killed in match league of legends.*"},
                    {"role": "assistant", "content": "give 1 short dirty and cringe league of legends joke 10 words only or less start it with /all"},
                ]
                response = requests.post(f"{openai_api_base}/chat/completions", json={"messages": messages})
                print(response.content)  # Print the response content for debugging
                if response.status_code == 200:
                    model_name = response.json()['model']
                    message = response.json()['choices'][0]['message']['content']
                    print("Generated kill Message:", message)
                    current_kill_model_name = log_response(kill_notepad_file, current_kill_model_name, model_name, message)

                    if send_message_with_retry(message):
                        last_death_time = time.time()

                else:
                    print("Failed to get response from the API.")
            elif current_kill_model_name != "":
                # If a kill message was generated, wait for some time before sending death messages
                if last_death_time + death_cooldown < time.time():
                    current_death_model_name = current_kill_model_name
                    print("Sending death message...")
        if new_deaths > deaths:
            current_time = time.time()
            if current_time - last_death_time > death_cooldown:
                deaths = new_deaths
                last_death_time = current_time
                # Use the chat-based API for a more interactive conversation
                messages = [
                   {"role": "user", "content": "*Ashe is not a bot has died in match league of legends.*"},
                   {"role": "assistant", "content": "give 1 short and dirty cringe league of legends joke 10 words only or less start it with /all"}

                 ]
                response = requests.post(f"{openai_api_base}/chat/completions", json={"messages": messages})
                print(response.content)  # Print the response content for debugging
                if response.status_code == 200:
                    model_name = response.json()['model']
                    message = response.json()['choices'][0]['message']['content']
                    print("Generated death Message:", message)
                    current_death_model_name = log_response(death_notepad_file, current_death_model_name, model_name, message)
                     
                    if send_message_with_retry(message):
                        last_death_time = time.time()

                else:
                    print("Failed to get response from the API.")

        # Check for repeating messages and apply a penalty score
        message_length = len(message)
        max_length = 10  # Adjust the maximum length of the message as needed
        if is_repeating(message, message_history["kills"], repeating_penalty):
            print("Repeated kill message detected. Applying penalty score.")
            penalty_score = length_penalty_score(message_length, max_length, repeating_penalty)
        elif is_repeating(message, message_history["deaths"], repeating_penalty):
            print("Repeated death message detected. Applying penalty score.")
            penalty_score = length_penalty_score(message_length, max_length, repeating_penalty)
        else:
            penalty_score = 1.0

        # Update the message history and calculate the final score
        if new_kills != 0:
            kills_score = (1.0 - penalty_score) * kills / new_kills
        else:
            kills_score = 0.0

        if new_deaths != 0:
            deaths_score = (1.0 - penalty_score) * deaths / new_deaths
        else:
            deaths_score = 0.0

        final_score = kills_score + deaths_score

        # Print the final score only when it changes
        if final_score != current_final_score:
            print("Final Score:", round(final_score, 2))
            current_final_score = final_score

        time.sleep(3)

    except Exception as e:
        if in_game:
            print(f"Searching for the game... Error: {e}")
        in_game = False
        time.sleep(5)

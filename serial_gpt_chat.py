import openai
import serial
import time
import random
import textwrap
from unidecode import unidecode

# Serial communication functions
def send_to_printer(ser, message, clean_prefix=""):

    # Send the clean prefix without typos or delay
    if clean_prefix:
        ser.write(clean_prefix.encode('ascii', errors='replace'))
        ser.flush()

    ascii_message = unidecode(message)

    typo_probability = 0.03  # Set the probability of a typo occurring
    
    # Map of common typo substitutions (considering a QWERTY keyboard layout)
    typo_substitutions = {
        'a': 'sqwz',
        'b': 'vghn',
        'c': 'xdfv',
        'd': 'serfcx',
        'e': 'wsdfr',
        'f': 'drtgvc',
        'g': 'ftyhbv',
        'h': 'gyujnb',
        'i': 'ujko',
        'j': 'huikmn',
        'k': 'jiolm',
        'l': 'kop',
        'm': 'njkl',
        'n': 'bhjm',
        'o': 'iklp',
        'p': 'ol',
        'q': 'wa',
        'r': 'edft',
        's': 'wazx',
        't': 'rfgy',
        'u': 'yihj',
        'v': 'cfgb',
        'w': 'qase',
        'x': 'zsdc',
        'y': 'tghu',
        'z': 'asx'
        #' ': 'vcxz<,>.?/:;"[{]}|=+-_)(*&^%$#@!`~'
    }
    
    for char in ascii_message:
        # Insert a typo
        if random.uniform(0, 1) < typo_probability:
            if char.lower() in typo_substitutions:
                typo_char = random.choice(typo_substitutions[char.lower()])
                ser.write(typo_char.encode('ascii'))
                ser.flush()
                time.sleep(random.uniform(0.05, 0.2))
            
                # Simulate correcting the typo
                ser.write(b'\b')  # Backspace character
                ser.flush()
                time.sleep(random.uniform(0.2, 0.4))  # Slightly longer pause to "realize" the mistake
        
        # Type the actual character
        ser.write(char.encode('ascii', errors='replace'))
        ser.flush()
        
        # Basic delay for all characters
        time.sleep(random.uniform(0.05, 0.2))
        
        # Additional delay for punctuation and whitespace
        if char in ".,?!":
            time.sleep(random.uniform(0.3, 0.7))
        elif char == " ":
            time.sleep(random.uniform(0.1, 0.3))

    ser.write(b'\r')
    ser.flush()
    time.sleep(1)

def receive_and_echo(ser):
    response_data = b''
#     while True:
#         if ser.in_waiting:
#             char = ser.read(1)
#             response_data += char
#             ser.write(char)
    add_margin = True
    
    while True:
        if ser.in_waiting:
            char = ser.read(1)
            response_data += char
            
            # Add a margin before the line
            if add_margin:
                ser.write(b'  ')  # Add two spaces as left margin
                add_margin = False
            
            # Echo the character
            ser.write(char)
            
            # If newline or carriage return, set flag to add margin on the next line
            if char in [b'\n', b'\r']:
                add_margin = True
            if char == b'\r':
                break
        time.sleep(0.05)
    return response_data.decode('ascii', errors='ignore')

def format_message(message, width=70, indent=5):
    # Wrap text after a certain width
    wrapped_lines = textwrap.wrap(message, width)

    # Join lines together, adding a newline and indent to all but the first line
    formatted_message = '\r' + ' ' * indent
    formatted_message = formatted_message.join(wrapped_lines)
    
    return formatted_message

# Set up your OpenAI API key
openai.api_key = 'YOUR-OPENAI-KEY'

def generate_gpt3_5_response(prompt, conversation_history, retry=False):
    # If retrying, you might want to modify the prompt, e.g., ask for a different movie
    if retry:
        prompt += " Can you suggest something else?"
    
    # Add user's message to conversation history
    conversation_history.append({"role": "user", "content": prompt})
    
    try:
        # API call to OpenAI GPT-3.5-turbo
        response = openai.ChatCompletion.create(
            model="ft:gpt-3.5-turbo-0613:personal::XXXXXXX",
            messages=conversation_history,
            max_tokens=512,
            temperature=0.94,
            top_p=1,
            frequency_penalty=0.2
        )
        response_content = response['choices'][0]['message']['content'].strip()
        print(f"Diary Bot: {response_content}")  # Debugging line to see responses in console
        return response_content
    except Exception as e:
        print("Error calling OpenAI API:", str(e))
        return "Oops, I had trouble thinking there. Can we try a different topic?"

# Main interaction loop
def main():
    # Configure your serial port accordingly
    with serial.Serial(port='/dev/tty.usbserial-FTDJA246', baudrate=1200, bytesize=8, parity='N', stopbits=1, xonxoff=True, timeout=1) as ser:
        # send_to_printer(ser, "     > Hey there.")
        
        # Initialize conversation history
        conversation_history = [{"role": "system", "content": ("You are a good friend. Have an original perspective. No response over 150 characters.")}]
        
        while True:
            # Receive message from typewriter
            user_message = receive_and_echo(ser)

            print(f"EP-44: {user_message}")  # Debugging line to see responses in console

            # Get response from OpenAI GPT-3.5-turbo
            ai_message = generate_gpt3_5_response(user_message, conversation_history)
            
            # Update conversation history with AI response
            conversation_history.append({"role": "assistant", "content": ai_message})
            
            formatted_message = format_message(ai_message)

            # Send AI message to typewriter
            # send_to_printer(ser, f"     > {formatted_message}")
            send_to_printer(ser, formatted_message, clean_prefix="     > ")

# Run the main loop
if __name__ == "__main__":
    main()
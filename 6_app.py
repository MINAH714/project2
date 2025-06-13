import ollama

def stream_chat():
    stream = ollama.chat(
        model='gemma3:12b',
        messages=[
            {
                'role': 'system',
                'content': (
                    "You are a data generator for an empathetic chatbot. "
                    "Generate realistic Korean-language conversations between virtual characters. "
                    "Each character should have a specified age group (teen, adult, senior), gender (male, female), and a clear emotional state (e.g., happy, sad, anxious, excited). "
                    "Always answer ONLY in Korean, in JSON format with keys: age_group, gender, emotion, role, content. "
                    "Do not add any explanation or English translation."
                )
            },
            {
                'role': 'user',
                'content': (
                    "Generate a sample conversation turn for a chatbot training dataset. "
                    "Specify the character's age group, gender, and emotion."
                )
            }
        ],
        stream=True
    )

    for chunk in stream:
        print(chunk['message']['content'], end='', flush=True)

stream_chat()

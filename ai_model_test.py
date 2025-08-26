from ai_model import AIModel


def test_grok_api():
    print("=== Testing _call_grok_api ===")
    grok_model = AIModel(use_grok=True)
    try:
        response = grok_model._call_grok_api("Hello, how are you?", "Act as a hella rude coach who is tryna motivate me to do my habits. When I talk to you, respond in that tone. Make sure you use hella swear words.")
        print(f"Success - {response}")
    except Exception as e:
        print(f"Error: {e}")
    print()

def test_first_message():
    print("=== Testing first_message ===")
    grok_model = AIModel(use_grok=True)
    try:
        response = grok_model.first_message("tracking daily journaling + prayer log")
        print(f"Success: {response}")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"Error: {e}")
    print()

def test_choose_tag():
    print("=== Testing choose_tag ===")
    grok_model = AIModel(use_grok=True)
    try:
        tag = grok_model.choose_tag("I prayed for 10 minutes today and felt peaceful")
        print(f"Success: {tag}")
    except Exception as e:
        print(f"Error: {e}")
    print()

def test_choose_title():
    print("=== Testing choose_title ===")
    grok_model = AIModel(use_grok=True)
    try:
        title = grok_model.choose_title("Had a great workout and meal prep session")
        print(f"Success: {title}")
    except Exception as e:
        print(f"Error: {e}")
    print()

def test_call_grok_api():
    print("=== Testing _call_grok_api directly ===")
    grok_model = AIModel(use_grok=True)
    try:
        response = grok_model._call_grok_api("Hello, how are you?", "You are a helpful assistant.")
        print(f"Success: {response}")
    except Exception as e:
        print(f"Error: {e}")
    print()

if __name__ == "__main__":
    # test_grok_api()
    test_first_message()
    # test_choose_tag()
    # test_choose_title()
    # test_call_grok_api()
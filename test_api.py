import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from google import genai

# Load environment variables
load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Azure OpenAI Config
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_API_VERSION = os.getenv("AZURE_API_VERSION")
AZURE_DEPLOYMENT = os.getenv("AZURE_DEPLOYMENT")


def test_openai():
    try:
        client = AzureOpenAI(
            api_key=OPENAI_API_KEY,
            azure_endpoint=AZURE_ENDPOINT,
            api_version=AZURE_API_VERSION,
        )

        response = client.chat.completions.create(
            model=AZURE_DEPLOYMENT,
            messages=[
                {
                    "role": "user",
                    "content": "Say OK"
                }
            ],
            max_completion_tokens=5,
        )

        print("[OpenAI] OK")
        print("Response:", response.choices[0].message.content.strip())

    except Exception as e:
        print(f"[OpenAI] FAILED — {e}")


def test_gemini():
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Say OK"
        )

        print("[Gemini] OK")
        print("Response:", response.text)

    except Exception as e:
        print(f"[Gemini] FAILED — {e}")


if __name__ == "__main__":
    print("Testing APIs...\n")

    test_openai()
    print()

    test_gemini()
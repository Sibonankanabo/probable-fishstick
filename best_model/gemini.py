import os
import google.generativeai as genai

# Set your API key for Google Generative AI
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    # raise ValueError("API_KEY environment variable not set!")
     API_KEY = 'AIzaSyCIAYnp6w6TkXUeryfuRL1n_tLfJnwzgS4'
# Configure Google Generative AI
genai.configure(api_key=API_KEY)

# Directory to temporarily save uploaded files
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def analyze_file():
    file_name = "cleaned_data.csv"  # Correct the file extension if it's a CSV
    file_path = os.path.join(file_name)

    if not os.path.exists(file_path):
        print(f"File {file_path} not found!")
        return

    try:
        # Upload the file to Google Generative AI
        sample_file = genai.upload_file(path=file_path, display_name=file_name)

        # Use the generative model
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config={"response_mime_type": "text/plain"},
            )
 # Adjust to your available model, e.g., Gemini
        query = "Analyze this dataset and provide insights."

        # Generate content
        ai_response = model.generate_content([sample_file, query])
        print("AI Response:")
        print(ai_response.text)  # Adjust based on the response format
    except Exception as e:
        print(f"An error occurred: {e}")

# Call the function to analyze the file
analyze_file()

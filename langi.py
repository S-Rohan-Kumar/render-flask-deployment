import pytesseract
from PIL import Image
import os
import re

# Set the image path directly in the code
# # Change this to your image file path
IMAGE_PATH = "" # <-- EDIT THIS LINE with your image path

# Dictionary mapping language codes to their full names
LANGUAGE_NAMES = {
    'eng': 'English',
    'hin': 'Hindi',
    'kan': 'Kannada',
    'tam': 'Tamil',
    'tel': 'Telugu',
    'mar': 'Marathi',
    'ben': 'Bengali',
    'guj': 'Gujarati',
    'ori': 'Odia',
    'pan': 'Punjabi',
    'mal': 'Malayalam',
    'urd': 'Urdu',
    'asm': 'Assamese',
    'san': 'Sanskrit'
}

# Unicode ranges for various Indian languages
UNICODE_RANGES = {
    'Devanagari': (0x0900, 0x097F),  # Hindi, Marathi, Sanskrit
    'Bengali': (0x0980, 0x09FF),
    'Gurmukhi': (0x0A00, 0x0A7F),    # Punjabi
    'Gujarati': (0x0A80, 0x0AFF),
    'Oriya': (0x0B00, 0x0B7F),       # Odia
    'Tamil': (0x0B80, 0x0BFF),
    'Telugu': (0x0C00, 0x0C7F),
    'Kannada': (0x0C80, 0x0CFF),
    'Malayalam': (0x0D00, 0x0D7F),
    'Sinhala': (0x0D80, 0x0DFF),
    'Urdu': (0x0600, 0x06FF)         # Urdu uses Arabic script
}

def detect_script_from_text(text):
    """
    Detect which script is predominantly used in the text
    based on Unicode character ranges.
    """
    if not text:
        return "Unknown"
    
    # Count characters in each script
    script_counts = {}
    for char in text:
        code_point = ord(char)
        for script, (start, end) in UNICODE_RANGES.items():
            if start <= code_point <= end:
                script_counts[script] = script_counts.get(script, 0) + 1
                break
    
    # Check for English (Latin script)
    latin_count = len(re.findall(r'[a-zA-Z]', text))
    if latin_count > 0:
        script_counts['Latin'] = latin_count
    
    # Find predominant script
    if not script_counts:
        return "Unknown"
    
    predominant_script = max(script_counts, key=script_counts.get)
    return predominant_script

def get_tesseract_lang_code(script):
    """Map script name to Tesseract language code"""
    script_to_lang = {
        'Devanagari': 'hin',
        'Bengali': 'ben',
        'Gurmukhi': 'pan',
        'Gujarati': 'guj',
        'Oriya': 'ori',
        'Tamil': 'tam',
        'Telugu': 'tel',
        'Kannada': 'kan',
        'Malayalam': 'mal',
        'Latin': 'eng',
        'Urdu': 'urd'
    }
    return script_to_lang.get(script, 'eng')

def extract_text_auto_language(image_path):
    """
    Try to detect language from image and extract text with appropriate OCR.
    
    This function follows these steps:
    1. Try a preliminary OCR with multiple languages enabled
    2. Detect the script from the preliminary OCR results
    3. Run OCR again with the specific detected language for better results
    """
    try:
        # Open the image file
        img = Image.open(image_path)
        
        # Initial OCR with multiple languages to detect script
        # This is a best-effort first pass
        initial_text = pytesseract.image_to_string(
            img, 
            lang='eng+hin+tam+tel+kan+ori+pan+guj+ben+mal+urd',
            config='--psm 6'  # Assume a single uniform block of text
        )
        
        # Detect the script from the initial OCR
        detected_script = detect_script_from_text(initial_text)
        
        if detected_script == "Unknown":
            # If script detection failed, default to multi-language
            final_text = initial_text
            detected_lang_code = 'mul'  # Multiple languages
            detected_lang_name = 'Multiple/Unknown'
        else:
            # Get the corresponding Tesseract language code
            lang_code = get_tesseract_lang_code(detected_script)
            
            # Second OCR pass with the specific detected language
            final_text = pytesseract.image_to_string(
                img, 
                lang=lang_code,
                config='--psm 6'  # Assume a single uniform block of text
            )
            
            detected_lang_code = lang_code
            detected_lang_name = LANGUAGE_NAMES.get(lang_code, detected_script)
        
        return final_text.strip(), f"{detected_lang_name} ({detected_script} script)"
    
    except Exception as e:
        return f"Error extracting text: {str(e)}", "Error"

def main():
    print(f"Processing image: {IMAGE_PATH}")
    
    # Check if image file exists
    if not os.path.exists(IMAGE_PATH):
        print(f"Error: Image file '{IMAGE_PATH}' not found!")
        return
    
    # Extract text with automatic language detection
    print("Extracting text with automatic language detection...")
    text, language = extract_text_auto_language(IMAGE_PATH)
    
    # Print results
    print("\n===== RESULTS =====")
    print(f"Detected Language: {language}")
    print("\n===== EXTRACTED TEXT =====")
    print(text)
    
    # Save to file with proper encoding
    with open('extracted_text.txt', 'w', encoding='utf-8') as f:
        f.write(text)
    print("\nText saved to extracted_text.txt")
    return text

def extract_text(image_path):
    return extract_text_auto_language(image_path)

if __name__ == "__main__":
    image_path = input("Enter image file name: ")
    text = extract_text(image_path)
    print("\nExtracted Text:\n", text)
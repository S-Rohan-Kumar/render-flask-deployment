from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from PIL import Image
import pytesseract
from groq import Groq
import moviepy as moviepy
import speech_recognition as sr
from pydub import AudioSegment
import os
import tempfile
from langi import extract_text
import yt_dlp
from pydub.utils import make_chunks
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
import pdfplumber
import bcrypt
import re
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

CORS(app, supports_credentials=True)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key_for_dev')

# Database configuration from environment variables
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', 'Rohan@2005')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'login')
mysql = MySQL(app)

# API keys from environment variables
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Configure Tesseract path
TESSERACT_PATH = os.getenv('TESSERACT_PATH', r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe')
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# Create temp directory if it doesn't exist
TEMP_DIR = os.path.join(os.getcwd(), 'temp')
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

@app.route('/')
def home():
    """Render home page"""
    return render_template("entry.html")
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    cursor = None
    if request.method == 'GET':
        # Render the login page
        return render_template("login.html")
    
    try:
        logger.info("Login request received")
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "No data received"}), 400
            
        email = data.get("email")
        password = data.get("password")
        
        # Validate data
        if not email or not password:
            logger.warning("Missing email or password")
            return jsonify({"success": False, "message": "Email and password are required"}), 400
        
        # Email format validation
        if not is_valid_email(email):
            return jsonify({"success": False, "message": "Invalid email format"}), 400
        
        # Create cursor
        cursor = mysql.connection.cursor()
        
        # Check if the user exists
        query = "SELECT id, fstname, lstname, email, password FROM register WHERE email=%s"
        cursor.execute(query, (email,))
        user = cursor.fetchone()
        
        if not user:
            logger.warning(f"No user found with email: {email}")
            return jsonify({"success": False, "message": "User not found"}), 404
        
        # Extract user details
        user_id, firstname, lastname, user_email, hashed_password = user
        
        # Verify the password
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
            # Set session and return success
            session['user_id'] = user_id
            logger.info(f"User {email} logged in successfully")
            return jsonify({"success": True, "message": "Login successful", "user_id": user_id}), 200
        else:
            logger.warning(f"Invalid password attempt for {email}")
            return jsonify({"success": False, "message": "Invalid password"}), 401
        
    except Exception as e:
        logger.error("Login error: %s", str(e))
        return jsonify({"success": False, "message": str(e)}), 500
    
    finally:
        if cursor:
            cursor.close()

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    cursor = None
    if request.method == 'GET':
        # Render the registration page
        return render_template("register.html")
    try:
        logger.info("Registration request received")
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "No data received"}), 400
            
        fstname = data.get("fstname")
        lstname = data.get("lstname")
        email = data.get("email")
        password = data.get("password")
        
        # Validate data
        if not all([fstname, lstname, email, password]):
            logger.warning("Missing registration fields")
            return jsonify({"success": False, "message": "All fields are required"}), 400
        
        # Email format validation
        if not is_valid_email(email):
            return jsonify({"success": False, "message": "Invalid email format"}), 400
            
        # Password strength validation
        if len(password) < 8:
            return jsonify({"success": False, "message": "Password must be at least 8 characters long"}), 400
            
        # Create cursor
        cursor = mysql.connection.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT id FROM register WHERE email=%s", (email,))
        if cursor.fetchone():
            logger.warning(f"Email already registered: {email}")
            return jsonify({"success": False, "message": "Email already registered"}), 409
        
        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Execute query with hashed password
        query = "INSERT INTO register (fstname, lstname, email, password) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (fstname, lstname, email, hashed_password))
        
        # Commit changes
        mysql.connection.commit()
        logger.info(f"New user registered: {email}")
        
        return jsonify({"success": True, "message": "Registration successful"}), 201
        
    except Exception as e:
        logger.error("Registration error: %s", str(e))
        return jsonify({"success": False, "message": str(e)}), 500
    
    finally:
        if cursor:
            cursor.close()
@app.route('/main', methods=['GET','POST'])
def main():
    return render_template("main.html")    
@app.route('/imgtxt', methods=['POST'])
def imgtxt():
    """Extract text from an uploaded image"""
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400
        
        image_file = request.files['image']
        logger.info("Image uploaded: %s", image_file.filename)
        text =extract_text(image_file)
        client = Groq(api_key="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")
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": f"summarize this in a very beautiful in the language the input is provided:{text}"
            }]
        )

        summary = response.choices[0].message.content
        
        
        return jsonify({"txt":summary})
    except Exception as e:
        logger.error("Error in image to text: %s", str(e))
        return jsonify({"error": f"Failed to process image: {str(e)}"}), 500


def extract_pdf_in_chunks(pdf_path, chunk_size=4000, by_pages=False):
    """
    Extract text from a PDF in chunks.
    - chunk_size: Number of characters per chunk (if by_pages=False) or pages per chunk (if by_pages=True).
    - by_pages: If True, split by number of pages instead of characters.
    Returns a list of text chunks.
    """
    chunks = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = min(100, len(pdf.pages))  # Limit to 100 pages
            full_text = ""
            
            # Extract text from all pages first
            for page_num in range(total_pages):
                page_text = pdf.pages[page_num].extract_text() or ""
                full_text += page_text + "\n"
            
            if by_pages:
                # Split by number of pages
                for i in range(0, total_pages, chunk_size):
                    start_page = i
                    end_page = min(i + chunk_size, total_pages)
                    chunk_text = ""
                    for j in range(start_page, end_page):
                        page_text = pdf.pages[j].extract_text() or ""
                        chunk_text += page_text + "\n"
                    if chunk_text.strip():
                        chunks.append(chunk_text)
            else:
                # Split by character count
                for i in range(0, len(full_text), chunk_size):
                    chunk = full_text[i:i + chunk_size]
                    if chunk.strip():
                        chunks.append(chunk)
                        
        return chunks
    
    except Exception as e:
        logger.error("Error extracting PDF text: %s", str(e))
        return [f"Error extracting text: {str(e)}"]

@app.route('/ytaudio', methods=['POST'])
def youtube_audio_to_text():
    """Extract and transcribe audio from YouTube videos"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({"error": "URL is required"}), 400
            
        url = data.get("url", "")
        logger.info("Processing YouTube URL: %s", url)
        
        transcript = process_youtube_audio(url, language="en-US")
        
        if not transcript or not isinstance(transcript, str) or transcript.strip() == "":
            return jsonify({"error": "Failed to generate transcript"}), 400

        # Initialize the Groq client
        client = Groq(api_key="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")

        # Create a chat completion request
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": f"As a news journalist, summarize this text for a general audience in bullet points highlighting the main ethical points and even give your own opinion on this with proper headings: [{transcript}]"
            }]
        )

        # Get the summarized text
        summary = response.choices[0].message.content
        
        # Return the response as JSON
        return jsonify({
            "transcript": transcript,
            "summary": summary
        })
    except Exception as e:
        logger.error("YouTube processing error: %s", str(e))
        return jsonify({"error": f"Failed to process YouTube video: {str(e)}"}), 500

def process_youtube_audio(url, language="en-US"):
    """Download and transcribe audio from YouTube"""
    temp_audio_file = os.path.join(TEMP_DIR, f"yt_{int(os.urandom(4).hex(), 16)}.wav")
    
    try:
        audio_file = download_audio(url, temp_audio_file)
        if not audio_file:
            logger.error("Failed to download audio from YouTube")
            return None

        transcript = transcribe_in_chunks(audio_file, language=language)
        logger.info("Transcription completed")
        return transcript
        
    except Exception as e:
        logger.error("Error in YouTube audio processing: %s", str(e))
        return None
    finally:
        # Cleanup the audio file
        if os.path.exists(temp_audio_file):
            try:
                os.remove(temp_audio_file)
                logger.info("Audio file deleted: %s", temp_audio_file)
            except Exception as e:
                logger.error("Failed to delete audio file: %s", str(e))

def transcribe_in_chunks(audio_path, chunk_length_ms=90000, language="en-US"):
    """Break audio into chunks and transcribe each chunk"""
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_wav(audio_path)
    chunks = make_chunks(audio, chunk_length_ms)
    full_transcript = ""

    logger.info("Splitting audio into %d chunks...", len(chunks))

    for i, chunk in enumerate(chunks):
        logger.info("Transcribing chunk %d/%d...", i+1, len(chunks))
        chunk_path = os.path.join(TEMP_DIR, f"chunk_{i}.wav")
        
        try:
            chunk.export(chunk_path, format="wav")

            with sr.AudioFile(chunk_path) as source:
                audio_data = recognizer.record(source)

            try:
                text = recognizer.recognize_google(audio_data, language=language)
                full_transcript += text + " "
            except sr.UnknownValueError:
                full_transcript += "[Unrecognized] "
                logger.warning("Chunk %d was not recognized", i+1)
            except sr.RequestError as e:
                full_transcript += f"[Request Error] "
                logger.error("Request error in chunk %d: %s", i+1, str(e))
        finally:
            if os.path.exists(chunk_path):
                os.remove(chunk_path)

    return full_transcript.strip()

def download_audio(url, output_path):
    """Download audio from YouTube URL"""
    ydl_opts = {
        'format': 'bestaudio',
        'outtmpl': os.path.join(TEMP_DIR, 'temp.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        temp_file = os.path.join(TEMP_DIR, "temp.wav")
        if os.path.exists(temp_file):
            os.rename(temp_file, output_path)
            return output_path
        else:
            logger.error("Downloaded audio file not found")
            return None
    except Exception as e:
        logger.error("Error downloading audio: %s", str(e))
        return None

@app.route('/upload-pdf', methods=['POST'])
def pdfimg():
    """Process uploaded PDF files"""
    try:
        # Check if file is in the request
        if 'pdf' not in request.files:
            return jsonify({"error": "No PDF file in request"}), 400
        
        pdf_file = request.files['pdf']
        
        # Check if file was selected
        if pdf_file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Secure the filename
        filename = secure_filename(pdf_file.filename)
        temp_path = os.path.join(TEMP_DIR, filename)
        
        # Save the uploaded file temporarily
        pdf_file.save(temp_path)
        logger.info("PDF saved temporarily: %s", temp_path)
        
        try:
            # Process the PDF
            chunk_size = 4000  # Characters per chunk
            text_chunks = extract_pdf_in_chunks(temp_path, chunk_size)
            
            # Check if there was an error during extraction
            if not text_chunks:
                return jsonify({"error": "Failed to extract text, no chunks returned"}), 400
                
            if any(chunk.startswith("Error") for chunk in text_chunks):
                error_chunk = next(chunk for chunk in text_chunks if chunk.startswith("Error"))
                return jsonify({"error": error_chunk}), 400
            
            # Initialize the Groq client
            client = Groq(api_key="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")
            
            # Process all chunks and collect summaries
            all_summaries = []
            
            for i, text in enumerate(text_chunks, 1):
                logger.info("Processing PDF chunk %d/%d", i, len(text_chunks))
                # Create a chat completion request
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{
                        "role": "user",
                        "content": f"Summarize this with main topics and heading with bullet points: [{text}]"
                    }]
                )
                summary = response.choices[0].message.content
                all_summaries.append(summary)
                
            return jsonify({"pdf_summaries": all_summaries})
            
        except Exception as e:
            logger.error("Error processing PDF: %s", str(e))
            return jsonify({"error": str(e)}), 500
    finally:
        # Clean up the temporary file
        if 'temp_path' in locals() and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.info("PDF temporary file removed")
            except Exception as e:
                logger.error("Failed to remove temp PDF file: %s", str(e))
@app.route('/chatbot', methods=['POST',"GET])
def bot():
   return render_template("chatbot.html")

@app.route('/vidtotxt', methods=['POST'])
def vidtotxt():
    """Convert video to text"""
    temp_video_path = None
    audio_path = None
    
    try:
        if 'video' not in request.files:
            return jsonify({"error": "No video file provided"}), 400
        
        # Get the uploaded video file
        video_file = request.files.get("video")
        
        # Create unique filenames
        file_id = int(os.urandom(4).hex(), 16)
        temp_video_path = os.path.join(TEMP_DIR, f"temp_video_{file_id}.mp4")
        audio_path = os.path.join(TEMP_DIR, f"output_audio_{file_id}.wav")
        
        # Save the uploaded file temporarily
        video_file.save(temp_video_path)
        logger.info("Video saved temporarily: %s", temp_video_path)
        
        # Extract audio from video
        try:
            video = moviepy.VideoFileClip(temp_video_path)
            video.audio.write_audiofile(audio_path, logger=None)  # Suppress moviepy logs
            video.close()  # Close the video file
        except Exception as e:
            logger.error("Failed to extract audio from video: %s", str(e))
            return jsonify({"error": f"Failed to extract audio: {str(e)}"}), 500
        
        # Transcribe the audio in chunks for better handling of large files
        try:
            transcript = transcribe_in_chunks(audio_path)
            logger.info("Video transcription completed")
            return jsonify({"msg": transcript})
        except Exception as e:
            logger.error("Failed to transcribe audio: %s", str(e))
            return jsonify({"error": f"Transcription failed: {str(e)}"}), 500
        
    except Exception as e:
        logger.error("Video to text error: %s", str(e))
        return jsonify({"error": str(e)}), 500
    
    finally:
        # Clean up temporary files
        cleanup_files([temp_video_path, audio_path])

def cleanup_files(file_paths):
    """Remove temporary files"""
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info("Removed temp file: %s", file_path)
            except Exception as e:
                logger.error("Error removing file %s: %s", file_path, str(e))

@app.route('/audtotxt', methods=['POST'])
def audtotxt():
    """Convert audio to text"""
    audio_path = None
    wav_path = None
    
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400

        audio_file = request.files['audio']
        
        # Create unique filenames
        file_id = int(os.urandom(4).hex(), 16)
        audio_path = os.path.join(TEMP_DIR, f"uploaded_audio_{file_id}.mp3")
        wav_path = os.path.join(TEMP_DIR, f"converted_{file_id}.wav")
        
        # Save the uploaded file
        audio_file.save(audio_path)
        logger.info("Audio saved temporarily: %s", audio_path)

        # Convert to WAV format
        try:
            sound = AudioSegment.from_file(audio_path)  # More general than from_mp3
            sound.export(wav_path, format="wav")
        except Exception as e:
            logger.error("Failed to convert audio format: %s", str(e))
            return jsonify({"error": f"Failed to convert audio: {str(e)}"}), 500

        # Transcribe the audio in chunks for better handling
        try:
            transcript = transcribe_in_chunks(wav_path)
            logger.info("Audio transcription completed")
            return jsonify({"message": transcript})
        except Exception as e:
            logger.error("Failed to transcribe audio: %s", str(e))
            return jsonify({"error": f"Transcription failed: {str(e)}"}), 500

    except Exception as e:
        logger.error("Audio to text error: %s", str(e))
        return jsonify({"error": str(e)}), 500
        
    finally:
        # Clean up temporary files
        cleanup_files([audio_path, wav_path])

# Helper function to validate email format
def is_valid_email(email):
    """Check if email has a valid format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

         

@app.route('/logout', methods=['GET','POST'])
def logout():
    """Handle user logout"""
    try:
        # Clear the session
        session.pop('user_id', None)
        logger.info("User logged out")
        return jsonify({"success": True, "message": "Logout successful"}), 200
    except Exception as e:
        logger.error("Logout error: %s", str(e))
        return jsonify({"success": False, "message": str(e)}), 500



@app.route('/txtsumz', methods=['POST'])
def txtsumz():
    """Summarize text input"""
    try:
        logger.info("Text summarization request received")
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({"error": "No text message provided"}), 400
            
        message = data.get("message", "")
        
        if not message.strip():
            return jsonify({"error": "Empty text cannot be summarized"}), 400
        
        client = Groq(api_key="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")
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": f"summarize this in a very beautiful in the language the input is provided:{message}"
            }]
        )

        summary = response.choices[0].message.content
        logger.info("Text summarization completed")
        return jsonify({"message": summary})
        
    except Exception as e:
        logger.error("Text summarization error: %s", str(e))
        return jsonify({"error": f"Failed to summarize text: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5010)

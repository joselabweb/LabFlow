# LabFlow
App that transcribes audio to text (voice dictation) using the Google Gemini API and formats the result. Free alternative to Wispr Flow.

# LabFlow: Audio Transcription and Enhancement Tool (Wispr Flow Free Alternative)

LabFlow is a Python-based desktop application designed to efficiently convert audio files to text and subsequently enhance the transcribed text for improved readability and coherence.

## 🚀 Key Features

*   **Audio-to-Text Transcription:** Converts audio files (such as MP3, WAV, etc.) into plain text using speech recognition technology.
*   **Automatic Text Enhancement:** Once transcribed, the software processes the text to:
    *   Add punctuation (commas, periods, etc.).
    *   Correct capitalization (capital letters at the beginning of sentences).
    *   Improve the overall structure for easier reading.
*   **Transcription History:** Saves a record of all transcriptions, allowing you to easily access them later.
*   **Usage Statistics:** Tracks application usage.

## 🛠️ How to Use

There are two ways to use this tool: by running the Python script directly or by using the executable file.

### Option 1: Run the Python Script Code (For Developers)

This option provides more flexibility if you want to modify the code.

**Prerequisites:**
*   Python 3 installed on your system.
*   `pip` (Python's package manager) installed.

**Steps:**
1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    ```
2.  **Navigate to the project directory:**
    
3.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv .venv
    ```
4.  **Activate the virtual environment:**
    *   On Windows:
        ```bash
        .venv\Scripts\activate
        ```
    *   On macOS/Linux:
        ```bash
        source .venv/bin/activate
        ```
5.  **Install the dependencies:**
    *(Note: It is highly recommended to create a `requirements.txt` file listing all the necessary libraries for your project. If you have one, use the following command).*
    ```bash
    pip install -r requirements.txt
    ```
6.  **Run the application:**
    ```bash
    python nuevo_mainsoft.py
    ```

### Option 2: Use the Executable File (The Easiest Way)

If you just want to use the application without dealing with Python installations or dependencies, this is your best option.

1.  Navigate to https://github.com/joselabweb/LabFlow/releases/tag/executable
2.  Download `LabFlow.exe` file.
3.  Double-click on `LabFlow.exe` to launch the application. That's it!

## 📂 Project File Structure

Here is a description of the most important files and their functions:

### Core Files (The heart of the software)

*   `nuevo_mainsoft.py`: The application's entry point. Run this file to start the program.
*   `nuevo_text_enhancer.py`: Contains all the logic for processing and enhancing the transcribed text (adding punctuation, capitalization, etc.).
*   `nuevo_transcription_history.py`: Manages the transcription history by saving and retrieving data.

### Secondary and Generated Files

*   `nuevo_config.json`: Configuration file. Important settings for the program's operation are stored here.
*   `nuevo_transcription_history.json`: A JSON-format database where the history of all transcriptions is stored.
*   `nuevo_usage_statistics.json`: A JSON file that saves data on how the application is used.
*   `logs/wisprflow_soft_nuevo.log`: A log file that records information about events or errors that may occur during execution.
*   `dist/`: The folder containing the ready-to-use **executable file (`.exe`)**.
*   `.venv/`: The folder for the Python virtual environment (if created).

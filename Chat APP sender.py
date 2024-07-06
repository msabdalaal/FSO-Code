import tkinter as tk
from tkinter import filedialog
import serial
import time
import threading
from datetime import datetime
import base64
import os
import zlib  # text compression
import os

class SenderApp:
    #App GUI
    def __init__(self, root):
        self.root = root
        self.root.title("Chat APP")

        self.send_button = tk.Button(root, text="Send Text", command=self.send_text)
        self.send_button.pack(pady=10)
        
        self.send_button = tk.Button(root, text="Send Image", command=self.send_image)
        self.send_button.pack(pady=10)
        
        self.send_button = tk.Button(root, text="Send Sound", command=self.send_sound)
        self.send_button.pack(pady=10)

        self.progress_label = tk.Label(root, text="Progress: 0%")
        self.progress_label.pack(pady=10)

        self.chat_label = tk.Label(root, text="Chat")
        self.chat_label.pack(pady=10)
        
        self.chat_display = tk.Text(root, height=15, width=50)
        self.chat_display.pack(pady=10)
        
        self.chat_entry = tk.Entry(root, width=40)
        self.chat_entry.pack(side=tk.LEFT, padx=10)
        
        self.chat_send_button = tk.Button(root, text="Send", command=self.send_chat)
        self.chat_send_button.pack(side=tk.RIGHT, padx=10)
#----------------------------------------------------------------
#Splitting text to chunk size
    def split_text(self, text, chunk_size=32): 
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
#----------------------------------------------------------------
    #Sending Functions
    def send_text(self):
        file_path = filedialog.askopenfilename()
        if not file_path:
            return

        with open(file_path, 'r' ,errors="ignore") as file:
            text = file.read()

        compressed_text = zlib.compress(text.encode('utf-8'))  # Compress the text
        encoded_text = base64.b64encode(compressed_text).decode('utf-8')  # Encode to base64

        self.total_size = len(encoded_text)
        self.sent_size = 0
        chunks = self.split_text(encoded_text)
        
        threading.Thread(target=self.send_chunks, args=(chunks,b'\x03')).start()

    def send_image(self):
        image_path = filedialog.askopenfilename()
        # Check if the image file exists
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"The image file {image_path} does not exist.")
        
        # Read the image file in binary mode
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
        
        
        # Encode the image data to base64
        encoded_image_data = base64.b64encode(image_data).decode('utf-8')
        
        # Get the directory and file name without extension
        file_dir, file_name = os.path.split(image_path)
        file_name_without_ext = os.path.splitext(file_name)[0]
        
        # Create the text file path
        text_file_path = os.path.join(file_dir, f"{file_name_without_ext}.txt")
        
        # Write the encoded image data to the text file
        with open(text_file_path, "w") as text_file:
            text_file.write(encoded_image_data)
    
        file_path = text_file_path
        if not file_path:
            return

        # Clear the chat display
        self.chat_display.delete(1.0, tk.END)

        with open(file_path, 'r') as file:
            text = file.read()

        self.total_size = len(text)
        self.sent_size = 0
        chunks = self.split_text(text)
        
        threading.Thread(target=self.send_chunks, args=(chunks,b'\x05')).start()

    def send_sound(self):

        file_path = filedialog.askopenfilename(
            title="Select an MP3 file",
            filetypes=[("MP3 files", "*.mp3")]
        )
        if not file_path:
            print("No file selected.")
            return

        # Read the MP3 file
        with open(file_path, 'rb') as mp3_file:
            mp3_data = mp3_file.read()
            
            # Encode the MP3 data to UTF-8
        base64_data = base64.b64encode(mp3_data).decode('utf-8')

        # Create a new filename for the encoded text file
        base_name = os.path.basename(file_path)
        name, _ = os.path.splitext(base_name)
        utf8_file_path = os.path.join(os.path.dirname(file_path), f"{name}_encoded.txt")

        # Save the encoded data to a text file
        with open(utf8_file_path, 'w', encoding='utf-8') as utf8_file:
            utf8_file.write(base64_data)

        # Clear the chat display
        self.chat_display.delete(1.0, tk.END)

        with open(utf8_file_path, 'r') as file:
            text = file.read()

        self.total_size = len(text)
        self.sent_size = 0
        chunks = self.split_text(text)
            
        threading.Thread(target=self.send_chunks, args=(chunks,b'\x06')).start()

    def send_chat(self):  
        message = self.chat_entry.get()
        if message:
            self.chat_entry.delete(0, tk.END)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            display_message = f"[{timestamp}] User1: {message}\n"
            self.chat_display.insert(tk.END, display_message)
            self.chat_display.see(tk.END)
            
            self.total_size = len(message)
            self.sent_size = 0
            chunks = self.split_text(message)
                
            threading.Thread(target=self.send_chunks, args=(chunks,b'\x04')).start()
    def update_progress(self):
        progress = (self.sent_size / self.total_size) * 100
        self.progress_label.config(text=f"Progress: {progress:.2f}%")
#----------------------------------------------------------------
    #Sending Mechanism
    def send_chunks(self, chunks, end_frame):
        with serial.Serial('COM3', 2000000, timeout=1) as ser:
            time.sleep(2)  # Wait for the serial connection to initialize
            ser.flush()  # Clear Arduino buffer

            # Send unique start frame for the first chunk
            ser.write(b'\x01')  # Unique start of transmission for the first chunk
            ser.write(b'\x01')  # Unique start of transmission for the first chunk
            time.sleep(0.1)  # Give Arduino time to process each character

            for chunk in chunks:
                ser.write(b'\x02')  # Standard start of transmission for each chunk
                self.send_chunk(ser, chunk)
                # ser.flushInput()  # Clear Arduino buffer
                ser.flushInput()  # Clear Arduino buffer
                ser.flush()  # Clear Arduino buffer
                ser.reset_input_buffer()  # Clear Arduino buffer
                ser.reset_output_buffer()  # Clear Arduino buffer
                time.sleep(0.15)  # Give Arduino time to process each character


            ser.write(end_frame)  # Unique end of transmission for the last chunk
            # ser.flushInput()  # Clear Arduino buffer
            ser.flush()  # Clear Arduino buffer

    def send_chunk(self, ser, chunk):
        for char in chunk:
            ser.write(char.encode('utf-8')) # Send the character to Arduino
            # self.chat_display.insert(tk.END, char)
            # self.chat_display.see(tk.END)
            self.sent_size += 1

        self.update_progress()
        self.root.update()


root = tk.Tk()
app = SenderApp(root)
root.mainloop()
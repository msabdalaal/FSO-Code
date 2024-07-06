import tkinter as tk
import serial
import threading
import os
import time
from datetime import datetime
import base64
import os
import zlib  # Text Decompression

class ReceiverApp:
    
    #App GUI
    def __init__(self, root):
        self.root = root
        self.root.title("Chat App")

        self.speed_label = tk.Label(root, text="Receiving Speed: 0 bits/second")
        self.speed_label.pack(pady=10)
        
        self.time_label = tk.Label(root, text="Elapsed Time: 0 seconds")
        self.time_label.pack(pady=10)
        
        self.status_label = tk.Label(root, text="Status: Waiting...")
        self.status_label.pack(pady=10)
        
        self.chat_label = tk.Label(root, text="Chat")
        self.chat_label.pack(pady=10)
        
        self.chat_display = tk.Text(root, height=15, width=50)
        self.chat_display.pack(pady=10)
        
        #variable Intialization
        self.received_data = []
        self.chunk_files = []
        self.start_text = '\x01'  # Unique start of transmission for the first chunk
        self.start_chunk = '\x02'  # Start of transmission for each chunk
        self.end_text = '\x03'   # Unique end of transmission for the last chunk
        self.end_chat = '\x04'  # Unique end frame for chat
        self.end_image = '\x05'  # Unique end frame for image
        self.end_sound = '\x06'  # Unique end frame for sound
        self.receiving = False
        self.receiving_chat = False
        self.start_time = time.time()
        self.total_bits_received = 0
        
        # Start the receiving thread
        threading.Thread(target=self.receive_file).start()

    #main receiving function
    def receive_file(self):
        base_file_name = "received_chunk"
        
        with serial.Serial('COM5', 2000000, timeout=1) as ser:
            while True:
                if ser.in_waiting > 0:
                    incoming_byte = ser.read().decode('utf-8' , errors='ignore')
                    #Intiazling Receiving
                    if incoming_byte == self.start_text:
                        # Clear everything before in memory
                        self.chunk_files = []
                        self.received_data = []
                        self.status_label.config(text=f"Receiving...")
                        self.start_time = time.time()  # Start timing
                        self.total_bits_received = 0  # Reset bit counter

                    #Handling Chunk Receiving
                    if incoming_byte == self.start_text or incoming_byte == self.start_chunk:
                        if self.received_data:  # Save previous chunk if exists
                            chunk_file_name = self.get_unique_filename(base_file_name, extension=".chunk")
                            with open(chunk_file_name, 'w') as file:
                                file.write(''.join(self.received_data))
                            self.chunk_files.append(chunk_file_name)
                        # ser.flushInput()  # Clear Arduino buffer for the next chunk
                        # ser.flush()  # Clear Arduino buffer for the next chunk
                        # ser.reset_output_buffer()
                        # ser.reset_input_buffer()
                        self.receiving = True
                        self.received_data = []  # Reset received data
                    
                    #text file receiving
                    elif incoming_byte == self.end_text:
                        combined_file_name = self.receive_data()
                        self.decompress_and_save_file(combined_file_name, 'txt')

                    #image receiving
                    elif incoming_byte == self.end_image:
                        
                        text_file_path = self.receive_data()

                        # Read the base64 encoded image data from the text file
                        with open(text_file_path, "r") as text_file:
                            encoded_image_data = text_file.read()

                        # Decode the base64 image data
                        image_data = base64.b64decode(encoded_image_data)

                        # Get the directory and file name without extension
                        file_dir, file_name = os.path.split(text_file_path)
                        file_name_without_ext = os.path.splitext(file_name)[0]

                        # Create the image file path
                        image_file_path = os.path.join(file_dir, f"{self.get_unique_filename(file_name_without_ext)}_decoded.png")

                        # Write the image data to the image file
                        with open(image_file_path, "wb") as image_file:
                            image_file.write(image_data)
                    
                    #sound receiving
                    elif incoming_byte == self.end_sound:

                        file_path = self.receive_data()
                        # Check if a file was selected
                        if not file_path:
                            print("No file selected.")
                            return
                        
                        # Read the text file
                        with open(file_path, 'r', encoding='utf-8') as text_file:
                            base64_data = text_file.read()
                            
                        # Decode the UTF-8 data back to the original binary MP3 data
                        mp3_data = base64.b64decode(base64_data.encode('utf-8'))

                        # Create a new filename for the MP3 file
                        base_name = os.path.basename(file_path)
                        name, _ = os.path.splitext(base_name)
                        if name.endswith('_encoded'):
                                name = name[:-8]  # Remove '_encoded' from the name if present
                        mp3_file_path = os.path.join(os.path.dirname(file_path), f"{self.get_unique_filename(name)}.mp3")

                        # Save the decoded data to an MP3 file
                        with open(mp3_file_path, 'wb') as mp3_file:
                            mp3_file.write(mp3_data)

                    #chat receiving
                    elif incoming_byte == self.end_chat:
                        
                        combined_file_name = self.receive_data()
                        with open(combined_file_name, "r") as text_file:
                            message = text_file.read()
                        
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        display_message = f"[{timestamp}] User1: {message}\n"
                        
                        self.chat_display.insert(tk.END, display_message)
                        self.chat_display.see(tk.END)
                        self.root.update()
                        
                        os.remove(combined_file_name)
                    
                    #handling buffering data 
                    elif self.receiving:
                        self.received_data.append(incoming_byte)
                        self.total_bits_received += 8  # Increment bit counter by 8 bits (1 byte)
    
    #Text Decompression
    def decompress_and_save_file(self, file_path, file_type):
        
        with open(file_path, 'r') as text_file:
            encoded_data = text_file.read()

        decoded_data = base64.b64decode(encoded_data)
        decompressed_data = zlib.decompress(decoded_data)

        file_dir, file_name = os.path.split(file_path)
        file_name_without_ext = os.path.splitext(file_name)[0]

        output_file_path = os.path.join(file_dir, f"{self.get_unique_filename(file_name_without_ext)}.{file_type}")

        with open(output_file_path, 'wb') as output_file:
            output_file.write(decompressed_data)
            
        os.remove(file_path)
        
        return output_file_path
    
    #chunk compining
    def receive_data(self):
        self.receiving = False
        # Calculate and display receiving speed and elapsed time
        elapsed_time = time.time() - self.start_time
        bit_rate = self.total_bits_received / elapsed_time
        self.speed_label.config(text=f"Receiving Speed: {bit_rate:.2f} bits/second")
        self.time_label.config(text=f"Elapsed Time: {elapsed_time:.2f} seconds")
        self.status_label.config(text=f"Waiting...")
        # Save the last chunk data to a unique file
        chunk_file_name = self.get_unique_filename("received_chunk", extension=".chunk")
        with open(chunk_file_name, 'w') as file:
            file.write(''.join(self.received_data))
        self.chunk_files.append(chunk_file_name)
        # Combine all chunk files into one file
        combined_file_name = self.get_unique_filename("received_text")
        with open(combined_file_name, 'w') as combined_file:
            for chunk_file in self.chunk_files:
                with open(chunk_file, 'r') as file:
                    combined_file.write(file.read())
        # Delete all chunk files after combining
        for chunk_file in self.chunk_files:
            os.remove(chunk_file)
            
        return combined_file_name
    
    #getting unique filenames for received file
    def get_unique_filename(self, base_name, extension=".txt"):
        """
        Generate a unique file name by appending a number if the file exists.
        """
        counter = 1
        file_name = f"{base_name}{extension}"
        while os.path.isfile(file_name):
            file_name = f"{base_name}_{counter}{extension}"
            counter += 1
        return file_name

root = tk.Tk()
app = ReceiverApp(root)
root.mainloop()

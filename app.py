import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from flask import Flask, request, Response
import requests
from PIL import Image
import io
import pytesseract
import os
import logging
import threading

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# WhatsApp Business API credentials
WHATSAPP_API_URL = 'https://your-whatsapp-api-url/v1/messages'
WHATSAPP_API_TOKEN = 'EAAPJB9nzpJEBOztZAxxyUbym0E3jSK56EQnZBdCiB9raGYEgkvC3JaNUsmfAQKmfD6BsQXafWXeZBBkTjWkMIVgWsKaKPO6s39BZAVtXlX8CQ8eIWsmFbKlVRlXgddDyKe57SnLkW8LwKiIZBNG2r4X19LfVzXGr7v6JNDoTCbeLCDlHTyERpe4cbKwJuuF2XEdqIdNR3DNqXm1tmWMKRJaER0uYZA3kXVZAWcZD'

# Configure Tesseract path if necessary
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'  # Update with the correct path

@app.route('/whatsapp', methods=['POST'])
def whatsapp():
    msg = request.form.get('Body')
    media_url = request.form.get('MediaUrl0')
    from_number = request.form.get('From')
    
    logging.debug(f"Received message: {msg}")
    logging.debug(f"Received media URL: {media_url}")
    logging.debug(f"From number: {from_number}")
    
    # Send initial "Processing..." response
    initial_resp = "Processing your image, please wait..."
    send_whatsapp_message(initial_resp, from_number)
    
    # Start a new thread to process the image and send the follow-up response
    threading.Thread(target=process_image_and_respond, args=(media_url, from_number)).start()
    
    return Response(status=200)

def process_image_and_respond(media_url, from_number):
    if media_url:
        response = requests.get(media_url)
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            img.save("input_image.jpg")
            
            # Process the image and perform OCR
            extracted_text = perform_ocr("input_image.jpg")
            logging.debug(f"Extracted text: {extracted_text}")
            
            # Send the extracted text
            send_whatsapp_message(f"Extracted text: {extracted_text}", from_number)
            
            # Send the result message
            response_msg = "Here is the result of the OCR processing."
            send_whatsapp_message(response_msg, from_number)
        else:
            response_msg = "Failed to download image."
            logging.debug(f"Failed to download image. Status code: {response.status_code}")
            send_whatsapp_message(response_msg, from_number)
    else:
        response_msg = "Please send an image."
        logging.debug("No media URL found.")
        send_whatsapp_message(response_msg, from_number)

def send_whatsapp_message(message, to_number):
    headers = {
        'Authorization': f'Bearer {WHATSAPP_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        'to': to_number,
        'type': 'text',
        'text': {
            'body': message
        }
    }
    response = requests.post(WHATSAPP_API_URL, headers=headers, json=data)
    logging.debug(f"WhatsApp API response: {response.status_code}, {response.text}")

def perform_ocr(image_path):
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    return text

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

# SPDX-FileCopyrightText: 2023 Brent Rubell for Adafruit Industries
# SPDX-License-Identifier: MIT
#
# An open-source IoT birdfeeder camera with Adafruit MEMENTO

import os
import ssl
import binascii
import board
import digitalio
import socketpool
import wifi
import adafruit_pycamera
import adafruit_requests
from adafruit_io.adafruit_io import IO_HTTP, AdafruitIO_RequestError
import time
import gifio
#import ulab.numpy as np
import displayio
#import gc
import analogio
import alarm

print("MEMENTO Birdfeeder Camera")


# Prepare the URL and headers for the POST request
url = "http://192.168.68.85:5000/upload"
url_volatge = "http://192.168.68.85:5000/upload_voltage"
urlgif = "http://192.168.68.85:5000/upload_gif"
headers = {
    "Content-Type": "application/json"
}

wifi.radio.connect(os.getenv("CIRCUITPY_WIFI_SSID"), os.getenv("CIRCUITPY_WIFI_PASSWORD"))
print(f"Connected to {os.getenv('CIRCUITPY_WIFI_SSID')}!")

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

# initialize camera
pycam = adafruit_pycamera.PyCamera()
# turn off the display backlight
pycam.display.brightness = 0.0
# set photo resolution
pycam.resolution = 3
# set focus to estimated bird location
pycam.autofocus_vcm_step = 145

# initialize PIR sensor
pir = digitalio.DigitalInOut(board.A0)
pir.direction = digitalio.Direction.INPUT

battery = analogio.AnalogIn(board.BATTERY_MONITOR)

def get_voltage(pin):
    return (pin.value * 3.3) / 65535 * 2

voltage = get_voltage(battery)
print("Battery voltage: {:.2f} V".format(voltage))

def create_alarm(deep):
    if deep:
        return alarm.time.TimeAlarm(monotonic_time=time.monotonic() + 46800)
    return alarm.time.TimeAlarm(monotonic_time=time.monotonic() + 20)

def get_most_recent_file(directory):
    recent_file = None
    recent_time = 0
    # List all files in the specified directory
    for file in os.listdir("/sd"):
        stats = os.stat("/sd/" + file)
        mod_time = stats[7]
        if mod_time > recent_time:
            recent_time = mod_time
            recent_file = "/sd/" + file
    print(recent_file)
    return recent_file

def send_jpeg_to_server(jpeg):
    # before we send the image to IO, it needs to be encoded into base64
    encoded_data = binascii.b2a_base64(jpeg).strip()

    print("Sending image to Server...")
    json_payload = {
    "image": encoded_data.decode('utf-8')  # Convert bytes to string for JSON
    }
    #io.send_data(feed_camera["key"], encoded_data)
    try:
        response = requests.post(url, json=json_payload, headers=headers)
        print(response)
        print("Sent image to Server!")
    except Exception as e:
        print(f"POST Socket error for Image Upload: {e}")

def send_volatge():
    json_payload = {
    "voltage": get_voltage(battery)  # Convert bytes to string for JSON
    }
    try:
        response = requests.post(url_volatge, json=json_payload, headers=headers)
        print("Sent Volatge to server: ",response)
    except Exception as e:
        print(f"POST Socket error for Volatge Upload: {e}") 
    
def send_gif_to_server(gif_path):
    try:
        with open(gif_path, 'rb') as gif_file:
            # Prepare the multipart/form-data request
            print("Sending GIF to server as binary data...", gif_path)
            files = {
                'file': ('gif_file.gif', gif_file, 'image/gif')
            }
            
            # Send the GIF to the Flask server
            response = requests.post(urlgif, files=files)
            
            if response.status_code == 200:
                print("GIF sent successfully!")
            else:
                print(f"Failed to send GIF: {response.text}")
    
    except Exception as e:
        print(f"Error reading or sending GIF: {e}")

def test_camera():
    print("Testing the camera send")
    jpeg = pycam.capture_into_jpeg()
    if jpeg is not None:
        send_jpeg_to_server(jpeg)
    else:
        print("ERROR: JPEG capture failed!")

# def create_gif():
#     try:
#         f = pycam.open_next_image("gif")
#     except RuntimeError as e:
#         pycam.display_message("Error\nNo SD Card", color=0xFF0000)
#         time.sleep(0.5)
#         return
#     
#     i = 0
#     ft = []
#     pycam.continuous_capture_start()
# 
#     pycam.display.refresh()
#     g=None
#     with gifio.GifWriter(
#         f,
#         pycam.camera.width,
#         pycam.camera.height,
#         displayio.Colorspace.RGB565_SWAPPED,
#         dither=True,
#     ) as g:
#         t00 = t0 = time.monotonic()
#         i=0
#         while (i < 15):
#             print(i," Recording")
#             i += 1
#             _gifframe = pycam.continuous_capture()
#             print(_gifframe)
#             g.add_frame(_gifframe, 0.12)
#             pycam.blit(_gifframe)
#             t1 = time.monotonic()
#             ft.append(1 / (t1 - t0))
#             print(end=".")
#             t0 = t1
#     print(f"\nfinal size {f.tell()} for {i} frames")
#     print(f"average framerate {i/(t1-t00)}fps")
#     print(type(f))
#     f.close()
#     g.deinit()
#     g = None
#     gc.collect()
#     pycam.display.refresh()


brightness_set = False
old_pir_value = pir.value
send_interval = time.monotonic() + 60
while True:
    now = time.localtime()

    if now.tm_hour == 19 and now.tm_min >= 0:
        print("It's exactly 19:00 (7:00 PM)! Going to Sleep")
        time_alarm = create_alarm(True)
        alarm.exit_and_deep_sleep_until_alarms(time_alarm)

    pycam.keys_debounce()
    if send_interval == time.monotonic():
        send_volatge()
        send_interval = time.monotonic() + 60
        
    #time_alarm = create_alarm(False)
    #alarm.light_sleep_until_alarms(time_alarm)
    pir_value = pir.value
    # if we detect movement, take a photo
    if pir_value:
        if not old_pir_value:
            print("Movement detected, taking picture!")
            # take a picture and save it into a jpeg bytes object
            jpeg = pycam.capture_into_jpeg()
            # if the camera successfully captured a jpeg, send it to IO
            if jpeg is not None:
                send_jpeg_to_server(jpeg)
            else:
                print("ERROR: JPEG capture failed!")
    else:
        if old_pir_value:
            print("Movement ended")
        # update old_pir_value
    old_pir_value = pir_value
    if pycam.right.fell:
        test_camera()
    elif pycam.ok.fell:
        if brightness_set:
            pycam.display.brightness = 0.0
        else:
            pycam.display.brightness = 1.0
        brightness_set = not brightness_set
    # elif pycam.left.fell:
    #     create_gif()
    #     send_gif_to_server(get_most_recent_file("/sd"))
    

import json
import time
import os
import psutil
import requests
import subprocess

last_connection_time = time.time() # Track the last connection time
last_update_time = time.time()     # Track the last update time
posting_interval = 900             # Post data once every 2 minutes
update_interval = 900               # Update once every 15 seconds

write_api_key = "MYAPIKEY" # Replace YOUR-CHANNEL-write_api_key with your channel write API key
channel_ID = "2068639"              # Replace YOUR-channel_ID with your channel ID
url = "https://api.thingspeak.com/channels/" + channel_ID + "/bulk_update.json" # ThingSpeak server settings
message_buffer = []

def httpRequest():
    # Function to send the POST request to ThingSpeak channel for bulk update.
        global message_buffer
        bulk_data = json.dumps({'write_api_key':write_api_key,'updates':message_buffer}) # Format the json data buffer
        request_headers = {"User-Agent":"mw.doc.bulk-update (Raspberry Pi)","Content-Type":"application/json","Content-Length":str(len(bulk_data))}
    # Make the request to ThingSpeak
        try:
            print(request_headers)
            response = requests.post(url,headers=request_headers,data=bulk_data)
            print (response) # A 202 indicates that the server has accepted the request
        except e:
            print((e.code)) # Print the error code
        message_buffer = [] # Reinitialize the message buffer
        global last_connection_time
        last_connection_time = time.time() # Update the connection time

def getData():
    # Function that returns the CPU temperature and percentage of CPU utilization
        cmd_temp101 = 'curl -s http://141.51.190.101/atmoweb?Temp1Read='
        cmd_hum101 = 'curl -s http://141.51.190.101/atmoweb?HumRead='
        cmd_temp102 = 'curl -s http://141.51.190.102/atmoweb?Temp1Read='
        cmd_hum102 = 'curl -s http://141.51.190.102/atmoweb?HumRead='
        cmd_led102 = 'curl -s http://141.51.190.102/atmoweb?LightLED='
        cmd_freezer = "sed 'x;$!d' < /home/ZOOLOGY-observ/Programs/freezer.log"
        cmd_cpu_temp = 'vcgencmd measure_temp'
        process_temp101 = subprocess.run(cmd_temp101, shell=True, capture_output=True, text=True).stdout.strip()
        process_hum101 = subprocess.run(cmd_hum101, shell=True, capture_output=True, text=True).stdout.strip()
        process_temp102 = subprocess.run(cmd_temp102, shell=True, capture_output=True, text=True).stdout.strip()
        process_hum102 = subprocess.run(cmd_hum102, shell=True, capture_output=True, text=True).stdout.strip()
        process_led102 = subprocess.run(cmd_led102, shell=True, capture_output=True, text=True).stdout.strip()
        process_freezer = subprocess.run(cmd_freezer, shell=True, capture_output=True, text=True).stdout.strip()
        process_cpu_temp = subprocess.run(cmd_cpu_temp, shell=True, capture_output=True, text=True).stdout.strip()
        temp101 = process_temp101.split(': ')[1].split(",")[0]
        hum101 = process_hum101.split(': ')[1].split(",")[0]
        temp102 = process_temp102.split(': ')[1].split(",")[0]
        hum102 = process_hum102.split(': ')[1].split(",")[0]
        led102 = process_led102.split('D": ')[1].split(', "LightLED_Range"')[0]
        freezer = process_freezer.split('- ')[1].split(' C')[0]
        cpu_temp = process_cpu_temp.split('=')[1].split("'")[0]
        cpu_usage = psutil.cpu_percent(interval=2)
        return temp101,hum101,temp102,hum102,cpu_temp,cpu_usage,led102,freezer
        
def updatesJson():
    # Function to update the message buffer every 15 seconds with data. 
    # And then call the httpRequest function every 2 minutes. 
    # This examples uses the relative timestamp as it uses the "delta_t" parameter.
    # If your device has a real-time clock, you can also provide the absolute timestamp 
    # using the "created_at" parameter.

        global last_update_time
        message = {}
        message['delta_t'] = int(round(time.time() - last_update_time))
        Temp101,Hum101,Temp102,Hum102,CPU_temp,CPU_usage,LED102,Freezer = getData()
        message['field1'] = Temp101
        message['field2'] = Hum101
        message['field3'] = Temp102
        message['field4'] = Hum102
        message['field5'] = CPU_temp
        message['field6'] = CPU_usage
        message['field7'] = -int(Freezer)
        message['field8'] = LED102
        print (" left:",Temp101,"°C,",Hum101,"%; right:",Temp102,"°C,",Hum102,"%, LED",LED102,"%; Freezer:",-int(Freezer),"°C; CPU:",CPU_temp,"°C,",CPU_usage,"%")
        global message_buffer
        message_buffer.append(message)
    # If posting interval time has crossed 2 minutes update the ThingSpeak channel with your data
        if time.time() - last_connection_time >= posting_interval:
                httpRequest()
                last_update_time = time.time()

if __name__ == "__main__":  # To ensure that this is run directly and does not run when imported
        while True:
                # If update interval time has crossed 15 seconds update the message buffer with data
            if time.time() - last_update_time >= update_interval:
                updatesJson()
            time.sleep(1)

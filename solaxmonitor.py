import os
import requests
import json
import time
import datetime

# Set from Docker runtime
token_id = os.environ.get('TOKEN_ID')
sn = os.environ.get('SERIAL_NUMBER')

if not token_id or not sn:
    raise ValueError(
        "TOKEN_ID and SERIAL_NUMBER environment variables must be set"
    )

# Solax Configuration
# Max API calls according to Solax API docs
# https://www.eu.solaxcloud.com/phoebus/resource/files/userGuide/Solax_API.pdf
url = (
    f"https://www.eu.solaxcloud.com:9443/proxy/api/getRealtimeInfo.do"
    f"?tokenId={token_id}&sn={sn}"
)
max_calls_per_day = 10000
max_calls_per_minute = 6

# Define API calls local limits
delay_between_calls = 60 / max_calls_per_minute
api_calls_today = 0

# Paths
output_file_path = "/var/www/solax/solax_values.json"
log_file_path = "/var/log/solaxmonitor.log"

while True:
    if api_calls_today >= max_calls_per_day:
        with open(log_file_path, "a") as log_file:
            log_file.write(
                f"{datetime.datetime.now()} - Maximum API calls per day "
                f"reached. Exiting.\n"
            )
        break

    response = requests.get(url)

    if response.status_code == 200:
        api_calls_today += 1

        data = response.json()

        # Result is now a dictionary
        result_data = data["result"]

        with open(output_file_path, "w") as output_file:
            json.dump(result_data, output_file, indent=2)

        with open(log_file_path, "a") as log_file:
            log_file.write(
                f"{datetime.datetime.now()} - Extraction and saving complete. "
                f"Output saved to {output_file_path}\n"
            )

    else:
        with open(log_file_path, "a") as log_file:
            log_file.write(
                f"{datetime.datetime.now()} - Error: {response.status_code}, "
                f"{response.text}\n"
            )

    time.sleep(delay_between_calls)

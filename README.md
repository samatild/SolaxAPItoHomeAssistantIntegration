# Solax Monitor Docker Container

I have created this repository to share with the community the way that I managed to get the data from my Solax inverter to Home Assistant. Tough is a bit tricky to get the data from the Solax API, I have created a Docker container that will poll the API and store the data locally. This way you can pull the data from local API in Home Assistant without the rate limits of the Solax API as we create a backoff mechanism to avoid hitting the API too often.

# Table of Contents
- [Solax Monitor Docker Container](#solax-monitor-docker-container)
- [Table of Contents](#table-of-contents)
  - [1. The challenge with Solax API rate limiter](#1-the-challenge-with-solax-api-rate-limiter)
    - [1.1 Solution through proxied API](#11-solution-through-proxied-api)
    - [Explanation](#explanation)
  - [2. Deploying the Container](#2-deploying-the-container)
    - [2.1 Using Docker Compose (Recommended)](#21-using-docker-compose-recommended)
    - [2.2 Alternative: Using Docker CLI](#22-alternative-using-docker-cli)
  - [3. Home Assistant Integration](#3-home-assistant-integration)
    - [3.1 REST Sensor Configuration](#31-rest-sensor-configuration)
- [License](#license)
## 1. The challenge with Solax API rate limiter

- API rate limits (6 calls/minute, 10,000/day)
- Refer to: [Solax API Documentation](https://www.eu.solaxcloud.com/phoebus/resource/files/userGuide/Solax_API.pdf)

### 1.1 Solution through proxied API
To overcome the API rate limits, this Docker container implements a polling mechanism that fetches data at a controlled rate. The data is stored locally and can be accessed via a lightweight HTTP server.

[![Solax Monitor](/img/diagram.png)]

### Explanation
1. Fetches real-time inverter data at regulated intervals usinng the Solax API.
2. Stores the data in a local JSON file.
3. Serves the data through a lightweight HTTP server.
4. Home Assistant can access the data via REST sensor integration without additional configuration.


## 2. Deploying the Container

### 2.1 Using Docker Compose (Recommended)

1. Create `.env` file:
```bash
echo "TOKEN_ID=your_solax_token
SERIAL_NUMBER=your_inverter_serial" > .env 
```

2. Create `docker-compose.yml` file:

```yml
version: '3.8'

services:
  solax-monitor:
    image: samuelmatildes/solax-local-api:latest
    container_name: solax-monitor
    restart: unless-stopped
    environment:
      - TOKEN_ID=${TOKEN_ID}
      - SERIAL_NUMBER=${SERIAL_NUMBER}
    ports:
      - "8080:8080"
    volumes:
      - ./data:/var/www/solax
      - ./logs:/var/log
```

3. Start the container:
```bash
docker-compose up -d
```

### 2.2 Alternative: Using Docker CLI
```bash
docker run -d \
  --name solax-monitor \
  -p 8080:8080 \
  -v ./data:/var/www/solax \
  -v ./logs:/var/log \
  -e TOKEN_ID="your_solax_token" \
  -e SERIAL_NUMBER="your_inverter_serial" \
  --restart unless-stopped \
  samuelmatildes/solax-local-api:latest
  ``` 

Note down the IP address of the Docker container. You will need this to configure Home Assistant.

## 3. Home Assistant Integration

### 3.1 REST Sensor Configuration
Add the following configuration to your `configuration.yaml` file in Home Assistant:

```yaml
sensor:
  - platform: rest
    resource: http://<solax-docker-IP>:8080/solax_values.json
    name: Solax Inverter SN
    value_template: "{{ value_json.inverterSN }}"
  - platform: rest
    resource: http://<solax-docker-IP>:8080/solax_values.json
    name: Solax Serial Number
    value_template: "{{ value_json.sn }}"
  - platform: rest
    resource: http://<solax-docker-IP>:8080/solax_values.json
    name: Solax AC Power
    value_template: "{{ value_json.acpower }}"
    unit_of_measurement: "W"
  - platform: rest
    resource: http://<solax-docker-IP>:8080/solax_values.json
    name: Solax Yield Today
    state_class: total_increasing
    value_template: "{{ value_json.yieldtoday }}"
    unit_of_measurement: "kWh"
    device_class: energy
  - platform: rest
    resource: http://<solax-docker-IP>:8080/solax_values.json
    name: Solax Yield Total
    value_template: "{{ value_json.yieldtotal }}"
    state_class: total_increasing
    unit_of_measurement: kWh
    device_class: energy
  - platform: rest
    resource: http://<solax-docker-IP>:8080/solax_values.json
    name: Solax Feedin Power
    value_template: "{{ value_json.feedinpower }}"
    unit_of_measurement: "W"
  - platform: rest
    resource: http://<solax-docker-IP>:8080/solax_values.json
    name: Solax Feedin Energy
    value_template: "{{ value_json.feedinenergy }}"
    state_class: total_increasing
    unit_of_measurement: kWh
    device_class: energy
  - platform: rest
    resource: http://<solax-docker-IP>:8080/solax_values.json
    name: Solax Consumed Energy
    value_template: "{{ value_json.consumeenergy }}"
    state_class: total_increasing
    unit_of_measurement: kWh
    device_class: energy
  - platform: rest
    resource: http://<solax-docker-IP>:8080/solax_values.json
    name: Solax Power DC1
    value_template: "{{ value_json.powerdc1 }}"
    unit_of_measurement: "W"
  - platform: rest
    resource: http://<solax-docker-IP>:8080/solax_values.json
    name: Solax Power DC2
    value_template: "{{ value_json.powerdc2 }}"
    unit_of_measurement: "W"
  - platform: rest
    resource: http://<solax-docker-IP>:8080/solax_values.json
    value_template: >
      {% if value_json.inverterStatus == '100' %}Wait
      {% elif value_json.inverterStatus == '101' %}Check
      {% elif value_json.inverterStatus == '102' %}Normal
      {% elif value_json.inverterStatus == '103' %}Fault
      {% elif value_json.inverterStatus == '104' %}Permanent Fault
      {% elif value_json.inverterStatus == '105' %}Update
      {% elif value_json.inverterStatus == '106' %}EPS Check
      {% elif value_json.inverterStatus == '107' %}EPS
      {% elif value_json.inverterStatus == '108' %}Self-test
      {% elif value_json.inverterStatus == '109' %}Idle
      {% elif value_json.inverterStatus == '110' %}Standby
      {% elif value_json.inverterStatus == '111' %}Pv Wake Up Bat
      {% elif value_json.inverterStatus == '112' %}Gen Check
      {% elif value_json.inverterStatus == '113' %}Gen Run
      {% else %}I dont know{% endif %}
    name: "Solax status"
```	

## 3.2 Integration with Tesla Style Power Card

One question I got , is how to integrate the data with the Tesla style power card from [reptilex/tesla-style-power-card](https://github.com/reptilex/tesla-style-solar-power-card).

You will need to create some template sensors to get the data in the right format. This idea was originated from AviadorLP reply on reptilex tesla style power card [issue #96](https://github.com/reptilex/tesla-style-solar-power-card/issues/96#issuecomment-1062249859). 

1. Create a new file `apf_sensors.yaml` in the `config` folder and add the following code:

```yaml
# Templates for Actual Powerflow transfer charts (APF - Actual PowerFlow)
#
# For the math to add up a new Real House Load must be calculated and used, witch includes
# the inverter consumption and excludes rounding errors and corrects inaccurate power readings.
#
# It never made sense that inbound power sometimes does not equal outbound power. This fixes it!
#
# Developed by AviadorLP
#
# Just replace the 4 words below "ReplaceWithYourSensor" with your specific sensors,
# for grid, house, solar and battery entities, example "sensor.solax_house_load"
#
# If your sensor is negative when it should be positive replace that complete line with
#         state: "{{ 0 - states('ReplaceWithYourSensor')|int(default=0) }}"
#
# If you don't have a battery replace that complete line with
#         state: "{{ 0 }}"

template:
  - sensor:
      # grid sensor must be negative when importing and positive when exporting
      - name: APF Grid Entity
        device_class: power
        state_class: measurement
        unit_of_measurement: W
        state: "{{ states('sensor.solax_feedin_power')|int(default=0) }}"

      # sensor must always be 0 or positive (i think they always are)
      - name: APF House Entity
        device_class: power
        state_class: measurement
        unit_of_measurement: W
        state: "{{ states('sensor.solax_ac_power')|int(default=0) }}"

      # sensor must always be 0 or positive (i think they always are)
      - name: APF Generation Entity
        device_class: power
        state_class: measurement
        unit_of_measurement: W
        state: "{{ states('sensor.solar_total')|int(default=0) }}"

      # Required to reduce code later on
      - name: APF Grid Import
        device_class: power
        state_class: measurement
        unit_of_measurement: W
        state: >
          {% if states('sensor.apf_grid_entity')|int(default=0) < 0 %}
            {{ states('sensor.apf_grid_entity')|int(default=0)|abs }}
          {% else %}
            0
          {% endif %}

      #   Inverter consumption and power losses due to Inverter transfers and power conversions (AC/DC)
      #   excludes rounding errors made worst by the fact that some inverters round all sensors readings to INT
      #   Occasionally this might be negative probably due to cumulative errors in not so accurate power readings.
      - name: APF Inverter Power Consumption
        device_class: power
        state_class: measurement
        unit_of_measurement: W
        state: "{{ states('sensor.apf_generation_entity')|int(default=0) - states('sensor.apf_house_entity')|int(default=0) - states('sensor.apf_grid_entity')|int(default=0) }}"

      # Real House Load Includes Inverter consumption and transfer conversions and losses and rounding errors.
      # It never made sense that inbound power sometimes does not equal outbound power. This fixes it!
      - name: APF Real House Load
        device_class: power
        state_class: measurement
        unit_of_measurement: W
        state: "{{ states('sensor.apf_house_entity')|int(default=0) + states('sensor.apf_inverter_power_consumption')|int(default=0) }}"
        icon: mdi:home-lightning-bolt

      - name: APF Grid2House
        device_class: power
        state_class: measurement
        unit_of_measurement: W
        state: >
          {% if states('sensor.apf_grid_import')|int(default=0) > states('sensor.apf_real_house_load')|int(default=0) %}
            {{ states('sensor.apf_real_house_load')|int(default=0) }}
          {% else %}
            {{ states('sensor.apf_grid_import')|int(default=0) }}
          {% endif %}

      - name: APF Grid2Batt
        device_class: power
        state_class: measurement
        unit_of_measurement: W
        state: >
          {% if states('sensor.apf_grid_import')|int(default=0) > states('sensor.apf_real_house_load')|int(default=0) %}
            {{ states('sensor.apf_grid_import')|int(default=0) - states('sensor.apf_real_house_load')|int(default=0) }}
          {% else %}
            0
          {% endif %}

      - name: APF Solar2Grid
        device_class: power
        state_class: measurement
        unit_of_measurement: W
        state: >
          {% if states('sensor.apf_grid_entity')|int(default=0) > states('sensor.apf_batt2grid')|int(default=0) %}
            {{ states('sensor.apf_grid_entity')|int(default=0) - states('sensor.apf_batt2grid')|int(default=0) }}
          {% else %}
            0
          {% endif %}

      - name: APF Solar2House
        device_class: power
        state_class: measurement
        unit_of_measurement: W
        state: >
          {% if states('sensor.apf_generation_entity')|int(default=0) > 0 and states('sensor.apf_real_house_load')|int(default=0) > states('sensor.apf_batt2house')|int(default=0) + states('sensor.apf_grid_import')|int(default=0) %}
            {% if states('sensor.apf_generation_entity')|int(default=0) > states('sensor.apf_real_house_load')|int(default=0) - states('sensor.apf_batt2house')|int(default=0) - states('sensor.apf_grid2house')|int(default=0) %}
              {{ states('sensor.apf_real_house_load')|int(default=0) - states('sensor.apf_batt2house')|int(default=0) - states('sensor.apf_grid2house')|int(default=0) }}
            {% else %}
              {{ states('sensor.apf_generation_entity')|int(default=0) }}
            {% endif %}
          {% else %}
            0
          {% endif %}
```

2. Don't forget to import the `apf_sensors.yaml` file in your `configuration.yaml`:

```yaml
homeassistant:
  packages:
    apf_sensors: !include apf_sensors.yaml
```

3. Install the Tesla Style Power Card in your Home Assistant. You can do this via HACS or manually (will not cover this here).
4. Import the card in your lovelace configuration, mine looks like this (I don't have a battery, so I removed the battery part):

```yaml
type: custom:tesla-style-solar-power-card
name: Actual Power Flow
grid_to_house_entity: sensor.apf_grid2house
generation_to_grid_entity: sensor.apf_solar2grid
generation_to_house_entity: sensor.apf_solar2house
grid_entity: sensor.apf_grid_entity
house_entity: sensor.apf_real_house_load
generation_entity: sensor.apf_generation_entity
show_w_not_kw: 1
```	

It will look like this (took the screenshot later on the afternoon, so production was not that good at the time):

![Tesla Style Power Card](/img/teslapowercard.png)

And that's it! You should now have a working Solax Monitor Docker container that fetches data from your inverter and serves it to Home Assistant. If you have any questions or suggestions, feel free to open an issue or a pull request.

# License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

#!/usr/bin/env python3

# Yaesu FT-5D memory generator according to https://przemienniki.net
# by @pstankie

import requests
import xml.etree.ElementTree as ET
import csv

# Constants
XML_URL = "https://przemienniki.net/export/rxf.xml"
OUTPUT_CSV = "adms14_ft5d.csv"

# ADMS-14 CSV headers based on detailed table
CSV_HEADERS = [
    "Channel No",
    "Priority CH",
    "Receive Frequency",
    "Transmit Frequency",
    "Offset Frequency",
    "Offset Direction",
    "AUTO MODE",
    "Operating Mode",
    "DIG/ANALOG",
    "TAG",
    "Name",
    "Tone Mode",
    "CTCSS Frequency",
    "DCS Code",
    "DCS Polarity",
    "USer CTCSS",
    "RX DG-ID",
    "TX DG-ID",
    "Tx Power",
    "Skip",
    "AUTO STEP",
    "Step",
    "Memory Mask",
    "ATT",
    "S-Meter SQL",
    "Bell",
    "Narrow",
    "Clock Shift",
    "BANK 1",
    "BANK 2",
    "BANK 3",
    "BANK 4",
    "BANK 5",
    "BANK 6",
    "BANK 7",
    "BANK 8",
    "BANK 9",
    "BANK 10",
    "BANK 11",
    "BANK 12",
    "BANK 13",
    "BANK 14",
    "BANK 15",
    "BANK 16",
    "BANK 17",
    "BANK 18",
    "BANK 19",
    "BANK 20",
    "BANK 21",
    "BANK 22",
    "BANK 23",
    "BANK 24",
    "Comment",
    "Extra Column"
]

def fetch_xml_data(url):
    """Fetch XML data from the given URL."""
    response = requests.get(url)
    response.raise_for_status()
    return response.content

def parse_adms4b(xml_data):
    """Parse ADMS-4b XML data and extract necessary fields."""
    root = ET.fromstring(xml_data)
    repeater_data = []
    seen_repeaters = set()

    repeaters = root.find("repeaters")
    if not repeaters:
        print("No <repeaters> element found in the XML.")
        return repeater_data

    for repeater in repeaters.findall("repeater"):
        try:
            name = repeater.find("qra").text if repeater.find("qra") is not None else "Unknown"
            if not name.startswith("SR9"):
                continue  # Skip repeaters not starting with "SR9"

            tx_frequency = float(repeater.find("qrg[@type='rx']").text)  # Exchange RX and TX
            rx_frequency = float(repeater.find("qrg[@type='tx']").text)

            # Filter for 2m and 70cm bands
            if not ((144.000 <= rx_frequency <= 148.000) or (420.000 <= rx_frequency <= 450.000)):
                continue  # Skip repeaters outside 2m and 70cm bands

            # Check for duplicate frequencies with the same prefix
            prefix = name.split("-")[0] if "-" in name else name
            if (prefix, rx_frequency) in seen_repeaters:
                continue

            seen_repeaters.add((prefix, rx_frequency))

            offset_frequency = abs(rx_frequency - tx_frequency)
            offset_direction = "+RPT" if tx_frequency > rx_frequency else ("-RPT" if tx_frequency < rx_frequency else "OFF")

            ctcss_rx = repeater.find("ctcss[@type='rx']").text if repeater.find("ctcss[@type='rx']") is not None else "88.5"
            if not ctcss_rx.endswith(" Hz"):
                ctcss_rx += " Hz"

            # Determine DIG/ANALOG field value based on mode
            mode = repeater.find("mode").text.upper() if repeater.find("mode") is not None else "FM"
            dig_analog = "DN" if "C4FM" in mode else "FM"

            # Set Tone Mode based on activation
            activation = repeater.find("activation").text.upper() if repeater.find("activation") is not None else ""
            tone_mode = "OFF" if "CARRIER" in activation else "TONE"

            repeater_data.append({
                "Channel No": len(repeater_data) + 1,
                "Priority CH": "OFF",
                "Receive Frequency": f"{rx_frequency:.5f}",
                "Transmit Frequency": f"{tx_frequency:.5f}",
                "Offset Frequency": f"{offset_frequency:.3f}",
                "Offset Direction": offset_direction,
                "AUTO MODE": "ON",
                "Operating Mode": "FM",
                "DIG/ANALOG": dig_analog,
                "TAG": "OFF",
                "Name": name[:16],  # Limit to 16 characters
                "Tone Mode": tone_mode,
                "CTCSS Frequency": ctcss_rx,
                "DCS Code": "023",
                "DCS Polarity": "RX Normal TX Normal",
                "USer CTCSS": "1600 Hz",
                "RX DG-ID": "RX 00",
                "TX DG-ID": "TX 00",
                "Tx Power": "High (5W)",
                "Skip": "OFF",
                "AUTO STEP": "ON",
                "Step": "12.5KHz",
                "Memory Mask": "OFF",
                "ATT": "OFF",
                "S-Meter SQL": "OFF",
                "Bell": "OFF",
                "Narrow": "OFF",
                "Clock Shift": "OFF",
                "BANK 1": "OFF",
                "BANK 2": "OFF",
                "BANK 3": "OFF",
                "BANK 4": "OFF",
                "BANK 5": "OFF",
                "BANK 6": "OFF",
                "BANK 7": "OFF",
                "BANK 8": "OFF",
                "BANK 9": "OFF",
                "BANK 10": "OFF",
                "BANK 11": "OFF",
                "BANK 12": "OFF",
                "BANK 13": "OFF",
                "BANK 14": "OFF",
                "BANK 15": "OFF",
                "BANK 16": "OFF",
                "BANK 17": "OFF",
                "BANK 18": "OFF",
                "BANK 19": "OFF",
                "BANK 20": "OFF",
                "BANK 21": "OFF",
                "BANK 22": "OFF",
                "BANK 23": "OFF",
                "BANK 24": "OFF",
                "Comment": "",
                "Extra Column": 0
            })
        except Exception as e:
            print(f"Error processing repeater: {e}")

    # Fill remaining entries up to 900 with empty rows
    current_count = len(repeater_data)
    for i in range(current_count + 1, 901):
        repeater_data.append({
            "Channel No": i,
            "Priority CH": "",
            "Receive Frequency": "",
            "Transmit Frequency": "",
            "Offset Frequency": "",
            "Offset Direction": "",
            "AUTO MODE": "",
            "Operating Mode": "",
            "DIG/ANALOG": "",
            "TAG": "",
            "Name": "",
            "Tone Mode": "",
            "CTCSS Frequency": "",
            "DCS Code": "",
            "DCS Polarity": "",
            "USer CTCSS": "",
            "RX DG-ID": "",
            "TX DG-ID": "",
            "Tx Power": "",
            "Skip": "",
            "AUTO STEP": "",
            "Step": "",
            "Memory Mask": "",
            "ATT": "",
            "S-Meter SQL": "",
            "Bell": "",
            "Narrow": "",
            "Clock Shift": "",
            "BANK 1": "",
            "BANK 2": "",
            "BANK 3": "",
            "BANK 4": "",
            "BANK 5": "",
            "BANK 6": "",
            "BANK 7": "",
            "BANK 8": "",
            "BANK 9": "",
            "BANK 10": "",
            "BANK 11": "",
            "BANK 12": "",
            "BANK 13": "",
            "BANK 14": "",
            "BANK 15": "",
            "BANK 16": "",
            "BANK 17": "",
            "BANK 18": "",
            "BANK 19": "",
            "BANK 20": "",
            "BANK 21": "",
            "BANK 22": "",
            "BANK 23": "",
            "BANK 24": "",
            "Comment": "",
            "Extra Column": 0
        })

    return repeater_data

def write_adms14_csv(data, output_file):
    """Write the repeater data to a CSV file in ADMS-14 format."""
    with open(output_file, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_HEADERS, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)

def main():
    try:
        print("Fetching XML data...")
        xml_data = fetch_xml_data(XML_URL)

        print("Parsing XML data...")
        repeater_data = parse_adms4b(xml_data)

        print("Writing CSV file...")
        write_adms14_csv(repeater_data, OUTPUT_CSV)

        print(f"ADMS-14 CSV file generated: {OUTPUT_CSV}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()


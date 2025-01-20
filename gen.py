#!/usr/bin/env python3

# Yaesu FT-5D memory generator according to https://przemienniki.net
# by @pstankie

import requests
import xml.etree.ElementTree as ET
import csv
from geopy.distance import geodesic
from colorama import Fore, Style

# Constants
XML_URL = "https://przemienniki.net/export/rxf.xml"
OUTPUT_CSV = "adms14_ft5d.csv"
STATIC_CSV = "static_frequencies.csv"

# Offset direction constants
OFFSET_PLUS = "+RPT"
OFFSET_MINUS = "-RPT"
OFFSET_OFF = "OFF"

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

def locator_to_coordinates(locator):
    """Convert Maidenhead locator to latitude and longitude."""
    if len(locator) < 4 or not locator[:2].isalpha() or not locator[2:4].isdigit():
        raise ValueError(f"Invalid locator: {locator}. Expected a Maidenhead locator like JO90AA.")

    lon = (ord(locator[0].upper()) - 65) * 20 - 180 + (int(locator[2]) * 2)
    lat = (ord(locator[1].upper()) - 65) * 10 - 90 + (int(locator[3]) * 1)

    if len(locator) >= 6 and locator[4].isalpha() and locator[5].isalpha():
        lon += (ord(locator[4].lower()) - 97) * 5 / 60  # 5 minutes in longitude
        lat += (ord(locator[5].lower()) - 97) * 2.5 / 60  # 2.5 minutes in latitude

    return lat, lon

def parse_adms4b(xml_data, reference_locator, max_distance):
    """Parse ADMS-4b XML data and extract necessary fields."""
    root = ET.fromstring(xml_data)
    repeater_data = []
    seen_repeaters = set()

    # Convert reference locator to coordinates
    ref_coords = locator_to_coordinates(reference_locator)

    repeaters = root.find("repeaters")
    if not repeaters:
        print("No <repeaters> element found in the XML.")
        return repeater_data

    for repeater in repeaters.findall("repeater"):
        try:
            name = repeater.find("qra").text if repeater.find("qra") is not None else "Unknown"

            locator_element = repeater.find("location/locator")
            locator = locator_element.text if locator_element is not None else None
            if locator is None:
                latitude = repeater.find("location/latitude").text
                longitude = repeater.find("location/longitude").text
                if latitude is not None and longitude is not None:
                    locator = f"{latitude},{longitude}"
                else:
                    continue

            repeater_coords = locator_to_coordinates(locator)
            distance = geodesic(ref_coords, repeater_coords).km

            # Print distance in green if within max_distance, red otherwise
            distance_color = Fore.GREEN if distance <= max_distance else Fore.RED
            print(
                f"Name: {name[:16]}, "
                f"{distance_color}Distance: {distance:.2f} km{Style.RESET_ALL}, "
                f"Locator: {locator}"
            )

            if distance > max_distance:
                continue  # Skip repeaters outside the specified distance

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
            if tx_frequency > rx_frequency:
                offset_direction = OFFSET_PLUS
            elif tx_frequency < rx_frequency:
                offset_direction = OFFSET_MINUS
            else:
                offset_direction = OFFSET_OFF

            ctcss_rx_element = repeater.find("ctcss[@type='rx']")
            ctcss_rx = ctcss_rx_element.text if ctcss_rx_element is not None else "88.5"
            if not ctcss_rx.endswith(" Hz"):
                ctcss_rx += " Hz"

            # Determine DIG/ANALOG field value based on mode
            mode = repeater.find("mode").text.upper() if repeater.find("mode") is not None else "FM"
            dig_analog = "DN" if "C4FM" in mode else "FM"

            # Set Tone Mode based on activation
            activation = repeater.find("activation").text.upper() if repeater.find("activation") is not None else ""
            tone_mode = "OFF" if "CARRIER" in activation else "TONE"

            # Check for "fm-poland" or "FM POLAND" in remarks or link
            remarks = repeater.find("remarks").text.lower() if repeater.find("remarks") is not None else ""
            link = repeater.find("link").text.lower() if repeater.find("link") is not None else ""
            if "fm-poland" in remarks or "fm poland" in remarks or "fm-poland" in link or "fm poland" in link:
                name += " fmpol"

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
                "BANK 12":                 "OFF",
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

    return repeater_data

def add_static_frequencies(data, start_channel):
    """Add entries from static_frequencies.csv, adjusting channel numbers."""
    try:
        with open(STATIC_CSV, mode="r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            if "Channel No" not in reader.fieldnames:
                raise ValueError("The CSV file does not contain the required 'Channel No' column.")
            
            for row in reader:
                if row["Channel No"] == "-1":  # Adjust channel numbers
                    row["Channel No"] = str(start_channel)
                    start_channel += 1
                data.append(row)
    except FileNotFoundError:
        print(f"Error: The file {STATIC_CSV} was not found.")
    except ValueError as e:
        print(f"Error: {e}")
    return data

def ensure_900_rows(data):
    """Ensure the total number of rows is 900 by adding empty rows if needed."""
    current_count = len(data)
    for i in range(current_count + 1, 901):
        data.append({
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
    return data

def write_adms14_csv(data, output_file):
    """Write the repeater data to a CSV file in ADMS-14 format."""
    with open(output_file, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_HEADERS, extrasaction="ignore")
        writer.writerows(data)  # Write data without headers

def main():
    import sys
    if len(sys.argv) != 3 or "--help" in sys.argv:
        print("Usage: python script.py <locator> <distance_km>")
        print("<locator>: Reference Maidenhead locator, e.g., JO90AA")
        print("<distance_km>: Maximum distance in kilometers from the locator")
        sys.exit(1)

    reference_locator = sys.argv[1]
    max_distance = float(sys.argv[2])

    try:
        print("Fetching XML data...")
        xml_data = fetch_xml_data(XML_URL)

        print("Parsing XML data...")
        repeater_data = parse_adms4b(xml_data, reference_locator, max_distance)

        print("Adding static frequencies...")
        repeater_data = add_static_frequencies(repeater_data, start_channel=len(repeater_data) + 1)

        print("Ensuring 900 rows...")
        repeater_data = ensure_900_rows(repeater_data)

        print("Writing CSV file...")
        write_adms14_csv(repeater_data, OUTPUT_CSV)

        print(CSV_HEADERS)

        print(f"ADMS-14 CSV file generated: {OUTPUT_CSV}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

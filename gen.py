#!/usr/bin/env python3

# Yaesu FT-5D memory generator according to https://przemienniki.net
# by @pstankie

import requests
import xml.etree.ElementTree as ET
import csv
from geopy.distance import geodesic

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

def locator_to_coordinates(locator):
    """Convert Maidenhead locator to latitude and longitude."""
    if len(locator) < 4:
        raise ValueError("Locator must be at least 4 characters long.")

    lon = (ord(locator[0].upper()) - 65) * 20 - 180 + (int(locator[2]) * 2)
    lat = (ord(locator[1].upper()) - 65) * 10 - 90 + (int(locator[3]) * 1)

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

            locator = repeater.find("location/locator").text if repeater.find("location/locator") is not None else None
            if locator is None:
                continue

            repeater_coords = locator_to_coordinates(locator)
            distance = geodesic(ref_coords, repeater_coords).km

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

    return repeater_data

def write_adms14_csv(data, output_file):
    """Write the repeater data to a CSV file in ADMS-14 format."""
    with open(output_file, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_HEADERS, extrasaction='ignore')
        writer.writerows(data)  # Removed header row

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

        print("Writing CSV file...")
        write_adms14_csv(repeater_data, OUTPUT_CSV)

        print(f"ADMS-14 CSV file generated: {OUTPUT_CSV}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()


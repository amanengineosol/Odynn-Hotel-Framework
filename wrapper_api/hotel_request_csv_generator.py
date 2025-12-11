import csv
import uuid
from datetime import datetime, timedelta

input_file = "hotels_marriott_mappings.csv"      # Source CSV with hotel_id, hotel_name, combined
output_file = "marriott_hotel_requests.csv"   # Output CSV file (500 records)
start_date = datetime(2025, 9, 22)   # Start from tomorrow

records_needed = 500
hotels = []

# Read original hotels
with open(input_file, "r", newline="", encoding="utf-8") as fin:
    reader = csv.DictReader(fin)
    hotels = [row for row in reader if row["hotel_id"]]

# Prepare output records
output = []
for i in range(records_needed):
    hotel = hotels[i % len(hotels)]     # Cycle through hotel list if <500 rows
    request_id = str(uuid.uuid4())
    report_id = request_id
    check_in_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
    check_out_date = (start_date + timedelta(days=i+4)).strftime("%Y-%m-%d")
    guest_count = 1
    hotel_id = hotel["hotel_id"]
    hotel_site_id = "Marriott-" + hotel_id
    record = {
        "hotel_id": hotel_id,
        "hotel_site_id":hotel_site_id,
        "client_id": '1c20d88b-215f-4ba1-9930-986c12f88afd',
        "site_name":'Hyatt',
        "request_id": request_id,
        "report_id": report_id,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "guest_count": guest_count
    }
    output.append(record)

# Write to new CSV
fieldnames = ["hotel_id","hotel_site_id", "client_id", "site_name", "request_id", "report_id", "check_in_date", "check_out_date", "guest_count"]
with open(output_file, "w", newline="", encoding="utf-8") as fout:
    writer = csv.DictWriter(fout, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(output)

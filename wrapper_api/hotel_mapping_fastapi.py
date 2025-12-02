import csv

input_file = "hotels_marriott_mappings.csv"
output_file = "hotels_marriott_mappings.csv"


def add_hotel_site_id():
    rows = []

    # Read original CSV
    with open(input_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Add new column values
        for row in reader:
            row["hotel_site_id"] = f"Marriott-{row['hotel_id']}"
            rows.append(row)

    # Write updated CSV
    with open(output_file, mode="w", newline="", encoding="utf-8") as f:
        fieldnames = list(rows[0].keys())  # include new column
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(rows)

    print(f"Successfully created: {output_file}")


if __name__ == "__main__":
    add_hotel_site_id()

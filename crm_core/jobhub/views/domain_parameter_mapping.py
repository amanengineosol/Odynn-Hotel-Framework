# Mapping domain names to their respective parameter JSON templates
DOMAIN_PARAMETER_MAP = {
    "hotel": {
        "currency": "USD",
        "hotel_id": "",
        "check_in_date": "",
        "check_out_date": "",
        "guest_count": "",
        "pos": "US"
    },
    "airline": {
        "currency": "USD",
        "source_iata": "",
        "destination_iata": "",
        "departure_date": "",
        "return_date": "",
        "pos": "US",
        "num_of_adults": 2,
        "num_of_stops": 0,
        "is_round_trip": False
    },
    # Add more domain mappings here in future in the same manner
}

import pandas as pd
from math import radians, cos, sin, sqrt, atan2

data = pd.read_csv('hospital_directory.csv', low_memory=False)


def parse_coordinates(coord_str):
    if isinstance(coord_str, str):
        coord_str = coord_str.strip()
        if coord_str != 'Error' and coord_str:
            try:
                lat, lon = map(float, coord_str.split(","))
                return lat, lon
            except ValueError:
                pass
    return None, None


hospitals = []
for _, row in data.iterrows():
    lat, lon = parse_coordinates(row["Location_Coordinates"])
    if lat is not None and lon is not None:
        hospitals.append({
            'Hospital_Name': row["Hospital_Name"],
            'Latitude': lat,
            'Longitude': lon,
            'Location': row["Location"],
            'State': row["State"],
            'District': row["District"],
            'Address': row["Address_Original_First_Line"],
            'contact': row["Mobile_Number"]
        })


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def get_bounded_hospitals(user_lat, user_lon, hospitals, radius_km=25):
    lat_diff = radius_km / 111.0
    lon_diff = radius_km / (111.0 * cos(radians(user_lat)))
    min_lat = user_lat - lat_diff
    max_lat = user_lat + lat_diff
    min_lon = user_lon - lon_diff
    max_lon = user_lon + lon_diff
    return [
        hospital for hospital in hospitals
        if min_lat <= hospital['Latitude'] <= max_lat and min_lon <= hospital['Longitude'] <= max_lon
    ]


def get_nearest_hospitals(user_lat, user_lon, hospitals, radius_km=25, top_n=5):
    bounded_hospitals = get_bounded_hospitals(user_lat, user_lon, hospitals, radius_km)
    hospital_distances = []
    for hospital in bounded_hospitals:
        dist = haversine(user_lat, user_lon, hospital['Latitude'], hospital['Longitude'])
        hospital_distances.append((hospital, dist))
    hospital_distances.sort(key=lambda x: x[1])
    return hospital_distances[:top_n]


def get_nearest_hospitals_info(lat, lon, radius_km=25, top_n=5):
    nearest = get_nearest_hospitals(lat, lon, hospitals, radius_km, top_n)
    results = []
    for hospital, dist in nearest:
        mobile = hospital['contact']
        mobile_display = "Not available" if not mobile or str(mobile).strip() in ['0', 'nan', 'NaN'] else str(mobile)
        results.append({
            "Hospital Name": hospital['Hospital_Name'],
            "Location": hospital['Location'],
            "Mobile Number": mobile_display,
            "Distance (km)": round(dist, 2)
        })
    return results

import pandas as pd
from math import radians, cos, sin, sqrt, atan2 # for haversine formula


my_data = pd.read_csv("train/train.csv") # dataframe
# print(my_data)

print(my_data.head())
print(my_data.describe())
print(my_data.info())
print(my_data.duplicated().sum())
print(my_data.isnull().sum())
print(my_data.isnull())

# Derived features
my_data['trip_duration_hours'] = my_data['trip_duration'] / 3600
print(my_data['trip_duration_hours'])
print(my_data["trip_duration"])

# Trip distance
def haversine_distance(row):
    R = 6371 
    # we convert from degrees to radians because we only have degrees in this case
    lon1, lat1, lon2, lat2 = map(radians, [row['pickup_longitude'], row['pickup_latitude'], row['dropoff_longitude'], row['dropoff_latitude']])
    
# we can now apply the haversine formula
    dlon = lon2 - lon1 # difference in longitudes 
    dlat = lat2 - lat1 # difference in latitudes
    a = sin(dlat / 2) **2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2 # haversine formula
    c = 2 * atan2(sqrt(a), sqrt(1 - a)) # helps us get the real distance in km
    distance = R * c # distance in km
    
    # convert to miles (1 mile = 1.609 km)
    distance_miles = distance / 1.609 
    return distance_miles 

my_data['trip_distance_miles'] = my_data.apply(haversine_distance, axis=1) #
print("Trip distance in miles:") 
print(my_data[['trip_duration' ,'trip_distance_miles']])

# Expalin how this works
# axis=1 means we are applying the function to each row
print(my_data[['pickup_longitude', 'pickup_latitude', 'dropoff_longitude', 'dropoff_latitude', 'trip_distance_miles']].head())    

# Save the cleaned data to a new CSV file
print("clean data saved")
my_data.to_csv("data/raw/processed/cleaned_data.csv", index=False)
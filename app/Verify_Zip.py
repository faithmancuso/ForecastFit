# import csv
# import pandas as pd
# time_availabilty=[6,7,8]
# phone=(input("enter a phone number"))
# z=len(phone)
# time=int((input("Enter hrs like 6,7,8 its am")))
# if time not in time_availabilty:
#     print("Wrong timing")
# else:
#     if (z!=10 or phone.isnumeric==False):
#         print("Wrong number")
#     else:
#         zip=int(input("enter a txt:"))
#         print(zip)
#         df=pd.read_csv('zip_code.csv')
#         if (df == zip).any().any():
#             file=open('data.csv','a',newline='')
#             file=csv.writer(file)
#             file.writerow([phone,zip,time])
#             print("Thank you")
#         else:
#             print("False Zipcode")
#TRY AND ERROR
import pandas as pd
import requests

# Function to get weather information from the API
def get_weather(zip_code):
    # Replace with your weather API endpoint and key
    api_key = '3fc72f97a7404f9a8d0213532241211'
    url = f'http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={zip_code}'
    
    response = requests.get(url)
    

# Read the CSV file
df = pd.read_csv('data.csv')  # Replace with your file path

# Assuming the column with zip codes is called 'Zip Code'
df['Weather'] = df['Zipcode'].apply(get_weather)

# Save the updated CSV file with the new 'Weather' column
df.to_csv('cities_with_weather.csv', index=False)

print("Weather information added successfully!")

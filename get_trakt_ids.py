import requests
import csv
import time
import toml # Import the toml library


import os # Import the os module to access environment variables
from dotenv import load_dotenv # Import load_dotenv from python-dotenv

from datetime import datetime, timezone # Import for dynamic timestamp

# --- Configuration ---
load_dotenv() # <--- THIS IS THE MISSING LINE! It loads your .env file

# --- Configuration ---
OMDB_API_KEY = os.getenv("OMDB_API_KEY") # Get the API key from environment variables

# Check if the API key was loaded successfully
if OMDB_API_KEY is None:
    print("Error: OMDb API Key not found. Please ensure it's set in your .env file as OMDB_API_KEY.")
    exit()
    
MEDIA_LIST_FILE = "sampleMedia.toml" # The name of your TOML file

output_csv_filename = "trakt_import_list.csv"

# --- Function to get IMDb ID from OMDb ---
def get_imdb_id_from_omdb(title, media_type="movie"):
    """
    Searches OMDb API for a movie or show by title and returns its IMDb ID.
    media_type can be 'movie' or 'series'.
    """
    omdb_type = "series" if media_type == "show" else "movie"
    params = {
        "apikey": OMDB_API_KEY,
        "s": title,  # 's' for search by title
        "type": omdb_type,
    }

    omdb_url = "http://www.omdbapi.com/"

    try:
        response = requests.get(omdb_url, params=params)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        data = response.json()

        if data and data.get("Response") == "True":
            first_result = data["Search"][0]
            if first_result.get("imdbID"):
                return f"{first_result['imdbID']}"
            else:
                return f"No IMDb ID found for {title}"
        else:
            return f"Not Found: {data.get('Error', 'Unknown error for ' + title)}"

    except requests.exceptions.RequestException as e:
        return f"API Error: {e}"

# --- Main Script Logic ---
def process_titles(titles, media_type, writer, watchlisted_timestamp):
    if not titles:
        print(f"No {media_type} titles found to process.")
        return

    for title in titles:
        print(f"Searching for {media_type}: {title}...")
        trakt_id_string = get_imdb_id_from_omdb(title, media_type=media_type)
        writer.writerow({'id': trakt_id_string, 'original_title': title, 'media_type': media_type, 'watchlisted_at': watchlisted_timestamp})
        time.sleep(0.5) # Be kind to the API: pause for half a second between requests

# --- Read titles from TOML file ---
media_data = {}
try:
    with open(MEDIA_LIST_FILE, 'r', encoding='utf-8') as f:
        media_data = toml.load(f)
except FileNotFoundError:
    print(f"Error: The file '{MEDIA_LIST_FILE}' was not found.")
    print("Please make sure 'sampleMedia.toml' is in the same directory as the script.")
    exit()
except toml.TomlDecodeError as e:
    print(f"Error parsing TOML file '{MEDIA_LIST_FILE}': {e}")
    print("Please check the syntax of your TOML file.")
    exit()


movie_titles = media_data.get('movies', {}).get('titles', [])
tv_show_titles = media_data.get('tv_shows', {}).get('titles', [])

watchlisted_timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')


# Open the CSV file for writing
with open(output_csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['id', 'media_type', 'watchlisted_at','original_title',] # Added original_title for reference
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader() # Write the header row

    print("Processing Movies...")
    process_titles(movie_titles, "movie", writer, watchlisted_timestamp )

    print("\nProcessing TV Shows...")
    process_titles(tv_show_titles, "show", writer, watchlisted_timestamp ) # OMDb uses 'show' for TV shows

print(f"\nProcessing complete! Results saved to '{output_csv_filename}'")
print("Review the CSV, especially rows marked 'Not Found' or 'API Error'.")
print("You might need to manually search for those or refine their titles.")
print("For Trakt import, you will only need the 'id' column.")
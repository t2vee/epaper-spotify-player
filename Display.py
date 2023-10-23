import os
import sys
import logging
import time
from dotenv import load_dotenv
import spotipy

# Directory for the e-paper library and fonts
picdir = "/home/user/e-Paper/RaspberryPi_JetsonNano/python/pic"
libdir = "/home/user/e-Paper/RaspberryPi_JetsonNano/python/lib"

# Append the library directory to sys.path
if os.path.exists(libdir):
    sys.path.append(libdir)

from spotipy.oauth2 import SpotifyOAuth
from waveshare_epd import epd2in13_V3
from PIL import Image, ImageDraw, ImageFont



# Initialize logging
logging.basicConfig(level=logging.DEBUG)

# Load Spotify credentials from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
scope = "user-read-currently-playing user-library-read"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))


def display_on_epaper(track_info):
    epd = epd2in13_V3.EPD()
    epd.init()
    epd.Clear(0xFF)

    # Fonts
    title_font = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 20)
    details_font = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 18)
    icon_size = (24, 24)

    # Create a blank image and get a drawing context
    image = Image.new('1', (epd.height, epd.width), 0)  # Black background
    draw = ImageDraw.Draw(image)

    # Song and Album Name
    text = f"{track_info['name']}"
    text_width, text_height = draw.textsize(text, font=title_font)
    x_text = epd.width - text_width // 2
    draw.text((x_text, 10), text, font=title_font, fill=255)

    # Song progress and duration
    song_progress_time = str(int(track_info['progress_ms'] / 60000)) + ":" + str(
        int((track_info['progress_ms'] % 60000) / 1000)).zfill(2)
    song_length = str(int(track_info['duration_ms'] / 60000)) + ":" + str(
        int((track_info['duration_ms'] % 60000) / 1000)).zfill(2)

    song_progress_time_width, _ = draw.textsize(song_progress_time, font=details_font)
    song_length_width, _ = draw.textsize(song_length, font=details_font)

    # Progress bar and song time
    progress_percentage = track_info['progress_ms'] / track_info['duration_ms']
    buffer_space = 0  # you can adjust this to increase/decrease the gap
    #max_progress_bar_width = epd.width - song_progress_time_width - song_length_width - buffer_space
    max_progress_bar_width = epd.width - 10
    print("================DEBUGDEBUGDEBUGDEBUGDEBUGDEBUGDEBUGDEBUGDEBUGDEBUGDEBUGDEBUGDEBUGDEBUG")
    print("max_progress_bar_width: " + str(max_progress_bar_width))
    print("song_progress_time_width: " + str(song_progress_time_width))
    print("song_length_width: " + str(song_length_width))
    print("epd.width: " + str(epd.width))
    progress_filled = int(max_progress_bar_width * progress_percentage)

    y_progress_bar = 40
    y_time = y_progress_bar - 5  # This positions the time texts just above the progress bar

    # Calculate starting x-coordinate to center the progress bar and time
    x_progress_start = epd.width - (song_progress_time_width + max_progress_bar_width + song_length_width) // 2
    x_start_time = x_progress_start
    x_end_time = x_progress_start + max_progress_bar_width + song_progress_time_width

    draw.text((x_start_time - 5, y_time), song_progress_time, font=details_font, fill=255)
    draw.text((x_end_time + 5, y_time), song_length, font=details_font, fill=255)

    # Draw the progress bar
    draw.rectangle([(x_start_time + song_progress_time_width, y_progress_bar),
                    (x_start_time + song_progress_time_width + progress_filled, y_progress_bar + 10)], fill=255)
    draw.rectangle([(x_start_time + song_progress_time_width + progress_filled, y_progress_bar),
                    (x_end_time, y_progress_bar + 10)], outline=255)

    # Artist name below the progress bar
    artist_text = "by " + track_info['artist']
    artist_text_width, artist_text_height = draw.textsize(artist_text, font=details_font)
    x_artist = epd.width - artist_text_width // 2
    y_artist = y_progress_bar + 15
    draw.text((x_artist, y_artist), artist_text, font=details_font, fill=255)

    # Album name below the artist name
    album_text = "in " + track_info['album']
    album_text_width, album_text_height = draw.textsize(album_text, font=details_font)
    x_album = epd.width - album_text_width // 2
    y_album = y_artist + artist_text_height
    draw.text((x_album, y_album), album_text, font=details_font, fill=255)

    # Icons at the bottom
    icon_spacing = 40
    icons_x_position = 10
    if track_info['liked']:
        liked_icon = Image.open('liked.bmp')
        image.paste(liked_icon, (icons_x_position, epd.height - icon_size[1] - 10))
        icons_x_position += icon_spacing

    if track_info['shuffle_state']:
        random_icon = Image.open('shuffle.bmp')
        image.paste(random_icon, (icons_x_position, epd.height - icon_size[1] - 10))
        icons_x_position += icon_spacing

    if track_info['repeat_state']:
        repeat_icon = Image.open('repeat.bmp')
        image.paste(repeat_icon, (icons_x_position, epd.height - icon_size[1] - 10))

    # Display the image on e-paper
    epd.display(epd.getbuffer(image))
    time.sleep(300)
    epd.Clear(0xFF)
    epd.sleep()

def get_spotify_track_info():
    try:
        results = sp.current_user_playing_track()
        if results and results['item']:
            track_id = results["item"]["id"]
            is_liked = sp.current_user_saved_tracks_contains([track_id])[0]

            track_info = {
                'name': results["item"]["name"][:24-3] + "..." if len(results["item"]["name"]) > 24 else results["item"]["name"],
                'artist': results["item"]["artists"][0]["name"][:24-3] + "..." if len(results["item"]["artists"][0]["name"]) > 24 else results["item"]["artists"][0]["name"],
                'album': results["item"]["album"]["name"][:24-3] + "..." if len(results["item"]["album"]["name"]) > 24 else results["item"]["album"]["name"],
                'progress_ms': results["progress_ms"],
                'duration_ms': results["item"]["duration_ms"],
                'liked': is_liked,
                'repeat_state': results.get("repeat_state", "off"),  # using .get() method to handle missing keys
                'shuffle_state': results.get("shuffle_state", False)
            }
            return track_info
    except Exception as e:
        print(f"Error fetching track info: {e}")
        return None


if __name__ == "__main__":
    track_info = get_spotify_track_info()
    if track_info:
        display_on_epaper(track_info)
    else:
        print("No track is currently playing or there was an error.")

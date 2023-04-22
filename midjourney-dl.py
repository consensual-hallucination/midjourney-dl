import requests
import urllib.request
from datetime import datetime
import time
import random
import os

"""
# Downloads images and prompts from Midjourney archive
# Put yor token in token.txt: In your browser's dev tools, 
# find the `__Secure-next-auth.session-token` cookie.

    # Menu:
    # Who's archive do you want to download? ('Enter' for your own, or 'userID'): 
    #   1. Download images for a specific date
    #   2. Download all images
"""


SESSION_TOKEN = ''
# -------------------URLS-------------------
API_BASE = 'https://www.midjourney.com/api/app/'
JOB_STATUS = f'{API_BASE}job-status/'
CDN_BASE = 'https://cdn.midjourney.com/'
APP_URL = 'https://www.midjourney.com/app/'
DATA = 'https://www.midjourney.com/_next/data/'


# ------------------------------------------
UA = 'Midjourney-archive-downloader/0.0.1'
HEADERS = {'User-Agent': UA}
COOKIES = {'__Secure-next-auth.session-token': SESSION_TOKEN}


# ------------------------------------------
API_URL = ''
USER_ID = ''
BUILD_ID = ''
DAY = ''
MONTH = ''
YEAR = ''
notOwn = False

""" !!! IMPORTANT !!!
SLEEP_TIME: is the time-range in seconds to wait between each image download.
PLEASE DO NOT MAKE THIS ANY LOWER, you don't want to hammer Midjourney's servers.
Be Nice. 
"""
SLEEP_TIME = random.uniform(1, 2) 
DOWNLOAD_DIR = "images"
# ------------------------------------------


def download_image(image_url, filename, prompt):
    global DOWNLOAD_DIR
    print(f"Downloading {image_url}")
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', UA)]
    urllib.request.install_opener(opener)
    url = image_url

    if(notOwn):
        download_dir  = f"images/{USER_ID}/{YEAR}/{MONTH}/{DAY}"
    else:
        download_dir  = f"images/my/{YEAR}/{MONTH}/{DAY}"

    if not os.path.exists(download_dir ):
        os.makedirs(download_dir )

    if prompt is not None:
        shortened_prompt = (prompt[:200]) if len(prompt) > 200 else prompt
    else:
        shortened_prompt = "No prompt"

    special_chars = "/\\:*?\"<>|"
    for char in special_chars:
        shortened_prompt = shortened_prompt.replace(char, "-")

    image_path = f"{download_dir}/{shortened_prompt}_{filename}.png"
    if os.path.exists(image_path):
        print("File already exists, skipping")
        return

    try:   
        urllib.request.urlretrieve(url, image_path)
    except Exception as e:
        print("")
        print("Error downloading image - saving error info")
        print("Skipping this one and retrying in 5 seconds")
        print("")
        
        with open("errors.txt", "a") as text_file:
            text_file.write(f"{e} - {image_url}\n")
            text_file.close()
        time.sleep(5)
        return

    # save full command to file
    with open(f"{download_dir}/{shortened_prompt}_{filename}.txt", "w", encoding="utf-8") as text_file:
        if prompt is None:
            prompt = "No prompt"
        response = requests.post(JOB_STATUS, json={"jobIds": [filename]}, cookies=COOKIES, headers=HEADERS)
        if response.history:
            print("Session token is invalid: exiting")
            exit()
        job_status_obj = response.json()
        full_command = job_status_obj["full_command"]
        try:   
            text_file.write(full_command)
            text_file.close()
        except Exception as e:
            print("Error writing full command to file")
            print(str(e))
            print(shortened_prompt)
            pass
        text_file.close()
    time.sleep(SLEEP_TIME)


def get_archive_by_date(API_URL):
    global COOKIES
    response = requests.get(API_URL, cookies=COOKIES, headers=HEADERS)

    if response.history:
        new_session_token = input("Session invalid, Please paste new sesion token: ")
        COOKIES = {'__Secure-next-auth.session-token': new_session_token}

        # save cookies to file
        with open("token.txt", "w") as text_file:
            text_file.write(new_session_token)
        response = requests.get(API_URL, cookies=COOKIES, headers=HEADERS)
        if response.history:
            print("Session token is invalid: exiting")
            exit()

    object_list = response.json()
    print(f"Downloading upscaled images for {DAY}/{MONTH}/{YEAR}")
    print("")

    for object in object_list:
        object_type = object['type']
        if object_type in ["yfcc_upsample", "sizigi_upscale", "v4_upscaler"]: 
            image_url = f"{CDN_BASE}{object['id']}/grid_0.png"
            download_image(image_url, object['id'], object['prompt'])

        elif object['type'] == "v5_virtual_upsample" and object['parent_id'] is not None:
            image_url = f"{CDN_BASE}{object['parent_id']}/0_{object['parent_grid']}.png"
            download_image(image_url, object['id'], object['prompt'])
        elif object['type'] == "v5_diffusion" or object['type'] == "v4_diffusion":
            continue
        else:
            # store possible new object types
            with open("object_types.csv", "a") as text_file:
                text_file.write(f"{object['type']}\n")
    
    

if __name__ == "__main__":
    print("")
    print("")
    print("#----------------------------------#")
    print("# Midjourney Archive Downloader    #")
    print("# v0.0.1                           #")
    print("#----------------------------------#")
    print("")

    try:
        with open("token.txt", "r") as text_file:
            COOKIES = {'__Secure-next-auth.session-token': text_file.read()}
            text_file.close()
    except:
            new_session_token = input("Please paste session token:")
            COOKIES = {'__Secure-next-auth.session-token': new_session_token}
            with open("token.txt", "w") as text_file:
                text_file.write(new_session_token)
    try:
        response = requests.get(APP_URL)
        build_id = response.text.split('"buildId":"')[1].split('"')[0]
        BUILD_ID = build_id
        print(f"Midjourney App Build ID: {BUILD_ID}")
    except:
        print("Error getting build ID")
        pass
    print("")

    USER_ID = input("Who's archive do you want to download? (Enter for your own): ")
    if USER_ID == "":
        USER_ID = "me"
    else:
        notOwn = True
    
    print("\n\n1. Download images for a specific date\n2. Download all images\n")
    download_option = input("Enter your choice: ")

    if download_option == "1":
        DAY = input("Day (1-31, 'Enter' for Today): ")
        # must be numeric and between 1 and 31
        if DAY == "":
            DAY = datetime.now().day
            MONTH = datetime.now().month
            YEAR = datetime.now().year
        else:
            MONTH = input("Month (1-12, 'Enter' for current month): ")
            if MONTH == "":
                MONTH = datetime.now().month
            YEAR = input("Year ('Enter' for current year): ")
            if YEAR == "":
                YEAR = datetime.now().year

        if USER_ID == "me":
            API_URL = f"{API_BASE}archive/day/?day={DAY}&month={MONTH}&year={YEAR}&includePrompts=true"
        else:
            notOwn = True
            API_URL = f"{API_BASE}archive/day/?day={DAY}&month={MONTH}&year={YEAR}&userId={USER_ID}&includePrompts=true" 
        get_archive_by_date(API_URL)
   
   
    elif download_option == "2":
        # get list of all dates
        if USER_ID == "me":
            url = f"{DATA}{BUILD_ID}/app/archive.json"
            response = requests.get(url, cookies=COOKIES, headers=HEADERS)
            if response.history:
                print("Session token is invalid: exiting")
                exit()
            object_list = response.json()
            days = object_list['pageProps']['days']
            for day in days:
                DAY = day['d']
                MONTH = day['m']
                YEAR = day['y']
                API_URL = f"{API_BASE}archive/day/?day={DAY}&month={MONTH}&year={YEAR}&includePrompts=true"
                get_archive_by_date(API_URL)
        else:
            url = f"{DATA}{BUILD_ID}/app/users/{USER_ID}/archive.json?user={USER_ID}"
            response = requests.get(url, cookies=COOKIES, headers=HEADERS)
            if response.history:
                print("Session token is invalid: exiting")
                exit()
            object_list = response.json()
            days = object_list['pageProps']['days']
            for day in days:
                DAY = day['d']
                MONTH = day['m']
                YEAR = day['y']
                API_URL = f"{API_BASE}archive/day/?day={DAY}&month={MONTH}&year={YEAR}&userId={USER_ID}&includePrompts=true"
                get_archive_by_date(API_URL)

    print("--------------------")
    print("")
    print("Done!")
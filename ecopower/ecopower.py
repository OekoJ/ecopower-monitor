from PIL import Image, ImageDraw, ImageFont
import time
import os
import json
from datetime import datetime
import requests
# from inky.auto import auto # uncomment for other inky versions
from inky import InkyPHAT

url = "https://api.energy-charts.info/ren_share_forecast?country=de" # https://api.energy-charts.info/ren_share_forecast?country=de
update_interval = 3600 # load new values from url every 1 hour (60s * 60min = 3600s)
local_file = "last_jsonValues.json" # same path as script
out_of_range_img = "out_of_range.png" # same path as script

# Get the current path
PATH = os.path.dirname(__file__)

font1 = ImageFont.truetype(os.path.join(PATH, "PixelOperator-Bold.ttf"), 16) # https://www.dafont.com/de/pixel-operator.font
font2 = ImageFont.truetype(os.path.join(PATH, "PixelOperator-Bold.ttf"), 32) # https://www.dafont.com/de/pixel-operator.font

weekdays = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"]

maxY = 103 # Display height 104 - 1
maxX = 211 # Display width 212 - 1
faktorY = 1
startX = 0

timestamp_now = int(time.time())
date_objectNow = datetime.fromtimestamp(timestamp_now)
timeStringToday0H = date_objectNow.strftime("%d/%m/%Y") + " 00:00"
timestamp_today_0h = int(time.mktime(datetime.strptime(timeStringToday0H, "%d/%m/%Y %H:%M").timetuple()))

# load last jsonValues from file
with open(os.path.join(PATH, local_file), 'r') as f:
    jsonValues = json.load(f)

# switch off red Power LED
# Pi 2 Version B
if os.path.isfile("/sys/class/leds/PWR/brightness"):
    os.system("sudo bash - c \"echo 0 > /sys/class/leds/PWR/brightness\"") 
    # print("Switch off red Power LED on Pi 2 Version B")

# switch off green Power LED
# Pi Zero W
if os.path.isfile("/sys/class/leds/ACT/brightness"):
    os.system("sudo bash -c \"echo 0 > /sys/class/leds/ACT/brightness\"")
    # print("Switch off green Power LED on Pi Zero W")

# Set up the Inky display
try:
    # inky_display = auto(ask_user=True, verbose=False) # uncomment for other inky versions
    inky_display = InkyPHAT('red')
except TypeError:
    raise TypeError("You need to update the Inky library to >= v1.1.0")


def getLoadprofile(url):
    r = requests.get(url)
    loadprofile = r.json()
    # print(json.dumps(loadprofile, indent=2))
    return loadprofile # alle Eintraege


# load new values from url every update_interval)
if (timestamp_now - jsonValues['last_timestamp']) >= update_interval:
    try:
        new_jsonValues = getLoadprofile(url)
        jsonValues = new_jsonValues
        jsonValues['last_timestamp'] = timestamp_now
        print("Load new values from " + url)
        # write jsonValues to file
        try:
            with open(os.path.join(PATH, local_file), "w") as f:
                json.dump(jsonValues, f, indent=4)
        except Exception as error:
            print(error)
    except:
        print("ERROR: Failed to connect to: " + url)

# step along the display to show all 24 hours = 96 * 15-min values
stepX = (maxX-startX)/96

# calculate actual values
timestamp_before = int(int(timestamp_now/900)*900) # previous 15-minutes-value
timestamp_next = timestamp_before + 900 # next 15-minutes-value
timestamp_last_jsonValue = jsonValues['unix_seconds'][-1]

if (timestamp_before in jsonValues['unix_seconds']):
    ren_share_before = jsonValues['ren_share'][jsonValues['unix_seconds'].index(timestamp_before)]
else:
    ren_share_before = 0
if (timestamp_next in jsonValues['unix_seconds']):
    ren_share_next = jsonValues['ren_share'][jsonValues['unix_seconds'].index(timestamp_next)]
else:
    ren_share_next = 0

# linear interpolation of ren_share_now between ren_share_next and ren_share_before
ren_share_now = ren_share_before + (ren_share_next - ren_share_before)/900 * (timestamp_now - timestamp_before)

# make graph only if timestamp_now is in range
if timestamp_now <= timestamp_last_jsonValue:

    print(weekdays[int(date_objectNow.strftime("%w"))] + date_objectNow.strftime(" %d.%m.%Y"), date_objectNow.strftime("%H:%M"), "-->", str(round(ren_share_now)) + "%")

    # generate solar curve
    rememberNext = True
    x = startX
    others = []
    wind = []
    solar = []
    offset = jsonValues['unix_seconds'].index(timestamp_today_0h)
    timenowX = round(startX + (timestamp_now - jsonValues['unix_seconds'][offset])/900 * stepX)
    max_index = len(jsonValues['unix_seconds']) - 1
    for i in range(0,98):
        if (i+offset) > max_index:
            break
        # add missing values (if not present)
        if (i+offset) >= len(jsonValues['ren_share']):
            jsonValues['ren_share'] += [0]
        if (i+offset) >= len(jsonValues['solar_share']):
            jsonValues['solar_share'] += [0]
        if (i+offset) >= len(jsonValues['wind_onshore_share']):
            jsonValues['wind_onshore_share'] += [0]
        if (i+offset) >= len(jsonValues['wind_offshore_share']):
            jsonValues['wind_offshore_share'] += [0]

        othersY = round(jsonValues['ren_share'][i+offset] - jsonValues['solar_share'][i+offset] - jsonValues['wind_onshore_share'][i+offset] - jsonValues['wind_offshore_share'][i+offset])
        others += [(x, maxY - faktorY * othersY)]
        windY = round(jsonValues['ren_share'][i+offset] - jsonValues['solar_share'][i+offset])
        wind += [(x, maxY - faktorY * windY)]
        solarY = round(jsonValues['ren_share'][i+offset])
        solar += [(x, maxY - faktorY * solarY)]
        x += stepX

    # make closed polygon out of lines
    others += [(x - stepX, maxY), (startX, maxY)]
    solar  += [(x - stepX, maxY), (startX, maxY)]
    wind  += [(x - stepX, maxY), (startX, maxY)]

    img = Image.new("RGB", (212, 104), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    draw.polygon(solar, fill=(255, 0, 0))
    draw.polygon(wind, fill=(255, 100, 100))
    draw.polygon(others, fill=(255, 200, 200))

    # line for actual time
    timenowY = (maxY - faktorY * ren_share_now)
    draw.line((timenowX , timenowY + 5, timenowX , maxY), (255, 127, 127), width=3) # rot - weiss - schwarz
    draw.line((timenowX , timenowY, timenowX , maxY), (0, 0, 0), width=1) # schwarz

    # print arrow
    # ImageDraw.regular_polygon(bounding_circle, n_sides, rotation=0, fill=None, outline=None, width=1)
    draw.regular_polygon(bounding_circle=(timenowX, timenowY + 5, 5), n_sides=3, rotation=0, fill=(0,0,0))


    # draw percent and "Ökostrom"
    percentString = str(round(ren_share_now)) + "%"
    # ImageDraw.text(xy, text, fill=None, font=None, anchor=None, spacing=4, align='left', direction=None, features=None, language=None, stroke_width=0, stroke_fill=None, embedded_color=False, font_size=None)
    draw.text((212 -4 - font2.getlength(percentString), -2), percentString, (0, 0, 0), font=font2, stroke_width=1, stroke_fill=(255, 255, 255))
    draw.text(((212 -4 - font1.getlength("Ökostrom")), 26), "Ökostrom", (0, 0, 0), font=font1, stroke_width=1, stroke_fill=(255, 255, 255))

    # draw time and date
    draw.text((4, -2), date_objectNow.strftime("%H:%M"), (0, 0, 0), font=font2, stroke_width=1, stroke_fill=(255, 255, 255))
    draw.text((6, 26), weekdays[int(date_objectNow.strftime("%w"))] + date_objectNow.strftime(" %d.%m.%y"), (0, 0, 0), font=font1, stroke_width=1, stroke_fill=(255, 255, 255))

# graph with image if time is out of range
else:
    print(weekdays[int(date_objectNow.strftime("%w"))] + date_objectNow.strftime(" %d.%m.%Y"), date_objectNow.strftime("%H:%M"), "-->", "Keine aktuellen Werte verfügbar, zeichne Bildschirmschoner.")

    # img = Image.new("RGB", (212, 104), (255, 255, 255))
    img = Image.open(os.path.join(PATH, out_of_range_img))
    draw = ImageDraw.Draw(img)
    draw.polygon(((3,3),(88,3),(88,42),(3,42)), fill=(255, 255, 255))
    # draw time and date
    draw.text((4, -2), date_objectNow.strftime("%H:%M"), (0, 0, 0), font=font2)
    draw.text((6, 26), weekdays[int(date_objectNow.strftime("%w"))] + date_objectNow.strftime(" %d.%m.%y"), (0, 0, 0), font=font1)

# print y-axis
stepYlines = round (maxY / 10)
for lineY in range(1,11):
    if lineY % 5:
        draw.line((startX + round((maxX-startX) / 2) - 1,  maxY - lineY * stepYlines, startX + round((maxX-startX) / 2) + 1, maxY - lineY * stepYlines), (0, 0, 0), width=1) # 
    else:
        draw.line((startX + round((maxX-startX) / 2) - 2,  maxY - lineY * stepYlines, startX + round((maxX-startX) / 2) + 2, maxY - lineY * stepYlines), (0, 0, 0), width=1) # 

# print x-axis
stepXlines = ((maxX - startX) / 24)
for lineX in range(25):
    if lineX % 6:
        draw.line((round(startX + lineX * stepXlines), maxY, round(startX + lineX * stepXlines), maxY - 3), (0, 0, 0), width=1) # 
    else:
        draw.line((round(startX + lineX * stepXlines), maxY, round(startX + lineX * stepXlines), maxY - 6), (0, 0, 0), width=1) # 



# color ajustment 
if(True):
    # reduziere Farben auf weiss, schwarz, rot
    pal_img = Image.new("P", (1, 1))
    pal_img.putpalette((255, 255, 255, 0, 0, 0, 255, 0, 0) + (0, 0, 0) * 252)
    img = img.convert("RGB").quantize(palette=pal_img)

if(True):
    # Display data on Inky pHAT
    inky_display.set_image(img)
    inky_display.show()

if(False):
    # show on screen
    print(img.format, img.size, img.mode)
    img.show()

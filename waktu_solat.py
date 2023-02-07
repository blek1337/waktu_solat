# -*- coding: utf-8 -*-
# !/usr/bin/python
# coded by blek
def __install__(package: str | list) -> bool:
    import pip
    try:
        __import__(package) if type(package) != list else  __import__(package[0])
    except ModuleNotFoundError:
        if hasattr(pip, "main"):
            pip.main(["install", package]) if type(package) != list else pip.main(["install", package[1]])
        else:
            pip._internal.main(["install", package]) if type(package) != list else pip._internal.main(["install", package[1]])
        try:
            __import__(package) if type(package) != list else __import__(package[0])
        except ModuleNotFoundError:
            print(f"Unable to install {package[0] if type(package) == list else package}.")
        except (KeyboardInterrupt, Exception) as e:
            print(e)
            print("Unknown error. Terminating...")
            exit(1)

requirements = ["geocoder", "pick", "wikipedia", "requests", "tabulate"]
for x in requirements:
    __install__(x)
# library import
import geocoder
import math
import pick
import requests
import re
import datetime
import os
import tabulate

data = {}
dates = []

def daerah():
    response = requests.get("https://ms.wikipedia.org/wiki/Senarai_daerah_bagi_setiap_negeri_di_Malaysia_mengikut_populasi")
    if response.status_code == 200:
        states = re.findall('<span class="mw-headline" id="[A-Za-z0-9_]+">([A-Za-z_\s]+)</span>', response.text)
        tbodies = re.findall('<table[^>]*>(.*?)</table>', response.text, re.DOTALL)
        for x in range(len(tbodies)):
            data[states[x].replace("Negeri ", "")] = re.findall("<td[^>]*><a[^>]*>(.*?)</a></td>", tbodies[x])

class waktu_solat:
    def __init__(self, latitude: float, longitude: float, year: int, month: int, day: int, hour: int = 0, zone: int = 8) -> None:
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.zone = int(zone)
        self.calculate()
    def day_since_1st_jan(self, year, month, day):
        date = datetime.date(year, month, day)
        subtracted = date - datetime.date(year, 1, 1)
        return subtracted.days
    def d2k(self, year, month, day, hour, zone):
        if month <= 2:
            year -= 1
            month += 12
        AAAA      = int(year / 100)
        BBBB      = 2 - AAAA + int(AAAA / 4)
        CCCC      = int(365.25 * year)
        DDDD      = int(30.6001 * (month + 1))#
        JD        = BBBB + CCCC + DDDD + day + (hour-zone)/24.- 730550.5
        return JD
    def EoT(self, year, month, day, hour, zone):
        day_since_epoch = self.d2k(year, month, day, hour, zone)
        mean_long_sun_d = (280.46 + 0.9856474  * day_since_epoch) % 360.
        mean_anomaly_d = (357.528 + 0.9856003 * day_since_epoch) % 360.
        mean_anomaly_r = math.radians(mean_anomaly_d)
        ecliptic_Long_d = mean_long_sun_d + 1.915 *math.sin(mean_anomaly_r) + 0.020 * math.sin(2*mean_anomaly_r)
        ecliptic_Long_r = math.radians(ecliptic_Long_d)
        obliquity_d = 23.439 - 0.0000004 * day_since_epoch
        obliquity_r = math.radians(obliquity_d)
        right_ascension_r = math.atan2(math.cos(obliquity_r) * math.sin(ecliptic_Long_r),math.cos(ecliptic_Long_r))
        right_ascension_d = (math.degrees(right_ascension_r)) % 360.
        # declination_r     = math.asin(math.sin(obliquity_r) * math.sin(ecliptic_Long_r))
        EoT_d = mean_long_sun_d - right_ascension_d
        if EoT_d > 50:
            EoT_d -= 360
        return  -EoT_d * 4
    def decimal_to_hms(self, decimal):
        decimal = float(decimal)
        hours = int(decimal)
        minutes = int((decimal - hours) * 60)
        seconds = int((((decimal - hours) * 60) - minutes) * 60)
        return datetime.time(hours, minutes, seconds).strftime("%H:%M:%S")
    def calculate(self):
        self.lat = math.radians(self.latitude)
        n_days = int(self.day_since_1st_jan(self.year, self.month, self.day))
        t_days =  2 * (math.pi * (n_days - 1)) / 365
        self.declination = 0.006918 - (0.399912 * math.cos(t_days)) + (0.070257 * math.sin(t_days)) - (0.006758 * math.cos(2 * t_days)) + (0.000907 * math.sin(2 * t_days)) - (0.002696 * math.cos(3 * t_days)) + (0.00148 * math.sin(3 * t_days))
        jd2 = self.EoT(self.year, self.month, self.day, self.hour, self.zone)
        self.istiwa = (12 + (jd2/60)) + ((120 - self.longitude)/15)
    @property
    def imsak(self):
        radians = math.radians(-18)
        subh = (math.degrees(math.acos((math.sin(radians) - (math.sin(self.declination) * math.sin(self.lat))) / (math.cos(self.declination) * math.cos(self.lat))))) / 15
        return self.decimal_to_hms(self.istiwa - subh - (10/60))
    @property
    def subuh(self):
        radians = math.radians(-18)
        subh = (math.degrees(math.acos((math.sin(radians) - (math.sin(self.declination) * math.sin(self.lat))) / (math.cos(self.declination) * math.cos(self.lat))))) / 15
        return self.decimal_to_hms(self.istiwa - subh)
    @property
    def syuruk(self):
        radians = math.radians(-1)
        syurh = (math.degrees(math.acos((math.sin(radians) - (math.sin(self.declination) * math.sin(self.lat))) / (math.cos(self.declination) * math.cos(self.lat))))) / 15
        return self.decimal_to_hms(self.istiwa - syurh)
    @property
    def zuhr(self):
        return self.decimal_to_hms(self.istiwa + (2/60))
    @property
    def asar(self):
        radians = math.atan(1 / (1 + math.tan(abs((self.lat - self.declination)))))
        asr =  (math.degrees(math.acos((math.sin(radians) - (math.sin(self.declination) * math.sin(self.lat))) / (math.cos(self.declination) * math.cos(self.lat))))) / 15
        return self.decimal_to_hms(self.istiwa + asr)
    @property
    def maghrib(self):
        radians = math.radians(-1)
        maghrb =(math.degrees(math.acos((math.sin(radians) - (math.sin(self.declination) * math.sin(self.lat))) / (math.cos(self.declination) * math.cos(self.lat))))) / 15
        return self.decimal_to_hms(self.istiwa + maghrb)
    @property
    def isyak(self):
        radians = math.radians(-18)
        isyk = (math.degrees(math.acos((math.sin(radians) - (math.sin(self.declination) * math.sin(self.lat))) / (math.cos(self.declination) * math.cos(self.lat))))) / 15
        return self.decimal_to_hms(self.istiwa + isyk)

if __name__ == "__main__":
    dates.append(datetime.datetime.now())
    for i in range(1, 6):
        # dates.append(datetime.datetime.now() - datetime.timedelta(days=i))
        dates.append(datetime.datetime.now() + datetime.timedelta(days=i))
    os.system(["clear", "cls"][os.name == "nt"])
    daerah()
    titles = ["Please choose your state:", "Please choose your area:", "Please choose date:"]
    states = [x for x in data.keys()]
    state, state_index = pick.pick(states, titles[0])
    areas = data[state]
    area, area_index = pick.pick(areas, titles[1])
    geo = geocoder.arcgis(f"{area}, {state}")
    waktu = {"Solat": ["Imsak", "Subuh", "Syuruk", "Zuhr", "Asar", "Maghrib", "Isyak"]}
    for x in dates:
        solat = waktu_solat(geo.latlng[0], geo.latlng[1], x.year, x.month, x.day)
        waktu[x.strftime("%Y-%m-%d")] = [solat.imsak, solat.subuh, solat.syuruk, solat.zuhr, solat.asar, solat.maghrib, solat.isyak]
    table = tabulate.tabulate(waktu, headers="keys", tablefmt="fancy_grid")
    print(table)
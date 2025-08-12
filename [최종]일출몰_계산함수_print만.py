# -*- coding: utf-8 -*-
"""
지정한 기간/포트의 일출·일몰을 콘솔에 출력 (CSV 저장 없음)
시간대: KST (UTC+9)
작성: lsh 
"""

from __future__ import annotations
from typing import Dict, Tuple, Optional, List, Iterable, Union
from math import sin, cos, tan, acos, asin, radians, degrees, floor
from datetime import datetime, timedelta, timezone, date

# ====== 사용자 설정 (여기만 바꿔서 사용) ======
START_DATE = "20240101"                 # 'YYYYMMDD' 또는 'YYYY-MM-DD'
END_DATE   = "20240102"                 # 'YYYYMMDD' 또는 'YYYY-MM-DD'
PORT_NAMES: Union[str, List[str]] = [
    "Busan", "Incheon", "Ulsan", "Mokpo", "Pohang", "Gunsan", "Daesan", "Ptdj", "Yeosu"
]
# PORT 사용할 것만 사용하고 나머지는 주석으로 처리하길.

# ====== 태양 계산(SPA-lite) ======
def julian_day(year: int, month: int, day: int) -> float:
    if month <= 2:
        year -= 1
        month += 12
    A = floor(year / 100)
    B = 2 - A + floor(A / 4)
    return floor(365.25 * (year + 4716)) + floor(30.6001 * (month + 1)) + day + B - 1524.5

def equation_of_time(T: float):
    L0 = 280.46646 + T * (36000.76983 + 0.0003032 * T)
    L0 %= 360
    M = 357.52911 + T * (35999.05029 - 0.0001537 * T)
    e = 0.016708634 - T * (0.000042037 + 0.0000001267 * T)
    C = (1.914602 - T * (0.004817 + 0.000014 * T)) * sin(radians(M)) + \
        (0.019993 - 0.000101 * T) * sin(radians(2 * M)) + \
        0.000289 * sin(radians(3 * M))
    true_long = L0 + C
    omega = 125.04 - 1934.136 * T
    lambda_sun = true_long - 0.00569 - 0.00478 * sin(radians(omega))
    epsilon0 = 23 + (26 + ((21.448 - T * (46.815 + T * (0.00059 - T * 0.001813)))) / 60) / 60
    epsilon = epsilon0 + 0.00256 * cos(radians(omega))
    y = tan(radians(epsilon / 2)) ** 2
    EoT = 4 * degrees(
        y * sin(2 * radians(L0)) -
        2 * e * sin(radians(M)) +
        4 * e * y * sin(radians(M)) * cos(2 * radians(L0)) -
        0.5 * y * y * sin(4 * radians(L0)) -
        1.25 * e * e * sin(2 * radians(M))
    )
    return EoT, lambda_sun, epsilon

def solar_declination(lambda_sun: float, epsilon: float) -> float:
    return degrees(asin(sin(radians(epsilon)) * sin(radians(lambda_sun))))

def round_to_minute(dt: datetime) -> datetime:
    return (dt + timedelta(seconds=30)).replace(second=0, microsecond=0)

def sunrise_sunset(year: int, month: int, day: int, lat: float, lon: float,
                   tz_offset: int = 9, h0: float = -0.833):
    JD = julian_day(year, month, day)
    T = (JD - 2451545.0) / 36525
    EoT, lambda_sun, epsilon = equation_of_time(T)
    delta = solar_declination(lambda_sun, epsilon)

    solar_noon_utc = 720 - 4 * lon - EoT
    cosH0 = (sin(radians(h0)) - sin(radians(lat)) * sin(radians(delta))) / (cos(radians(lat)) * cos(radians(delta)))
    if cosH0 > 1 or cosH0 < -1:
        return None, None  # 극야/백야

    H0 = degrees(acos(max(-1, min(1, cosH0))))
    sunrise_utc_min = solar_noon_utc - 4 * H0
    sunset_utc_min  = solar_noon_utc + 4 * H0

    utc0 = datetime(year, month, day, tzinfo=timezone.utc)
    sr = round_to_minute(utc0 + timedelta(minutes=sunrise_utc_min) + timedelta(hours=tz_offset))
    ss = round_to_minute(utc0 + timedelta(minutes=sunset_utc_min)  + timedelta(hours=tz_offset))
    return sr, ss

# ====== 좌표 매핑 ======
PORT_COORDS: Dict[str, Tuple[float, float]] = {
    "Busan":   (35.1796, 129.0756),
    "Incheon": (37.3680, 126.6540),
    "Ulsan":   (35.4460, 129.2700),
    "Mokpo":   (34.7320, 126.3440),
    "Pohang":  (35.9560, 129.3100),
    "Gunsan":  (35.9040, 126.7040),
    "Daesan":  (36.6600, 126.2520),
    "Ptdj":    (37.2300, 126.7800),    
    "Yeosu":   (34.6700, 127.6200),
    # 원하는 지역 좌표 추가하고 싶으면 추가 하면 될 듯.
}

def map_coords(name: str) -> Tuple[Optional[float], Optional[float]]:
    if name is None:
        return None, None
    n = str(name).strip()
    if n in PORT_COORDS:
        return PORT_COORDS[n]
    for k, (lat, lon) in PORT_COORDS.items():
        if k.lower() == n.lower():
            return lat, lon
    return None, None

# ====== 날짜 유틸 ======
def parse_date(s: str) -> date:
    s = s.strip().replace("-", "")
    return date(int(s[0:4]), int(s[4:6]), int(s[6:8]))

def daterange(d0: date, d1: date):
    cur = d0
    one = timedelta(days=1)
    while cur <= d1:
        yield cur
        cur += one

# ====== 출력 유틸 ======
def print_port_table(start: str, end: str, port: str):
    lat, lon = map_coords(port)
    if lat is None or lon is None:
        raise ValueError(f"좌표 매핑을 찾을 수 없습니다: '{port}'")

    d0, d1 = parse_date(start), parse_date(end)
    if d1 < d0:
        raise ValueError("END_DATE가 START_DATE보다 빠릅니다.")

    header = f"[{port}] (KST)"
    print(header)
    print("-" * len(header))
    print("날짜       출(HH:MM)  몰(HH:MM)")
    for d in daterange(d0, d1):
        sr, ss = sunrise_sunset(d.year, d.month, d.day, lat, lon, tz_offset=9, h0=-0.833)
        sr_str = sr.strftime("%H:%M") if sr else "--:--"
        ss_str = ss.strftime("%H:%M") if ss else "--:--"
        print(f"{d.strftime('%Y%m%d')}  {sr_str:>7}  {ss_str:>7}")
    print()  # 빈 줄

# ====== 엔트리 포인트 ======
def main():
    if isinstance(PORT_NAMES, str):
        print_port_table(START_DATE, END_DATE, PORT_NAMES)
    else:
        for p in PORT_NAMES:
            print_port_table(START_DATE, END_DATE, str(p))

if __name__ == "__main__":
    main()


import math
from datetime import datetime, timezone, timedelta
from skyfield.api import EarthSatellite, load, wgs84

# ─── MSAR Observer Location (KDU, Sri Lanka) ────────────────────────────────
OBS_LAT  =  7.2906   # degrees N
OBS_LON  = 80.6337   # degrees E
OBS_ALT  =  0.500    # km above sea level

# ─── Sample TLE sets  ──────────────
SATELLITES = {
    "ISS (ZARYA)": (
        "1 25544U 98067A   24100.50000000  .00006000  00000-0  11000-3 0  9999",
        "2 25544  51.6400 137.5300 0005000  85.4000 274.7500 15.49560000450000"
    ),
    "NOAA 19": (
        "1 33591U 09005A   24100.50000000  .00000089  00000-0  72000-4 0  9999",
        "2 33591  99.1700 220.4700 0014000 280.3000  79.7000 14.12300000800000"
    ),
    "METEOR-M 2": (
        "1 40069U 14037A   24100.50000000  .00000050  00000-0  42000-4 0  9999",
        "2 40069  98.5700 240.1200 0005000 350.2000   9.9000 14.20600000550000"
    ),
    "FUNCUBE-1 (AO-73)": (
        "1 39444U 13066AE  24100.50000000  .00000100  00000-0  15000-3 0  9999",
        "2 39444  97.8000 230.0000 0102000 345.0000  14.0000 14.82500000600000"
    ),
    "CUTE-1 (CO-55)": (
        "1 27844U 03031E   24100.50000000  .00000080  00000-0  12000-3 0  9999",
        "2 27844  98.6900 200.5000 0010000 100.0000 260.0000 14.29900000550000"
    ),
    "OSCAR-7 (AO-7)": (
        "1 07530U 74089B   24100.50000000 -.00000004  00000-0  10000-4 0  9999",
        "2 07530 101.6800 220.3000 0012000  50.0000 310.0000 12.53600000900000"
    ),
}

# ─── Colour helpers (ANSI) ───────────────────────────────────────────────────
R  = "\033[91m"   # red
G  = "\033[92m"   # green
Y  = "\033[93m"   # yellow
B  = "\033[94m"   # blue
M  = "\033[95m"   # magenta
C  = "\033[96m"   # cyan
W  = "\033[97m"   # white
DIM= "\033[2m"
BLD= "\033[1m"
RST= "\033[0m"

def hr(char="─", n=70, color=DIM):
    print(color + char * n + RST)

def header(title, color=BLD+C):
    print()
    hr("═", 70, C)
    print(f"{color}  {title}{RST}")
    hr("═", 70, C)

def section(title, color=BLD+Y):
    print()
    hr("─", 70, DIM)
    print(f"{color}  {title}{RST}")
    hr("─", 70, DIM)

# ════════════════════════════════════════════════════════════════════════════════
#  PART 1 — TLE STRUCTURE EXPLAINER
# ════════════════════════════════════════════════════════════════════════════════
def explain_tle_structure():
    header("PART 1 — What is a TLE (Two-Line Element Set)?")

    tle_name = "ISS (ZARYA)"
    l1, l2   = SATELLITES[tle_name]

    print(f"""
{W}A TLE is a standardised two-line data format used to describe the{RST}
{W}orbital elements of an Earth-orbiting object at a specific epoch.{RST}
{W}The SGP4 model uses these elements to propagate the orbit forward{RST}
{W}in time and compute the satellite's position and velocity.{RST}
""")

    print(f"{BLD}Example TLE — {M}{tle_name}{RST}")
    print()
    print(f"  {G}{tle_name}{RST}")
    print(f"  {Y}{l1}{RST}")
    print(f"  {B}{l2}{RST}")
    print()

    # ── Parse Line 1 ──────────────────────────────────────────────────────────
    section("Line 1 Field Breakdown")

    fields_l1 = [
        ("Col 01",       l1[0],             "Line number (always 1)"),
        ("Col 03–07",    l1[2:7],           "NORAD Catalog Number (25544 = ISS)"),
        ("Col 08",       l1[7],             "Classification: U=Unclassified"),
        ("Col 10–11",    l1[9:11],          "International Designator — launch year (98 → 1998)"),
        ("Col 12–14",    l1[11:14],         "International Designator — launch number (067)"),
        ("Col 15–17",    l1[14:17],         "International Designator — piece (A = first piece)"),
        ("Col 19–20",    l1[18:20],         "Epoch year (24 → 2024)"),
        ("Col 21–32",    l1[20:32].strip(), "Epoch day of year + fraction (100.5 = April 9, noon)"),
        ("Col 34–43",    l1[33:43].strip(), "First derivative of mean motion (drag effect)"),
        ("Col 45–52",    l1[44:52].strip(), "Second derivative of mean motion (usually 0)"),
        ("Col 54–61",    l1[53:61].strip(), "BSTAR drag coefficient (atmospheric drag)"),
        ("Col 63",       l1[62],            "Ephemeris type (0 = SGP4)"),
        ("Col 65–68",    l1[64:68].strip(), "Element set number"),
        ("Col 69",       l1[68],            "Checksum digit"),
    ]

    for col, val, desc in fields_l1:
        print(f"  {DIM}{col:12s}{RST}  {Y}{val:15s}{RST}  {W}{desc}{RST}")

    # ── Parse Line 2 ──────────────────────────────────────────────────────────
    section("Line 2 Field Breakdown")

    inc        = float(l2[8:16].strip())
    raan       = float(l2[17:25].strip())
    ecc_str    = l2[26:33].strip()
    ecc        = float("0." + ecc_str)
    argp       = float(l2[34:42].strip())
    ma         = float(l2[43:51].strip())
    mm         = float(l2[52:63].strip())

    fields_l2 = [
        ("Col 01",     l2[0],             "Line number (always 2)"),
        ("Col 03–07",  l2[2:7],           "NORAD Catalog Number (must match line 1)"),
        ("Col 09–16",  f"{inc:.4f}°",     "Inclination — angle of orbit to equator"),
        ("Col 18–25",  f"{raan:.4f}°",    "RAAN — Right Ascension of the Ascending Node"),
        ("Col 27–33",  f"0.{ecc_str}",    f"Eccentricity (0=circle, 1=parabola) → {ecc:.7f}"),
        ("Col 35–42",  f"{argp:.4f}°",    "Argument of Perigee — where perigee is in orbit"),
        ("Col 44–51",  f"{ma:.4f}°",      "Mean Anomaly — satellite's position in orbit at epoch"),
        ("Col 53–63",  f"{mm:.8f}",       "Mean Motion — revolutions per day"),
        ("Col 64–68",  l2[63:67].strip(), "Revolution number at epoch"),
        ("Col 69",     l2[68],            "Checksum digit"),
    ]

    for col, val, desc in fields_l2:
        print(f"  {DIM}{col:12s}{RST}  {Y}{val:18s}{RST}  {W}{desc}{RST}")

    # ── Derived quantities ────────────────────────────────────────────────────
    section("Derived Orbital Parameters")

    period_min = 1440.0 / mm
    mu_km3s2   = 398600.4418             # Earth's gravitational parameter km³/s²
    a_km       = (mu_km3s2 / (2 * math.pi * mm / 86400)**2) ** (1/3)
    Re_km      = 6378.137
    alt_km     = a_km - Re_km

    print(f"  {'Mean motion':30s}  {G}{mm:.8f} rev/day{RST}")
    print(f"  {'Orbital period':30s}  {G}{period_min:.2f} min  ({period_min/60:.2f} h){RST}")
    print(f"  {'Semi-major axis':30s}  {G}{a_km:.2f} km{RST}")
    print(f"  {'Approximate altitude':30s}  {G}{alt_km:.2f} km{RST}")
    print(f"  {'Inclination':30s}  {G}{inc:.4f}°{RST}")
    print(f"  {'Eccentricity':30s}  {G}{ecc:.7f}{RST}")
    print()
    print(f"  {DIM}Note: ISS orbits at ~410 km altitude with period ~92 min.{RST}")


# ════════════════════════════════════════════════════════════════════════════════
#  PART 2 — SGP4 PROPAGATION
# ════════════════════════════════════════════════════════════════════════════════
def demonstrate_sgp4():
    header("PART 2 — SGP4 Propagation (ECI Position & Velocity)")

    print(f"""
{W}SGP4 (Simplified General Perturbations 4) is the standard algorithm{RST}
{W}for propagating TLE orbital elements forward in time. It accounts{RST}
{W}for atmospheric drag, Earth's oblateness (J2 perturbation), and{RST}
{W}solar radiation pressure effects.{RST}

{W}Output: position in the ECI (Earth-Centred Inertial) frame (km){RST}
{W}        velocity in ECI frame (km/s){RST}
""")

    ts   = load.timescale()
    now  = datetime.now(timezone.utc)

    section("Computing ECI State Vectors for All Satellites")
    print(f"  {DIM}Epoch: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC{RST}")
    print()

    print(f"  {BLD}{'Satellite':<22} {'X (km)':>12} {'Y (km)':>12} {'Z (km)':>12} {'|V| (km/s)':>11} {'Alt (km)':>9}{RST}")
    hr(" ", 70)

    for name, (l1, l2) in SATELLITES.items():
        sat   = EarthSatellite(l1, l2, name, ts)
        t     = ts.from_datetime(now)
        geo   = sat.at(t)
        pos   = geo.position.km
        vel   = geo.velocity.km_per_s
        v_mag = math.sqrt(sum(v**2 for v in vel))
        subp  = wgs84.subpoint_of(geo)
        alt   = subp.elevation.km

        print(f"  {M}{name:<22}{RST} "
              f"{Y}{pos[0]:>12.1f}{RST} "
              f"{Y}{pos[1]:>12.1f}{RST} "
              f"{Y}{pos[2]:>12.1f}{RST} "
              f"{G}{v_mag:>11.4f}{RST} "
              f"{C}{alt:>9.1f}{RST}")

    section("Detailed State Vector — ISS")

    l1, l2 = SATELLITES["ISS (ZARYA)"]
    sat     = EarthSatellite(l1, l2, "ISS", ts)

    offsets = [0, 10, 20, 30, 45, 60, 90]
    print(f"  {DIM}Propagating ISS position at T+0 to T+90 minutes from now{RST}")
    print()
    print(f"  {BLD}{'T+ (min)':>8} {'X (km)':>12} {'Y (km)':>12} {'Z (km)':>12} {'Lat (°)':>8} {'Lon (°)':>9} {'Alt (km)':>9}{RST}")
    hr(" ", 70)

    for dt_min in offsets:
        t_future = ts.from_datetime(now + timedelta(minutes=dt_min))
        geo      = sat.at(t_future)
        pos      = geo.position.km
        subp     = wgs84.subpoint_of(geo)
        lat      = subp.latitude.degrees
        lon      = subp.longitude.degrees
        alt      = subp.elevation.km
        print(f"  {DIM}{dt_min:>8}{RST} "
              f"{Y}{pos[0]:>12.1f}{RST} "
              f"{Y}{pos[1]:>12.1f}{RST} "
              f"{Y}{pos[2]:>12.1f}{RST} "
              f"{G}{lat:>8.2f}{RST} "
              f"{G}{lon:>9.2f}{RST} "
              f"{C}{alt:>9.1f}{RST}")


# ════════════════════════════════════════════════════════════════════════════════
#  PART 3 — ECI → ECEF → AZIMUTH / ELEVATION CONVERSION
# ════════════════════════════════════════════════════════════════════════════════
def demonstrate_az_el_conversion():
    header("PART 3 — ECI → ECEF → Topocentric AZ / EL for MSAR Observer")

    print(f"""
{W}The MSAR system needs azimuth (AZ) and elevation (EL) angles to{RST}
{W}point the antenna. These are computed in the SEZ (South-East-Zenith){RST}
{W}topocentric frame centred on the observer's location.{RST}

{W}Pipeline:{RST}
  {DIM}TLE + SGP4{RST} → {Y}ECI (X,Y,Z km){RST} → {G}ECEF (X,Y,Z km){RST} → {C}SEZ (AZ°, EL°, Range km){RST}

{W}MSAR Observer:{RST}
  {G}Latitude : {OBS_LAT}° N{RST}
  {G}Longitude: {OBS_LON}° E{RST}
  {G}Altitude : {OBS_ALT} km{RST}
""")

    ts       = load.timescale()
    now      = datetime.now(timezone.utc)
    observer = wgs84.latlon(latitude_degrees=OBS_LAT,
                            longitude_degrees=OBS_LON,
                            elevation_m=OBS_ALT * 1000)

    section("Current AZ / EL for All Satellites")
    print(f"  {DIM}Time: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC{RST}")
    print()
    print(f"  {BLD}{'Satellite':<22} {'AZ (°)':>8} {'EL (°)':>8} {'Range (km)':>12} {'Visible?':>10}{RST}")
    hr(" ", 70)

    for name, (l1, l2) in SATELLITES.items():
        sat  = EarthSatellite(l1, l2, name, ts)
        t    = ts.from_datetime(now)
        diff = sat - observer
        alt_obj, az_obj, dist = diff.at(t).altaz()
        el   = alt_obj.degrees
        az   = az_obj.degrees
        rng  = dist.km
        vis  = el > 0

        vis_str  = f"{G}YES ✓{RST}" if vis else f"{R}NO{RST}"
        el_color = G if vis else R
        print(f"  {M}{name:<22}{RST} "
              f"{Y}{az:>8.2f}{RST} "
              f"{el_color}{el:>8.2f}{RST} "
              f"{C}{rng:>12.1f}{RST} "
              f"  {vis_str}")

    section("Detailed AZ / EL Timeline — ISS (next 90 minutes, every 10 min)")

    l1, l2 = SATELLITES["ISS (ZARYA)"]
    sat     = EarthSatellite(l1, l2, "ISS", ts)

    print(f"  {BLD}{'UTC Time':>22} {'AZ (°)':>8} {'EL (°)':>8} {'Range (km)':>12} {'Visible?':>10} {'Motor action':>20}{RST}")
    hr(" ", 70)

    prev_az = None
    for dt_min in range(0, 91, 10):
        t_future = ts.from_datetime(now + timedelta(minutes=dt_min))
        diff     = sat - observer
        alt_obj, az_obj, dist = diff.at(t_future).altaz()
        el       = alt_obj.degrees
        az       = az_obj.degrees
        rng      = dist.km
        vis      = el > 0
        t_str    = (now + timedelta(minutes=dt_min)).strftime("%Y-%m-%d %H:%M")

        if prev_az is not None and vis:
            d_az = az - prev_az
            if d_az >  180: d_az -= 360
            if d_az < -180: d_az += 360
            action = f"ΔAZ={d_az:+.1f}°"
        else:
            action = "—"

        vis_str  = f"{G}YES ✓{RST}" if vis else f"{R}NO{RST}"
        el_color = G if vis else R

        print(f"  {DIM}{t_str:>22}{RST} "
              f"{Y}{az:>8.2f}{RST} "
              f"{el_color}{el:>8.2f}{RST} "
              f"{C}{rng:>12.1f}{RST} "
              f"  {vis_str:<14}"
              f"  {DIM}{action}{RST}")
        prev_az = az


# ════════════════════════════════════════════════════════════════════════════════
#  PART 4 — PASS PREDICTION
# ════════════════════════════════════════════════════════════════════════════════
def predict_passes():
    header("PART 4 — Next Pass Prediction for MSAR Location")

    print(f"""
{W}For the MSAR system to autonomously track a satellite, it must{RST}
{W}know WHEN a satellite rises above the horizon (EL > 0°) and{RST}
{W}WHERE it will appear (AZ at rise, max EL, AZ at set).{RST}

{W}The pass predictor scans forward in time and detects transitions{RST}
{W}from EL < 0 to EL > 0. It reports the AOS (Acquisition of Signal){RST}
{W}maximum elevation, and LOS (Loss of Signal) times.{RST}
""")

    ts       = load.timescale()
    now      = datetime.now(timezone.utc)
    observer = wgs84.latlon(latitude_degrees=OBS_LAT,
                            longitude_degrees=OBS_LON,
                            elevation_m=OBS_ALT * 1000)

    section("Next Pass for Each Satellite (scanning next 24 hours)")

    for name, (l1, l2) in SATELLITES.items():
        sat    = EarthSatellite(l1, l2, name, ts)
        t0     = ts.from_datetime(now)
        t1     = ts.from_datetime(now + timedelta(hours=24))

        try:
            times, events = sat.find_events(observer, t0, t1, altitude_degrees=0.0)
        except Exception as e:
            print(f"  {R}{name}: pass prediction error — {e}{RST}")
            continue

        # events: 0=AOS, 1=Culmination, 2=LOS
        passes = []
        i = 0
        while i < len(events) - 1:
            if events[i] == 0:
                aos_t  = times[i]
                culm_i = None
                los_t  = None
                j = i + 1
                while j < len(events):
                    if events[j] == 1:
                        culm_i = j
                    if events[j] == 2:
                        los_t = times[j]
                        break
                    j += 1
                if los_t is not None:
                    # Compute AZ/EL at AOS
                    d_aos  = (sat - observer).at(aos_t)
                    el_aos, az_aos, _ = d_aos.altaz()
                    # Compute max EL at culmination
                    if culm_i is not None:
                        d_culm = (sat - observer).at(times[culm_i])
                        el_max, az_max, _ = d_culm.altaz()
                    else:
                        el_max, az_max = el_aos, az_aos
                    # Compute AZ/EL at LOS
                    d_los  = (sat - observer).at(los_t)
                    el_los, az_los, _ = d_los.altaz()

                    duration_min = (los_t.tt - aos_t.tt) * 1440.0
                    passes.append({
                        "aos_utc":   aos_t.utc_datetime(),
                        "los_utc":   los_t.utc_datetime(),
                        "duration":  duration_min,
                        "az_aos":    az_aos.degrees,
                        "el_max":    el_max.degrees,
                        "az_los":    az_los.degrees,
                    })
            i += 1  # Ensures loop continues if condition isnt met or completes iteration

        if not passes:
            print(f"  {M}{name:<22}{RST}  {R}No visible pass in next 24 hours{RST}")
            continue

        p = passes[0]
        quality = "HIGH" if p["el_max"] > 40 else "MED" if p["el_max"] > 15 else "LOW"
        q_color = G if quality == "HIGH" else Y if quality == "MED" else R
        aos_str = p["aos_utc"].strftime("%H:%M:%S UTC")
        los_str = p["los_utc"].strftime("%H:%M:%S UTC")

        print(f"  {M}{BLD}{name}{RST}")
        print(f"    AOS : {G}{aos_str}{RST}   AZ = {Y}{p['az_aos']:>6.1f}°{RST}")
        print(f"    MAX : {C}EL = {p['el_max']:>5.1f}°{RST}   Quality = {q_color}{quality}{RST}")
        print(f"    LOS : {G}{los_str}{RST}   AZ = {Y}{p['az_los']:>6.1f}°{RST}")
        print(f"    Dur : {DIM}{p['duration']:.1f} min{RST}")
        print()


# ════════════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════════════
def main():
    print()
    print(f"{BLD}{C}{'=' * 70}{RST}")
    print(f"{BLD}{W}   MSAR — TLE Dataset Demonstration{RST}")
    print(f"{DIM}   Group 10 · KDU COE12992 · Mini Satellite Antenna Rotator{RST}")
    print(f"{BLD}{C}{'=' * 70}{RST}")
    print()
    print(f"  {W}This script demonstrates:{RST}")
    print(f"  {G}  1.{RST} TLE structure and field parsing")
    print(f"  {G}  2.{RST} SGP4 propagation → ECI position & velocity")
    print(f"  {G}  3.{RST} ECI → ECEF → Topocentric AZ/EL conversion")
    print(f"  {G}  4.{RST} Pass prediction for the next 24 hours")

    explain_tle_structure()
    demonstrate_sgp4()
    demonstrate_az_el_conversion()
    predict_passes()

    print()
    hr("═", 70, C)
    print(f"{BLD}{G}  Demo complete. All computations used live SGP4 propagation.{RST}")
    hr("═", 70, C)
    print()

if __name__ == "__main__":
    main()
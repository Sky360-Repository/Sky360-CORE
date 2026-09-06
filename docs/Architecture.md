# s360-core-node Architecture
Sky360 Project - Core Node Specification

## 1. Overview

`s360-core-node` is the **central node** in the Sky360 system.

Its purpose is to:
- Acquire **ADS-B aircraft data**
- Acquire **GNSS satellite and timing data**
- Maintain **astral and aircraft catalogues**
- Provide **time alignment** across all nodes
- Publish structured protobuf messages over **eCAL**
- Act as the authoritative **time source** for the entire Sky360 cluster


## 2. High-Level Architecture

```
s360-core-node
 +-- orchestrator/
 |     +-- main orchestrator loop
 |     +-- module lifecycle mgmt
 |     +-- eCAL publishers/subscribers
 |     +-- time alignment + monotonic clock
 |
 +-- adsb/
 |     +-- rtl-sdr v4 receiver
 |     +-- ADS-B decoder
 |     +-- pb.sky.AdsbMessage publisher
 |
 +-- satellite/
 |     +-- NEO-M8T NMEA parser
 |     +-- pb.sky.GpsLog publisher
 |     +-- satellite unit-vector generator
 |
 +-- catalogues/
       +-- astral catalogue downloader (periodic)
       +-- aircraft catalogue downloader (periodic)
       +-- catalogue parser + index
       +-- pb.sky.CatalogueEntry publisher
```

## 3. Component Responsibilities

### **Orchestrator**
- Starts/stops modules
- Maintains monotonic clock
- Aligns GNSS epoch time with system time
- Publishes heartbeat/status
- Routes data between modules
- Publishes unified events (optional)

### **ADS-B Module**
- Interfaces with RTL-SDR v4
- Decodes Mode-S / ADS-B frames
- Computes azimuth/elevation/range
- Publishes `pb.sky.AdsbMessage`

### **Satellite Module**
- Parses NEO-M8T NMEA messages
- Publishes `pb.sky.GpsLog`
- Computes satellite unit vectors
- Provides GNSS timing to orchestrator

### **Catalogue Module**
- Downloads astral catalogue (periodic)
- Downloads aircraft registry (periodic)
- Parses and indexes catalogue entries
- Publishes `pb.sky.AstralCatalogueEntry` and `pb.sky.AircraftCatalogueEntry`


# 4. Interfaces

Below are the formal interface definitions for **data flow**, **processing stages**, **inputs**, **outputs**, and **eCAL topics**.


## 4.1 DATA FLOW & ARCHITECTURE

| Component | Direction | Data Type | Topic | Description |
|----------|-----------|-----------|--------|-------------|
| ADS-B Module | Out | `pb.sky.AdsbMessage` | `sky360/adsb` | Aircraft position, velocity, metadata |
| Satellite Module | Out | `pb.sky.GpsLog` | `sky360/gps` | GNSS positioning, DOP, satellites in view |
| Satellite Module | Out | `TimingMessage` | `sky360/timing` | PPS lock, GNSS epoch, monotonic alignment |
| Catalogue Module | Out | `AstralCatalogue` | `sky360/catalogue/astral` | Star/planet catalogue entries |
| Catalogue Module | Out | `AircraftCatalogue` | `sky360/catalogue/aircraft` | ICAO aircraft registry |
| Orchestrator | Out | `OrchestratorStatus` | `sky360/core/status` | Node health, module status |
| Orchestrator | In | `GpsLog` | `sky360/gps` | GNSS time alignment |
| Orchestrator | In | `TimingMessage` | `sky360/timing` | PPS lock + epoch time |

## 4.2 PROCESSING STAGES

| Stage | Process | Input | Output | Configurable | Notes |
|-------|---------|--------|---------|--------------|-------|
| ADS-B Acquisition | RTL-SDR capture | IQ samples | Raw ADS-B frames | Gain, frequency | Uses dump1090-like decoder |
| ADS-B Decode | Mode-S decode | Raw frames | `AdsbMessage` | None | Includes az/el/range |
| GNSS Parsing | NMEA parsing | UART stream | `GpsLog` | Baud rate | Supports GGA, GSA, GSV |
| Catalogue Download | HTTP fetch | URL | JSON/CSV | Update interval | Astral + aircraft |
| Catalogue Parse | Parser | JSON/CSV | Catalogue entries | None | Indexed by name/ICAO |
| Orchestrator | Routing | All modules | eCAL messages | None | Heartbeat + lifecycle |

## 4.3 INPUT FIELDS (from sensors)

### **ADS-B Input Fields**

| Field Name | Proto Type | Required | Default | Range/Values | Description |
|------------|------------|----------|---------|--------------|-------------|
| raw_line | string | Yes | - | ASCII | Raw ADS-B frame |
| hex | string | Yes | - | Hex | Hex payload |
| df | int32 | Yes | - | 0-31 | Downlink Format |
| icao | string | Yes | - | Hex | ICAO aircraft ID |
| altitude_m | double | Yes | - | meters | Barometric altitude |
| latitude | double | Yes | - | -90..90 | Position |
| longitude | double | Yes | - | -180..180 | Position |
| azimuth_deg | double | Yes | - | 0..360 | Bearing |
| elevation_deg | double | Yes | - | -90..90 | Elevation angle |
| range_m | double | Yes | - | meters | Slant range |
| epoch_time | Timestamp | Yes | - | GNSS time | Sensor timestamp |
| mono_time | Timestamp | Yes | - | Monotonic | Local timestamp |

### **Satellite Input Fields**

| Field Name | Proto Type | Required | Default | Range/Values | Description |
|------------|------------|----------|---------|--------------|-------------|
| utc_time | string | Yes | - | HHMMSS | GNSS UTC time |
| latitude | double | Yes | - | -90..90 | GNSS latitude |
| longitude | double | Yes | - | -180..180 | GNSS longitude |
| satellites_used | int32 | Yes | - | 0-32 | GNSS satellites |
| hdop | double | Yes | - | 0-99 | Horizontal dilution |
| altitude | double | Yes | - | meters | GNSS altitude |
| epoch_time | Timestamp | Yes | - | GNSS time | Sensor timestamp |
| mono_time | Timestamp | Yes | - | Monotonic | Local timestamp |

## 4.4 OUTPUT FIELDS (published messages)

### **AdsbMessage Output**

| Field | Type | Description |
|-------|------|-------------|
| header | Header | Common metadata |
| data | repeated Adsb_data | List of ADS-B frames |

### **GpsLog Output**

| Field | Type | Description |
|-------|------|-------------|
| header | Header | Common metadata |
| data | GpsData | GNSS positioning or satellite info |

### **TimingMessage Output**

| Field | Type | Description |
|-------|------|-------------|
| gnss_time | Timestamp | GNSS epoch |
| mono_time | Timestamp | Local monotonic |
| pps_count | uint64 | PPS pulse index |
| fix_quality | int32 | GNSS fix |
| satellites_used | int32 | Count |
| time_offset_ns | int64 | GNSS vs monotonic offset |
| pps_locked | bool | PPS lock state |

### **Catalogue Outputs**

| Message | Description |
|---------|-------------|
| AstralCatalogue | Star/planet catalogue |
| AircraftCatalogue | ICAO aircraft registry |

# 5. eCAL TOPIC DEFINITIONS

| Topic Name | Direction | Message Type | Description |
|------------|-----------|--------------|-------------|
| `sky360/adsb` | Out | `pb.sky.AdsbMessage` | ADS-B aircraft data |
| `sky360/gps` | Out | `pb.sky.GpsLog` | GNSS positioning |
| `sky360/timing` | Out | `TimingMessage` | PPS + GNSS time |
| `sky360/catalogue/astral` | Out | `AstralCatalogue` | Astral catalogue |
| `sky360/catalogue/aircraft` | Out | `AircraftCatalogue` | Aircraft registry |
| `sky360/core/status` | Out | `OrchestratorStatus` | Node health |
| `sky360/core/heartbeat` | Out | `OrchestratorStatus` | 1 Hz heartbeat |
| `sky360/core/control` | In | `ControlMessage` (optional) | Remote control |


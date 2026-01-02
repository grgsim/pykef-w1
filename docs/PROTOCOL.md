# KEF Wireless Speaker Protocol Reference

## Supported Speakers

This protocol applies to KEF's first-generation wireless speaker platform:

- **KEF LS50 Wireless** (original, not LS50 Wireless II)
- **KEF LSX** (original, not LSX II)

Both speakers share the same TCP protocol. Some features are LSX-specific and are marked accordingly.

## Table of Contents

- [Introduction](#introduction)
- [Connection](#connection)
- [TCP Protocol](#tcp-protocol-port-50001)
  - [Command Format](#command-format)
  - [Response Format](#response-format)
- [Command Reference](#command-reference)
  - [Device Information](#device-information)
  - [Volume](#volume-0x25)
  - [Balance](#balance-0x26)
  - [Volume Limit](#volume-limit-0x3d)
  - [Source & Power](#source--power-0x30)
  - [Playback Control](#playback-control-0x31)
  - [Cable Mode](#cable-mode-0x41) *(LSX only)*
  - [WiFi Signal](#wifi-signal-0x2f)
  - [EQ Mode](#eq-mode-0x27)
  - [EQ Settings](#eq-settings-0x28---0x2d)
  - [LSX UI Controls](#lsx-ui-controls-0x43) *(LSX only)*
- [Unverified Commands](#unverified-commands)
- [UPnP/DLNA](#upnpdlna-port-8080)

---

## Introduction

The KEF LS50 Wireless and LSX are pairs of wireless active speakers. The primary speaker (right by default) acts as the controller, handling all network communication and forwarding audio to the secondary speaker via a wireless or wired connection.

This document describes the binary TCP protocol used by the KEF Control mobile app to communicate with the speakers. It covers device configuration, audio settings, playback control, and EQ adjustments.

The protocol was tested on KEF LSX speakers running firmware version 5.2.

---

## Connection

| Protocol | Port | Purpose |
|----------|------|---------|
| TCP | 50001 | Binary protocol for speaker control |
| HTTP | 8080 | UPnP/DLNA for track metadata |

**Important:** The TCP connection is exclusive. Only one client can connect at a time. If the KEF Control app is connected, your client will not be able to connect, and vice versa.

---

## TCP Protocol (Port 50001)

### Byte Notation

Throughout this document, byte sequences are shown in square brackets with hexadecimal values:

```
[0x47, 0x25, 0x80]
```

This represents **3 raw bytes**: `0x47` (71), `0x25` (37), `0x80` (128). Send these bytes directly over the TCP socket with no delimiters, framing, or termination characters.

### Command Format

**GET command** - Read a value:
```
[0x47, <cmd>, 0x80]
```

**SET command (single byte)** - Write a byte value:
```
[0x53, <cmd>, 0x81, <value>]
```

**SET command (string)** - Write a text string:
```
[0x53, <cmd>, <length>, <string bytes...>, 0x00]
```
Where `<length>` = (string length + 1) | 0x80. The string must be null-terminated.

### Response Format

All responses begin with `0x52` ('R').

**SET response (success):**
```
[0x52, 0x11, 0xFF]
```
Byte 1 = `0x11` indicates success.

**GET response (with data):**
```
[0x52, <cmd>, <length>, <data...>, <trailing>]
```
- Byte 1: Command byte echoed back
- Byte 2: Data length with high bit set (`length | 0x80`)
- Byte 3+: Returned data
- Trailing byte(s): See note below

**Important:** Responses include one or more trailing bytes after the documented data. These extra bytes appear in all response types but are not used by the KEF Control app and their purpose is unknown. When parsing responses, read only the documented data positions and ignore any additional bytes.

Example response for Volume (0x25):
```
[0x52, 0x25, 0x81, 0x1B, 0xB1]
  │     │     │     │     └── Trailing byte (ignore)
  │     │     │     └── Volume data: 27%, unmuted
  │     │     └── Length byte (1 | 0x80)
  │     └── Command echo
  └── Response marker
```

**Parsing GET responses:**
1. Verify byte 0 is `0x52` and byte 1 matches your command
2. Get data length: `length = response[2] & 0x7F`
3. For single-byte values: read `response[3]`
4. For strings: read bytes 3 through `3 + length - 1`, stopping at null terminator
5. Ignore any bytes beyond the declared length

---

## Command Reference

### Device Information

| Cmd | Name | Type | Response Format |
|-----|------|------|-----------------|
| 0x11 | Firmware Version | GET | XML: `<module>...</module><system>...</system><DSP>...</DSP>` |
| 0x14 | Hardware Version | GET | XML: `<Hardware>...</Hardware>` |
| 0x15 | Serial (Master) | GET | XML: `<Serial>...</Serial>` |
| 0x16 | Serial (Slave) | GET | XML with 0xFF fill bytes if not available |
| 0x20 | Device Name | GET/SET | Plain text (the friendly name shown in the app) |

---

### Volume (0x25)

Controls the speaker volume and mute state.

| Bits | Meaning |
|------|---------|
| 0-6 | Volume level (0-100) |
| 7 | Mute flag (0 = unmuted, 1 = muted) |

**Examples:**
- `0x32` (50) = Volume 50%, unmuted
- `0xB2` (178) = Volume 50%, muted (50 + 128)
- `0x00` (0) = Volume 0%, unmuted

---

### Balance (0x26)

Controls the left/right audio balance.

| Value | Position |
|-------|----------|
| 0 | Full Left |
| 30 | Center (default) |
| 60 | Full Right |

**Note:** GET returns the value with bit 7 set. SET requires bit 7 to be set. To decode: `balance = raw & 0x7F`. To encode: `raw = balance | 0x80`.

---

### Volume Limit (0x3D)

Restricts the maximum volume level. Useful for preventing accidental loud playback.

| Bits | Meaning |
|------|---------|
| 0-6 | Maximum volume (0-100) |
| 7 | Enabled flag (0 = disabled, 1 = enabled) |

**Examples:**
- `0x64` (100) = Limit at 100%, disabled (effectively no limit)
- `0xC8` (200) = Limit at 72%, enabled (72 + 128)

---

### Source & Power (0x30)

A single byte encoding the input source, auto-standby timeout, speaker orientation, and power state.

| Bits | Field |
|------|-------|
| 0-3 | Source |
| 4-5 | Standby timeout |
| 6 | Orientation |
| 7 | Power state |

#### Source (bits 0-3)

The active audio input.

| Value | Source |
|-------|--------|
| 2 | WiFi (AirPlay, DLNA, Spotify Connect) |
| 9 | Bluetooth |
| 10 | Aux (3.5mm input) |
| 11 | Optical (TOSLINK) |
| 12 | PC (USB audio) |

#### Standby Timeout (bits 4-5)

How long the speaker waits without audio before entering standby mode.

| Value | Bits | Timeout |
|-------|------|---------|
| 0 | 00 | 20 minutes |
| 1 | 01 | 60 minutes |
| 2 | 10 | Never (always on) |

#### Orientation (bit 6)

Physical speaker placement. The system has a primary speaker (with all the inputs) and a secondary speaker. By default, the primary speaker is placed on the right.

| Value | Placement |
|-------|-----------|
| 0 | Normal - Primary speaker on the RIGHT |
| 1 | Inverted - Primary speaker on the LEFT |

When inverted, the speakers swap their stereo channels internally so the soundstage remains correct.

#### Power (bit 7)

| Value | State |
|-------|-------|
| 0 | ON |
| 1 | OFF (standby) |

**Note:** Power state changes take a few seconds to complete. After sending a power command, wait before sending additional commands.

**Example values:**
- `0x02` = WiFi, 20min standby, Normal, Power ON
- `0x12` = WiFi, 60min standby, Normal, Power ON
- `0x42` = WiFi, 20min standby, Inverted, Power ON
- `0x82` = WiFi, 20min standby, Normal, Power OFF

---

### Playback Control (0x31)

Controls media playback for streaming sources (WiFi, Bluetooth).

#### SET Commands

| Value | Action |
|-------|--------|
| 0x80 (128) | Pause |
| 0x81 (129) | Play / Resume |
| 0x82 (130) | Next track |
| 0x83 (131) | Previous track (or restart current track) |

#### GET Response (current state)

| Value | State |
|-------|-------|
| 0x81 (129) | Playing |
| 0x84 (132) | Stopped or Paused |

**Notes:**
- The protocol does not distinguish between "stopped" and "paused" - both return 0x84
- State updates may be delayed by several seconds after playback changes
- On Bluetooth, GET returns `[0x52, 0x12, 0xFF]` (state not available), but SET commands still work

---

### Cable Mode (0x41)

> **LSX only.** Not available on LS50 Wireless.

Controls how the primary and secondary speakers communicate with each other.

| Value | Mode | Description |
|-------|------|-------------|
| 1 | Wired | Speakers connected via the inter-speaker cable |
| 129 | Wireless | Speakers communicate over WiFi |

The wired connection provides lower latency and higher reliability.

---

### WiFi Signal (0x2F)

GET only. Reports the WiFi connection status of the speaker.

| Value | Meaning |
|-------|---------|
| 0xFF (255) | Not connected (wired mode or disconnected) |
| 0x83 (131) | Connected via WiFi |

**Note:** This appears to be a binary indicator rather than a signal strength meter.

---

### EQ Mode (0x27)

Bit field controlling the speaker's EQ mode settings (desk mode, wall mode, phase correction, etc.).

| Bit | Feature | 0 | 1 |
|-----|---------|---|---|
| 0 | Desk Mode | Off | On |
| 1 | Wall Mode | Off | On |
| 2 | Phase Correction | Off | On |
| 3 | High Pass | Off | On |
| 4-5 | Bass Extension | (see below) | |
| 6 | Sub Polarity | Normal (+) | Inverted (-) |
| 7 | SET flag | - | Required for SET |

**Desk Mode:** Compensates for acoustic reflections when speakers are placed on a desk surface.

**Wall Mode:** Compensates for bass boost when speakers are placed near a wall.

**Phase Correction:** Adjusts phase alignment between drivers.

**High Pass:** Enables the high-pass filter (frequency set by command 0x2B). Use when pairing with a subwoofer.

**Bass Extension values (bits 4-5):**
| Value | Mode |
|-------|------|
| 0 | Standard |
| 1 | Extra (more bass) |
| 2 | Less (reduced bass) |

**Sub Polarity:** Phase of the subwoofer output. Invert if the sub sounds thin or cancels bass.

---

### EQ Settings (0x28 - 0x2D)

Equalizer values use an index-based encoding with an XOR mask.

**Decoding (GET):**
```
index = raw_byte XOR 0x80
display_value = minimum + (step × index)
```

**Encoding (SET):**
```
index = (display_value - minimum) / step
raw_byte = index XOR 0x80
```

#### EQ Parameters

| Cmd | Name | Min | Max | Step | Unit |
|-----|------|-----|-----|------|------|
| 0x28 | Desk dB | -6.0 | 0.0 | 0.5 | dB |
| 0x29 | Wall dB | -6.0 | 0.0 | 0.5 | dB |
| 0x2A | Treble | -2.0 | +2.0 | 0.5 | dB |
| 0x2B | High Pass | 50 | 120 | 5 | Hz |
| 0x2C | Sub Out LP | 40 | 250 | 5 | Hz |
| 0x2D | Sub Gain | -10 | +10 | 1 | dB |

**Desk/Wall dB:** Attenuation applied when Desk/Wall mode is enabled.

**Treble:** High frequency adjustment.

**High Pass:** Cutoff frequency for the high-pass filter (removes bass below this frequency). Only active when High Pass is enabled in EQ Mode.

**Sub Out LP:** Low-pass filter frequency for the subwoofer output.

**Sub Gain:** Volume adjustment for the subwoofer output.

#### Decoding Example

Speaker returns `0x8A` (138) for Desk dB:
```
index = 138 XOR 128 = 10
value = -6.0 + (0.5 × 10) = -1.0 dB
```

#### Encoding Example

Set Treble to +1.0 dB:
```
index = (+1.0 - (-2.0)) / 0.5 = 3.0 / 0.5 = 6
raw = 6 XOR 128 = 134 (0x86)
```
Send: `[0x53, 0x2A, 0x81, 0x86]`

---

### LSX UI Controls (0x43)

> **LSX only.** Not available on LS50 Wireless.

Controls LED behavior and startup sound.

**Important: All bits use inverted logic (active low).**

| Bit | Feature | 0 | 1 |
|-----|---------|---|---|
| 0 | Source LED | ON | OFF |
| 1 | Standby LED | ON | OFF |
| 6 | Startup Tone | ON | OFF |
| 7 | SET flag | - | Required for SET |

**Source LED:** When disabled, the source LED will slowly fade and then turn off until the next source change.

**Standby LED:** Turn off to disable the LEDs during standby mode.

**Startup Tone:** Turn off to disable the startup tone.

**Example values:**
- `0x80` = All features ON (bits 0, 1, 6 are 0)
- `0x83` = Source LED OFF, Standby LED OFF, Startup Tone ON
- `0xC3` = Source LED OFF, Standby LED OFF, Startup Tone OFF

---

## Unverified Commands

The following commands were discovered but not fully tested. Use with caution.

| Cmd | Name | Type | Notes |
|-----|------|------|-------|
| 0x21 | WiFi SSID | SET | Network name for WiFi setup |
| 0x22 | WiFi Security | SET | Security type (e.g., WPA2) |
| 0x23 | WiFi Cipher | SET | Encryption cipher |
| 0x24 | WiFi Password | SET | Network password |
| 0x2E | Network List | GET | Triggers WiFi network scan |
| 0x3E | Update Status | GET | Firmware update state |
| 0x3F | Update Percentage | GET | Update progress (0-100) |
| 0x40 | Country Version | GET/SET | Region code |
| 0x52 | Reset Speaker | SET | Format: `[0x52, 0x20, 0x80]` |

**Warning:**
- WiFi commands (0x21-0x24) will modify network configuration
- Reset (0x52) may factory reset the speaker and require physical re-setup

---

## UPnP/DLNA (Port 8080)

> **Note:** This section is for reference only. The library does not implement UPnP/DLNA - use a dedicated library like [async-upnp-client](https://github.com/StevenLooman/async_upnp_client) if needed.

The speaker exposes a standard UPnP MediaRenderer for track metadata and transport control.

**Device description:** `http://<IP>:8080/description.xml`

### Available Services

| Service | Control URL | Purpose |
|---------|-------------|---------|
| AVTransport | /AVTransport/ctrl | Track info, play/pause |
| RenderingControl | /RenderingControl/ctrl | Volume control |

### Getting Track Information

Use the `GetPositionInfo` SOAP action on AVTransport.

**SOAP Action:** `urn:schemas-upnp-org:service:AVTransport:1#GetPositionInfo`

**Available fields:**
- Title, Artist, Album
- AlbumArtURI (cover image URL)
- Duration, RelTime (current position)
- TrackURI
- TransportState: `PLAYING`, `PAUSED_PLAYBACK`, `STOPPED`, `NO_MEDIA_PRESENT`

---

*Protocol documented December 2025. Tested on KEF LSX firmware 5.2.*

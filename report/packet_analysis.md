# Module 1 Assignment — Packet Analysis
## Task 4: Wire-Level Protocol Annotation

---

## 4.2 MQTT Packet Annotations

### CONNECT Packet

| Field | Offset (bytes) | Raw Hex | Decoded Value |
|-------|---------------|---------|---------------|
| Frame type + flags (byte 1) | 0 | `10` | Type=CONNECT (1), flags=0 |
| Remaining length (byte 2) | 1 | `2B` | 43 bytes |
| Protocol name length | 2–3 | `00 04` | 4 |
| Protocol name | 4–7 | `4D 51 54 54` | "MQTT" |
| Protocol version | 8 | `04` | 4 (MQTT 3.1.1) |
| Connect flags | 9 | `2E` | See breakdown below |
| Keep-alive | 10–11 | `00 3C` | 60 seconds |
| Client ID length | 12–13 | `00 1A` | 26 |
| Client ID | 14–… | `73 6D ...` | "smartfactory-publisher-001" |

**Connect Flags byte breakdown:**

| Bit | Name | Value | Meaning |
|-----|------|-------|---------|
| 7 | Username flag | 0 | False |
| 6 | Password flag | 0 | False |
| 5 | Will retain | 1 | True |
| 4–3 | Will QoS | 01 | QoS 1 |
| 2 | Will flag | 1 | True |
| 1 | Clean session | 0 | False (Persistent) |
| 0 | Reserved | 0 | — |

---

### QoS 1 PUBLISH Packet

| Field | Offset (bytes) | Raw Hex | Decoded Value |
|-------|---------------|---------|---------------|
| Fixed header byte 1 | 0 | `32` | Type=PUBLISH(3), DUP=0, QoS=1, RETAIN=0 |
| Remaining length | 1 | `5E` | 94 bytes |
| Topic length | 2–3 | `00 19` | 25 |
| Topic string | 4–… | `66 61 ...` | "factory/line1/temperature" |
| Packet Identifier | … | `00 01` | 1 |
| Payload | … | `7B 22 ...` | '{"value": 70.123, "unit": "C"}' |

**Fixed header byte 1 bit expansion:**

| Bits 7–4 (packet type) | Bit 3 (DUP) | Bits 2–1 (QoS) | Bit 0 (RETAIN) |
|------------------------|-------------|----------------|----------------|
| `0011` = PUBLISH (3)  | `0` = False | `01` = QoS 1 | `0` = False |

---

### PUBACK Packet

| Field | Offset | Raw Hex | Decoded Value |
|-------|--------|---------|---------------|
| Fixed header | 0 | `40` | Type=PUBACK (01000000) |
| Remaining length | 1 | `02` | 2 bytes |
| Packet Identifier | 2–3 | `00 01` | 1 |

**Packet Identifier match:** PUBLISH PKT ID = 1 ; PUBACK PKT ID = 1 ; **Match? Yes**

---

## 4.3 CoAP Packet Annotations

### CON GET Request

```
Bytes: 44 01 AD 13  B1 4F AB E1  B7 ...
       [   Header   ] [  Token  ] [Options...]
```

| Field | Bits/Bytes | Raw Value | Decoded Value |
|-------|-----------|-----------|---------------|
| Version (bits 7–6) | 2 bits | `01` | 1 (always 1) |
| Type (bits 5–4) | 2 bits | `00` | 0 = CON |
| TKL (bits 3–0) | 4 bits | `04` | Token length = 4 |
| Code (byte 1) | 8 bits | `01` | 0.01 = GET |
| Message ID (bytes 2–3) | 16 bits | `AD 13` | 44307 |
| Token (bytes 4–TKL+3) | TKL bytes | `B1 4F ...` | 0xB14FABE1 |
| Option Delta | 4 bits | `B` | Delta = 11, Option# = 11 (Uri-Path) |
| Option Length | 4 bits | `7` | 7 |
| Option Value | 7 bytes | `66 61 ...` | "factory" (Uri-Path) |

**Byte 0 full expansion:**

| Bit 7 | Bit 6 | Bit 5 | Bit 4 | Bit 3 | Bit 2 | Bit 1 | Bit 0 |
|-------|-------|-------|-------|-------|-------|-------|-------|
| Ver   | Ver   | T     | T     | TKL   | TKL   | TKL   | TKL   |
| `0`   | `1`   | `0`   | `0`   | `0`   | `1`   | `0`   | `0`   |

---

### ACK 2.05 Content Response

| Field | Bytes | Raw Hex | Decoded Value |
|-------|-------|---------|---------------|
| Fixed header byte 0 | 0 | `64` | Ver=01, T=10 (ACK), TKL=4 |
| Code byte 1 | 1 | `45` | 2.05 = Content |
| Message ID | 2–3 | `AD 13` | 44307 (matches request? Yes) |
| Token | 4–… | `B1 4F ...` | 0xB14FABE1 (matches request? Yes) |
| Option: Content-Format | … | `11 32` | Option# = 12, Value = 50 (app/json) |
| Payload Marker | … | `FF` | 0xFF |
| Payload | … | `7B 22 ...` | '{"value": 70.1, "unit": "C"}' |

---

### Observe Notification

| Field | Value |
|-------|-------|
| Observe option number | 6 |
| Observe sequence value | 1 |
| Message type | NON (or CON) |
| Response code | 2.05 Content |

---

## 4.4 AMQP Frame Annotations

### basic.publish Method Frame

```
Bytes: 01  00 01  00 00 00 NN  [payload]  CE
       [T] [Ch] [Payload Sz] [.........] [End]
```

| Field | Bytes | Raw Hex | Decoded Value |
|-------|-------|---------|---------------|
| Frame Type | 0 | `__` | __ = Method |
| Channel | 1–2 | `__ __` | __ |
| Payload Size | 3–6 | `__ __ __ __` | ___ |
| Class ID | 7–8 | `__ __` | __ = basic (60) |
| Method ID | 9–10 | `__ __` | __ = basic.publish (40) |
| Reserved (ticket) | 11–12 | `00 00` | — |
| Exchange name length | 13 | `__` | __ |
| Exchange name | 14–… | `__ …` | "_______" |
| Routing key length | … | `__` | __ |
| Routing key | … | `__ …` | "_______" |
| Mandatory + Immediate | … | `__` | mandatory=_, immediate=_ |
| Frame End | last | `CE` | 0xCE ✓ |

---

### Content Header Frame

| Field | Bytes | Raw Hex | Decoded Value |
|-------|-------|---------|---------------|
| Frame Type | 0 | `02` | 2 = Header |
| Channel | 1–2 | `__ __` | __ |
| Payload Size | 3–6 | `__ __ __ __` | ___ |
| Class ID | 7–8 | `__ __` | 60 = basic |
| Weight | 9–10 | `00 00` | (unused) |
| Body Size | 11–18 | `__ … __` | ___ bytes |
| Property Flags | 19–20 | `__ __` | bits set: _______________ |
| delivery_mode | … | `__` | __ (1=transient, 2=persistent) |
| content_type length | … | `__` | __ |
| content_type | … | `__ …` | "_______" |
| Frame End | last | `CE` | 0xCE ✓ |

---

### Heartbeat Frame

| Field | Value |
|-------|-------|
| Frame Type | __ |
| Channel | __ |
| Payload Size | __ |
| Payload | _(empty)_ |
| Frame End | `CE` |

**Why is the Heartbeat payload empty?**

> _Your answer here (1–2 sentences)_

---

*Module 1 Assignment — Real-Time Data Analytics for IoT*

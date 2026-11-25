---
title: "How the Internet Actually Works: IP Addresses, Ports, DNS, and the TCP Handshake"
slug: how-the-internet-works-networking-basics-for-security
date: 2026-11-12
category: Cybersecurity
topic: cybersecurity
tags: [Cybersecurity, Networking, TCP/IP, DNS, Web Security, Beginners]
description: "Before you can secure or pentest a network, you must understand how data travels. A beginner-friendly breakdown of IP addresses, ports, DNS resolution, and the TCP 3-way handshake."
featured: false
type: article
---

In our introductory guide, we explored [what cybersecurity actually is](../../posts/what-is-cybersecurity-explained-simply/) and how digital defense protects data.

When beginners jump into cybersecurity or web penetration testing, they often try to jump straight to hacking tools like Nmap, Wireshark, or Burp Suite. But within ten minutes, they hit a wall of jargon:

> *"Target IP resolved on port 443 with a TCP SYN packet after DNS lookup..."*

If you don't understand how data travels across cables, routers, and Wi-Fi airwaves, security tools will feel like magic incantations rather than engineering instruments.

In this guide, we will break down the **four core pillars of networking** that every developer, cybersecurity enthusiast, and ethical hacker must understand.

---

## 1. IP Addresses: Your Device's Street Address

Every single device connected to the internet—your phone, laptop, smart TV, or a Google web server—must have a unique identifier so data packets know where to go. This is an **IP (Internet Protocol) Address**.

Think of an IP address like a **postal street address**:

```text
Physical World:   124 Maple Street, Apt 4B, Springfield
Digital World:    142.250.190.46 (An IPv4 address for Google)
```

### IPv4 vs. IPv6
* **IPv4** (The Classic): Made of 4 numbers separated by dots (e.g., `192.168.1.1`). It supports roughly **4.3 billion addresses**. Because the world ran out of IPv4 addresses, we created IPv6.
* **IPv6** (The Modern Standard): Looks like `2001:0db8:85a3:0000:0000:8a2e:0370:7334`. It supports trillions of unique addresses—enough to give every grain of sand on Earth its own IP address.

### Public vs. Private IP Addresses
* **Private IP**: Used inside your home or office local Wi-Fi network (typically starting with `192.168.x.x` or `10.x.x.x`). Devices outside your home cannot see or talk directly to your private IP.
* **Public IP**: The single external address assigned to your home router by your Internet Service Provider (ISP). All devices in your house share this public IP when browsing the web through a technique called **NAT (Network Address Translation)**.

---

## 2. Ports: The Apartment Numbers

If an IP address is a building's street address, **ports are the apartment unit numbers inside that building**.

A single computer or server has one IP address, but it runs dozens of different services simultaneously: it might host a website, receive emails, and allow remote management. How does the computer know which incoming data packet belongs to which application? **Ports.**

There are **65,535 possible ports** on every IP address. By convention, common services use standardized default ports:

| Port Number | Protocol / Service | What It Does |
|---|---|---|
| **80** | HTTP | Plaintext unencrypted web traffic |
| **443** | HTTPS | Encrypted, secure web traffic |
| **22** | SSH (Secure Shell) | Encrypted remote terminal server login |
| **53** | DNS | Domain Name System address lookups |
| **21** | FTP | File Transfer Protocol |
| **3306** | MySQL | Common database port |

```text
                 Server IP: 192.0.2.1
                 ┌────────────────────────────────┐
                 │  Port 80   ➔ Web Server (HTTP) │
Incoming Traffic │  Port 443  ➔ Web Server (HTTPS)│
 ──────────────> │  Port 22   ➔ SSH Terminal      │
                 │  Port 3306 ➔ MySQL Database    │
                 └────────────────────────────────┘
```

> **Security Takeaway**: When penetration testers perform a "port scan" using tools like Nmap, they are simply knocking on all 65,535 doors to see which ones are open and what software is listening behind them.

---

## 3. DNS: The Internet's Phonebook

Computers understand numbers like `142.250.190.46`, but humans remember names like `google.com` or `github.com`.

**DNS (Domain Name System)** translates human-readable domain names into machine-readable IP addresses.

### What Happens When You Type `google.com`?

```text
1. You type "google.com" in browser
             │
             ▼
2. Browser asks DNS Resolver: "What is the IP for google.com?"
             │
             ▼
3. DNS responds: "It lives at 142.250.190.46"
             │
             ▼
4. Browser connects directly to: 142.250.190.46:443
```

> **Security Takeaway**: If an attacker can tamper with your DNS queries (called **DNS Spoofing** or **DNS Cache Poisoning**), they can trick your computer into visiting a malicious replica website when you type your bank's real domain name!

---

## 4. The TCP 3-Way Handshake: How Connections Begin

Once your browser has the IP address and the port, it needs to establish a reliable connection with the remote server. 

Most internet traffic (web pages, file downloads, emails) relies on **TCP (Transmission Control Protocol)** because it guarantees that every packet arrives reliably and in the correct order.

Before sending any web page data, the client and server perform a synchronized dance called the **TCP 3-Way Handshake**:

```text
Client (Your Laptop)                               Server (Website)
         │                                                │
         │  1. SYN ("Hey, can we talk?")                  │
         │───────────────────────────────────────────────>│
         │                                                │
         │  2. SYN-ACK ("Yes, I hear you! Can you hear me?")
         │<───────────────────────────────────────────────│
         │                                                │
         │  3. ACK ("Loud and clear! Let's chat.")        │
         │───────────────────────────────────────────────>│
         │                                                │
         │ <======== Secure Connection Established =====> │
```

### Step-by-Step:
1. **SYN (Synchronize)**: Your computer sends a packet with the `SYN` flag set to the server, indicating it wants to establish a session.
2. **SYN-ACK (Synchronize-Acknowledge)**: If the port is open and accepting connections, the server replies with both `SYN` and `ACK` flags turned on.
3. **ACK (Acknowledge)**: Your computer sends an `ACK` packet back. The connection is now established, and HTTP/HTTPS data transfer can begin!

### What If a Port is Closed?
If you send a `SYN` packet to a closed port, the server immediately replies with an **`RST` (Reset)** packet, telling your machine: *"Nobody is listening on this port. Go away."*

> **Pentesting Insight**: This exact mechanism is how **SYN Stealth Scanning** works in Nmap (`nmap -sS`). Nmap sends a `SYN` packet; if the server replies with `SYN-ACK`, Nmap knows the port is open. Nmap then immediately tears down the connection before completing the handshake, allowing it to scan without creating a full application log entry!

---

## Summary Checklist

| Concept | Everyday Analogy | Security Relevance |
|---|---|---|
| **IP Address** | Street Address | Identifies where a target server or device is located. |
| **Port** | Apartment Number | Shows which specific services and doors are exposed. |
| **DNS** | Phonebook / Contact List | Targets can be tricked if DNS answers are manipulated. |
| **TCP Handshake** | Formal Greeting (`SYN ➔ SYN-ACK ➔ ACK`) | The foundation for network scanning and connection reliability. |

Now that you understand how devices discover each other and shake hands over the network, our next step will be inspecting the actual messages they exchange: **HTTP, HTTPS, and Web Request Headers**!

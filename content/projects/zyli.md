## Project Overview

**Zyli** (configured as the **Zoftcares HR Voice Assistant**) is a next-generation real-time conversational AI mobile application built with **Flutter**. As generative AI shifts from text-based chatbots to low-latency bidirectional voice experiences, Zyli delivers fluid, interruptible, hands-free voice interactions with an intelligent agent.

The application combines **Clean Architecture**, reactive **BLoC** state management, ultra-low-latency **WebRTC** peer connections over WebSockets, hardware-level **Acoustic Echo Cancellation (AEC)**, and a futuristic glassmorphic UI with dynamic animated canvas visualizations.

---

## Architectural Breakdown: Clean Architecture

To ensure modularity, complete testability, and resilience during real-time media streams, Zyli's codebase is decoupled into three distinct layers:

```text
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                      │
│     VoiceCallScreen · HomeScreen · LoginScreen              │
│     VoiceBloc (flutter_bloc) · Animated WavePainter & Orb    │
│     Glassmorphic Dock (BackdropFilter) · AutoScroll Physics │
└──────────────────────────────┬──────────────────────────────┘
                               │ streams events & listens to state
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                        DOMAIN LAYER                         │
│     VoiceEventEntity · VoiceRepository (contract)            │
│     StartVoiceCallUseCase · ManageAudioSettingsUseCase      │
│     EndVoiceCallUseCase · ManageApiKeyUseCase               │
│     (Pure Dart — Zero UI or hardware dependencies)          │
└──────────────────────────────▲──────────────────────────────┘
                               │ implemented by
                               │
┌─────────────────────────────────────────────────────────────┐
│                         DATA LAYER                          │
│     VoiceWebRTCClient (flutter_webrtc + WebSockets)         │
│     VoiceRemoteDataSource (REST Handshake & TURN relays)    │
│     SecureLocalDataSource (flutter_secure_storage)          │
│     AudioSessionUtils (hardware DSP & AEC configuration)    │
└─────────────────────────────────────────────────────────────┘
```

### 1. Presentation Layer (`lib/presentation/`)
* **State Management**: Built with `flutter_bloc` (`VoiceBloc`, `VoiceEvent`, `VoiceState`) to reactively stream voice states (listening, thinking, bot speaking, live transcriptions, network latency) directly to the UI without blocking the rendering thread.
* **Ambient Canvas Audio Waves**: Custom `_WavePainter` running on mathematical sine-wave equations that render slow, panning, intersecting audio waves in the background, signaling an "always-listening" ambiance.
* **Dynamic Intelligence Orb**: The centerpiece of the voice call interface. Driven by an `AnimationController` synchronized with `VoiceBloc`, the orb rests in a gentle breathing pulse while listening, expanding into an illuminated neon cyan glow when the AI speaks.
* **Frosted Glass Control Dock**: Rounded floating island dock housing call controls (Mute, Speakerphone, End Call) rendered with `BackdropFilter` glassmorphism and gaussian blur.
* **WhatsApp-Style Live Streaming Transcriptions**: Real-time speech-to-text and response streaming directly into chat bubbles. Unfinished sentences display micro-loading indicators, and smart `BouncingScrollPhysics` lock to the bottom during live speech while unlocking smoothly when users scroll up to inspect conversation history.

### 2. Domain Layer (`lib/domain/`)
* **Entities**: Core business objects like `VoiceEventEntity` mapping real-time transcript deltas, speaker status, and connection states.
* **Repositories (Contracts)**: Abstract interfaces (`VoiceRepository`, `SecureStorageRepository`) defining call lifecycle and credential operations.
* **Use Cases**: Single-responsibility domain logic:
  * `StartVoiceCallUseCase`: Initiates signaling, permissions, and media exchange.
  * `EndVoiceCallUseCase`: Tears down peer connections and releases audio focus.
  * `ManageAudioSettingsUseCase`: Toggles microphone mute and hardware speakerphone routing.
  * `ManageApiKeyUseCase`: Validates and retrieves encrypted credentials.

### 3. Data Layer (`lib/data/`)
* **VoiceWebRTCClient**: Encapsulates `RTCPeerConnection`, local media streams, ICE candidate trickling, and WebSocket signaling.
* **VoiceRemoteDataSource**: Communicates with the backend for session handshakes, auth token verification, and TURN/STUN credential provisioning.
* **SecureLocalDataSource**: Interfaces with `flutter_secure_storage` to keep API keys encrypted at rest using the Android Keystore and iOS Keychain.

---

## Tech Stack & Ecosystem

| Capability | Package & Technologies | Engineering Role |
|---|---|---|
| **Core Framework** | Flutter SDK (Dart `^3.13.5`) | Cross-platform client for high-frame-rate glassmorphic rendering |
| **Real-Time Audio** | `flutter_webrtc (^1.2.0)` | Ultra-low latency bidirectional audio streaming |
| **Hardware Audio Session** | `audio_session (^0.1.21)` | DSP hardware mode configuration for Acoustic Echo Cancellation (AEC) |
| **Signaling & Handshakes** | `web_socket_channel (^3.0.1)` + `http` | Real-time ICE trickling and session handshake communication |
| **State Management** | `flutter_bloc (^9.1.1)` + `equatable` | Reactive unidirectional state management for voice events |
| **Hardware Encryption** | `flutter_secure_storage (^9.2.2)` | Android Keystore / iOS Keychain credential security |
| **Permission Management** | `permission_handler (^11.3.1)` | Runtime microphone and audio hardware authorization |
| **Responsive Layout** | `flutter_screenutil (^5.9.3)` | Pixel-perfect UI scaling across various device resolutions |

---

## The Audio Engine: WebRTC & Hardware Echo Cancellation

Standard HTTP polling or REST streaming is inadequate for full-duplex conversational voice AI due to unacceptable latency and audio feedback. Zyli tackles this through two critical engineering choices:

1. **WebRTC Media Pipeline**: Low-latency RTP audio transport paired with persistent WebSockets for bidirectional signaling, keeping round-trip latency to sub-second conversational speeds.
2. **Hardware Acoustic Echo Cancellation (AEC)**:
   * **The Problem**: When the AI speaks through the device loudspeaker, the open microphone captures that audio and mistakenly triggers the server-side Voice Activity Detector (VAD), cutting off the AI mid-sentence.
   * **The Solution**: Through `audio_session`, the app activates the smartphone's hardware Digital Signal Processor (DSP) in `voiceCommunication` mode. The OS-level DSP subtracts speaker output from microphone input in real-time before audio packets are packetized for WebRTC.

```dart
// Configuring hardware Acoustic Echo Cancellation
final session = await AudioSession.instance;
await session.configure(const AudioSessionConfiguration(
  avAudioSessionCategory: AVAudioSessionCategory.playAndRecord,
  avAudioSessionCategoryOptions: AVAudioSessionCategoryOptions.defaultToSpeaker |
      AVAudioSessionCategoryOptions.allowBluetooth,
  avAudioSessionMode: AVAudioSessionMode.voiceChat,
  androidAudioAttributes: AndroidAudioAttributes(
    contentType: AndroidAudioContentType.speech,
    usage: AndroidAudioUsage.voiceCommunication,
  ),
  androidAudioFocusGainType: AndroidAudioFocusGainType.gainTransientMayDuck,
));
```

---

## Enterprise Security & Zero Hardcoded Secrets

To ensure enterprise readiness:
* The user authenticates using a secure API Key on the onboarding screen.
* The key is never saved in plaintext; it is passed immediately to `flutter_secure_storage`, encrypting it via the device hardware security module (Android Keystore / Apple Keychain).
* On app launch, the `SplashScreen` interrogates secure storage to validate session credentials before routing to the main AI voice agent dashboard.

## Project Overview

**Aigosys** is a feature-rich, cross-platform mobile application tailored for modern e-learning. Built with **Flutter**, the application boasts a strictly decoupled Clean Architecture, predictable BLoC state management, and seamless media playback integrations, delivering a responsive and reliable educational experience to students.

As the mobile frontend developer on the team, my responsibility was engineering the client-side architecture, implementing the multi-format curriculum engine (video, articles, timed quizzes), configuring resilient networking against a Go (Golang) REST backend, and ensuring pixel-perfect responsiveness across diverse Android and iOS devices.

---

## Architecture: The Clean Architecture Approach

To ensure maintainability, scalability, and independent testability across a rapidly expanding feature set, the application strictly adheres to **Clean Architecture** principles. The directory structure is divided into three distinct layers with unidirectional dependencies:

```text
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                      │
│      screens/ · widgets/ · bloc/ (flutter_bloc)             │
└──────────────────────────────┬──────────────────────────────┘
                               │ depends on
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                        DOMAIN LAYER                         │
│  usecases/ · entities/ · repository/ (abstract contracts)   │
│                 (Pure Dart — Zero UI Framework)             │
└──────────────────────────────▲──────────────────────────────┘
                               │ implemented by
                               │
┌─────────────────────────────────────────────────────────────┐
│                         DATA LAYER                          │
│  api_client.dart · dio_client.dart · model/ · data_source/  │
└─────────────────────────────────────────────────────────────┘
```

### 1. Data Layer (`data/`)
Handles all communication with external APIs, persistent device storage, and serialization:
* **`dio_client.dart` & `api_client.dart`**: Centralized HTTP client configured with cookie jars, token refresh interceptors, and error sanitization.
* **`model/`**: JSON-to-Dart Data Transfer Objects (DTOs) with serialization and mapping methods to domain entities.
* **`data_source/`**: Concrete implementations for both remote endpoints (REST API) and local cached data (`get_storage`).
* **`repositories/`**: Implements the abstract repository interfaces defined in the domain layer.

### 2. Domain Layer (`domain/`)
The foundational business core of the application, completely isolated from Flutter UI dependencies or third-party data packages:
* **`usecases/`**: Encapsulates single-responsibility business workflows (e.g., `login_use_case.dart`, `get_course_detail_use_case.dart`, `submit_quiz_use_case.dart`).
* **`entities/`**: Clean, immutable domain models representing business objects.
* **`repository/`**: Abstract interfaces defining the contract for data operations without dictating how the data is fetched.

### 3. Presentation Layer (`presentation/`)
Controls what the user sees and handles UI state transitions:
* **`screens/`**: High-level page widgets structured feature-by-feature (Auth, Courses, Quizzes, Profile, My Learning).
* **`widgets/`**: Reusable UI components (shimmer skeletons, custom progress indicators, animated buttons).
* **`bloc/`**: `flutter_bloc` state containers that map incoming user actions to immutable states.

---

## Tech Stack & State Management Strategy

The technology stack was chosen to balance performance, code predictability, and rich user feedback:

| Category | Technology | Purpose & Implementation |
|---|---|---|
| **Core SDK** | Flutter (Dart ^3.12.2) | Cross-platform framework targeting high frame rates and uniform rendering |
| **Primary State** | `flutter_bloc` | Predictable, event-driven state handling across Home, Profile, Course Details, and My Learning |
| **Auxiliary State** | `provider` & `get` | Lightweight scoped dependencies: `provider` drives dynamic localization; Get utilities support context-free navigation |
| **Networking** | `dio`, `dio_cookie_manager`, `cookie_jar` | Robust HTTP requests, cookie session persistence, and global authentication interceptors |
| **Local Storage** | `get_storage` | High-speed key-value persistence for tokens, active theme modes, and session caching |
| **Routing** | `no_context_navigation` + `page_transition` | Decoupled navigation service allowing route pushes from background services with smooth transitions |
| **Responsiveness** | `flutter_screenutil` | Dynamic adaptation ensuring fonts, margins, and card widths scale across varying phone aspect ratios |
| **Media Streaming** | Cloudflare Stream SDK | Secure, adaptive-bitrate video delivery optimized for mobile bandwidth constraints |

---

## Core Modules & Engineering Features

### 1. 🔐 Authentication & Session Engine
The authentication flow (`auth_wrapper.dart`) provides a secure, friction-free onboarding experience:
* **Multi-Step Verification**: Clean transition pipeline between Phone/Email Login, Signup, and dedicated **OTP Verification**.
* **Session Lifecycle**: Automatic token verification on launch with `auth_wrapper.dart` determining whether to route the student to the main dashboard or the login screen.
* **Cookie-Based Sessions**: Leverages `dio_cookie_manager` and persistent `cookie_jar` to maintain authenticated states seamlessly across app restarts.

### 2. 🏠 Course Discovery & Home Dashboard
The primary landing experience presents active and catalog courses with zero perceived latency:
* **Skeleton Shimmer**: Implemented `course_card_shimmer.dart` to show smooth placeholder animations while asynchronous course lists load.
* **Categorized Browsing**: Dynamic course filtering by topics, tags, and enrollment status.

### 3. 📚 Course Consumption Engine
The core value proposition of Aigosys is delivering structured educational content across multiple media types:
* **Cloudflare Stream Integration (`cloudflare_stream_player.dart`)**: Secure video streaming with adaptive bitrate streaming (HLS), custom playback controls, and orientation handling.
* **Article Reader (`article_reader_screen.dart`)**: Formatted technical reading view with customizable font scaling and distraction-free scrolling.
* **Interactive Assessment Engine (`quiz_screen.dart`)**: Timed quizzes supporting multiple question formats, instant client-side answer validation, and detailed score breakdown reviews.
* **Student Reviews**: Interactive bottom sheets allowing students to submit course feedback and ratings directly to the backend.

### 4. 📈 My Learning & Progress Tracking
A dedicated portal tracking user enrollment and lecture completion:
* Powered by `enrollment_progress_model.dart`, tracking exact video timestamps, completed modules, and remaining quiz requirements.
* Real-time synchronization with the Go backend so students can resume learning exactly where they left off on any device.

### 5. 👤 Profile & Student Account Management
Allows students to manage personal info, contact details, educational qualification, and account preferences:
* Integrated `image_picker` for seamless profile picture selection and multipart upload.
* Direct editing and validation for address, contact numbers, and credentials.

---

## UI/UX, Micro-Interactions & Resilience

### Theming & Typography
* **Typography**: Clean, readable sans-serif typography powered by `google_fonts`.
* **Centralized Design System**: Comprehensive `theme.dart` managing both **Light Mode** and **Dark Mode** color tokens, high-contrast borders, and surface elevations.

### Feedback & Motion
* **Micro-Interactions**: Enhanced with `lottie` animations and Flutter's `animations` package for delightful transitions on quiz completions and milestone unlocks.
* **Feedback Delivery**: Custom toast notifications and loading overlays using `cherry_toast` and `flutter_easyloading` for unobtrusive user alerts.

### Network Resilience (`presentation/network_fails/`)
Real-world mobile connections are unstable. Rather than allowing raw exception screens or infinite spinners, Aigosys incorporates dedicated fallback screens:
* **No Internet Screen**: Automatically intercepts network drops, prompting the user with a retry button once connectivity is restored.
* **500 Server Error Screen**: Gracefully catches backend outages, explaining the situation clearly and guiding the student safely back to the home view.

---

## Advanced Integrations: Push Notifications & Deep Linking

* **Firebase Cloud Messaging**: Integrated `firebase_core`, `firebase_messaging`, and `flutter_local_notifications` for scheduled study reminders, quiz deadlines, and announcement blasts.
* **Deep Linking (`global_deep_link_handler.dart`)**: Leveraged `app_links` to enable universal web-to-app routing. Tapping an email or web link directly opens the exact course or quiz screen inside the app.

---

## Key Takeaways from Production

1. **Clean Architecture Pays Dividends Early**: Separating `data`, `domain`, and `presentation` made it straightforward to swap out storage solutions and introduce Cloudflare Stream without breaking existing UI widgets.
2. **Defensive Network Modeling**: Coupling `dio` interceptors with custom error wrappers ensured that every Go backend error code mapped predictably to human-readable UI toasts.
3. **Optimized for Real Mobile Devices**: Combining `flutter_screenutil` with dedicated Light and Dark mode palettes delivered a native, polished look on screens of all sizes.

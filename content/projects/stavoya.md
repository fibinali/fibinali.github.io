## Project Overview

**Stavoya** is a comprehensive, production-grade mobile application designed for the property technology (**PropTech**) sector. Serving as a modern rental and booking ecosystem (similar to Airbnb), Stavoya enables guests to explore verified properties, check real-time availability, calculate dynamic pricing, create curated wishlists, reserve stays, dynamically extend bookings, and process secure payments.

The project is built on modern software engineering foundations, combining **Flutter (Dart ^3.12.2)** with a strict **Clean Architecture** directory pattern, hybrid dependency injection, and predictable **BLoC** state management to deliver an enterprise-grade, maintainable codebase.

---

## Architectural Breakdown: Clean Architecture

To ensure strict separation of concerns, testability, and scalability across more than 30 business workflows, Stavoya is divided into three isolated layers:

```text
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                      │
│     screens/ · widgets/ · bloc/ (flutter_bloc)              │
│     no_context_navigation · toastification · ScreenUtil     │
└──────────────────────────────┬──────────────────────────────┘
                               │ depends on
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                        DOMAIN LAYER                         │
│   usecases/ (30+) · entities/ · repository/ (contracts)     │
│             (Pure Dart — Zero UI or Framework ties)         │
└──────────────────────────────▲──────────────────────────────┘
                               │ implemented by
                               │
┌─────────────────────────────────────────────────────────────┐
│                         DATA LAYER                          │
│   models/ (DTOs) · data_source/ · repositories/ (impl)      │
│   api_client.dart (HTTP) · get_storage (Local caching)      │
└─────────────────────────────────────────────────────────────┘
```

### 1. Domain Layer (`lib/domain/`)
The foundational business core of Stavoya, containing pure Dart code with zero external dependencies on Flutter or serialization libraries:
* **Entities**: Core business objects such as `UserEntity`, `PropertyEntity`, `BookingEntity`, and `AppError`.
* **Repositories (Interfaces)**: Abstract contracts (`AuthRepository`, `DataRepository`) declaring required capabilities without dictating transport details.
* **Use Cases**: Encapsulates over 30 isolated, single-responsibility business operations:
  * `ReservePropertyUseCase` & `CalculatePropertyPriceUseCase`
  * `ExtendStayUseCase` (dynamic booking prolongation)
  * `PaymentDetailsUseCase` (checkout and Stripe session validation)
  * `AddWishlistItemUseCase` & `GetWishlistsUseCase`
  * `EmailVerificationUseCase` (OTP email authentication)
  * `CreateReviewUseCase`, `UpdateReviewUseCase`, `DeleteReviewUseCase`
* **Params**: Strongly-typed parameter data structures (`ReserveParams`, `UpdateUserParams`) ensuring type safety between the UI and use cases.

### 2. Data Layer (`lib/data/`)
Implements the interfaces declared in the domain layer, handling external communication and persistence:
* **Models**: JSON-serializable DTOs (`booking_detail_model.dart`, `property_details_model.dart`) mapping remote payloads into clean domain entities.
* **Data Sources**: Divided cleanly between `RemoteDataSource` (REST API over HTTP) and `LocalDataSource` (`get_storage` for token management and offline caching).
* **Repositories (Implementations)**: `AuthRepositoryImpl` and `DataRepositoryImpl` coordinate remote network calls, error mapping, and local persistence.
* **Core API Client**: A centralized `api_client.dart` that configures base endpoints (`api.staging.stavoya.com`), sets standard headers, and handles HTTP response deserialization and sanitization.

### 3. Presentation Layer (`lib/presentation/`)
Handles UI rendering, responsive scaling, and state transitions:
* **Feature-Based Architecture**: Grouped into dedicated modules (`screens/booking`, `screens/wishlists`, `screens/property`, `screens/auth`), each containing its screen widgets and respective BLoC.
* **BLoC State Management**: Powered by `flutter_bloc` to guarantee unidirectional data flow across asynchronous booking stages.
* **Context-Free Navigation**: Uses `no_context_navigation` along with `page_transition` to decouple routing commands from the widget tree.
* **Reusable Widgets**: Structured directory for modular components (`bottom_sheet`, `app_bar`, `textfield`, `animation`).

---

## Tech Stack & Ecosystem

| Layer / Capability | Package & Technologies | Engineering Role |
|---|---|---|
| **Core Framework** | Flutter SDK (Dart `^3.12.2`) | Cross-platform high-performance client rendering |
| **State Management** | `flutter_bloc` | Unidirectional state management for reservations and discovery |
| **Dependency Injection** | Hybrid: `get_it` + `get` (GetX) | Service locator for UI BLoCs + lazy loading for domain use cases |
| **Payments** | `flutter_stripe` (Stripe Mobile SDK) | In-app mobile payment sheets, tokenization & Apple/Google Pay |
| **Mapping & Geospatial** | `google_maps_flutter` | Interactive property discovery, radius exploration & location markers |
| **Networking** | `http` + Centralized `api_client.dart` | REST API communication, header injection & error normalization |
| **Local Storage** | `get_storage` | High-speed key-value cache for session tokens & preferences |
| **Responsive UI** | `flutter_screenutil` | Dynamic adaptation across diverse screen sizes and pixel densities |
| **Notifications** | `firebase_messaging` + `flutter_local_notifications` | Push notifications and local reminders for booking confirmations |
| **Feedback & UX** | `shimmer`, `lottie`, `toastification` | Micro-interactions, skeleton loading, and polished toast alerts |

---

## Core Engineering Features

### 1. Robust Authentication & Email OTP Flow
Stavoya features a multi-step user onboarding flow including standard credentials, password recovery, and email OTP verification driven by `EmailVerificationUseCase`. Authentication tokens and user metadata are saved securely in local storage, powering automatic session restoration on app launch.

### 2. Property Discovery, Dynamic Pricing & Maps
* **Interactive Map View**: Integrates `google_maps_flutter` to render property pins, interactive bottom preview cards, and geographic boundaries.
* **Real-time Price Calculation**: Leveraging `CalculatePropertyPriceUseCase`, dynamic pricing calculations adapt instantly to selected calendar dates, guest counts, cleaning fees, and seasonal discounts before initiating reservations.

### 3. End-to-End Booking Engine & Dynamic Stay Extensions
The reservation engine guarantees atomic step transitions:
1. Date selection with real-time room inventory validation.
2. Capacity checking against guest allowances.
3. Summary generation and hold locking.
4. **Extend Stay Mechanism**: Through `ExtendStayUseCase`, users can extend an existing booking dynamically without creating a disconnected reservation record.

### 4. Integrated Stripe Checkout & Digital Invoicing
* Integrated via `flutter_stripe` with mobile-native Payment Sheets.
* Validates payment intents via `PaymentDetailsUseCase` against server webhooks.
* Generates digital receipts and order confirmations upon payment settlement.

### 5. Curated User Wishlists & Property Reviews
* **Wishlist Management**: Allows guests to organize and save properties into customizable collections.
* **Full CRUD Review Lifecycle**: Review submissions, rating updates, and deletions encapsulated in `CreateReviewUseCase`, `UpdateReviewUseCase`, and `DeleteReviewUseCase`.

---

## Noteworthy Architecture Implementations

### Hybrid Dependency Injection Architecture
Stavoya implements an optimized hybrid dependency injection strategy (`lib/di/di.dart`):
* **`get_it`**: Used as a clean service locator to provide and inject BLoC instances into the presentation widget hierarchy.
* **`GetX` (`Get.put`, `Get.lazyPut`)**: Leveraged throughout the data and domain layers to lazily instantiate data sources, repository implementations, and 30+ domain use cases only when accessed, minimizing cold-start overhead and device RAM footprint.

### Global Deep Linking Engine (`GlobalDeepLinkHandler`)
The app utilizes a centralized deep-linking handler that captures incoming web links (such as `stavoya.com/properties/{id}` or `stavoya.com/reset-password?token=XYZ`):
* Intercepts URI payloads on cold boot and background resume.
* Parses query parameters and path segments.
* Dispatches appropriate BLoC events and executes seamless route transitions without screen flicker or lost state.

### Production Network Resilience & Global Fail-Safes
To prevent silent crashes or confusing empty screens during network disruptions:
* **`no_internet_screen.dart`**: Detects connectivity loss and prompts real-time retry handshakes.
* **`server500_screen.dart`**: Gracefully captures 5xx gateway/server errors, logging diagnostic codes and providing a clear path back to the home dashboard.
* **Localization Ready**: Implemented with `AppLocalizations` for straightforward multi-language deployment across global markets.

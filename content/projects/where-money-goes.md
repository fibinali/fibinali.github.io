## Project Overview

**Where Money Goes** is a cross-platform personal finance mobile application engineered using **Flutter** and **Firebase**. The application provides real-time expense and income tracking, categorized financial analytics, interactive data visualizations, and secure cloud synchronization across Android and iOS.

The project adheres to **Clean Architecture** principles and unidirectional data flow using **flutter_bloc**, guaranteeing a testable, maintainable, and decoupled codebase.

---

## Architectural Breakdown: Clean Architecture

To ensure separation of concerns, testability, and maintainability, the project decouples business rules from UI frameworks and platform-specific backend services:

```text
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                      │
│     screens/ · widgets/ · bloc/ (flutter_bloc + equatable)  │
│     go_router (declarative routing & auth guards) · fl_chart │
└──────────────────────────────┬──────────────────────────────┘
                               │ dispatches events / listens to state
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                        DOMAIN LAYER                         │
│       usecases/ · entities/ · repository contracts          │
│       (Pure Dart business logic, zero UI dependencies)      │
└──────────────────────────────▲──────────────────────────────┘
                               │ implemented by
                               │
┌─────────────────────────────────────────────────────────────┐
│                         DATA LAYER                          │
│   models/ (DTOs) · data_sources/ (Remote & Local)           │
│   cloud_firestore · firebase_auth · shared_preferences      │
└─────────────────────────────────────────────────────────────┘
```

### 1. Presentation Layer (`lib/presentation/`)
* **Feature-Driven Structure**: Modular screens and widgets for transactions, analytics dashboards, budgeting, and authentication.
* **BLoC State Consumption**: Built with `BlocBuilder`, `BlocConsumer`, and `BlocListener` to handle reactive UI updates, loading spinners, and snackbar notifications without manual lifecycle management.
* **Declarative Routing**: Managed via `go_router` with dedicated `ShellRoute` navigation for persistent bottom navigation bars and deep-link parameters.

### 2. Domain & Business Logic Layer (`lib/domain/`)
* **Unidirectional Data Flow (UDF)**: User interactions trigger immutable `Event` objects; the BLoC processes these events, calls domain use cases, and emits immutable `State` objects.
* **Equatable Value Equality**: Prevents redundant widget rebuilds by evaluating structural equality across events and states.
* **Repository Contracts**: Abstract interfaces (`ExpenseRepository`, `UserRepository`, `AnalyticsRepository`) defining data operations independently of any concrete storage engine.

### 3. Data & Infrastructure Layer (`lib/data/`)
* **Data Sources**: Concrete implementations interfacing with `cloud_firestore` for cloud persistence and `shared_preferences` for offline cached settings.
* **Data Transfer Objects (DTOs)**: Model classes with JSON serialization and Firestore document snapshot conversion methods.
* **Repository Implementations**: Coordinates queries, batch operations, real-time Firestore streams, and local fallback caching.

---

## Tech Stack & Ecosystem

| Capability | Package & Technologies | Engineering Role |
|---|---|---|
| **Core Framework** | Flutter SDK (Dart `^3.12.2`) | Cross-platform client framework for Android and iOS |
| **State Management** | `flutter_bloc (^9.1.1)` + `equatable (^2.0.7)` | Predictable, event-driven state transitions with value equality |
| **Declarative Routing** | `go_router (^16.1.0)` | URL/deep link handling, nested shell routes, and auth redirection |
| **Dependency Injection** | `get_it (^8.2.0)` | Service locator for decoupled singleton services and factory BLoCs |
| **Cloud Backend & DB** | `cloud_firestore (^5.6.12)` | Real-time NoSQL database with client snapshot listeners |
| **User Authentication** | `firebase_auth (^5.7.0)` | Secure credentials handling, token renewal, and auth state streams |
| **Local Persistence** | `shared_preferences (^2.5.3)` | Device-level preference caching and local flags |
| **Data Visualization** | `fl_chart (^1.0.0)` | High-performance interactive charts (pie charts, line graphs) |

---

## Key Features & Capabilities

1. **Transaction & Cash Flow Tracking**: Real-time logging of expenses and income with category tagging, timestamps, and note attachments.
2. **Financial Analytics & Visualization**:
   * **Categorical Breakdown (Pie Chart)**: Visualizes expense distribution across categories (Housing, Food, Entertainment, Utilities, Savings).
   * **Cash Flow Trends (Line Graph)**: Dynamic weekly, monthly, and yearly expenditure vs. income trend lines powered by `fl_chart`.
3. **Real-Time Cloud Synchronization**: Instant sync across devices using Cloud Firestore snapshot streams.
4. **Session Management & Route Guards**: Declarative authentication guards in `go_router` that automatically route unauthenticated users to login/signup.
5. **Granular Cloud Security**: Firestore security rules ensuring strict user-level isolation where users can only read and write their own financial records.
6. **Dark & Light Mode Support**: Seamless theme switching optimized for modern OLED mobile screens and battery efficiency.

---

## Dependency Injection Strategy (`get_it`)

To ensure clean decoupling and painless unit testing, `get_it` acts as the central service locator:

* **Lazy Singletons**: Used for external SDK instances and global infrastructure services (`FirebaseAuth`, `FirebaseFirestore`, `SharedPreferences`).
* **Factory Registration**: Instantiates fresh BLoC instances tied to the lifecycle of individual screens and navigation scopes.

```dart
final sl = GetIt.instance;

void setupLocator() {
  // External Services
  sl.registerLazySingleton(() => FirebaseAuth.instance);
  sl.registerLazySingleton(() => FirebaseFirestore.instance);

  // Repositories
  sl.registerLazySingleton<ExpenseRepository>(
    () => ExpenseRepositoryImpl(firestore: sl()),
  );

  // BLoCs
  sl.registerFactory(() => ExpenseBloc(repository: sl()));
}
```

---

## Backend Security & Firestore Rules

User financial records are protected using strict server-side Firestore authorization rules, preventing unauthorized cross-user access:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId}/{document=**} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

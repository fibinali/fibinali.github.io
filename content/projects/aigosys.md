## Overview

**Aigosys** is an enterprise learning and education mobile application built for students. Developed as an official company project, it provides an end-to-end digital learning environment featuring modular courses, multimedia study material, interactive timed assessments, and real-time student progress tracking.

As the Flutter mobile frontend developer on the team, my primary role was translating product requirements into a responsive, high-performance mobile client that interfaces seamlessly with a high-concurrency Go (Golang) backend. Phase 1 of the application has been successfully completed, and active feature development is currently ongoing.

---

## Architecture: Enterprise-Scale BLoC

Building an educational platform requires managing interconnected states: active course progress, quiz timers, video playback timestamps, and notification payload routing. To ensure high maintainability and testability across features, I structured the application using feature-first Clean Architecture with **BLoC (Business Logic Component)**:

```text
Student Interaction ─────► Event (e.g. SubmitAnswerEvent)
                                 │
                                 ▼
                         QuizBloc (Handler)
                                 │
                ┌────────────────┴────────────────┐
                ▼                                 ▼
      Emit State (QuizSubmitting)         Go Backend API Call
                │                                 │
                ▼                                 ▼
      Emit State (QuizCompleted)    ◄─── HTTP 200 (Score & Review)
```

### Modular Feature Slices

The app is broken down into autonomous feature modules:

- **`features/auth`**: JWT session management, secure storage, and token refresh interceptors.
- **`features/courses`**: Course discovery, syllabus tree traversal, and content playback.
- **`features/quizzes`**: Interactive question renderers, countdown timers, and answer aggregation.
- **`features/progress`**: Student analytics, completed milestone sync, and streak counters.
- **`features/notifications`**: Firebase FCM token registration and deep link payload parsing.

---

## Interfacing with a Go Backend

Working on a company team alongside backend engineers writing Go offered unique opportunities and challenges compared to solo indie development:

### 1. Contract-First API Integration
Before writing UI code, we established strict OpenAPI/Swagger schemas. Go’s strong typing meant backend responses were predictable, but required rigorous Dart model serialization. Using code-generated `freezed` and `json_serializable` classes ensured that any schema discrepancies between the Go structs and Dart DTOs were caught early.

### 2. Resilient Error Handling
Go microservices return structured machine-readable error codes. I built a centralized HTTP interceptor layer that maps backend error envelopes directly into localized user-facing failure states:

```dart
class ApiException implements Exception {
  final String code;
  final String message;
  final int statusCode;

  ApiException({required this.code, required this.message, required this.statusCode});

  factory ApiException.fromJson(Map<String, dynamic> json, int statusCode) {
    return ApiException(
      code: json['code'] ?? 'UNKNOWN_ERROR',
      message: json['message'] ?? 'An unexpected error occurred.',
      statusCode: statusCode,
    );
  }
}
```

---

## Key Implementations

### 1. Interactive Assessment & Quiz Engine

The quiz engine is one of the most critical parts of the student experience:

- **Timer State Machine**: Quizzes run on strict countdowns. The timer runs independently within a Dart stream, maintaining accuracy even if the student temporarily receives an incoming phone call.
- **Local Answer Persistence**: Answers are saved to local SQLite/Hive storage on every selection. If the network drops or the app restarts, students don't lose their progress.
- **Question Variety**: Modular widget builders support multiple choice, multi-select, boolean, and short answer inputs with smooth page-curl transitions between questions.

### 2. Student Progress & Analytics

To keep students motivated, Aigosys features visual progress tracking:

- Animated custom circular progress gauges displaying course completion percentages.
- Weekly study activity heatmaps and quiz score trajectory charts.
- Optimistic UI updates when marking lessons as complete, synchronized in the background with the Go backend.

### 3. Firebase Cloud Messaging & Deep Links

Keeping students engaged requires timely notifications:

- **Firebase Notifications (FCM)**: Configured background and foreground notification handlers for quiz reminders, new module releases, and company announcements.
- **Deep Link Routing**: Integrated custom deep links (`aigosys://course/{id}` and `aigosys://quiz/{id}`) with Flutter navigation, routing students directly to the target learning screen upon tapping a notification.

### 4. Custom Widgets & Responsive Layouts

Students use a wide variety of devices, from compact entry-level smartphones to large tablets:

- Custom responsive layout builders adapting between single-column phone view and dual-pane tablet view for course modules.
- Smooth micro-animations using Flutter's `AnimationController` and implicit animations for test completion confetti and score counters.

---

## Real-World Lessons from a Production Company Project

1. **Defensive Parsing is Mandatory**: In production, backend data can sometimes contain unexpected nulls or partial payloads during deployments. Adding strict fallback defaults prevented production crashes.
2. **State Isolation Prevents Leaks**: Separating transient UI state (like scroll positions and form text controllers) from business domain state (enrolled courses and quiz submissions) keeps BLoCs lightweight and easy to test.
3. **Communication Across Teams**: The biggest speed boost didn't come from writing code faster, but from agreeing on API payloads, pagination parameters, and status codes with the backend team before starting frontend implementation.

Aigosys has been a rewarding real-world project demonstrating how clean architecture, robust state management, and clear cross-team communication lead to high-quality mobile software.


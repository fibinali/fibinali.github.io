---
title: "Building Aigosys: Engineering a Production Flutter App for Students"
description: "Key architectural and engineering lessons from building Aigosys — a real-world education mobile app in Flutter with BLoC, Go backend integration, interactive quizzes, and Firebase."
category: "Flutter"
tags: [Flutter, Dart, BLoC, Mobile, Go, Firebase]
type: article
---

Working on a real-world company project is fundamentally different from building personal hobby apps. On a solo side project, you make all the decisions, control both ends of the wire, and can easily change an API schema whenever your UI needs an extra field.

When developing **Aigosys**—a mobile learning platform for students—I served as the Flutter mobile frontend developer on a team where the backend was independently built using **Go (Golang)**. 

With Phase 1 of the application completed and active development continuing, here are the architectural patterns, team collaboration practices, and engineering lessons I learned from bringing a production Flutter app to life.

---

## 1. Structuring BLoC for Multi-Feature Production Apps

In small apps, managing state in a few loose controllers is fine. But when an app encompasses authentication, a hierarchical course catalog, video players, a timed quiz engine, and offline progress sync, code structure dictates velocity.

I applied **Clean Architecture with BLoC**, separating features into autonomous vertical slices:

```text
lib/
├── core/
│   ├── network/          # Dio client, auth interceptors, error mapper
│   ├── theme/            # Design tokens, typography, custom widgets
│   └── utils/            # Formatters, validators, deep link helper
└── features/
    ├── auth/             # Login, token refresh, biometric locks
    ├── courses/          # Syllabus outline, module viewer, downloads
    ├── quizzes/          # Question state machine, timer streams, reviews
    ├── progress/         # Completion metrics, streak trackers
    └── notifications/    # Firebase FCM listener, background handler
```

Each feature slice contains three distinct layers:
1. **Domain**: Entities and business logic use cases (pure Dart, zero Flutter dependencies).
2. **Data**: DTOs, API providers, and local cache repositories.
3. **Presentation**: Widgets, screens, and BLoCs.

This separation paid off immediately: when the backend API team updated the quiz submission response schema, only the `quizzes/data` DTO layer required changes; the UI widgets and state handlers remained untouched.

---

## 2. Interfacing Flutter with a Go Backend

Connecting a Flutter mobile client to a Go backend taught me several practical realities of enterprise client-server architecture:

### Contract-First Development

Rather than waiting for backend endpoints to be deployed, we agreed on request and response contracts beforehand using Swagger/OpenAPI specifications. 

Go's strong typing means backend responses are strict and consistent. However, on mobile, if a nullable field comes back as `null` instead of an empty array `[]`, a poorly typed Dart model will throw a runtime serialization exception. I used `json_serializable` with explicit `@JsonKey(defaultValue: ...)` annotations on every nullable collection to ensure the mobile client never crashed on unexpected backend payloads.

### Unified Error Envelopes

The Go backend standardizes errors with structured JSON payloads:

```json
{
  "code": "EXAM_WINDOW_CLOSED",
  "message": "The submission deadline for this assessment has passed.",
  "timestamp": 1728220800
}
```

By mapping these error codes centrally in a network interceptor, the Flutter presentation layer simply listens for specific domain failure states (e.g. `QuizDeadlineExceededState`) and renders tailored dialogs rather than generic "Something went wrong" messages.

---

## 3. Building an Interactive Quiz Engine

The assessment engine was one of the most technically demanding parts of Aigosys:

```text
QuizStarted ──► [Timer Stream Active]
      │
      ├─► Student selects answer ──► Auto-save to Local Cache
      ├─► Incoming Call / Pause  ──► Background timer calculates elapsed delta
      └─► Timer Reaches 00:00   ──► Emit QuizAutoSubmitting ──► API Call
```

### Key Engineering Requirements:

1. **Independent Timer Streams**: The countdown timer runs as an isolated broadcast stream. Even when students swipe between question cards or open question reference sheets, the timer tick does not trigger unnecessary widget tree rebuilds.
2. **Crash-Resilient Answer Caching**: Students taking exams cannot afford to lose answers if the app crashes or the battery dies. Every selection is written instantly to local storage before sending optimistic updates to the server.
3. **Question Type Polymorphism**: Assessments include multiple choice, multi-select, boolean statements, and short text inputs. Modeling question items with sealed classes in Dart 3 made rendering each question variant clean, type-safe, and exhaustive.

---

## 4. Push Notifications & Deep Linking in Practice

Education apps rely heavily on timely reminders: an exam starting in 15 minutes, graded assignment feedback, or a new lecture upload.

- **Firebase Cloud Messaging (FCM)**: Configured background isolate handlers and foreground notification banners so alerts display consistently whether the app is active, backgrounded, or terminated.
- **Deep Link Navigation**: Notification payloads include routing parameters (e.g. `{"type": "quiz", "id": "452"}`). The app's router parses the payload, validates authentication state, and pushes the student directly to the target quiz screen, passing any necessary route arguments automatically.

---

## 5. What Working on a Real-World Project Taught Me

Building Aigosys as a company product fundamentally shaped how I approach software engineering:

### 1. Defensive Programming is Not Optional
In a personal project, you know what inputs to expect. In production with real students across hundreds of Android and iOS device models, edge cases will happen. Null safety, try-catch guards around network parsing, and graceful offline fallback states are essential.

### 2. Agree on Contracts First
Spending 30 minutes in a meeting aligning on API request/response structures with backend developers saves hours of frontend refactoring down the road.

### 3. Polish Drives Retention
Students spend hours inside study apps. Thoughtful micro-animations, clear loading indicators, and intuitive gesture feedback make the experience feel effortless and professional.

With Phase 1 delivered, Aigosys continues to evolve—and the architectural foundation laid in this first phase ensures that scaling future modules will remain smooth and maintainable.


## Overview

**Stavoya** is a mobile hotel booking and reservation application built from the ground up in Flutter. As the solo frontend engineer on the project, my responsibility was to take an existing MERN backend API and turn it into a high-performance, fluid mobile experience.

Hotel booking apps present unique frontend engineering hurdles: unlike standard e-commerce carts with static inventory, hotel reservations involve dynamic real-time availability, strict date-range validations, guest capacity rules, temporary checkout holds, and secure external payment handshakes.

---

## Architectural Foundation: Why BLoC?

When state transitions span across multiple screens (from initial exploration to date selection, room tier selection, guest customization, and checkout), ad-hoc state management quickly leads to race conditions and desynchronized UI.

I opted for the **BLoC (Business Logic Component)** pattern to enforce strict unidirectional data flow:

```text
User Event ────────► BLoC (Event Handler) ────────► Emit State
                         │
                         ▼
                Repository / Network
```

### Clean Layering

1. **Presentation Layer**: Custom stateless/stateful widgets listening via `BlocBuilder` and `BlocConsumer`.
2. **Business Logic Layer**:
   - `HotelSearchBloc`: Manages search queries, debouncing, and multi-filter state (price brackets, star ratings, amenities, and location sorting).
   - `BookingBloc`: Tracks the active reservation session (check-in/check-out dates, room tier, room count, and guest configurations).
   - `PaymentBloc`: Orchestrates Stripe payment intents, loading states, and transaction receipts.
3. **Data Layer**:
   - HTTP clients with authentication interceptors for JWT token attachment and automated refresh handling.
   - DTOs and entity mappers converting raw JSON responses into typed, immutable Dart data models.

---

## Key Technical Implementations

### 1. Multi-Step Booking State Machine

A booking isn't a single API call—it is a sequence of state validations:

1. **Date Selection**: Ensuring check-in is before check-out, with minimum stay durations respected.
2. **Room Hold**: Checking inventory locks with the backend so two users don't book the same room concurrently.
3. **Price Calculation**: Calculating dynamic night counts, cleaning fees, taxes, and applied promo discounts.
4. **Checkout Session**: Requesting a Payment Intent from the server and launching the payment sheet.

By encapsulating these transitions inside `BookingBloc`, the app ensures that invalid transitions (such as paying before date verification) are structurally impossible.

### 2. Custom Interactive Calendar

Standard date pickers rarely offer the UX needed for hotel booking. I built a custom calendar component featuring:

- Fast swipe navigation across months with pre-cached calendar days.
- Continuous visual range highlighting between check-in and check-out days.
- Dynamic blackout states for dates with zero room availability.
- Reactive night counters updating pricing summaries in real-time.

### 3. Stripe Mobile Payment Sheet Integration

Payments were integrated using the official Stripe Flutter SDK:

1. When the user taps **Proceed to Pay**, `PaymentBloc` triggers an endpoint on the backend to create a Stripe `PaymentIntent`.
2. The backend responds with the `client_secret` and ephemeral key.
3. Flutter initializes `Stripe.instance.initPaymentSheet()`.
4. `Stripe.instance.presentPaymentSheet()` presents the native Android/iOS payment sheet (supporting credit cards, Google Pay, and Apple Pay).
5. Upon confirmation, the app polls the booking confirmation endpoint or awaits webhook-driven status update before navigating to the animated success screen.

### 4. Deep Linking & Notification Routing

- **Deep Links**: Configured custom scheme and App Links / Universal Links (`stavoya://hotel/{id}` and `stavoya://booking/{id}`) so shared links or promotional emails open directly into the corresponding hotel details or reservation summary.
- **Push Notifications**: Integrated local and push notification services to notify users of reservation confirmations, check-in reminders, and status changes.

---

## Challenges & Edge Cases Solved

::: note State desynchronization on app backgrounding
When users switch apps to complete 3D Secure bank authentication during a Stripe payment, the Flutter engine can be paused. I implemented lifecycle listeners to gracefully verify payment status with the server when the app resumes, preventing double-charge scenarios or abandoned booking holds.
:::

- **Image Heavy Feeds**: Hotel discovery feeds require multiple high-resolution photos per property. Implemented aggressive image caching, lazy memory evictions, and blur hash placeholders to maintain smooth 60fps scrolling on budget Android devices.
- **Form Resiliency**: Created custom bottom sheets for guest allocation (adults, children, infants, pets) that retain validation state even if dismissed and reopened.

---

## Key Takeaways

1. **Strict State Management Pays Off**: For complex transactional flows like reservations and payments, BLoC's explicitness prevents elusive bugs that simpler reactive stores tend to obscure.
2. **Contract-First API Integration**: Working with an existing backend as a solo frontend developer meant creating rock-solid Dart DTOs with thorough null-safety checks to prevent runtime serialization crashes.
3. **UX Details Matter**: Micro-interactions, smooth bottom-sheet physics, and immediate visual feedback during network delays turn a utilitarian booking form into a trustworthy, polished application.


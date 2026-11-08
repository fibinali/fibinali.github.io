---
title: "Building Stavoya: What I Learned Building a Flutter Hotel Booking App"
description: "A deep dive into building a full-featured hotel booking mobile app in Flutter: BLoC architecture, multi-step booking state, Stripe payments, custom calendar UI, and deep links."
category: "Flutter"
tags: [Flutter, Dart, BLoC, Mobile, Stripe]
type: article
---

When I set out to build the frontend for **Stavoya**—a hotel booking mobile application—I knew it would test my Flutter skills far beyond standard CRUD screens. Booking apps sit at the intersection of e-commerce, real-time availability checks, date manipulation, and high-stakes payment transactions.

As the solo Flutter developer connecting to an existing MERN backend, I had full ownership of the mobile architecture, state management, and user experience. Here is an honest breakdown of how the app was engineered, the architecture that kept the codebase manageable, and the practical lessons I took away.

---

## 1. Why State Management Dictates Everything in Booking Apps

In a simple content app, state is usually local: fetch data, render list, push detail view. But in hotel booking, state is intensely interdependent:

- Changing a check-in date immediately recalculates nights, pricing tiers, and room availability.
- Selecting a room requires reserving a temporary hold so another user cannot book the same room while you enter payment details.
- Applying a discount code updates the price breakdown in the checkout drawer in real-time.

To prevent bugs and race conditions, I relied on the **BLoC (Business Logic Component)** pattern. BLoC separates business logic from presentation using Dart streams, ensuring unidirectional data flow:

```text
User Event ────────► BLoC (Event Handler) ────────► Emit State
                         │
                         ▼
                Repository / Network
```

By defining discrete states for every step of the reservation lifecycle (`BookingInitial`, `BookingDatesSelected`, `BookingHoldingRoom`, `BookingPaymentReady`, `BookingSuccess`, `BookingFailure`), the UI can never enter an impossible state—like displaying the checkout payment button without verified room inventory.

```dart
// Core states modeling the booking progression
abstract class BookingState extends Equatable {
  const BookingState();
}

class BookingDatesSelected extends BookingState {
  final DateTime checkIn;
  final DateTime checkOut;
  final int totalNights;
  final double estimatedSubtotal;

  const BookingDatesSelected({
    required this.checkIn,
    required this.checkOut,
    required this.totalNights,
    required this.estimatedSubtotal,
  });

  @override
  List<Object?> get props => [checkIn, checkOut, totalNights, estimatedSubtotal];
}
```

---

## 2. Crafting a Custom Interactive Calendar

Off-the-shelf date pickers rarely deliver the smooth, polished UX users expect from modern travel apps. Hotel booking requires:

1. **Range Selection**: Continuous visual highlighting between check-in and check-out days.
2. **Disabled Blackout Dates**: Dates where rooms are sold out must be unselectable and visually dimmed.
3. **Dynamic Feedback**: As soon as two dates are tapped, a floating pill displays the total nights (e.g., *"3 nights"*) and updates the checkout estimate.

Building this custom calendar required careful attention to widget rebuilds. Rebuilding the entire month grid on every tap introduced frame drops. The fix was isolating each day cell into its own `ValueListenableBuilder` or granular widget that only rebuilds when its selection state changes.

---

## 3. Stripe Mobile Payment Sheet Integration

Handling payments on mobile requires ironclad reliability. Nobody likes being charged without seeing a confirmation screen, or worse, having the app crash midway through bank authentication.

I integrated the **Stripe Flutter SDK** using Stripe's native Payment Sheet flow:

```text
Flutter App                   Backend (MERN)                   Stripe API
    │                               │                              │
    │── 1. Create PaymentIntent ───►│                              │
    │                               │── 2. Create PaymentIntent ──►│
    │                               │◄─ 3. Returns client_secret ──│
    │◄─ 4. Returns client_secret ───│                              │
    │                                                              │
    │── 5. Stripe.initPaymentSheet()                               │
    │── 6. Stripe.presentPaymentSheet()                            │
    │                                                              │
    │──────────────── 7. User completes 3DS auth ─────────────────►│
    │◄─────────────── 8. Payment confirmation ─────────────────────│
    │                                                              │
    │── 9. Confirm booking with server ──►                         │
```

### Handling 3D Secure and App Backgrounding

One critical edge case in mobile payments is **3D Secure (3DS)** verification: the user is often redirected to their banking app or an SMS OTP screen, putting your Flutter app into the background.

If the app process is paused or if the user takes two minutes to find their password, naive async calls can lose context. I added app lifecycle observers (`WidgetsBindingObserver`) to verify transaction state directly against the backend when the app returns to the foreground, ensuring no completed payments go unacknowledged.

---

## 4. Deep Linking & Push Notifications

A booking app doesn't live in a vacuum—users interact with booking confirmations from emails, push alerts, and shared links.

- **Deep Links**: Configured Universal Links (iOS) and App Links (Android) so URLs like `https://stavoya.app/hotel/123` open directly into the Flutter app's hotel detail screen with smooth hero image transitions.
- **Push Notifications**: Integrated Firebase Cloud Messaging (FCM) to deliver instant confirmation badges, check-in reminders 24 hours prior to arrival, and booking status updates.

Routing deep links cleanly into a BLoC-driven app required a centralized route parser that could initialize the necessary bloc dependencies before pushing the target screen onto the navigation stack.

---

## 5. Major Hurdles and How I Solved Them

### Image Heavy Scrolling Feeds

Hotel apps are visually driven. A search results page can display dozens of properties, each with high-resolution thumbnail carousels. On mid-range devices, this caused memory pressure and stutter.

**Solution**:
- Used `cached_network_image` with explicit `memCacheWidth` and `memCacheHeight` constraints to prevent storing oversized 4K images in memory.
- Added BlurHash placeholders while images loaded over spotty mobile networks.
- Enforced automatic memory cache cleanup when scrolling past viewports.

### Form Resiliency

Guest selection forms (number of rooms, adults, children, infants) were housed in modal bottom sheets. Initially, dismissing the bottom sheet accidentally wiped out unconfirmed selections.

**Solution**:
- Decoupled the working draft state inside the bottom sheet from the committed `BookingBloc` state.
- Selections were only committed when the user tapped **"Apply"**, with auto-saving drafts so re-opening the sheet restored their previous inputs.

---

## What Building Stavoya Taught Me

Building a complex mobile application solo is one of the fastest ways to grow as a software engineer:

1. **Architecture is insurance**: Clean layering (data, domain, presentation) felt like extra boilerplate in week one, but in week four, when adding new filter parameters and payment retries, it prevented everything from crumbling.
2. **Design for latency**: Users are impatient. Instant optimistic UI updates, shimmer loading skeletons, and clear feedback make an app feel twice as fast even on slow connections.
3. **Edge cases are the real product**: Happy paths are easy to code. The real work is handling payment timeouts, network dropouts midway through reservation holds, and back-button presses during checkout.

Stavoya proved to be an invaluable hands-on journey in building resilient, production-ready Flutter mobile applications.


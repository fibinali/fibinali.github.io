---
title: "Structuring a Flutter App With Riverpod and Clean Architecture"
description: "A practical folder structure and state-management pattern for Flutter apps that stays sane past the first ten screens, using Riverpod for dependency injection and state."
category: "Flutter"
tags: [Flutter, Programming, Dart]
type: tutorial
---

Most Flutter tutorials show a counter app and stop before the architecture question gets hard. This one lays out a folder structure and state pattern that holds up once an app has real features — auth, a network layer, and screens that depend on each other.

## The folder structure

```text
lib/
  core/
    network/       # Dio client, interceptors, exceptions
    theme/          # ThemeData, colors, text styles
  features/
    auth/
      data/         # repositories, DTOs, API calls
      domain/       # entities, use cases
      presentation/ # widgets, providers
    notes/
      data/
      domain/
      presentation/
  main.dart
```

Each feature is self-contained: `data` talks to the network or database, `domain` holds plain Dart business logic with no Flutter imports, and `presentation` holds widgets and the Riverpod providers that connect them.

::: tip
The rule that keeps this structure honest: nothing in `domain/` may import from `package:flutter/*`. If a domain class needs `Color` or `Widget`, that's a sign the logic belongs in presentation instead.
:::

## Defining a repository

```dart
// features/notes/domain/note_repository.dart
abstract class NoteRepository {
  Future<List<Note>> fetchNotes();
  Future<void> saveNote(Note note);
}
```

```dart
// features/notes/data/note_repository_impl.dart
class NoteRepositoryImpl implements NoteRepository {
  NoteRepositoryImpl(this._client);
  final Dio _client;

  @override
  Future<List<Note>> fetchNotes() async {
    final response = await _client.get('/notes');
    return (response.data as List)
        .map((json) => Note.fromJson(json))
        .toList();
  }

  @override
  Future<void> saveNote(Note note) =>
      _client.post('/notes', data: note.toJson());
}
```

The domain layer depends only on the abstract `NoteRepository`, never on `NoteRepositoryImpl` directly. That's what makes it possible to swap in a fake implementation for tests without touching any widget code.

## Wiring it with Riverpod

```dart
// features/notes/presentation/providers.dart
final noteRepositoryProvider = Provider<NoteRepository>((ref) {
  return NoteRepositoryImpl(ref.watch(dioClientProvider));
});

final notesProvider = FutureProvider<List<Note>>((ref) async {
  final repo = ref.watch(noteRepositoryProvider);
  return repo.fetchNotes();
});
```

```dart
// features/notes/presentation/notes_screen.dart
class NotesScreen extends ConsumerWidget {
  const NotesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notesAsync = ref.watch(notesProvider);

    return notesAsync.when(
      data: (notes) => ListView.builder(
        itemCount: notes.length,
        itemBuilder: (_, i) => ListTile(title: Text(notes[i].title)),
      ),
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (err, _) => Center(child: Text('Failed to load: $err')),
    );
  }
}
```

`FutureProvider` handles the loading/error/data states for you, and `ref.watch` means the screen rebuilds automatically when the underlying data changes — no `setState`, no `StreamController` boilerplate.

::: note
Swap `FutureProvider` for `AsyncNotifierProvider` once you need to mutate state from the UI (marking a note as done, for example) rather than only reading it.
:::

## Testing the domain layer

Because `NoteRepository` is an interface, tests can substitute a fake without touching Dio, HTTP mocking, or Flutter's widget test harness at all:

```dart
class FakeNoteRepository implements NoteRepository {
  final List<Note> notes = [];

  @override
  Future<List<Note>> fetchNotes() async => notes;

  @override
  Future<void> saveNote(Note note) async => notes.add(note);
}

void main() {
  test('saveNote adds to the list', () async {
    final repo = FakeNoteRepository();
    await repo.saveNote(Note(id: '1', title: 'Test'));
    expect(await repo.fetchNotes(), hasLength(1));
  });
}
```

## Where this scales and where it doesn't

This structure comfortably handles apps with a handful of features and a moderate amount of shared state. Past roughly 15–20 features, consider splitting `features/` into separate packages within a monorepo so build times and ownership boundaries stay manageable — a topic for a future post.

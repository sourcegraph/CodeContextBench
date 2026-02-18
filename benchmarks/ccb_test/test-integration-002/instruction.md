# Write Integration Tests for Navidrome Media Scanning Pipeline

## Objective

Write comprehensive integration tests for Navidrome's media scanning pipeline. The repository is cloned at `/workspace`. Focus on the `scanner/` directory, which contains the core logic for discovering, reading, and indexing music files.

## Target File

Write your test file to:

```
/workspace/scanner/scanner_integration_test.go
```

## Pipeline Stages to Test

The Navidrome scanner pipeline processes a music library through several stages. Your tests must cover all of the following:

### 1. File Discovery
Test the scanner's ability to traverse a directory tree and locate audio files.

- Finding audio files across nested directory structures
- Handling symbolic links (following vs. ignoring)
- Ignoring non-audio files (images, text files, etc.)
- Respecting directory depth and skip patterns

### 2. Metadata Extraction
Test reading audio metadata (tags) from media files.

- Reading ID3/Vorbis/FLAC tags (artist, album, title, track number, year)
- Handling missing or incomplete tags (files with no artist, no title, etc.)
- Handling corrupt or malformed tag data
- Multi-value fields (multiple artists, multiple genres)

### 3. Database Persistence
Test that scanned media is correctly persisted to the data store.

- Creating new MediaFile records on first scan
- Updating existing records when file metadata changes
- Upserting behavior (create-or-update semantics)
- Handling duplicate file paths
- Deleting records for files that no longer exist on disk

### 4. Playlist Scanning
Test the scanner's playlist file handling.

- Parsing M3U playlist files
- Resolving relative paths within playlists
- Handling M3U8 and PLS formats if supported
- Gracefully handling playlists that reference missing files

### 5. Error Handling
Test resilience to filesystem and data errors.

- Permission denied on files or directories (os.ErrPermission / EACCES)
- Corrupt or unreadable audio files
- Empty directories (directories with no audio content)
- Concurrent or parallel scan operations (race conditions, sync primitives)

## Requirements

- Use **Go testing patterns** with the standard `testing` package
- Use `t.TempDir()` or equivalent for test fixtures; create temporary directory structures with sample file metadata
- Use **table-driven tests** with `t.Run()` subtests for systematic coverage
- Use **mocks or interfaces** to isolate the scanner from real database and filesystem dependencies where appropriate
- Include proper `t.Cleanup()` or `defer` statements for teardown
- Cover both **happy-path** and **error/edge cases**
- The package declaration must be `package scanner` or `package scanner_test`
- Tests must compile cleanly with `go vet`

## Anti-Requirements

- Do **not** test the HTTP API layer or REST endpoints
- Do **not** test the web UI or frontend
- Focus exclusively on scanner internals (file walking, tag reading, persistence logic)

## Quality Bar

- At least 5 distinct test functions (e.g., `TestFileDiscovery`, `TestMetadataExtraction`, etc.)
- Each pipeline stage should have dedicated test coverage
- Tests should be self-contained and not depend on execution order
- Use clear, descriptive test names and variable names
- Reference actual Navidrome types and interfaces (e.g., `Scanner`, `MediaFile`, tag-reading functions) where possible
- Audio format references should include at least two of: `.mp3`, `.flac`, `.ogg`, `.m4a`, `.opus`

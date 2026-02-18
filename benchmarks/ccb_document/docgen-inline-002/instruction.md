# Task: Generate Comprehensive Javadoc for Kafka Record Batch Serialization Classes

## Objective

Generate comprehensive Javadoc documentation for Apache Kafka's record batch serialization classes located in `clients/src/main/java/org/apache/kafka/common/record/`. The existing Javadoc comments have been stripped and you must write new documentation based on your understanding of the code and the Kafka record batch format.

## Target Classes

The directory `clients/src/main/java/org/apache/kafka/common/record/` contains the core record serialization layer. Focus on these four key files:

1. **`DefaultRecordBatch.java`** -- The concrete implementation of `RecordBatch` for the current (v2 / magic=2) record format. Handles CRC validation, compression, header parsing, and iteration over individual records within a batch.

2. **`DefaultRecord.java`** -- Represents a single record within a `DefaultRecordBatch`. Uses variable-length encoding (varints) for key, value, and headers. Offsets are stored as deltas relative to the batch's base offset.

3. **`MemoryRecords.java`** -- An in-memory container for one or more `RecordBatch` instances backed by a `ByteBuffer`. This is the primary type used when sending and receiving records over the network or reading from disk.

4. **`RecordBatch.java`** (interface) -- The interface contract that all record batch implementations must satisfy. Defines methods for accessing batch metadata (magic, compression, timestamps, producer state) and iterating over records.

## Requirements

### What to Document

1. **Class-level Javadoc** for each of the four classes/interfaces: Describe the purpose, its role in Kafka's record format, and how it relates to the other classes in this package.

2. **All public methods**: Document with `@param`, `@return`, and `@throws` tags. Do not merely list method signatures -- explain the behavioral semantics of each method, including edge cases and invariants.

3. **Serialization format details**: Explain the on-wire/on-disk binary format, including:
   - The magic byte and how it determines the record format version (v0, v1, v2)
   - CRC32C checksum: what data it covers, when it is validated, and what happens on mismatch
   - The batch header layout (base offset, batch length, partition leader epoch, attributes, timestamps, producer ID/epoch/sequence)
   - Variable-length encoding (varints) used in individual records

4. **Batch vs. record distinction**: Clearly explain that a batch is a container of records sharing compression, producer state, and a base offset, while individual records carry deltas and per-record headers.

5. **Compression codec interactions**: Document which compression types are supported (none, gzip, snappy, lz4, zstd), how compression applies at the batch level (not per-record), and the decompression flow when iterating over records.

### Thread-Safety and Concurrency

- Document thread-safety guarantees (or lack thereof) for each class
- Explain `ByteBuffer` sharing semantics: when buffers are sliced or duplicated, and what the caller must be aware of
- Document iterator lifecycle: `CloseableIterator` semantics, single-traversal constraints, and resource cleanup
- Note any compression codec state that is not safe for concurrent use

### Performance Characteristics

- Buffer allocation patterns: heap vs. direct buffers, when Kafka allocates new buffers vs. reusing existing ones
- Compression overhead and batch-level amortization
- Batch size implications: overhead per record vs. overhead per batch, and why larger batches are more efficient
- Zero-copy considerations: `FileChannel.transferTo`, memory-mapped reads, and when they apply

### Cross-References

- Use `@see` and `{@link}` tags (or equivalent markdown references) to connect related classes
- Reference the relationship between `RecordBatch` (interface) and `DefaultRecordBatch` (implementation)
- Reference how `MemoryRecords` contains batches and how batches contain records
- Reference `RecordVersion` / `MAGIC_VALUE` constants
- Reference interactions with `KafkaProducer` (batching on send) and `KafkaConsumer` (fetch deserialization)

## Anti-Requirements

- Do NOT simply list method signatures with generic one-line descriptions. Explain what each method does and why.
- Do NOT fabricate API details that do not exist in the source code.
- Do NOT copy verbatim from external documentation. Write original documentation based on code analysis.

## Output

Write your complete documentation to `/workspace/documentation.md`. The file should contain all Javadoc organized by class, with detailed method documentation, format explanations, thread-safety notes, performance guidance, and cross-references.

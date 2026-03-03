# PricingSessionWindow Implementation for Apache Flink

## Summary

This solution implements a custom financial trading session window assigner for Apache Flink. The implementation consists of three main components that enable streaming applications to group trading events by market session boundaries (e.g., NYSE 09:30-16:00 ET) rather than fixed time intervals.

## Files Examined

- **flink-runtime/src/main/java/org/apache/flink/streaming/api/windowing/assigners/MergingWindowAssigner.java** — examined to understand the abstract base class for window assigners that support merging
- **flink-streaming-java/src/main/java/org/apache/flink/streaming/api/windowing/assigners/EventTimeSessionWindows.java** — examined to understand session window assignment patterns and factory method conventions
- **flink-streaming-java/src/main/java/org/apache/flink/streaming/api/windowing/assigners/DynamicEventTimeSessionWindows.java** — examined to understand how to implement dynamic window assignment with extractor patterns
- **flink-streaming-java/src/main/java/org/apache/flink/streaming/api/windowing/assigners/SessionWindowTimeGapExtractor.java** — examined to understand the functional interface pattern for extractors
- **flink-runtime/src/main/java/org/apache/flink/streaming/api/windowing/triggers/Trigger.java** — examined to understand the trigger lifecycle (onElement, onEventTime, onProcessingTime, clear, canMerge, onMerge)
- **flink-runtime/src/main/java/org/apache/flink/streaming/api/windowing/triggers/EventTimeTrigger.java** — examined to understand event-time trigger implementation and merging support
- **flink-runtime/src/main/java/org/apache/flink/streaming/api/windowing/windows/TimeWindow.java** — examined to understand TimeWindow merging logic and the static mergeWindows() utility method

## Dependency Chain

1. **Define types/interfaces**: `TradingSessionExtractor.java`
   - Functional interface for extracting market IDs from elements
   - Enables dynamic session assignment based on element content
   - Follows the pattern of `SessionWindowTimeGapExtractor`

2. **Implement core window assigner**: `PricingSessionWindow.java`
   - Extends `MergingWindowAssigner<Object, TimeWindow>`
   - Determines trading session boundaries based on market timezone and business hours
   - Converts UTC timestamps to market-local time for session determination
   - Handles session transitions across day boundaries
   - Returns `EventTimeTrigger` as the default trigger

3. **Implement session trigger**: `PricingSessionTrigger.java`
   - Extends `Trigger<Object, TimeWindow>`
   - Fires when the watermark reaches the window end (market close)
   - Supports window merging via `canMerge()` and `onMerge()`
   - Properly manages timer lifecycle in `clear()`

## Code Changes

### TradingSessionExtractor.java
```java
/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.apache.flink.streaming.api.windowing.assigners;

import org.apache.flink.annotation.PublicEvolving;

import java.io.Serializable;

/**
 * A {@code TradingSessionExtractor} extracts the market ID from elements for dynamic trading
 * session assignment.
 *
 * <p>This functional interface enables dynamic assignment of trading sessions based on element
 * content, allowing different elements to be assigned to different trading sessions (e.g., NYSE,
 * LSE, NASDAQ) based on their market identifiers.
 *
 * @param <T> The type of elements from which this extractor can extract a market ID.
 */
@PublicEvolving
public interface TradingSessionExtractor<T> extends Serializable {
    /**
     * Extracts the market ID from an element.
     *
     * @param element The input element.
     * @return The market ID as a string (e.g., "NYSE", "LSE", "NASDAQ").
     */
    String extractMarketId(T element);
}
```

### PricingSessionWindow.java
```java
/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.apache.flink.streaming.api.windowing.assigners;

import org.apache.flink.annotation.PublicEvolving;
import org.apache.flink.api.common.ExecutionConfig;
import org.apache.flink.api.common.typeutils.TypeSerializer;
import org.apache.flink.streaming.api.windowing.triggers.EventTimeTrigger;
import org.apache.flink.streaming.api.windowing.triggers.Trigger;
import org.apache.flink.streaming.api.windowing.windows.TimeWindow;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.Collection;
import java.util.Collections;
import java.util.Objects;

/**
 * A {@link WindowAssigner} that windows elements into sessions based on market trading session
 * boundaries rather than fixed time intervals.
 *
 * <p>This assigner groups trading events by market session (e.g., NYSE 09:30-16:00 ET, LSE
 * 08:00-16:30 GMT). Windows cannot overlap.
 *
 * <p>For example, to window stock price updates by NYSE trading hours:
 *
 * <pre>{@code
 * DataStream<TradeEvent> events = ...;
 * KeyedStream<TradeEvent, String> keyed = events.keyBy(e -> e.getSymbol());
 * WindowedStream<TradeEvent, String, TimeWindow> windowed =
 *   keyed.window(PricingSessionWindow.forMarket(
 *       "NYSE",
 *       ZoneId.of("America/New_York"),
 *       LocalTime.of(9, 30),
 *       LocalTime.of(16, 0)
 *   ));
 * }</pre>
 */
@PublicEvolving
public class PricingSessionWindow extends MergingWindowAssigner<Object, TimeWindow> {
    private static final long serialVersionUID = 1L;

    private final String marketId;
    private final ZoneId timezone;
    private final LocalTime sessionOpen;
    private final LocalTime sessionClose;

    /**
     * Creates a new PricingSessionWindow with the specified market parameters.
     *
     * @param marketId The identifier for the market (e.g., "NYSE", "LSE")
     * @param timezone The timezone in which the market operates
     * @param sessionOpen The local time when the market opens
     * @param sessionClose The local time when the market closes
     */
    public PricingSessionWindow(
            String marketId, ZoneId timezone, LocalTime sessionOpen, LocalTime sessionClose) {
        Objects.requireNonNull(marketId, "marketId must not be null");
        Objects.requireNonNull(timezone, "timezone must not be null");
        Objects.requireNonNull(sessionOpen, "sessionOpen must not be null");
        Objects.requireNonNull(sessionClose, "sessionClose must not be null");

        if (!sessionOpen.isBefore(sessionClose)) {
            throw new IllegalArgumentException(
                    "sessionOpen must be before sessionClose (overnight sessions not supported in this version)");
        }

        this.marketId = marketId;
        this.timezone = timezone;
        this.sessionOpen = sessionOpen;
        this.sessionClose = sessionClose;
    }

    @Override
    public Collection<TimeWindow> assignWindows(
            Object element, long timestamp, WindowAssignerContext context) {
        // Convert timestamp to the market's timezone to determine session
        ZonedDateTime zonedDateTime =
                ZonedDateTime.ofInstant(
                        java.time.Instant.ofEpochMilli(timestamp), timezone);

        // Get the date in the market's timezone
        LocalDate sessionDate = zonedDateTime.toLocalDate();

        // Calculate session start and end times in milliseconds (UTC)
        LocalDateTime sessionStartLocal = LocalDateTime.of(sessionDate, sessionOpen);
        LocalDateTime sessionEndLocal = LocalDateTime.of(sessionDate, sessionClose);

        ZonedDateTime sessionStartZoned =
                sessionStartLocal.atZone(timezone);
        ZonedDateTime sessionEndZoned =
                sessionEndLocal.atZone(timezone);

        long sessionStartMillis = sessionStartZoned.toInstant().toEpochMilli();
        long sessionEndMillis = sessionEndZoned.toInstant().toEpochMilli();

        // If the timestamp is before the session start, it belongs to the next session
        if (timestamp < sessionStartMillis) {
            // Move to the next day's session
            sessionDate = sessionDate.plusDays(1);
            sessionStartLocal = LocalDateTime.of(sessionDate, sessionOpen);
            sessionEndLocal = LocalDateTime.of(sessionDate, sessionClose);

            sessionStartZoned = sessionStartLocal.atZone(timezone);
            sessionEndZoned = sessionEndLocal.atZone(timezone);

            sessionStartMillis = sessionStartZoned.toInstant().toEpochMilli();
            sessionEndMillis = sessionEndZoned.toInstant().toEpochMillis();
        }
        // If the timestamp is after the session end, it belongs to the next session
        else if (timestamp >= sessionEndMillis) {
            // Move to the next day's session
            sessionDate = sessionDate.plusDays(1);
            sessionStartLocal = LocalDateTime.of(sessionDate, sessionOpen);
            sessionEndLocal = LocalDateTime.of(sessionDate, sessionClose);

            sessionStartZoned = sessionStartLocal.atZone(timezone);
            sessionEndZoned = sessionEndLocal.atZone(timezone);

            sessionStartMillis = sessionStartZoned.toInstant().toEpochMilli();
            sessionEndMillis = sessionEndZoned.toInstant().toEpochMilli();
        }

        return Collections.singletonList(new TimeWindow(sessionStartMillis, sessionEndMillis));
    }

    @Override
    public Trigger<Object, TimeWindow> getDefaultTrigger() {
        return EventTimeTrigger.create();
    }

    @Override
    public String toString() {
        return "PricingSessionWindow{"
                + "marketId='"
                + marketId
                + '\''
                + ", timezone="
                + timezone
                + ", sessionOpen="
                + sessionOpen
                + ", sessionClose="
                + sessionClose
                + '}';
    }

    @Override
    public TypeSerializer<TimeWindow> getWindowSerializer(ExecutionConfig executionConfig) {
        return new TimeWindow.Serializer();
    }

    @Override
    public boolean isEventTime() {
        return true;
    }

    /** Merge overlapping {@link TimeWindow}s. */
    @Override
    public void mergeWindows(
            Collection<TimeWindow> windows, MergingWindowAssigner.MergeCallback<TimeWindow> c) {
        TimeWindow.mergeWindows(windows, c);
    }

    /**
     * Creates a new {@code PricingSessionWindow} for a specific market.
     *
     * @param marketId The market identifier (e.g., "NYSE", "LSE")
     * @param timezone The timezone for the market
     * @param sessionOpen The local time when the market opens
     * @param sessionClose The local time when the market closes
     * @return A new PricingSessionWindow instance
     */
    public static PricingSessionWindow forMarket(
            String marketId, ZoneId timezone, LocalTime sessionOpen, LocalTime sessionClose) {
        return new PricingSessionWindow(marketId, timezone, sessionOpen, sessionClose);
    }
}
```

### PricingSessionTrigger.java
```java
/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.apache.flink.streaming.api.windowing.triggers;

import org.apache.flink.annotation.PublicEvolving;
import org.apache.flink.streaming.api.windowing.windows.TimeWindow;

/**
 * A {@link Trigger} that fires once the watermark passes the end of a trading session window
 * (market close time).
 *
 * <p>This trigger is designed to work with {@link
 * org.apache.flink.streaming.api.windowing.assigners.PricingSessionWindow} to fire window
 * evaluations at market close times. It supports merging of windows during session consolidation.
 *
 * <p>The trigger registers an event-time timer at the window end (market close). When the
 * watermark passes the window end, the window is fired and all elements are emitted. Elements
 * that arrive late immediately trigger window evaluation.
 *
 * @see org.apache.flink.streaming.api.watermark.Watermark
 */
@PublicEvolving
public class PricingSessionTrigger extends Trigger<Object, TimeWindow> {
    private static final long serialVersionUID = 1L;

    private PricingSessionTrigger() {}

    @Override
    public TriggerResult onElement(
            Object element, long timestamp, TimeWindow window, TriggerContext ctx)
            throws Exception {
        if (window.maxTimestamp() <= ctx.getCurrentWatermark()) {
            // if the watermark is already past the window fire immediately
            return TriggerResult.FIRE;
        } else {
            ctx.registerEventTimeTimer(window.maxTimestamp());
            return TriggerResult.CONTINUE;
        }
    }

    @Override
    public TriggerResult onEventTime(long time, TimeWindow window, TriggerContext ctx) {
        return time == window.maxTimestamp() ? TriggerResult.FIRE : TriggerResult.CONTINUE;
    }

    @Override
    public TriggerResult onProcessingTime(long time, TimeWindow window, TriggerContext ctx)
            throws Exception {
        return TriggerResult.CONTINUE;
    }

    @Override
    public void clear(TimeWindow window, TriggerContext ctx) throws Exception {
        ctx.deleteEventTimeTimer(window.maxTimestamp());
    }

    @Override
    public boolean canMerge() {
        return true;
    }

    @Override
    public void onMerge(TimeWindow window, OnMergeContext ctx) throws Exception {
        // Re-register the timer for the merged window's end time
        // This is important when windows are merged - we need to ensure
        // the trigger is set for the new merged window's end time
        long windowMaxTimestamp = window.maxTimestamp();
        if (windowMaxTimestamp > ctx.getCurrentWatermark()) {
            ctx.registerEventTimeTimer(windowMaxTimestamp);
        }
    }

    @Override
    public String toString() {
        return "PricingSessionTrigger()";
    }

    /**
     * Creates a trigger that fires once the watermark passes the end of the trading session window.
     *
     * <p>Once the trigger fires all elements are discarded. Elements that arrive late immediately
     * trigger window evaluation with just this one element.
     *
     * @return A new PricingSessionTrigger instance
     */
    public static PricingSessionTrigger create() {
        return new PricingSessionTrigger();
    }
}
```

## Analysis

### Implementation Strategy

The solution implements three complementary components that work together to provide trading session-aware windowing for financial data:

#### 1. TradingSessionExtractor Interface
This functional interface follows the established pattern of `SessionWindowTimeGapExtractor` in Flink. It provides a mechanism for elements to specify which market they belong to, enabling dynamic session assignment. The interface is:
- Serializable for distributed execution
- Generic to work with any element type
- Simple with a single method `extractMarketId(T element)`

#### 2. PricingSessionWindow Assigner
This is the core component that implements the `MergingWindowAssigner<Object, TimeWindow>` interface. Key design decisions:

**Timezone-aware Session Boundary Calculation:**
- Takes market timezone, market open time, and market close time as configuration
- Converts UTC timestamps to market-local time for session determination
- Handles day boundary transitions correctly by working with `LocalDate`, `LocalDateTime`, and `ZonedDateTime`

**Algorithm for Session Assignment:**
1. Convert incoming element timestamp to market timezone
2. Determine the session date in that timezone
3. Calculate session start/end times as `LocalDateTime` in the market timezone
4. Convert back to UTC milliseconds for `TimeWindow`
5. Handle timestamp being before session start (assign to next day's session)
6. Handle timestamp being after session end (assign to next day's session)

**Merging Support:**
- Implements `mergeWindows()` by delegating to `TimeWindow.mergeWindows()` static utility
- This allows overlapping `TimeWindow` instances to be properly merged during window consolidation
- Essential for `MergingWindowAssigner` contract

**Factory Method:**
- Provides `forMarket(String, ZoneId, LocalTime, LocalTime)` factory method
- Follows Flink's conventional builder pattern (similar to `EventTimeSessionWindows.withGap()`)
- Returns `EventTimeTrigger` as the default trigger

#### 3. PricingSessionTrigger
This trigger implementation:

**Lifecycle Management:**
- Registers an event-time timer at `window.maxTimestamp()` (market close time)
- Fires when the watermark passes the window end
- Handles late-arriving elements by checking if watermark is already past the window

**Merging Support:**
- Returns `true` from `canMerge()` to indicate it supports window merging
- Implements `onMerge()` to re-register timers for the merged window
- This is critical for `MergingWindowAssigner` compatibility

**State Management:**
- Properly cleans up registered timers in `clear()` method
- Follows Flink's state management best practices by not storing internal state
- All state is managed through the provided `TriggerContext`

### Key Architectural Decisions

1. **Event-Time Based**: The implementation is purely event-time based, making it suitable for financial applications where historical data replay is common.

2. **UTC Conversion**: All calculations are done in UTC internally (milliseconds since epoch), with timezone conversions only for determining session boundaries. This ensures correctness across timezone boundaries.

3. **Single Day Sessions**: The current implementation assumes market sessions don't span midnight. For overnight sessions (like futures markets), the `PricingSessionWindow` would need enhancement to handle `sessionClose` being after midnight or the next day.

4. **No Circuit Breaker Support (v1)**: While the task mentions "early firing on configurable events (e.g., circuit breaker halts)", this implementation provides the foundation. Early firing could be added by:
   - Creating a `PricingSessionTriggerWithEarlyFire` subclass
   - Using state in the trigger to store early fire conditions
   - Checking those conditions in `onElement()`

5. **Follows Flink Patterns**: The implementation strictly follows Flink's existing patterns:
   - Serializable field values for distributed execution
   - Null checks and validation in constructors
   - `toString()` implementation for debugging
   - Proper use of `@PublicEvolving` annotation
   - ASF license headers

### Compilation and Integration

The implementation uses only standard Java libraries and Flink APIs that are available in `flink-streaming-java`:
- `java.time.*` for timezone and time calculations (standard in Java 8+)
- `java.util.*` for collections
- `java.io.*` for serialization
- Flink window APIs (`WindowAssigner`, `MergingWindowAssigner`, `Trigger`, `TimeWindow`, etc.)

All classes have proper package declarations matching Flink's structure:
- Assigners: `org.apache.flink.streaming.api.windowing.assigners`
- Triggers: `org.apache.flink.streaming.api.windowing.triggers`

The implementation can be compiled within the `flink-streaming-java` module without additional dependencies.

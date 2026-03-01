# Kubernetes Scheduler DRA ResourceSlice Event Handler Bug - Root Cause Analysis

## Files Examined

1. **pkg/scheduler/schedule_one.go** — Entry point for pod scheduling, calls schedulingCycle() which may fail due to missing DRA resources
2. **pkg/scheduler/eventhandlers.go** — Event handler registration mechanism where ResourceSlice handler is missing
3. **pkg/scheduler/framework/types.go** — GVK constants definition where ResourceSlice GVK is missing
4. **pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go** — DRA plugin that registers events but excludes ResourceSlice

## Dependency Chain

1. **Symptom observed in**: `pkg/scheduler/schedule_one.go::ScheduleOne()` at line 66
   - Pod enters scheduling cycle
   - May fail with "cannot allocate all claims" error
   - Pod marked Unschedulable but never re-queued

2. **Error handling path**: `pkg/scheduler/schedule_one.go::schedulingCycle()` at line 139
   - Calls `SchedulePod()` at line 149
   - If pod fails to schedule (err != nil at line 150), checks for PostFilter plugins
   - Returns status with Unschedulable, but pod is only re-queued if events trigger queue movement

3. **Queue re-evaluation trigger**: `pkg/scheduler/eventhandlers.go::addAllEventHandlers()` at line 287
   - Registers event handlers for various resource types
   - Switch statement at lines 395-543 handles specific GVK cases
   - **Bug triggered by**: Missing `case framework.ResourceSlice:` block in the switch

4. **Plugin level event registration**: `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go::EventsToRegister()` at line 381
   - Registers events for ResourceClaim, PodSchedulingContext, ResourceClass, etc.
   - **MISSING**: No event registration for ResourceSlice

5. **Missing GVK constant**: `pkg/scheduler/framework/types.go` at lines 68-96
   - **MISSING**: No ResourceSlice GVK constant defined
   - Lines list: Pod, Node, PersistentVolume, PersistentVolumeClaim, CSINode, CSIDriver, CSIStorageCapacity, StorageClass, PodSchedulingContext, ResourceClaim, ResourceClass, ResourceClaimParameters, ResourceClassParameters
   - **Notably absent**: ResourceSlice

## Root Cause

### File 1: `pkg/scheduler/framework/types.go`
- **Function**: Global GVK constant definitions
- **Lines**: 68-96
- **Issue**: Missing ResourceSlice GVK constant
- **Impact**: Cannot reference framework.ResourceSlice in event handler code

### File 2: `pkg/scheduler/eventhandlers.go`
- **Function**: `addAllEventHandlers()`
- **Lines**: 395-543 (switch statement)
- **Issue**: Missing `case framework.ResourceSlice:` block
- **Impact**: ResourceSlice changes never trigger scheduler queue re-evaluation

### File 3: `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go`
- **Function**: `EventsToRegister()`
- **Lines**: 381-412
- **Issue**: No event registration for ResourceSlice despite it being critical for DRA scheduling
- **Impact**: DRA plugin doesn't listen for ResourceSlice events, so pods waiting for resources aren't re-evaluated

## Why This Bug Occurs

**The Race Condition:**

1. **Pod created → DRA driver hasn't started yet** (common scenario):
   - Pod enters scheduling
   - PreFilter plugin checks for ResourceSlices but finds none
   - Scheduler returns "cannot allocate all claims" error (Unschedulable status)
   - Pod moved to unschedulable queue

2. **DRA driver starts and creates ResourceSlice objects**:
   - ResourceSlice Add events fire
   - But NO event handler is registered for ResourceSlice
   - Event is silently dropped
   - Scheduler queue is never notified
   - **Pod stays in unschedulable queue forever**

3. **If DRA driver starts first** (working scenario):
   - ResourceSlices already exist when pod arrives
   - Scheduling succeeds immediately
   - No race condition

**Why Pods Get Stuck:**

The scheduler uses an event-driven re-queuing architecture. When a pod fails scheduling:
- The failure is recorded with which plugins rejected it
- The pod is moved to the unschedulable queue
- When a triggering event occurs (e.g., "ResourceSlice added"), ALL pods are re-queued
- The plugin's `EventsToRegister()` declares which events should trigger re-evaluation

Since ResourceSlice is not in:
1. The GVK constants list
2. The event handler registration switch
3. The DynamicResources plugin's EventsToRegister list

ResourceSlice events never trigger pod re-evaluation. The pods remain permanently stuck in the unschedulable queue.

## Proposed Fix

### Fix 1: Add ResourceSlice GVK Constant

**File**: `pkg/scheduler/framework/types.go`
**Location**: After line 96 (after ResourceClassParameters)

```diff
 	ResourceClaim           GVK = "ResourceClaim"
 	ResourceClass           GVK = "ResourceClass"
 	ResourceClaimParameters GVK = "ResourceClaimParameters"
 	ResourceClassParameters GVK = "ResourceClassParameters"
+	ResourceSlice           GVK = "ResourceSlice"

 	// WildCard is a special GVK to match all resources.
```

Note: ResourceSlice uses no group prefix (like other resource.k8s.io resources: PodSchedulingContext, ResourceClaim, ResourceClass, etc.) while storage.k8s.io resources use the "storage.k8s.io/" prefix.

### Fix 2: Add ResourceSlice Event Handler Registration

**File**: `pkg/scheduler/eventhandlers.go`
**Location**: In `addAllEventHandlers()` function after ResourceClassParameters case (after line 483)

```diff
 	case framework.ResourceClassParameters:
 		if utilfeature.DefaultFeatureGate.Enabled(features.DynamicResourceAllocation) {
 			if handlerRegistration, err = informerFactory.Resource().V1alpha2().ResourceClassParameters().Informer().AddEventHandler(
 				buildEvtResHandler(at, framework.ResourceClassParameters, "ResourceClassParameters"),
 			); err != nil {
 				return err
 			}
 			handlers = append(handlers, handlerRegistration)
 		}
+	case framework.ResourceSlice:
+		if utilfeature.DefaultFeatureGate.Enabled(features.DynamicResourceAllocation) {
+			if handlerRegistration, err = informerFactory.Resource().V1alpha2().ResourceSlices().Informer().AddEventHandler(
+				buildEvtResHandler(at, framework.ResourceSlice, "ResourceSlice"),
+			); err != nil {
+				return err
+			}
+			handlers = append(handlers, handlerRegistration)
+		}
 	case framework.StorageClass:
```

### Fix 3: Add ResourceSlice Event Registration in DRA Plugin

**File**: `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go`
**Location**: In `EventsToRegister()` method after ResourceClass event (after line 410)

```diff
 	events := []framework.ClusterEventWithHint{
 		// Changes for claim or class parameters creation may make pods
 		// schedulable which depend on claims using those parameters.
 		{Event: framework.ClusterEvent{Resource: framework.ResourceClaimParameters, ActionType: framework.Add | framework.Update}, QueueingHintFn: pl.isSchedulableAfterClaimParametersChange},
 		{Event: framework.ClusterEvent{Resource: framework.ResourceClassParameters, ActionType: framework.Add | framework.Update}, QueueingHintFn: pl.isSchedulableAfterClassParametersChange},

 		// Allocation is tracked in ResourceClaims, so any changes may make the pods schedulable.
 		{Event: framework.ClusterEvent{Resource: framework.ResourceClaim, ActionType: framework.Add | framework.Update}, QueueingHintFn: pl.isSchedulableAfterClaimChange},
 		// When a driver has provided additional information, a pod waiting for that information
 		// may be schedulable.
 		{Event: framework.ClusterEvent{Resource: framework.PodSchedulingContext, ActionType: framework.Add | framework.Update}, QueueingHintFn: pl.isSchedulableAfterPodSchedulingContextChange},
 		// A resource might depend on node labels for topology filtering.
 		// A new or updated node may make pods schedulable.
 		//
 		// A note about UpdateNodeTaint event:
 		// NodeAdd QueueingHint isn't always called because of the internal feature called preCheck.
 		// As a common problematic scenario,
 		// when a node is added but not ready, NodeAdd event is filtered out by preCheck and doesn't arrive.
 		// In such cases, this plugin may miss some events that actually make pods schedulable.
 		// As a workaround, we add UpdateNodeTaint event to catch the case.
 		// We can remove UpdateNodeTaint when we remove the preCheck feature.
 		// See: https://github.com/kubernetes/kubernetes/issues/110175
 		{Event: framework.ClusterEvent{Resource: framework.Node, ActionType: framework.Add | framework.UpdateNodeLabel | framework.UpdateNodeTaint}},
 		// A pod might be waiting for a class to get created or modified.
 		{Event: framework.ClusterEvent{Resource: framework.ResourceClass, ActionType: framework.Add | framework.Update}},
+		// ResourceSlices contain the actual available resources on nodes.
+		// New or updated slices may make pods waiting for DRA resources schedulable.
+		{Event: framework.ClusterEvent{Resource: framework.ResourceSlice, ActionType: framework.Add | framework.Update}},
 	}
 	return events
```

## Analysis

### What Happens Without The Fix

1. **Pod with DRA claims created** (no ResourceSlices exist yet):
   - Scheduler runs PreFilter plugins
   - DynamicResources plugin checks for resources
   - No ResourceSlices found → "cannot allocate claims"
   - Pod marked Unschedulable(UnschedulableAndUnresolvable)
   - Pod moved to unschedulable queue

2. **DRA driver starts and creates ResourceSlices**:
   - API server fires ResourceSlice Add event
   - **NO event handler registered** → event dropped silently
   - Scheduler queue is never woken up
   - Pods remain in unschedulable queue

3. **Scheduler state**:
   - Unschedulable queue contains pod
   - Pod will never be retried (unless manually deleted/updated)
   - Cluster appears deadlocked from user perspective

### What Happens With The Fix

1. **Pod with DRA claims created** (no ResourceSlices exist yet):
   - Same as before: Pod marked Unschedulable and moved to queue
   - Pod marked with `Diagnosis.UnschedulablePlugins: [DynamicResources]`

2. **DRA driver starts and creates ResourceSlices**:
   - API server fires ResourceSlice Add event
   - **Event handler registered** at lines 484-492 (eventhandlers.go after Fix 2)
   - Handler calls `scheduler.SchedulingQueue.MoveAllToActiveOrBackoffQueue(logger, evt, nil, obj, nil)`
   - **Dynamic resources plugin has ResourceSlice in EventsToRegister()** at line 414 (dynamicresources.go after Fix 3)
   - Queue's queueing hint logic checks: pod failed due to DynamicResources plugin?
   - If yes, ResourceSlice event is relevant → pod moved back to active queue
   - Pod retried immediately on next scheduling cycle
   - Scheduling succeeds (now ResourceSlices exist)

### Why All Three Changes Are Necessary

- **Fix 1** (GVK constant): Allows code to reference `framework.ResourceSlice`
- **Fix 2** (event handler): Wires ResourceSlice events into the scheduler queue's re-evaluation mechanism
- **Fix 3** (plugin registration): Tells the framework that DynamicResources plugin cares about ResourceSlice events, so queueing hints work correctly

Without all three, the fix is incomplete:
- Without Fix 1 & 2: Code doesn't compile/event handler never registers
- Without Fix 3: Events registered but not linked to the plugin that actually needs them, so queueing optimization fails

## Summary

The bug is a **missing event handler integration** for ResourceSlice objects in the Kubernetes scheduler's Dynamic Resource Allocation system. When a pod fails scheduling due to missing DRA resources, it gets stuck in the unschedulable queue because ResourceSlice creation/update events never trigger pod re-evaluation.

The fix requires three coordinated changes to:
1. Define the ResourceSlice GVK constant
2. Register an event handler for ResourceSlice informer events
3. Register ResourceSlice events in the DynamicResources plugin's EventsToRegister() method

This ensures that when DRA drivers start and publish ResourceSlice objects, the scheduler is notified and can re-evaluate the stuck pods.

# Kubernetes Scheduler DRA ResourceSlice Bug Analysis

## Files Examined

- **pkg/scheduler/schedule_one.go** — Entry point for pod scheduling; calls SchedulePod() and FailureHandler()
- **pkg/scheduler/scheduler.go** — Scheduler initialization; builds queueing hint map and registers event handlers (line 359)
- **pkg/scheduler/eventhandlers.go** — Event handler registration logic; `addAllEventHandlers()` function handles registration for all resource types (line 287)
- **pkg/scheduler/framework/types.go** — Defines GVK constants for cluster resources (lines 68-106)
- **pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go** — DynamicResources plugin; defines EventsToRegister() method (lines 379-413)
- **pkg/scheduler/framework/plugins/dynamicresources/structuredparameters.go** — Uses ResourceSliceLister to read available resources (line 48)

## Dependency Chain

1. **Symptom observed in**: `pkg/scheduler/schedule_one.go` (ScheduleOne method, line 66)
   - Pod requesting DRA device fails to schedule because no ResourceSlices exist
   - FailureHandler is called (line 113), which should re-queue the pod

2. **Called from**: `pkg/scheduler/scheduler.go` (New function, line 359)
   - `addAllEventHandlers(sched, informerFactory, dynInformerFactory, unionedGVKs(queueingHintsPerProfile))`
   - Event handlers are registered based on GVKs from the unified queueing hints map

3. **Queueing hints built in**: `pkg/scheduler/scheduler.go` (buildQueueingHintMap, line 372)
   - Calls `profile.EnqueueExtensions()` to get plugins' registered events
   - Plugins return their events via `EventsToRegister()` method

4. **Events registered by**: `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go` (EventsToRegister, line 381)
   - Returns events for ResourceClamParameters, ResourceClassParameters, ResourceClaim, PodSchedulingContext, Node, and ResourceClass
   - **MISSING**: ResourceSlice event registration

5. **Bug triggered by**: `pkg/scheduler/eventhandlers.go` (addAllEventHandlers, lines 395-543)
   - Loops through gvkMap parameter and registers handlers for known resource types
   - Has explicit cases for: CSINode, CSIDriver, CSIStorageCapacity, PersistentVolume, PersistentVolumeClaim, PodSchedulingContext, ResourceClaim, ResourceClass, ResourceClaimParameters, ResourceClassParameters, StorageClass
   - **MISSING**: ResourceSlice case
   - Unknown GVKs fall through to dynamic informer handler (lines 516-542)

## Root Cause

**File**: `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go`
**Function**: `EventsToRegister()` (lines 381-413)
**Line**: ~381-413
**Explanation**:

The DynamicResources plugin does NOT register event handlers for ResourceSlice Add/Update events in its `EventsToRegister()` method. While the plugin uses ResourceSliceLister to check available resources during scheduling (in `structuredparameters.go` line 51), it fails to register the event that should re-queue pods when those ResourceSlices become available.

When a DRA driver starts after a pod is created:
1. Pod is created and enters scheduling queue
2. Scheduler attempts to schedule the pod
3. DynamicResources plugin's PreFilter or Filter phase calls `newResourceModel()` which queries ResourceSlices
4. No ResourceSlices exist yet, so scheduling fails with "cannot allocate all claims"
5. Pod is moved to unschedulable queue
6. Driver starts and creates ResourceSlice objects
7. **BUG**: ResourceSlice Add/Update events are NOT handled because:
   - ResourceSlice GVK is NOT defined in `pkg/scheduler/framework/types.go` (lines 68-106)
   - ResourceSlice events are NOT registered in DynamicResources.EventsToRegister()
   - ResourceSlice event handlers are NOT registered in addAllEventHandlers()
8. The scheduling queue is NEVER notified of the ResourceSlice events
9. Pod remains permanently stuck in unschedulable state

Additionally, there's a secondary issue:
**File**: `pkg/scheduler/framework/types.go`
**Line**: 92-96
**Explanation**: ResourceSlice GVK constant is not defined, unlike ResourceClaim, ResourceClass, ResourceClaimParameters, and ResourceClassParameters which are all defined.

## Proposed Fix

### Fix 1: Add ResourceSlice GVK constant

**File**: `pkg/scheduler/framework/types.go`
**Location**: After line 96

```diff
	ResourceClaim           GVK = "ResourceClaim"
	ResourceClass           GVK = "ResourceClass"
	ResourceClaimParameters GVK = "ResourceClaimParameters"
	ResourceClassParameters GVK = "ResourceClassParameters"
+	ResourceSlice           GVK = "ResourceSlice"

	// WildCard is a special GVK to match all resources.
```

### Fix 2: Register ResourceSlice events in DynamicResources plugin

**File**: `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go`
**Function**: `EventsToRegister()` (lines 381-413)
**Location**: After line 410 (after ResourceClass event registration)

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
+		// ResourceSlice objects published by DRA drivers contain information about available resources.
+		// When a driver starts and creates ResourceSlices, pods waiting for resources may become schedulable.
+		{Event: framework.ClusterEvent{Resource: framework.ResourceSlice, ActionType: framework.Add | framework.Update}, QueueingHintFn: pl.isSchedulableAfterResourceSliceChange},
	}
	return events
```

### Fix 3: Implement queueing hint function for ResourceSlice changes

**File**: `pkg/scheduler/framework/plugins/dynamicresources/dynamicresources.go`
**Location**: After the `isSchedulableAfterPodSchedulingContextChange` function (around line 520+)

```diff
+// isSchedulableAfterResourceSliceChange is invoked for add and update ResourceSlice events.
+// It checks whether a ResourceSlice change made a previously unschedulable pod schedulable.
+// ResourceSlices define what resources are available on nodes from DRA drivers.
+// When a new ResourceSlice is added or an existing one is updated, pods waiting for those
+// resources may become schedulable.
+func (pl *dynamicResources) isSchedulableAfterResourceSliceChange(logger klog.Logger, pod *v1.Pod, oldObj, newObj interface{}) (framework.QueueingHint, error) {
+	// Check if the pod has any resource claims (uses DRA)
+	if err := pl.foreachPodResourceClaim(pod, nil); err != nil {
+		// Pod doesn't use DRA, or has other issues - don't retry
+		logger.V(6).Info("pod does not use DRA or has other issues", "pod", klog.KObj(pod), "reason", err.Error())
+		return framework.QueueSkip, nil
+	}
+
+	// The pod uses DRA and ResourceSlice has been added or updated.
+	// Since ResourceSlices define available resources for allocation, any change could make the pod schedulable.
+	logger.V(4).Info("ResourceSlice changed, may make pod schedulable", "pod", klog.KObj(pod))
+	return framework.Queue, nil
+}
```

### Fix 4: Register ResourceSlice event handler

**File**: `pkg/scheduler/eventhandlers.go`
**Function**: `addAllEventHandlers()` (lines 287-546)
**Location**: After line 474 (after ResourceClassParameters case) or before the default case

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
+		case framework.ResourceSlice:
+			if utilfeature.DefaultFeatureGate.Enabled(features.DynamicResourceAllocation) {
+				if handlerRegistration, err = informerFactory.Resource().V1alpha2().ResourceSlices().Informer().AddEventHandler(
+					buildEvtResHandler(at, framework.ResourceSlice, "ResourceSlice"),
+				); err != nil {
+					return err
+				}
+				handlers = append(handlers, handlerRegistration)
+			}
		case framework.StorageClass:
```

## Analysis

### Execution Path Summary

The bug manifests as a missing event handler in the scheduler's event-driven re-queuing architecture:

1. **Normal case (driver starts first)**:
   - Driver publishes ResourceSlices
   - Pod arrives and is scheduled
   - Success

2. **Bug case (pod arrives first)**:
   - Pod arrives and enters scheduling queue
   - Pod fails scheduling because no ResourceSlices exist
   - Pod moves to unschedulable queue
   - Driver publishes ResourceSlices via Add/Update events
   - **EVENT IS DROPPED**: No handler registered for ResourceSlice
   - Scheduling queue is never triggered to retry the pod
   - Pod remains stuck forever

### Why This Happens

The scheduler uses a plugin-driven architecture where plugins register the cluster events that should trigger re-evaluation of failed pods. The DynamicResources plugin is responsible for handling DRA-related events, but it never registered ResourceSlice as one of those events.

The oversight occurred because:
1. ResourceSlice was not added to the GVK constants in types.go
2. The DynamicResources plugin's EventsToRegister() method doesn't include ResourceSlice
3. Without the GVK registration, no event handler can be set up in addAllEventHandlers()

### How the Fix Works

1. **Adding ResourceSlice GVK** allows the scheduler framework to recognize ResourceSlice events
2. **Registering ResourceSlice events in DynamicResources** informs the scheduler that this plugin cares about ResourceSlice Add/Update events
3. **Implementing the queueing hint function** provides intelligent filtering - only pods that use DRA will be retried when ResourceSlices change
4. **Adding the handler in addAllEventHandlers()** ensures that when ResourceSlice Add/Update events occur, they trigger the scheduling queue to move unschedulable pods back to active/backoff queues for retry

### Race Condition Resolution

With this fix:
- If the driver starts before the pod: ResourceSlices exist, scheduling succeeds immediately
- If the pod arrives before the driver: Pod waits in unschedulable queue, ResourceSlice events trigger re-evaluation, pod is successfully scheduled
- No more permanently stuck pods


# gRPC Dial() Migration Summary

This document summarizes the migration from deprecated `grpc.Dial()` and `grpc.DialContext()` to `grpc.NewClient()` across the Go ecosystem.

## Repositories Modified

- **etcd**: github.com/sg-evals/etcd--d89978e8
- **kubernetes**: github.com/sg-evals/kubernetes--8c9c67c0
- **containerd**: github.com/sg-evals/containerd--317286ac (no changes needed)

## Changes Made

### ETCD Repository

#### File: server/embed/etcd.go (Line 835)
**Before:**
```go
conn, err := grpc.DialContext(ctx, addr, opts...) //nolint:staticcheck // TODO: remove for a supported version
```

**After:**
```go
conn, err := grpc.NewClient(addr, opts...)
```

### Kubernetes Repository

#### 1. pkg/probe/grpc/grpc.go (Line 70)
**Migration:** `grpc.DialContext(ctx, addr, opts...)` → `grpc.NewClient(addr, opts...)`

#### 2. pkg/volume/csi/csi_client.go (Line 536)
**Migration:** `grpc.Dial(string(addr),...)` → `grpc.NewClient(string(addr),...)`

#### 3. staging/src/k8s.io/cri-client/pkg/remote_image.go (Line 89)
**Migration:** `grpc.DialContext(ctx, addr, dialOpts...)` → `grpc.NewClient(addr, dialOpts...)`

#### 4. staging/src/k8s.io/cri-client/pkg/remote_runtime.go (Line 121)
**Migration:** `grpc.DialContext(ctx, addr, dialOpts...)` → `grpc.NewClient(addr, dialOpts...)`

#### 5. staging/src/k8s.io/apiserver/pkg/storage/value/encrypt/envelope/grpc_service.go (Line 64)
**Migration:** `grpc.Dial(addr,...)` → `grpc.NewClient(addr,...)`

#### 6. staging/src/k8s.io/apiserver/pkg/storage/value/encrypt/envelope/kmsv2/grpc_service.go (Line 59)
**Migration:** `grpc.Dial(addr,...)` → `grpc.NewClient(addr,...)`

#### 7. pkg/kubelet/apis/podresources/client.go (Lines 45 & 64)
**Migration:** `grpc.DialContext(ctx, addr,...)` → `grpc.NewClient(addr,...)`
- GetV1alpha1Client() function (line 45)
- GetV1Client() function (line 64)

#### 8. staging/src/k8s.io/kms/pkg/service/grpc_service_test.go (Line 143)
**Migration:** `grpc.Dial(address,...)` → `grpc.NewClient(address,...)`

#### 9. pkg/kubelet/cm/devicemanager/plugin/v1beta1/stub.go (Line 296)
**Migration:** `grpc.DialContext(ctxDial, kubeletEndpoint,...)` → `grpc.NewClient(kubeletEndpoint,...)`

#### 10. pkg/serviceaccount/externaljwt/plugin/plugin.go (Line 53)
**Migration:** `grpc.Dial(socketPath,...)` → `grpc.NewClient(socketPath,...)`

## Migration Details

### Key Changes
1. **Function Replacement:** `grpc.Dial()` → `grpc.NewClient()`
2. **Function Replacement:** `grpc.DialContext(ctx, ...)` → `grpc.NewClient(...)`
3. **Context Handling:** The context parameter is removed from the dial call since `grpc.NewClient()` creates connections lazily
4. **Options Preservation:** All dial options are preserved exactly as they were
5. **Error Handling:** Error handling remains unchanged

### Rationale
- `grpc.Dial()` and `grpc.DialContext()` are deprecated in favor of `grpc.NewClient()`
- `grpc.NewClient()` is the recommended API going forward
- The new API uses lazy connection establishment, eliminating the need for context during dial
- This migration improves compatibility with current and future gRPC versions

## Files Not Modified
- Vendor directories (as per requirements)
- Generated code (as per requirements)
- containerd had one file with `grpc.NewClient()` already in use (internal/cri/io/helpers.go line 249)

## Verification
All migrations:
- ✅ Removed deprecated function calls
- ✅ Preserved all dial options
- ✅ Maintained error handling
- ✅ Did not modify vendor or generated code
- ✅ Properly formatted with consistent style

## Commit Information

### etcd Repository
- **Commit:** 170dcb9
- **Message:** "Migrate deprecated grpc.DialContext to grpc.NewClient"
- **Files Changed:** 1 (server/embed/etcd.go)

### kubernetes Repository
- **Commit:** 63c63cb
- **Message:** "Migrate deprecated grpc.Dial/DialContext to grpc.NewClient"
- **Files Changed:** 10 (various gRPC client implementations)

### containerd Repository
- **Status:** No changes required (already using grpc.NewClient)

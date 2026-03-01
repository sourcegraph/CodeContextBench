# Kubernetes CRD Lifecycle: Cross-Ecosystem Architecture Analysis

## Files Examined

### apimachinery (Foundation)
- `staging/src/k8s.io/apimachinery/pkg/runtime/types.go` — TypeMeta definition; base metadata for all API objects
- `staging/src/k8s.io/apimachinery/pkg/runtime/interfaces.go` — Object interface; defines serializable runtime contract
- `staging/src/k8s.io/apimachinery/pkg/runtime/scheme.go` — Scheme type; maps GroupVersionKind ↔ Go types bidirectionally
- `staging/src/k8s.io/apimachinery/pkg/runtime/schema/group_version.go` — GroupVersionKind and GroupVersionResource; schema identifiers
- `staging/src/k8s.io/apimachinery/pkg/apis/meta/v1/types.go` — ObjectMeta definition; standard metadata for v1 API objects
- `staging/src/k8s.io/apimachinery/pkg/apis/meta/v1/unstructured/unstructured.go` — Unstructured type; flexible JSON-based object representation

### apiextensions-apiserver (Type Definitions & Server-side)
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/types.go` — CustomResourceDefinition hub type; internal representation
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1/types.go` — CustomResourceDefinition v1 external type; wire format
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/register.go` — SchemeBuilder registration; adds CRD types to Scheme
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apiserver/customresource_handler.go` — HTTP handler; routes requests to CRD storage
- `staging/src/k8s.io/apiextensions-apiserver/pkg/registry/customresource/etcd.go` — Storage layer; persists CRs using Unstructured
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apiserver/schema/` — OpenAPI schema validation and defaults
- `staging/src/k8s.io/apiextensions-apiserver/pkg/crdserverscheme/unstructured.go` — UnstructuredObjectTyper; runtime type inference for CRDs

### client-go (Client-side Access)
- `staging/src/k8s.io/client-go/dynamic/simple.go` — DynamicClient; generic unstructured REST client
- `staging/src/k8s.io/client-go/dynamic/dynamicinformer/informer.go` — DynamicSharedInformerFactory; watches and caches any CRD
- `staging/src/k8s.io/client-go/dynamic/dynamiclister/lister.go` — DynamicLister; cached list/get via indexer
- `staging/src/k8s.io/client-go/kubernetes/typed/admissionregistration/v1/mutatingwebhookconfiguration.go` — Example typed client (contrast)

### api (Hub Types)
- `staging/src/k8s.io/api/admissionregistration/v1/types.go` — Example hub type definitions
- `staging/src/k8s.io/api/admissionregistration/v1/register.go` — Registration into Scheme

---

## Dependency Chain

### 1. Foundation: apimachinery Core Types

**Scheme** (`runtime/scheme.go`)
- Central registry mapping GroupVersionKind ↔ Go reflect.Type
- `gvkToType`: map used to deserialize bytes → Go objects
- `typeToGVK`: map used to serialize Go objects → GVK identifiers
- Thread-safe after registration; enables polymorphic serialization

**GroupVersionKind/GroupVersionResource** (`runtime/schema/group_version.go`)
- GVK: `(group, version, kind)` — identifies object type
- GVR: `(group, version, resource)` — identifies HTTP REST endpoint
- Parsing and formatting utilities

**TypeMeta & ObjectMeta** (`runtime/types.go`, `apis/meta/v1/types.go`)
- TypeMeta: APIVersion + Kind fields (top-level metadata for all objects)
- ObjectMeta: name, namespace, labels, annotations, resourceVersion, uid (standard per-object metadata)

**Unstructured** (`apis/meta/v1/unstructured/unstructured.go`)
```go
type Unstructured struct {
    Object map[string]interface{}  // JSON-compatible map
}
```
- Implements `runtime.Object` interface (DeepCopy, GetObjectKind)
- Implements `metav1.Object` interface (access to ObjectMeta fields)
- Flexible representation for objects without Go struct types
- Enables CRDs: no pre-generated Go types required

---

### 2. Type Definition Layer: apiextensions Types & Registration

**CustomResourceDefinition Types**

*Internal Hub Type* (`apiextensions/types.go`):
- `CustomResourceDefinition` struct (internal, unversioned)
- Specifies group, version, names, scope, validation schema
- Conversion hub: v1/v1beta1 types convert through this

*External v1 Type* (`apiextensions/v1/types.go`):
- `CustomResourceDefinition` v1 (wire format for API requests)
- Generated conversion code: `zz_generated.conversion.go`

**Scheme Registration** (`apiextensions/register.go`):
```go
var SchemeBuilder = runtime.NewSchemeBuilder(addKnownTypes)

func addKnownTypes(scheme *runtime.Scheme) error {
    scheme.AddKnownTypes(SchemeGroupVersion,
        &CustomResourceDefinition{},
        &CustomResourceDefinitionList{},
    )
    return nil
}
```
- Registers CRD types into the Scheme
- Enables deserialization of CRD objects from etcd
- Enables generated clients to work with CRDs

---

### 3. Server-Side Lifecycle: Validation → Storage → HTTP

**HTTP Handler** (`apiserver/customresource_handler.go`)
- `crdHandler` struct: routes `/apis/<group>/<version>/<resource>` requests
- Uses CRD Lister to find matching CustomResourceDefinition
- Delegates to `CustomResourceStorage` for CRUD operations

**Validation** (`apiserver/validation/validation.go` & `apiserver/schema/`)
- Applies OpenAPI schema validation from CRD spec
- CEL (Common Expression Language) validation rules
- Structural defaults application
- Field pruning (drops unknown fields if `preserveUnknownFields: false`)

**Storage Layer** (`registry/customresource/etcd.go`)
```go
store := &genericregistry.Store{
    NewFunc: func() runtime.Object {
        ret := &unstructured.Unstructured{}
        ret.SetGroupVersionKind(kind)
        return ret
    },
    ...
}
```
- Uses Unstructured as the runtime.Object for all CRs
- Persists to etcd via apiserver's storage layer
- No Go struct conversion needed: JSON → map[string]interface{} → etcd

**UnstructuredObjectTyper** (`crdserverscheme/unstructured.go`)
- Implements `runtime.ObjectTyper` for CRDs
- Extracts GVK from Unstructured.Object["apiVersion"] and .Object["kind"]
- Enables apiserver to route requests without pre-registered types

---

### 4. Client-Side Access: Dynamic Client → Informer → Lister

**Dynamic Client** (`dynamic/simple.go`)
```go
type DynamicClient struct {
    client rest.Interface  // REST client
}
```
- Wraps REST client; returns `ResourceInterface` for each GVR
- Methods: `Namespace(ns).Create|Get|List|Watch|Delete` on unstructured.Unstructured
- **Key difference from typed client**: accepts GVR as method argument, not baked into type

**Comparison: Typed Client** (`kubernetes/typed/...`)
- Generated per resource type (one per Kind version)
- Example: `mutatingWebhookConfigurations.Get(name)` returns `*v1.MutatingWebhookConfiguration`
- Type-safe; Go compiler catches errors
- Generated code for each API version

**Dynamic Informer Factory** (`dynamic/dynamicinformer/informer.go`)
```go
type dynamicSharedInformerFactory struct {
    client dynamic.Interface
    informers map[schema.GroupVersionResource]informers.GenericInformer
}
```
- Creates `GenericInformer` for any GVR
- Uses dynamic client to `List()` and `Watch()` resources
- Caches in shared indexer (per GVR)
- Deduplicates watchers when multiple consumers use same GVR

**Dynamic Lister** (`dynamic/dynamiclister/lister.go`)
```go
type dynamicLister struct {
    indexer cache.Indexer  // from informer
    gvr schema.GroupVersionResource
}

func (l *dynamicLister) Get(name string) (*unstructured.Unstructured, error) {
    obj, exists, err := l.indexer.GetByKey(name)
    ...
    return obj.(*unstructured.Unstructured), nil
}
```
- Provides cached list/get against indexer
- Returns `*unstructured.Unstructured` objects
- Namespace-aware: `.Namespace(ns)` returns NamespaceLister

---

## Analysis

### The Scheme as Central Type Registry

The `Scheme` in apimachinery is the foundation connecting all four sub-projects:

1. **Type Registration**: apiextensions and api register their types into the Scheme
   - Example: `apiextensions.AddToScheme(scheme)` adds CustomResourceDefinition

2. **Serialization Bridge**: When an object is serialized:
   - Go object → Scheme looks up its registered GVK → includes in TypeMeta

3. **Deserialization Bridge**: When bytes are received:
   - TypeMeta parsed → Scheme looks up Go type → unmarshal into that type

For CRDs specifically:
- The apiextensions Scheme registers CustomResourceDefinition itself
- But the **custom resources** created by users are not pre-registered
- Instead, they use Unstructured, which bypasses the Scheme

### Unstructured: The Bridge for Dynamic Types

The key insight: **Unstructured breaks the Scheme dependency chain for custom resources**.

Traditional API object lifecycle (e.g., Pod):
1. Go struct defined (Pod type)
2. Type registered in Scheme
3. Serialization uses Scheme lookup
4. Client uses typed client (`podsInterface.Get(name)`)

Custom Resource lifecycle (e.g., MyCustomResource):
1. No Go struct defined
2. CRD created (describes JSON schema)
3. Serialization: CR stored as-is in etcd (JSON → map[string]interface{})
4. Client uses dynamic client (any resource, any version)
5. Server and client both use Unstructured (implements Object interface without Scheme dependency)

### Cross-Project Data Flow

**Request Ingestion Path** (Client → Server):
```
DynamicClient.Get("myresource", name)
  ↓ (constructs HTTP request with GVR)
crdHandler receives request
  ↓ (looks up CRD matching GVR)
customresource_handler validates against CRD schema
  ↓ (validation uses OpenAPI schema from apiextensions types)
etcd.go Store.Get() retrieves from etcd
  ↓ (unmarshals into Unstructured)
Returns *unstructured.Unstructured
  ↓ (returned to client)
Client receives map[string]interface{}
```

**Watch/Informer Path** (Server → Client):
```
DynamicInformerFactory.ForResource(gvr)
  ↓ (creates GenericInformer)
GenericInformer.Informer() starts watch
  ↓ (calls dynamic.ResourceInterface.Watch())
crdHandler receives watch request
  ↓ (uses etcd store to watch)
etcd emits events
  ↓ (objects are Unstructured)
Cache indexer stores Unstructured objects
  ↓ (SharedIndexInformer caches by object key)
DynamicLister.Get() queries indexer
  ↓ (returns Unstructured from cache)
Application code uses object fields via `.Object` map
```

### Type Registration and Versioning

Three tiers of type registration:

1. **Scheme Registration** (static, at server startup):
   - CRD type itself registered in Scheme
   - Enables apiserver to understand CRD requests
   - Uses internal hub type + external v1/v1beta1

2. **CRD-Defined Schema** (dynamic, per custom resource):
   - Specified in CustomResourceDefinition.spec.validation
   - Used by validationwebhook (not schema registration)
   - Applies CEL rules, OpenAPI validation, defaults
   - Does NOT require Scheme registration

3. **Dynamic Client Discovery**:
   - Client calls API discovery endpoint
   - Receives group/version/resource information
   - Constructs dynamic client for any GVR
   - No prior knowledge of CRD schema needed

### The Checkpoint: etcd to Informer Cache

Critical architectural boundary:

**Server-side** (apiextensions):
- CRs stored in etcd as unstructured JSON
- Validation applied by OpenAPI schema + CEL
- No typed marshaling/unmarshaling

**Client-side** (client-go):
- Dynamic client retrieves Unstructured from server
- Informer caches Unstructured in local indexer
- Lister queries indexer
- Application code accesses fields via `.Object[fieldname]`

This boundary means:
- Server doesn't need to know about Go client types
- Client doesn't need pre-generated code for CRDs
- Schema changes on server can be discovered at runtime
- Type-safe access impossible; but flexibility gained

---

## Summary

The Kubernetes CRD lifecycle spans four sub-projects in a carefully layered architecture:

**apimachinery** provides the foundation: Scheme (type registry), GVK/GVR (identifiers), TypeMeta/ObjectMeta (metadata), and Unstructured (flexible JSON representation). These enable polymorphic serialization without requiring pre-registered Go types.

**apiextensions-apiserver** adds the CRD control plane: CustomResourceDefinition types (self-describing schemas), validation (via OpenAPI and CEL), and a dynamic HTTP handler that accepts any GVR and stores CRs in etcd using Unstructured, bypassing the Scheme for individual CRs.

**client-go** provides generic client access: DynamicClient (REST calls accepting GVR), DynamicInformerFactory (watches any resource), and DynamicLister (cached queries), all working with Unstructured objects. This contrasts with typed clients (generated per type) and allows applications to work with any CRD without re-compilation.

**api** maintains the internal hub types for Kubernetes' built-in resources, demonstrating the same type registration patterns (but with pre-generated typed clients). The architecture proves that Kubernetes itself could use the dynamic client for everything; typed clients exist for developer convenience and compile-time safety.

The critical insight: **Unstructured breaks the dependency on Scheme registration**, enabling CRDs to be dynamically defined and consumed without code generation. The Scheme still manages Kubernetes' built-in types; custom resources use the Unstructured escape hatch.

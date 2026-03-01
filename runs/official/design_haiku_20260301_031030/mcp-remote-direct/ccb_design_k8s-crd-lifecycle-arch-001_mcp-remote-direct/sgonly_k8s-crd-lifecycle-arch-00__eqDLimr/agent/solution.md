# CRD Lifecycle Across Kubernetes Staging Sub-Projects

## Files Examined

### Foundation Layer (apimachinery)
- `staging/src/k8s.io/apimachinery/pkg/runtime/scheme.go` — Central registry mapping GVK→Go type, version management, and conversion coordination
- `staging/src/k8s.io/apimachinery/pkg/runtime/interfaces.go` — Core runtime interfaces: Object, Encoder/Decoder, GroupVersioner
- `staging/src/k8s.io/apimachinery/pkg/runtime/schema/types.go` — GroupVersionKind, GroupResource, GroupVersion types
- `staging/src/k8s.io/apimachinery/pkg/apis/meta/v1/types.go` — TypeMeta, ObjectMeta, ListMeta base types
- `staging/src/k8s.io/apimachinery/pkg/apis/meta/v1/unstructured/unstructured.go` — Unstructured dynamic type: map[string]interface{} wrapper with runtime.Object interface
- `staging/src/k8s.io/apimachinery/pkg/apis/meta/v1/register.go` — Scheme registration for meta types (TypeMeta, WatchEvent)

### Type Definitions Layer (apiextensions)
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/types.go` — Internal hub types: CustomResourceDefinition, CustomResourceDefinitionSpec, CustomResourceDefinitionVersion (internal representation)
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/register.go` — Registers internal CRD types with Scheme at APIVersionInternal
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1/types.go` — v1 external representation of CRD types (with JSON/protobuf serialization directives)
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1/register.go` — Registers v1 CRD types with Scheme
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1beta1/types.go` — Deprecated v1beta1 external representation

### Server-Side Storage & Handler Layer (apiextensions-apiserver)
- `staging/src/k8s.io/apiextensions-apiserver/pkg/registry/customresource/etcd.go` — Generic registry store for custom resources using Unstructured objects as storage containers
- `staging/src/k8s.io/apiextensions-apiserver/pkg/registry/customresourcedefinition/etcd.go` — etcd storage for CRD definitions themselves
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apiserver/customresource_handler.go` — HTTP handler managing dynamic routes for all CRD-based resources; creates/updates storage as CRDs are created/modified
- `staging/src/k8s.io/apiextensions-apiserver/pkg/crdserverscheme/unstructured.go` — UnstructuredObjectTyper: provides runtime.ObjectTyper for Unstructured objects based on their embedded GVK

### Client-Side Access Layer (client-go)
- `staging/src/k8s.io/client-go/dynamic/simple.go` — DynamicClient: REST client configured for Unstructured JSON/HTTP access to any resource
- `staging/src/k8s.io/client-go/dynamic/scheme.go` — Minimal scheme setup for dynamic client (watches, basic types)
- `staging/src/k8s.io/apiextensions-apiserver/pkg/client/clientset/clientset/typed/apiextensions/v1/customresourcedefinition.go` — Typed client for CRD CRUD operations
- `staging/src/k8s.io/apiextensions-apiserver/pkg/client/informers/externalversions/apiextensions/v1/customresourcedefinition.go` — SharedIndexInformer for watching CRD definitions with local cache
- `staging/src/k8s.io/apiextensions-apiserver/pkg/client/listers/apiextensions/v1/customresourcedefinition.go` — Lister interface querying cached informer data

---

## Dependency Chain

### 1. Foundation: apimachinery Types & Runtime

**The base layer enables all higher-level functionality:**

- **Scheme**: `runtime.Scheme` is a bidirectional registry:
  - Maps `GroupVersionKind` → reflect.Type (for instantiation via `New(gvk)`)
  - Maps reflect.Type → `[]GroupVersionKind` (for serialization)
  - Stores conversion functions between types
  - Key: `gvkToType` and `typeToGVK` maps are the core of type identity

- **GVK/GVR**: `schema.GroupVersionKind` and `schema.GroupResource` are immutable identifiers:
  - GVK: (Group, Version, Kind) — used for type serialization/deserialization
  - GVR: (Group, Resource) — used for REST paths and storage
  - Example CRD: `apiextensions.k8s.io/v1/CustomResourceDefinition`

- **ObjectMeta/TypeMeta**: All Kubernetes objects have embedded metadata:
  - TypeMeta: apiVersion, kind
  - ObjectMeta: name, namespace, uid, labels, annotations, ownerReferences, etc.
  - Handled specially in validation/storage (always preserved)

- **Unstructured**: `map[string]interface{}` wrapper implementing `runtime.Object`:
  - No schema validation at Go type level
  - Implements TypeMeta/ObjectMeta accessors for compatibility
  - Enables dynamic resource access without generated Go types
  - Critical for CRDs: allows storing ANY custom resource shape

- **runtime.Object Interface**: All serializable objects must implement:
  - `GetObjectKind() schema.ObjectKind` — retrieve/set GVK
  - `DeepCopyObject() runtime.Object` — create copies

### 2. Type Definitions: apiextensions Hub & Versioned Types

**CRD type structure mirrors Kubernetes' own API versioning pattern:**

```
Internal Hub Type (runtime.APIVersionInternal)
    ↓
Scheme.AddKnownTypes(SchemeGroupVersion, &CustomResourceDefinition{}, ...)
    ↓
Conversion functions (if versions differ)
    ↓
External v1 Type (apiextensions.k8s.io/v1)
    ↓
JSON/Protobuf Serialization Directives
    ↓
Wire Format (HTTP JSON response)
```

- **Internal Hub** (`apiextensions/types.go`):
  - `CustomResourceDefinition` struct with embedded `metav1.TypeMeta`, `metav1.ObjectMeta`
  - Spec defines group, names, scope, validation schema
  - Status tracks Established, NamesAccepted, Terminating conditions
  - `+genclient:nonNamespaced` tag indicates cluster-scoped resource

- **Version Registration** (`apiextensions/register.go`):
  - `SchemeBuilder = runtime.NewSchemeBuilder(addKnownTypes)`
  - `addKnownTypes(scheme)` calls `scheme.AddKnownTypes(SchemeGroupVersion, &CustomResourceDefinition{}, &CustomResourceDefinitionList{})`
  - Registration happens at package init time

- **v1 External Type** (`apiextensions/v1/types.go`):
  - Identical structure to internal hub (no conversion needed for v1)
  - Includes protobuf tags for wire format
  - v1beta1 is deprecated but still supported for backwards compatibility

### 3. Server-Side: Storage, Validation, and Dynamic HTTP Handler

**Request flow for CRD-based custom resources:**

```
HTTP Request: POST /apis/example.com/v1/items
    ↓
customresource_handler.ServeHTTP()
    ↓
Lookup CRD definition in crdStorageMap (atomic.Value)
    ↓
Find version handler & validation schema
    ↓
customresource.CustomResourceStorage.Create()
    ↓
genericregistry.Store.Create()
    ↓
etcd storage with Unstructured object
    ↓
Return deserialized Unstructured via JSON
```

- **customresource_handler.go** (164 KB file, central dispatcher):
  - Maintains `crdStorageMap: map[types.UID]*crdInfo`
  - Watches CRD informer for create/update/delete
  - For each CRD version, creates:
    - `customresource.CustomResourceStorage` with etcd Store
    - Per-version validation schemas (OpenAPI v3)
    - Per-version request scopes for HTTP handling
  - Intercepts requests, routes to version-specific handlers

- **customresource/etcd.go** (CustomResourceStorage creation):
  - `NewStorage()` creates `genericregistry.Store`:
    - `NewFunc`: Creates blank `&unstructured.Unstructured{}` with GVK set
    - `NewListFunc`: Creates `&unstructured.UnstructuredList{}`
    - Integrates with `createStrategy`, `updateStrategy` for validation
    - Stores in etcd via `generic.RESTOptionsGetter`

- **Validation Flow**:
  - CRD spec includes `Validation.OpenAPIV3Schema` (JSON schema)
  - customresource_handler compiles schema at CRD creation time
  - On each create/update, validates Unstructured content against schema
  - Applies defaults, prunes unknown fields per spec

- **UnstructuredObjectTyper** (crdserverscheme):
  - Implements `runtime.ObjectTyper` for Unstructured objects
  - `ObjectKinds(obj)` extracts GVK from embedded TypeMeta
  - Enables serializer negotiation for dynamic resources

- **CRD Definition Storage**:
  - CRD objects themselves stored in separate etcd key space
  - Use typed storage (not Unstructured) for CRD definitions
  - Accessed via `customresourcedefinition/etcd.go` using internal hub types

### 4. Client-Side: Access and Caching

**Client-side workflow:**

```
User code: client.Resource(gvr).Namespace(ns).Create(ctx, obj, opts)
    ↓
DynamicClient.Resource(gvr) → dynamicResourceClient
    ↓
dynamicResourceClient.Create() → restClient.Post(...) with Unstructured
    ↓
basicNegotiatedSerializer: JSON codec configured in dynamic/scheme.go
    ↓
HTTP POST /apis/.../... with JSON body
    ↓
Server processes, returns Unstructured JSON
    ↓
Deserialize to &unstructured.Unstructured{}
```

- **DynamicClient** (`dynamic/simple.go`):
  - Created via `NewForConfig()` wrapping a REST client
  - Configured with `ConfigFor()`:
    - `ContentType = "application/json"`
    - `NegotiatedSerializer = basicNegotiatedSerializer{}`
  - Calls made to `/apis/<group>/<version>/...` endpoints

- **CRD Definition Client** (`clientset/clientset/typed/apiextensions/v1/`):
  - Typed client generated via client-gen
  - Methods: Create, Update, UpdateStatus, Delete, Get, List, Watch
  - Uses strongly-typed `*apiextensionsv1.CustomResourceDefinition` objects
  - Handles serialization/deserialization via Scheme

- **Informer & Lister Pattern**:
  - `CustomResourceDefinitionInformer.Informer()` returns `cache.SharedIndexInformer`
  - Internally:
    - Maintains local in-memory cache (backed by indexer)
    - Watches server with ListWatch
    - Notifies handlers on Add/Update/Delete
  - `CustomResourceDefinitionLister` queries the indexer directly (fast, local)

- **Cross-Project Coordination**:
  - CRD definitions created via typed client (`apiextensions/v1`)
  - CRD handler in apiextensions-apiserver watches for CRD changes
  - Dynamically creates storage & handlers for custom resources
  - Controllers/reconcilers use dynamic client to interact with instances

---

## Analysis

### How CRD Types Bridge the Four Sub-Projects

1. **apimachinery provides the foundation**: The Scheme is the central nervous system. It knows about GVK↔Type mappings and is shared across all sub-projects. The Unstructured type is the universal adapter for unknown resource shapes.

2. **apiextensions defines CRD types**: Two representations of CustomResourceDefinition:
   - Internal hub: Used internally for conversion and storage logic
   - External v1/v1beta1: User-facing API versions
   - Both are registered in their own Schemes, convertible via apimachinery converters

3. **apiextensions-apiserver stores & serves CRDs**:
   - Watches CRD definitions via informer (from client-go)
   - For each CRD, creates dynamic storage backed by Unstructured objects
   - Applies validation schemas defined in the CRD spec
   - HTTP handler intercepts requests and routes to version-specific backends

4. **client-go enables access**:
   - DynamicClient provides low-level REST access to any Unstructured resource
   - Typed clients for CRD CRUD via code generation
   - Informers watch CRD definition changes for discovery

### The Role of Scheme and GVK in Type Registration

The Scheme is **the central registry** that binds everything together:

- **Registration at startup**: Each package calls `AddToScheme` in `init()`:
  ```
  runtime.NewSchemeBuilder(addKnownTypes).AddToScheme(scheme)
  ```

- **Bidirectional mapping**:
  - Forward: `scheme.New(gvk)` → creates empty instance
  - Reverse: `scheme.ObjectKinds(obj)` → gets GVK from object's Go type

- **GVK as identity**:
  - CRD: `GroupVersionKind{Group: "apiextensions.k8s.io", Version: "v1", Kind: "CustomResourceDefinition"}`
  - Custom Resource: `GroupVersionKind{Group: "example.com", Version: "v1", Kind: "MyResource"}`

- **Critical for serialization**: When encoding/decoding, the Scheme determines:
  - What Go type to instantiate
  - What conversion functions to apply
  - Bidirectional mapping for versioned APIs

### How Unstructured Enables Dynamic Custom Resources

Without Unstructured, each custom resource would require generated Go types. Instead:

- **Unstructured = `map[string]interface{}`**: Generic container for any JSON-like structure
- **Implements `runtime.Object`**: Works with serializers, etcd storage, informers
- **Dynamic typing**: GVK embedded in object tells system how to handle it
- **Schema validation**: OpenAPI schema validates shape at runtime (not compile-time)

For a custom resource like:
```yaml
apiVersion: example.com/v1
kind: Item
metadata:
  name: my-item
spec:
  title: "Hello"
  count: 42
```

Flow:
1. HTTP POST with JSON body
2. Deserialize to `&unstructured.Unstructured{Object: map[string]interface{}{...}}`
3. Validate against CRD's OpenAPI schema
4. Store in etcd as Unstructured
5. List/Watch return Unstructured objects
6. Client receives JSON and unmarshals to Unstructured

### The Checkpoint: Server-Side Storage ↔ Client-Side Access

The boundary between server and client infrastructure is clean:

- **Server side (apiextensions-apiserver)**:
  - Stores Unstructured objects in etcd (no Go type needed)
  - Validates against CRD-defined schemas
  - Serves over HTTP with JSON content-type
  - Uses TypeMeta/ObjectMeta for all metadata operations

- **Client side (client-go + dynamic)**:
  - DynamicClient makes HTTP requests to server
  - Receives Unstructured JSON, deserializes to `map[string]interface{}`
  - No schema knowledge needed (server enforces it)
  - Generic enough to work with any resource

The **HTTP JSON exchange** is the protocol: if it's valid JSON with apiVersion/kind/metadata, the dynamic client can handle it.

### Cross-Project Dependency Flow

```
apimachinery (foundation)
    ↑ imports
apiextensions (CRD types)
    ↑ imports
apiextensions-apiserver (CRD storage/handler)
    ↑ imports
client-go (clients, informers, listers)
    ↑ used by
User code (controllers, kubectl, etc.)
```

- Each layer depends on types defined in lower layers
- apimachinery is the only foundational layer with no Kubernetes-specific types
- Scheme is the binding mechanism across all layers

---

## Summary

The CRD lifecycle flows through four Kubernetes staging sub-projects:

1. **apimachinery** provides the universal runtime: `Scheme` (type registry), `GVK` (identifiers), `ObjectMeta/TypeMeta` (metadata), and `Unstructured` (dynamic containers).

2. **apiextensions** defines CRD types in an internal hub + versioned external format, registered into the Scheme; CRD objects are themselves stored and served as strongly-typed resources.

3. **apiextensions-apiserver** implements the server: a dynamic HTTP handler watches CRD definitions via informers, creates per-CRD etcd storage backed by Unstructured objects, validates against OpenAPI schemas, and routes requests to version-specific handlers.

4. **client-go** implements client-side access: DynamicClient for generic Unstructured HTTP access, generated typed clients for CRD CRUD, SharedIndexInformers for watching/caching CRD definitions, and Listers for fast local queries.

The architecture hinges on Unstructured as the universal container—allowing any JSON shape to be stored, validated, and served without compile-time Go types—while Scheme provides the type registry that binds serialization, conversion, and introspection across all four layers.

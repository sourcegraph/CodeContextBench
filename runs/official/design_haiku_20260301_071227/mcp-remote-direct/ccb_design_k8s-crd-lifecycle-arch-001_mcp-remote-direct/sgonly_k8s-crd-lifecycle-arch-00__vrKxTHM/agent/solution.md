# Kubernetes CRD Lifecycle: Cross-Project Architecture Analysis

## Files Examined

### Foundation: apimachinery
- `staging/src/k8s.io/apimachinery/pkg/runtime/scheme.go` — Core Scheme type with gvkToType and typeToGVK mappings
- `staging/src/k8s.io/apimachinery/pkg/runtime/schema/group_version.go` — GroupVersionKind, GroupVersion, GroupKind definitions
- `staging/src/k8s.io/apimachinery/pkg/apis/meta/v1/unstructured/unstructured.go` — Unstructured type for dynamic resources
- `staging/src/k8s.io/apimachinery/pkg/apis/meta/v1/unstructured/helpers.go` — UnstructuredJSONScheme codec
- `staging/src/k8s.io/apimachinery/pkg/apis/meta/v1/unstructured/unstructuredscheme/scheme.go` — Unstructured-only scheme
- `staging/src/k8s.io/apimachinery/pkg/runtime/serializer/codec_factory.go` — CodecFactory for encoding/decoding
- `staging/src/k8s.io/apimachinery/pkg/runtime/interfaces.go` — Unstructured interface and runtime Object types
- `staging/src/k8s.io/apimachinery/pkg/util/managedfields/internal/typeconverter.go` — Conversion between structured/unstructured

### Type Layer: apiextensions-apiserver
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/types.go` — Internal hub types (unversioned)
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1/types.go` — External v1 types with metadata
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1beta1/types.go` — External v1beta1 types (deprecated)
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1/register.go` — Scheme registration for v1 CRDs
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1beta1/register.go` — Scheme registration for v1beta1 CRDs
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/install/install.go` — Scheme installation function

### Server-Side: apiextensions-apiserver
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apiserver/customresource_handler.go` — Dynamic HTTP handler and CRD storage management
- `staging/src/k8s.io/apiextensions-apiserver/pkg/registry/customresourcedefinition/etcd.go` — CRD etcd storage backend
- `staging/src/k8s.io/apiextensions-apiserver/pkg/registry/customresourcedefinition/strategy.go` — CRD storage strategy (validation, updates)
- `staging/src/k8s.io/apiextensions-apiserver/pkg/registry/customresource/strategy.go` — Custom resource storage strategy
- `staging/src/k8s.io/apiextensions-apiserver/pkg/registry/customresource/status_strategy.go` — Status subresource handling
- `staging/src/k8s.io/apiextensions-apiserver/pkg/apiserver/conversion/converter.go` — CRD version conversion
- `staging/src/k8s.io/apiextensions-apiserver/pkg/crdserverscheme/unstructured.go` — UnstructuredObjectTyper for CRD handler

### Client Layer: client-go
- `staging/src/k8s.io/client-go/dynamic/simple.go` — DynamicClient implementation
- `staging/src/k8s.io/client-go/dynamic/scheme.go` — Dynamic scheme for unstructured types
- `staging/src/k8s.io/client-go/tools/cache/shared_informer.go` — SharedIndexInformer base implementation
- `staging/src/k8s.io/client-go/informers/factory.go` — SharedInformerFactory for typed clients
- `staging/src/k8s.io/apiextensions-apiserver/pkg/client/informers/externalversions/factory.go` — CRD informer factory
- `staging/src/k8s.io/apiextensions-apiserver/pkg/client/listers/apiextensions/v1/customresourcedefinition.go` — CRD Lister interface
- `staging/src/k8s.io/apiextensions-apiserver/pkg/client/clientset/clientset/typed/apiextensions/v1/customresourcedefinition.go` — Typed CRD client

## Dependency Chain

### Level 1: Foundation (apimachinery)
**Purpose**: Provide runtime type system and codec infrastructure for all Kubernetes objects

**Key Types**:
- `runtime.Scheme`: Maps between Go types and GroupVersionKinds (GVK). Maintains bidirectional mappings:
  - `gvkToType`: map[schema.GroupVersionKind]reflect.Type (lookup Go type from GVK)
  - `typeToGVK`: map[reflect.Type][]schema.GroupVersionKind (lookup GVK from Go type)

- `schema.GroupVersionKind`: Uniquely identifies a Kubernetes object type (Group + Version + Kind)
  - Example: `apiextensions.k8s.io/v1/CustomResourceDefinition`

- `runtime.Unstructured` interface and `unstructured.Unstructured` struct: Enables manipulation of objects without Go types
  - Backed by `map[string]interface{}` (JSON-compatible representation)
  - Implements `runtime.Object` and `metav1.Object` interfaces

- `runtime.CodecFactory`: Creates encoders/decoders for specific versions and content types
  - Uses Scheme to serialize/deserialize objects
  - Supports JSON, YAML, protobuf formats

**How it works**:
```
User creates a CRD instance (YAML)
  → API server receives raw JSON
  → CodecFactory.UniversalDecoder() decodes JSON to Unstructured (no Go type needed)
  → Unstructured.SetGroupVersionKind() stores GVK metadata
  → Unstructured is passed through handlers/storage/clients
```

---

### Level 2: Type Layer (apiextensions-apiserver + api modules)

**Purpose**: Define CRD structure and how CRDs are themselves represented as API objects

**Architecture**:
1. **Internal Hub Types** (`apiextensions/types.go`):
   - `CustomResourceDefinition`: Unversioned internal type
   - Acts as the canonical storage format in etcd
   - Includes spec, status, and metadata

2. **External v1 Types** (`apiextensions/v1/types.go`):
   - `CustomResourceDefinition`: Versioned type with protobuf serialization
   - Adds validation, JSON tags, and API documentation
   - Includes embedded `metav1.TypeMeta` and `metav1.ObjectMeta`

3. **Scheme Registration** (`apiextensions/v1/register.go`):
   - `SchemeBuilder`: Registers CRD types into a Scheme
   - `addKnownTypes()`: Adds CustomResourceDefinition and CustomResourceDefinitionList
   - `addDefaultingFuncs()`: Adds version-specific defaults
   - Called during API server initialization to register all CRD types

**Key Pattern**:
```go
var (
  SchemeBuilder      = runtime.NewSchemeBuilder(addKnownTypes, addDefaultingFuncs)
  localSchemeBuilder = &SchemeBuilder
  AddToScheme        = localSchemeBuilder.AddToScheme
)

// In addKnownTypes:
func addKnownTypes(scheme *runtime.Scheme) error {
  scheme.AddKnownTypes(SchemeGroupVersion,
    &CustomResourceDefinition{},
    &CustomResourceDefinitionList{},
  )
  // ... more types
}
```

---

### Level 3: Server-Side Lifecycle (apiextensions-apiserver)

**Purpose**: Handle CRD definitions and serve custom resources

#### A. CRD Storage and Validation

**CRD Management Pipeline**:

1. **CRD Registration** (`customresourcedefinition/strategy.go`):
   - When a CRD is created, `MatchCustomResourceDefinition()` creates a storage predicate
   - `CustomResourceDefinitionToSelectableFields()` indexes CRD fields for listing/watching

2. **etcd Storage Backend** (`customresourcedefinition/etcd.go`):
   - Generic etcd storage for CustomResourceDefinition objects
   - Uses `runtime.Scheme` to serialize/deserialize CRD objects
   - Creates codec using `genericregistry.Store`

#### B. Dynamic Custom Resource Handler

**The crdHandler Bridge** (`customresource_handler.go`):

1. **Initialization**:
   - Listens for CustomResourceDefinition changes via informer
   - `crdLister`: Uses SharedIndexInformer to watch CRD updates
   - Maintains `customStorage` (atomic.Value) with map of all active CRD storages

2. **For Each CRD Created**:
   - Extract `spec.group`, `spec.names`, `spec.versions`
   - Create dynamic storage for each version of the custom resource
   - Build HTTP handlers for REST endpoints (`/apis/<group>/<version>/<resource>`)

3. **Storage Creation for Custom Resources** (`crdInfo.storages`):
   - For each CRD, create `customresource.CustomResourceStorage`
   - Uses `UnstructuredObjectTyper` to handle objects without pre-registered Go types
   - Creates serializer/codec using `unstructured.UnstructuredJSONScheme`
   - Result: Custom resource objects stored as Unstructured in etcd

4. **Request Processing**:
   ```
   HTTP POST /apis/mygroup/v1alpha1/myresources
   → crdHandler.ServeHTTP() intercepts
   → Looks up CRD info from customStorage
   → Extracts appropriate version storage
   → Uses UnstructuredJSONScheme to decode request body → Unstructured
   → Validates against CRD schema
   → Stores in etcd as JSON (Unstructured form)
   → Responds with stored Unstructured object
   ```

5. **Validation and Defaulting**:
   - `strategy.go` defines validation rules for custom resources
   - Uses CRD's OpenAPI schema for field validation
   - Supports pruning unknown fields (configurable per CRD)
   - Manages subresources like `/status`

#### C. Version Conversion

**CRD Conversion Strategy** (`apiserver/conversion/converter.go`):
- When a custom resource is requested in a different version:
  - If strategy is "None": just change apiVersion
  - If strategy is "Webhook": call external conversion service
  - Uses `typedscheme.Scheme.Convert()` for built-in conversions

---

### Level 4: Client-Side Access (client-go)

**Purpose**: Enable clients to access custom resources with type-safe or dynamic interfaces

#### A. DynamicClient (Untyped Access)

**Overview**: `dynamic.DynamicClient` enables runtime discovery and access of any CRD

**Architecture**:
```
DynamicClient
├── client: rest.Interface (REST client)
└── Resource(gvr GroupVersionResource) → ResourceInterface
    └── Namespace(ns string) → NamespaceableResourceInterface
        ├── Get(ctx, name) → *unstructured.Unstructured
        ├── List(ctx, opts) → *UnstructuredList
        ├── Watch(ctx, opts) → watch.Interface
        ├── Create(ctx, obj) → *unstructured.Unstructured
        ├── Update(ctx, obj) → *unstructured.Unstructured
        └── Delete(ctx, name) → error
```

**Key Implementation** (`dynamic/simple.go`):
- Uses `unstructured.UnstructuredJSONScheme` to encode/decode
- Does NOT require types to be registered in a Scheme
- Works with any GroupVersionResource (GVR)
- Returns/accepts `*unstructured.Unstructured` objects

**Creation**:
```go
config := rest.CopyConfig(inConfig)
config.NegotiatedSerializer = basicNegotiatedSerializer{} // JSON only
restClient, _ := rest.RESTClientForConfigAndClient(config, httpClient)
dynamicClient := &DynamicClient{client: restClient}
```

#### B. Typed Client and Informers (Type-Safe Access)

**For Built-in Resources** (generated by code-generator):
- Creates typed client: `clientset.Interface` with methods like `CoreV1()`, `AppsV1()`, etc.
- Generated from Go types registered in Scheme

**For CRD Resources** (custom):
- `apiextensions-apiserver/pkg/client/` contains generated code for CRD types themselves
- Clients can also use DynamicClient for instances of their CRDs

#### C. Informers and Caching

**SharedIndexInformer** (`tools/cache/shared_informer.go`):

1. **Purpose**: Local cache of API objects with event notifications
   - Maintains cache as Indexer (map-based store)
   - Watches for changes on server
   - Notifies registered event handlers

2. **Lifecycle**:
   ```
   NewSharedIndexInformer()
   ├── Creates ListWatcher (calls API list/watch)
   ├── Creates Indexer (local cache store)
   └── Returns SharedIndexInformer interface

   informer.Start(stopCh)
   ├── Starts goroutine to call list once
   ├── Establishes watch on resource
   ├── Updates cache on watch events
   └── Calls registered event handlers

   informer.GetStore() / informer.GetIndexer()
   ├── Returns local cache
   └── Can query without hitting API
   ```

**Generated Informer Factory** (`apiextensions-apiserver/pkg/client/informers/externalversions/factory.go`):

1. **SharedInformerFactory**:
   - Creates multiple SharedIndexInformer instances for related types
   - Ensures informers for same type share same backing store

2. **Usage Pattern**:
   ```go
   factory := informers.NewSharedInformerFactory(client, 30*time.Second)
   crdInformer := factory.Apiextensions().V1().CustomResourceDefinitions()

   informer := crdInformer.Informer() // returns cache.SharedIndexInformer
   lister := crdInformer.Lister()     // returns CustomResourceDefinitionLister

   factory.Start(stopCh)  // starts all informers
   factory.WaitForCacheSync(stopCh) // waits for initial list

   // Later: query cache without API calls
   crd, _ := lister.Get("myresource.mygroup.io")
   ```

#### D. Lister (Query Cache)

**CustomResourceDefinitionLister** (`client/listers/apiextensions/v1/`):

- Wraps SharedIndexInformer's cache
- Provides query methods:
  - `List(selector labels.Selector)` → []*CustomResourceDefinition
  - `Get(name string)` → *CustomResourceDefinition
  - Namespace variations for namespaced resources

---

## Architectural Integration: The Complete Flow

### Scenario: Create and Access a Custom Resource

**Step 1: Define the CRD**
```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: pandas.mygroup.io
spec:
  group: mygroup.io
  names:
    kind: Panda
    plural: pandas
  scope: Cluster
  versions:
  - name: v1
    served: true
    storage: true
    schema: {...}
```

**Step 2: CRD Creation (Server-Side)**
```
Client sends POST /apis/apiextensions.k8s.io/v1/customresourcedefinitions
  → crdHandler intercepts
  → UnstructuredJSONScheme decodes JSON → Unstructured
  → crdHandler looks up CRD storage in etcd
  → Validates CRD spec (group, names, versions)
  → Stores CRD object in etcd as Unstructured JSON
  → Also updates crdHandler.customStorage to enable Panda serving
    ├── Registers new HTTP endpoints for /apis/mygroup.io/v1/pandas
    ├── Creates new CustomResourceStorage for Panda type
    └── Uses UnstructuredObjectTyper (no Panda Go type exists)
```

**Step 3: Client Application Discovers CRD**
```
Client creates informer factory:
  factory := informers.NewSharedInformerFactory(kubeClient, 30s)
  crdInformer := factory.Apiextensions().V1().CustomResourceDefinitions()

  factory.Start(stopCh)
  // Informer calls: GET /apis/apiextensions.k8s.io/v1/customresourcedefinitions
  // Watches: WATCH /apis/apiextensions.k8s.io/v1/customresourcedefinitions

  crd := crdInformer.Lister().Get("pandas.mygroup.io")
  // crd is a typed *CustomResourceDefinition object
  // group: "mygroup.io", names.kind: "Panda", ...
```

**Step 4: Create Custom Resource Instance (Dynamic)**
```
dynamicClient := dynamic.NewForConfig(config)
gvr := schema.GroupVersionResource{
  Group: "mygroup.io",
  Version: "v1",
  Resource: "pandas",
}

panda := &unstructured.Unstructured{
  Object: map[string]interface{}{
    "apiVersion": "mygroup.io/v1",
    "kind": "Panda",
    "metadata": map[string]interface{}{
      "name": "fuzzy",
      "namespace": "default",
    },
    "spec": map[string]interface{}{
      "cuteness": 9000,
    },
  },
}

// Use dynamic client
created, _ := dynamicClient.Resource(gvr).Namespace("default").Create(ctx, panda, metav1.CreateOptions{})

// Flow:
// 1. DynamicClient.Create() encodes unstructured.Unstructured → JSON using UnstructuredJSONScheme
// 2. HTTP POST /apis/mygroup.io/v1/namespaces/default/pandas with JSON body
// 3. crdHandler intercepts request
// 4. Looks up "pandas" CRD from customStorage
// 5. Decodes request JSON → Unstructured (no Go type needed)
// 6. Validates against CRD schema from crd.spec.versions[0].schema
// 7. Stores in etcd as Unstructured (JSON representation)
// 8. Returns stored object as Unstructured
```

**Step 5: Access via Informer Cache (for resources with Scheme registration)**
```
// For built-in types, informers work with typed objects
// For CRD types, clients can use DynamicClient with unstructured
// OR register CRD schema into Scheme programmatically

// The Scheme registration happens via:
// 1. code-generator produces typed informers if CRD types are registered
// 2. OR client stays untyped and uses DynamicClient with SharedIndexInformer for discovery
```

---

## Critical Architecture Concepts

### 1. Scheme: The Type Registry
- **Central mapping**: GVK ↔ Go Type
- **Built-in types** (Pod, Service): Pre-registered at API server startup
- **CRD types**: NOT registered in Scheme (no Go types exist)
- **Purpose**: Enable serialization without JSON parsing (direct Go type → wire format)

### 2. Unstructured: The Dynamic Bridge
- **When Scheme has no type**: Use `unstructured.Unstructured`
- **Backed by**: `map[string]interface{}` (pure JSON representation)
- **Codec**: `UnstructuredJSONScheme` handles all serialization
- **Enables**: Servers to handle any object without pre-registered types

### 3. GroupVersionKind vs GroupVersionResource
- **GVK** (Group/Version/Kind): Used for Go type identification
  - Example: `apiextensions.k8s.io/v1/CustomResourceDefinition`
- **GVR** (Group/Version/Resource): Used for HTTP routing
  - Example: `apiextensions.k8s.io/v1/customresourcedefinitions` (plural)
- **Mapping**: Kind → Resource done via CRD.spec.names.plural or discovery

### 4. The Checkpoint: etcd Storage
- **Input**: Unstructured objects (no type system dependency)
- **Storage**: JSON in etcd
- **Output**: Unstructured objects to clients (or typed if client has Scheme)
- **Implication**: The server works purely with JSON; typing happens only in clients

### 5. Informer: Client-Side Caching
- **Watch**: Maintains list of objects from API server
- **Cache**: Local Indexer with objects
- **Events**: Calls handlers on Add/Update/Delete
- **Shared**: Multiple informers for same type share one cache
- **For CRDs**: Can use DynamicClient with informer to watch untyped objects

---

## Summary

The Kubernetes CRD lifecycle bridges four sub-projects through a carefully layered architecture:

1. **apimachinery** provides the type system (Scheme, GVK, Unstructured) that enables objects to exist with or without Go types
2. **apiextensions-apiserver** defines CRD types, validates them, and dynamically creates HTTP handlers that use Unstructured to store/serve any CRD instance
3. **client-go** provides DynamicClient and SharedInformer mechanisms for clients to discover and access CRD instances without pre-registration
4. **api** provides type definitions for built-in resources

The critical insight is that **CRDs are a pure JSON solution**—they bypass the Scheme's type system entirely. The server stores them as Unstructured in etcd, clients access them via dynamic clients or untyped informers, and the entire flow works without ever registering a Go type for the custom resource. This decoupling allows Kubernetes to support arbitrary user-defined resources with zero compiled-in knowledge about them.

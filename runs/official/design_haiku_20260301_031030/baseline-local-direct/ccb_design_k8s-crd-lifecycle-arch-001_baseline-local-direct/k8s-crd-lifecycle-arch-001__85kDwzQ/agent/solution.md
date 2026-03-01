# Kubernetes CRD Lifecycle: Cross-Repository Architectural Analysis

## Files Examined

### apimachinery (Foundation Layer)
- **staging/src/k8s.io/apimachinery/pkg/runtime/scheme.go** — Core type registry mapping GroupVersionKind ↔ Go types; foundation for all serialization
- **staging/src/k8s.io/apimachinery/pkg/runtime/interfaces.go** — Object and Unstructured interfaces; all K8s objects implement Object
- **staging/src/k8s.io/apimachinery/pkg/apis/meta/v1/types.go** — TypeMeta (Kind, APIVersion) and ObjectMeta; common metadata for all resources
- **staging/src/k8s.io/apimachinery/pkg/apis/meta/v1/unstructured/unstructured.go** — Unstructured struct implementing runtime.Object and runtime.Unstructured; wraps map[string]interface{}
- **staging/src/k8s.io/apimachinery/pkg/runtime/schema/interfaces.go** — ObjectKind interface for GVK metadata

### apiextensions-apiserver (CRD Type Definitions & Server-Side)
- **staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/types.go** — Internal hub types: CustomResourceDefinition, CustomResourceDefinitionSpec
- **staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1/types.go** — External v1 API types for CRD; schemas, validation rules, names
- **staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/register.go** — Internal hub type registration (runtime.APIVersionInternal)
- **staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1/register.go** — v1 external type registration with SchemeBuilder and AddToScheme
- **staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/install/install.go** — Install() registers all CRD types (internal, v1beta1, v1) into Scheme
- **staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/validation/validation.go** — ValidateCustomResourceDefinition() validates CRD spec against OpenAPI schema
- **staging/src/k8s.io/apiextensions-apiserver/pkg/apiserver/customresource_handler.go** — crdHandler serves `/apis` endpoint; manages per-CRD HTTP handlers and etcd storage
- **staging/src/k8s.io/apiextensions-apiserver/pkg/registry/customresource/etcd.go** — CustomResourceStorage: generic etcd storage using Unstructured NewFunc/NewListFunc
- **staging/src/k8s.io/apiextensions-apiserver/pkg/crdserverscheme/unstructured.go** — UnstructuredObjectTyper: runtime.ObjectTyper for Unstructured objects based on discovery

### client-go (Client-Side Access)
- **staging/src/k8s.io/client-go/dynamic/interface.go** — Dynamic client interfaces: Interface (Resource method), ResourceInterface, NamespaceableResourceInterface
- **staging/src/k8s.io/client-go/dynamic/simple.go** — DynamicClient: REST client implementation using Unstructured for Create/Update/Get/List/Watch/Patch
- **staging/src/k8s.io/client-go/dynamic/scheme.go** — basicNegotiatedSerializer for dynamic client JSON serialization
- **staging/src/k8s.io/client-go/dynamic/dynamicinformer/interface.go** — DynamicSharedInformerFactory interface for generic informer access
- **staging/src/k8s.io/client-go/dynamic/dynamicinformer/informer.go** — dynamicSharedInformerFactory creates SharedIndexInformers for any GVR; maintains cache.Indexer
- **staging/src/k8s.io/client-go/dynamic/dynamiclister/lister.go** — dynamicLister/dynamicNamespaceLister: access cached Unstructured objects via cache.Indexer

### api (Group Registration)
- **staging/src/k8s.io/api/{group}/{version}/register.go** — Type registration functions (AddToScheme, SchemeBuilder) for each API group

---

## Dependency Chain

### 1. **Foundation: apimachinery Types**

```
runtime.Scheme
├─ gvkToType: map[GroupVersionKind] → reflect.Type
├─ typeToGVK: map[reflect.Type] → []GroupVersionKind
└─ converter: runtime.Converter (for version conversion)

runtime.Object interface (all K8s objects implement this)
├─ GetObjectKind() → schema.ObjectKind
└─ DeepCopyObject() → Object

runtime.Unstructured interface (for dynamic resources)
├─ Object (embedded)
├─ UnstructuredContent() → map[string]interface{}
└─ SetUnstructuredContent(map[string]interface{})

unstructured.Unstructured struct (implementation)
└─ Object: map[string]interface{} (contains kind, apiVersion, metadata, spec, etc.)

metav1.TypeMeta
├─ Kind: string (e.g., "MyCustomResource")
└─ APIVersion: string (e.g., "mygroup.example.com/v1")

metav1.ObjectMeta
├─ Name, Namespace, Labels, Annotations, OwnerReferences, etc.
└─ (Standard metadata for all K8s resources)

schema.GroupVersionKind (unique identifier)
├─ Group: string (e.g., "apiextensions.k8s.io")
├─ Version: string (e.g., "v1")
└─ Kind: string (e.g., "CustomResourceDefinition")

schema.GroupVersionResource (for REST operations)
├─ Group, Version, Resource (plural name)
└─ Used for HTTP routing and client operations
```

---

### 2. **Type Definitions: apiextensions Ecosystem**

#### Internal Hub Types (runtime.APIVersionInternal):
- **CustomResourceDefinition** (apiextensions/types.go)
  - Spec: CustomResourceDefinitionSpec (group, names, scope, versions, validation, conversion)
  - Status: CustomResourceDefinitionStatus (conditions, storedVersions, acceptedNames)

#### External v1 Types (apiextensions/v1):
- **CustomResourceDefinitionSpec**
  - group: string (API group the CRD belongs to)
  - names: CustomResourceDefinitionNames (plural, singular, kind, categories)
  - scope: ResourceScope (Namespaced or Cluster)
  - versions: []CustomResourceDefinitionVersion (served, storage versions with schemas)
  - validation: *CustomResourceValidation (OpenAPI v3 schema for the CRD)
  - conversion: *CustomResourceConversion (webhook converter for multi-version support)
  - preserveUnknownFields: bool (whether to preserve fields not in schema)

#### Scheme Registration (runtime.Scheme integration):
1. **Register.go (internal hub)**:
   ```go
   SchemeGroupVersion = schema.GroupVersion{Group: "apiextensions.k8s.io", Version: "__internal"}
   addKnownTypes(scheme) registers CustomResourceDefinition and CustomResourceDefinitionList
   ```

2. **Register.go (v1 external)**:
   ```go
   SchemeGroupVersion = schema.GroupVersion{Group: "apiextensions.k8s.io", Version: "v1"}
   SchemeBuilder = NewSchemeBuilder(addKnownTypes, addDefaultingFuncs)
   AddToScheme adds types + metav1.AddToGroupVersion for standard metadata
   ```

3. **Install.go (initialization)**:
   ```go
   Install(scheme) calls:
   - apiextensions.AddToScheme(scheme)     // internal hub
   - v1beta1.AddToScheme(scheme)           // legacy external
   - v1.AddToScheme(scheme)                // current external
   - scheme.SetVersionPriority(v1, v1beta1) // prefer v1 for conversion
   ```

**Result**: Scheme contains bidirectional mappings:
- GroupVersionKind("apiextensions.k8s.io", "v1", "CustomResourceDefinition") ↔ *apiextensionsv1.CustomResourceDefinition
- GroupVersionKind("apiextensions.k8s.io", "__internal", "CustomResourceDefinition") ↔ *apiextensions.CustomResourceDefinition

---

### 3. **Server-Side Lifecycle: Validation → Storage → HTTP Handler**

#### Phase A: CRD Creation/Update - Validation
**File**: `apiextensions-apiserver/pkg/apis/apiextensions/validation/validation.go`

```
CRD YAML submission
       ↓
ValidateCustomResourceDefinition(crd *CustomResourceDefinition) → field.ErrorList
       ├─ validateCustomResourceDefinitionSpec()
       │   ├─ Validates group name (must match CRD metadata name: `<plural>.<group>`)
       │   ├─ Validates version list (must be non-empty, unique)
       │   ├─ Validates schema (OpenAPI v3, structural schema requirements)
       │   ├─ Validates CEL rules (x-kubernetes-validations)
       │   └─ Validates conversion webhook if present
       └─ ValidateCustomResourceDefinitionStatus()
```

**Key Checks**:
- Schema must be structural (deterministic serialization/deserialization)
- All versions must have compatible schemas
- Selectable fields limited to 8
- CEL validation rules within cost limits

---

#### Phase B: CRD Registration - Scheme & Handler Setup
**File**: `apiextensions-apiserver/pkg/apiserver/customresource_handler.go`

```
CRD stored in etcd
       ↓
crdHandler.ServeHTTP() watches CustomResourceDefinition resources
       ├─ Reads CRD via crdLister: listers.CustomResourceDefinitionLister
       ├─ Extracts spec.group, spec.names.plural, spec.versions
       ├─ Creates per-CRD storage for each version:
       │   └─ crdInfo.storages[version] = customresource.CustomResourceStorage
       ├─ Creates per-CRD HTTP request scopes:
       │   └─ crdInfo.requestScopes[version] = handlers.RequestScope
       │       ├─ Serializer with Unstructured codec
       │       ├─ Mapper: GroupVersionResource → GroupVersionKind
       │       └─ Admission webhooks (validate, mutate)
       └─ Routes HTTP requests to appropriate handler
           ├─ GET /apis/<group>/<version>/<plural>
           └─ POST /apis/<group>/<version>/namespaces/<ns>/<plural>
```

---

#### Phase C: CRD Storage - etcd Persistence
**File**: `apiextensions-apiserver/pkg/registry/customresource/etcd.go`

```
CustomResourceStorage (created per CRD version):
├─ NewStorage(resource, kind, strategy, optsGetter, ...)
│   ├─ Creates genericregistry.Store with:
│   │   ├─ NewFunc: () runtime.Object = &unstructured.Unstructured{}
│   │   │           ↓ SetGroupVersionKind(kind) to signal to decoder
│   │   │
│   │   ├─ NewListFunc: () runtime.Object = &unstructured.UnstructuredList{}
│   │   │
│   │   └─ Strategies: Create/Update/Delete from customResourceStrategy
│   │       ├─ MatchCustomResourceDefinitionStorage: predicate filter
│   │       ├─ GetAttrs: extract metadata for filtering
│   │       └─ Validation via strategy validator
│   │
│   └─ store.CompleteWithOptions() → configures etcd-generic RESTOptions
│       └─ Uses Unstructured marshaling for etcd serialization
│
├─ REST: wraps Store for single resource Create/Get/Update/Delete/List/Watch
├─ StatusREST: dedicated /status subresource handler
└─ ScaleREST: dedicated /scale subresource handler
```

**Key Point**: All custom resources are stored as `unstructured.Unstructured` in etcd:
- Serialized to JSON in etcd
- GVK info preserved in TypeMeta (kind, apiVersion fields)
- No Go struct needed — schema validation is done at handler layer

---

#### Phase D: CRD HTTP Handler - Request Processing
**File**: `apiextensions-apiserver/pkg/apiserver/customresource_handler.go`

```
HTTP Request: GET /apis/example.com/v1/namespaces/default/myresources/obj1
       ↓
crdHandler.ServeHTTP(w, r)
       ├─ ParseRequest() → GroupVersionResource = (example.com, v1, myresources)
       ├─ Lookup crdInfo.requestScopes[v1]
       ├─ Serializer: JSON ↔ unstructured.Unstructured
       ├─ Admission: mutating webhooks
       ├─ Call handler:
       │   └─ handlers.GetResource(ctx, scope, crdInfo.storages[v1].CustomResource)
       │       └─ Call store.Get(ctx, name)
       │           └─ etcd query → JSON → Unstructured
       ├─ Validation: validating webhooks
       └─ ResponseWriter writes Unstructured as JSON response
```

---

### 4. **Client-Side Access Layer: Dynamic Client → Informer → Lister**

#### Phase E: Dynamic Client - Direct Resource Access
**File**: `client-go/dynamic/interface.go`, `simple.go`

```
User Code:
    dynClient, _ := dynamic.NewForConfig(config)
           ↓
DynamicClient.Resource(schema.GroupVersionResource)
       ├─ Returns NamespaceableResourceInterface
       │   └─ Namespace(ns) → ResourceInterface
       │
       └─ ResourceInterface methods (all using *unstructured.Unstructured):
           ├─ Create(ctx, obj *Unstructured, options) → *Unstructured
           ├─ Update(ctx, obj *Unstructured, options) → *Unstructured
           ├─ Get(ctx, name, options) → *Unstructured
           ├─ List(ctx, listOptions) → *UnstructuredList
           ├─ Watch(ctx, listOptions) → watch.Interface
           ├─ Patch(ctx, name, patchType, data) → *Unstructured
           └─ Delete(ctx, name, deleteOptions) → error

REST Implementation:
    ResourceInterface operations
           ↓
    rest.Interface (HTTP client)
           ├─ ConfigFor() sets up:
           │   ├─ ContentType: application/json
           │   └─ NegotiatedSerializer: basicNegotiatedSerializer
           │
           └─ Encodes GroupVersionResource in URL:
               └─ /apis/<group>/<version>/<plural>
               └─ /api/v1/<plural> (for core API)
```

**Key Design**: DynamicClient uses no Go type stubs; everything is `*unstructured.Unstructured`.

---

#### Phase F: Dynamic Informers - Server-Side Watch + Local Cache
**File**: `client-go/dynamic/dynamicinformer/interface.go`, `informer.go`

```
User Code:
    factory := dynamicinformer.NewDynamicSharedInformerFactory(
        client, time.Minute,
    )
           ↓
DynamicSharedInformerFactory.ForResource(gvr)
       ├─ Returns informers.GenericInformer
       │   └─ Wraps genericInformer interface
       │
       └─ Creates dynamicInformer:
           ├─ reflector: Watches API Server
           │   ├─ client.Resource(gvr).Watch()
           │   ├─ Decodes server events into *unstructured.Unstructured
           │   └─ Puts into fifo queue
           │
           ├─ fifo: Work queue of Add/Update/Delete events
           │
           ├─ indexer: cache.Indexer (in-memory local cache)
           │   ├─ Indexed by default: cache.NamespaceIndex
           │   ├─ Functions: cache.MetaNamespaceIndexFunc (extract namespace)
           │   └─ Stores *unstructured.Unstructured objects
           │
           └─ processorListener: Notifies registered consumers of changes

factory.Start(stopCh <-chan struct{})
       ├─ Starts all informer goroutines
       └─ reflector.Run() → continuous list-watch cycle
           ├─ Initial list: client.Resource(gvr).List()
           ├─ Watch: client.Resource(gvr).Watch()
           └─ Reconciles in-memory cache with server state

factory.WaitForCacheSync(stopCh)
       └─ Blocks until all informer caches are synced with server
```

---

#### Phase G: Dynamic Listers - Cached Object Access
**File**: `client-go/dynamic/dynamiclister/lister.go`

```
User Code:
    informer := factory.ForResource(gvr)
    lister := dynamiclister.New(informer.GetIndexer(), gvr)
           ↓
DynamicLister interface:
    ├─ List(selector labels.Selector)
    │   └─ cache.ListAll(indexer, selector, callback)
    │       └─ Iterates cached objects matching label selector
    │
    ├─ Get(name string) → *unstructured.Unstructured
    │   └─ indexer.GetByKey(name)
    │       └─ Returns single cached object
    │
    └─ Namespace(ns string) → NamespaceLister
        ├─ List(selector) → []*Unstructured (filtered by namespace)
        └─ Get(name) → *Unstructured (from namespace + name key)

Key: **Lister always works against local cache (indexer)**
     No network calls; all operations O(cache size)
```

---

## Complete CRD Lifecycle Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    KUBERNETES CRD LIFECYCLE                             │
└─────────────────────────────────────────────────────────────────────────┘

USER CREATES CRD YAML:
  apiVersion: apiextensions.k8s.io/v1
  kind: CustomResourceDefinition
  metadata:
    name: myresources.example.com
  spec:
    group: example.com
    names:
      kind: MyResource
      plural: myresources
    scope: Namespaced
    versions:
    - name: v1
      served: true
      storage: true
      schema:
        openAPIV3Schema: { type: object, properties: {...} }

                              ↓

[1] APIEXTENSIONS-APISERVER SIDE:

    1a. Validation:
        customresource_handler receives CRD YAML
        → ValidateCustomResourceDefinition()
        → Validates spec.group matches CRD name format
        → Validates schema is structural
        → Validates CEL rules don't exceed cost limits

    1b. CRD Registration:
        CRD stored in etcd (as its own resource)
        crdHandler watches CustomResourceDefinition objects
        → Creates crdInfo for new CRD
        → For each version (v1):
           - Creates CustomResourceStorage with Unstructured NewFunc
           - Creates RequestScope with Unstructured serializer
           - Registers HTTP handler for /apis/example.com/v1/myresources

    1c. Storage Setup:
        genericregistry.Store configured with:
        - NewFunc() → &unstructured.Unstructured{}
        - Serializer: JSON ↔ map[string]interface{}
        - etcd backend via RESTOptionsGetter

                              ↓

[2] USER CREATES CUSTOM RESOURCE:

    kubectl apply -f - << EOF
    apiVersion: example.com/v1
    kind: MyResource
    metadata:
      name: obj1
      namespace: default
    spec:
      field1: value1
    EOF

                              ↓

[3] API SERVER RECEIVES REQUEST:

    POST /apis/example.com/v1/namespaces/default/myresources

    crdHandler.ServeHTTP()
    ├─ ParseRequest() → (group=example.com, version=v1, resource=myresources)
    ├─ Get crdInfo from watch cache
    ├─ Deserialize YAML → unstructured.Unstructured
    ├─ Run admission webhooks (mutating)
    ├─ Validate schema (OpenAPI v3 + CEL rules)
    ├─ Call store.Create()
    │   └─ Serialize Unstructured → JSON
    │   └─ Write to etcd with key: /myresources/v1/example.com/namespaces/default/obj1
    └─ Return Unstructured as JSON response

                              ↓

[4] CLIENT SETUP (client-go side):

    config := rest.InClusterConfig()

    // Dynamic Client (direct API access)
    dynClient, _ := dynamic.NewForConfig(config)

    // Dynamic Informer Factory (watch + local cache)
    factory := dynamicinformer.NewDynamicSharedInformerFactory(
        dynClient, time.Minute,
    )

    // Get informer for MyResource
    informer := factory.ForResource(
        schema.GroupVersionResource{
            Group: "example.com",
            Version: "v1",
            Resource: "myresources",
        },
    )

    // Get lister for cached access
    lister := dynamiclister.New(informer.GetIndexer(), gvr)

                              ↓

[5] DYNAMIC INFORMER OPERATION:

    factory.Start(stopCh)

    → dynamicInformer starts:
      ├─ reflector := cache.NewReflector(
      │   listerWatcher: DynamicResourceClient.Watch/List,
      │   expectedType: *unstructured.Unstructured,
      │   store: cache.Indexer,
      │ )
      ├─ reflector.Run() in goroutine:
      │   Loop:
      │   ├─ client.Resource(gvr).List() → *UnstructuredList
      │   │   └─ GET /apis/example.com/v1/myresources
      │   ├─ Populate indexer with all objects
      │   ├─ client.Resource(gvr).Watch() → watch.Interface
      │   │   └─ WATCH /apis/example.com/v1/myresources
      │   ├─ Receive Add/Modify/Delete events → indexer.Update()
      │   └─ Reconcile cache on watch reconnect
      │
      └─ processorListener notifies registered event handlers

    factory.WaitForCacheSync(stopCh)
    → Blocks until reflector synced for all informers

                              ↓

[6] APPLICATION CODE: DIRECT DYNAMIC CLIENT

    // Get single resource (network call)
    obj, _ := dynClient.
        Resource(gvr).
        Namespace("default").
        Get(context.Background(), "obj1", metav1.GetOptions{})

    // obj is *unstructured.Unstructured
    // HTTP GET /apis/example.com/v1/namespaces/default/myresources/obj1

    // List (network call)
    list, _ := dynClient.
        Resource(gvr).
        Namespace("default").
        List(context.Background(), metav1.ListOptions{})

                              ↓

[7] APPLICATION CODE: CACHED INFORMER

    // Get from local cache (NO network call)
    cached, _ := lister.Namespace("default").Get("obj1")

    // List from cache (NO network call)
    all, _ := lister.Namespace("default").List(labels.Everything())

    // Register event handler
    informer.AddEventHandler(cache.ResourceEventHandlerFuncs{
        AddFunc: func(obj interface{}) {
            unst := obj.(*unstructured.Unstructured)
            fmt.Println("Added:", unst.GetName())
        },
    })

```

---

## Architectural Integration Points

### 1. **Scheme as the Glue**
The `runtime.Scheme` object integrates all four sub-projects:
- **apiextensions** registers CRD types at startup via `install.Install(scheme)`
- **api** registers all core API types (Pod, Service, etc.) via group-specific `AddToScheme()`
- **apimachinery** provides the Scheme implementation and core Object/Unstructured interfaces
- **client-go** uses Scheme to encode/decode objects for REST operations

```go
// Every generated typed client carries a Scheme:
// clientset.Typed().CoreV1().Pods(namespace).Get(name)
// → encodes GroupVersionKind via Scheme
// → makes REST call
// → decodes response via Scheme
```

### 2. **Unstructured as the Bridge**
The `Unstructured` interface and `unstructured.Unstructured` struct are the critical bridge:
- **Server-side**: CRDs stored as Unstructured in etcd (no type stubs needed)
- **Wire format**: JSON serialization of Unstructured (same as any K8s object)
- **Client-side**: Dynamic client and informers work entirely with Unstructured

```go
type Unstructured struct {
    Object map[string]interface{} // Raw YAML/JSON structure
}
// Implements runtime.Object interface → can be used anywhere in Kubernetes
// Implements runtime.Unstructured interface → provides UnstructuredContent() accessor
```

### 3. **Request Scope as the Checkpoint**
The `handlers.RequestScope` object created per CRD version is the checkpoint between:
- **Server-side validation/storage** (CustomResourceStorage)
- **Client-side discovery/access** (dynamic client/informers)

```go
type RequestScope struct {
    Serializer runtime.NegotiatedSerializer // Unstructured codec
    Mapper     meta.RESTMapper // GVR ↔ GVK mapping
    Admission  admission.Interface // Webhook validation
    ...
}
// Used by customresource_handler to process HTTP requests
// Serializer determines how Unstructured objects are encoded/decoded
```

### 4. **TypeMeta Preservation in etcd**
Critical for dynamic resources:
```go
// Custom resource in etcd looks like:
{
  "apiVersion": "example.com/v1",     // From Unstructured.Object["apiVersion"]
  "kind": "MyResource",               // From Unstructured.Object["kind"]
  "metadata": { "name": "obj1", ... },
  "spec": { "field1": "value1", ... }
}

// When retrieved:
unst.SetGroupVersionKind(gvk) signals decoder to inject GVK info
// GVK extracted from "kind" and "apiVersion" JSON fields
// Stored in Unstructured's internal state via GetObjectKind()
```

---

## Cross-Project Dependency Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    apimachinery (Foundation)                    │
│  - Scheme: GVK ↔ Go type registry                              │
│  - Object interface: All K8s resources implement this           │
│  - Unstructured: Dynamic type for CRDs                         │
│  - TypeMeta/ObjectMeta: Standard metadata                      │
│  - runtime/schema: GVK, GVR types                              │
└────────────────────────┬────────────────────────────────────────┘
                         │ (implements)
        ┌────────────────┴────────────────┐
        │                                 │
┌───────▼──────────────────────┐ ┌──────▼──────────────────────┐
│   apiextensions-apiserver    │ │      client-go              │
│  (Server-Side)               │ │   (Client-Side)             │
│                              │ │                             │
│  1. CRD Types                │ │  1. DynamicClient           │
│     - Spec, Status           │ │     - Uses Unstructured     │
│     - Registered in Scheme   │ │     - Direct REST access    │
│                              │ │                             │
│  2. Validation               │ │  2. DynamicInformer         │
│     - OpenAPI schema check   │ │     - Watches via client    │
│     - CEL rules              │ │     - Maintains cache       │
│                              │ │                             │
│  3. HTTP Handler             │ │  3. DynamicLister           │
│     - crdHandler routes       │ │     - Queries cache         │
│     - Per-CRD RequestScope    │ │     - No network calls      │
│                              │ │                             │
│  4. etcd Storage             │ │  4. Dynamic Serializer      │
│     - Unstructured in etcd   │ │     - Unstructured codec    │
│     - Schema validation      │ │     - JSON ↔ map[string]any │
│                              │ │                             │
└──────────────────────────────┘ └─────────────────────────────┘
        │                                 │
        └────────────────┬────────────────┘
                         │
                  (shares Scheme)
                         │
        ┌────────────────▼────────────────┐
        │   api (Type Registration)       │
        │  - Core API group types         │
        │  - (Pod, Service, Deployment)   │
        │  - register.go per API group    │
        └────────────────────────────────┘
```

---

## Summary

The Kubernetes CRD lifecycle is a elegant example of cross-project integration:

1. **apimachinery** provides the foundational `Scheme`, `Object`, `Unstructured` abstractions and `TypeMeta`/`ObjectMeta` that every K8s resource shares.

2. **apiextensions-apiserver** defines CRD types, validates them against OpenAPI schemas, and implements the HTTP handler that stores custom resources as `Unstructured` objects in etcd. The `UnstructuredObjectTyper` bridges discovery metadata to runtime typing.

3. **client-go** provides the dynamic client that uses `Unstructured` for all CRD operations, plus informers and listers that maintain a local cache of CRDs via watch-list-watch semantics.

4. **api** registers the core API types in the shared Scheme, enabling typed clients for built-in resources (while CRDs use dynamic clients).

The key architectural insight: **CRDs are server-side resources whose instances are always stored as `map[string]interface{}` (Unstructured) in etcd, validated against their OpenAPI v3 schema, and accessed by clients via the dynamic client or informers**. This design enables Kubernetes to support arbitrary user-defined schemas without requiring pre-compilation of Go types, while maintaining the same serialization, caching, and list-watch semantics as built-in resources.


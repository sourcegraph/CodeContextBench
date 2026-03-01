# CRD Lifecycle Across Kubernetes Sub-Projects

## Files Examined

### Foundation Layer - apimachinery
- **staging/src/k8s.io/apimachinery/pkg/runtime/schema/group_version.go** — Defines GroupVersionKind (GVK), GroupVersionResource (GVR), and parsing logic for extracting group, version, and kind/resource from API objects
- **staging/src/k8s.io/apimachinery/pkg/runtime/scheme.go** — Core Scheme struct (gvkToType, typeToGVK mappings) that manages type registration, versioning, and conversion between Go types and their serialized forms
- **staging/src/k8s.io/apimachinery/pkg/runtime/interfaces.go** — Defines Object, Unstructured, Encoder/Decoder, and Scheme interfaces that all Kubernetes types implement
- **staging/src/k8s.io/apimachinery/pkg/apis/meta/v1/types.go** — TypeMeta (Kind, APIVersion), ObjectMeta (name, namespace, UID, timestamps), ListMeta (resourceVersion, continue token)
- **staging/src/k8s.io/apimachinery/pkg/apis/meta/v1/unstructured/unstructured.go** — Unstructured struct (map[string]interface{}) for dynamic resources; implements runtime.Object and runtime.Unstructured interfaces
- **staging/src/k8s.io/apimachinery/pkg/runtime/converter.go** — UnstructuredConverter for bidirectional conversion between concrete types and map[string]interface{}

### Type Definition Layer - apiextensions-apiserver
- **staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/types.go** — Internal (hub) CustomResourceDefinition type with spec describing group, version, names, validation, conversion strategy
- **staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1/types.go** — External v1 CustomResourceDefinition type (serialized form with json tags)
- **staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1beta1/types.go** — Deprecated v1beta1 external type (maintained for backward compatibility)
- **staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/register.go** — SchemeGroupVersion for internal hub; addKnownTypes registers CustomResourceDefinition and CustomResourceDefinitionList to Scheme with runtime.APIVersionInternal
- **staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1/register.go** — SchemeGroupVersion for v1; addKnownTypes with v1 version; registers conversion functions and defaulting functions
- **staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/v1/zz_generated.conversion.go** — Auto-generated conversion functions (Convert_v1_CustomResourceDefinition_To_apiextensions_CustomResourceDefinition, etc.)
- **staging/src/k8s.io/apiextensions-apiserver/pkg/apis/apiextensions/install/install.go** — Install() function that registers internal, v1beta1, and v1 to Scheme and sets version priority (v1 > v1beta1)

### Server-Side Handler Layer - apiextensions-apiserver
- **staging/src/k8s.io/apiextensions-apiserver/pkg/apiserver/apiserver.go** — Scheme initialization (line 54-76: install.Install(Scheme), metav1.AddToGroupVersion, AddUnversionedTypes); CustomResourceDefinitions server setup
- **staging/src/k8s.io/apiextensions-apiserver/pkg/apiserver/customresource_handler.go** — crdHandler struct with customStorageLock, customStorage (atomic.Value), crdLister; dynamically routes HTTP requests to custom resource endpoints; uses Unstructured for serialization
- **staging/src/k8s.io/apiextensions-apiserver/pkg/registry/customresourcedefinition/etcd.go** — REST struct implementing RESTStorage; NewREST creates genericregistry.Store with NewFunc/NewListFunc returning internal apiextensions.CustomResourceDefinition and CustomResourceDefinitionList
- **staging/src/k8s.io/apiextensions-apiserver/pkg/registry/customresourcedefinition/strategy.go** — MatchCustomResourceDefinition and CustomResourceDefinitionToSelectableFields for etcd filtering
- **staging/src/k8s.io/apiextensions-apiserver/pkg/crdserverscheme/unstructured.go** — UnstructuredObjectTyper for extracting GVK from Unstructured objects at runtime (ObjectKinds, Recognizes methods)

### Client-Side Dynamic Client Layer - client-go
- **staging/src/k8s.io/client-go/dynamic/interface.go** — ResourceInterface defining Create, Update, Delete, Get, List, Watch, Patch operations on *unstructured.Unstructured; NamespaceableResourceInterface with Namespace() support
- **staging/src/k8s.io/client-go/dynamic/simple.go** — DynamicClient implementation; ConfigFor configures REST with JSON serialization and basicNegotiatedSerializer; NewForConfig creates REST client
- **staging/src/k8s.io/client-go/dynamic/scheme.go** — basicNegotiatedSerializer using UnstructuredJSONScheme for Unstructured encoding/decoding

### Informer Layer - client-go
- **staging/src/k8s.io/client-go/dynamic/dynamicinformer/informer.go** — DynamicSharedInformerFactory with ForResource(GVR) returning GenericInformer; creates cache.SharedIndexInformer for each GVR
- **staging/src/k8s.io/client-go/tools/cache/shared_informer.go** — SharedInformer (sync.Informer) interface providing local cache (GetStore, GetIndexer); SharedIndexInformer adds indexing; sharedIndexInformer implementation with ListWatch, Controller, Indexer

### Lister Layer - client-go
- **staging/src/k8s.io/client-go/dynamic/dynamiclister/lister.go** — dynamicLister implementing Lister interface; List(selector) and Get(name) query cache.Indexer; NamespaceLister for namespace-scoped queries
- **staging/src/k8s.io/apiextensions-apiserver/pkg/client/listers/apiextensions/v1/customresourcedefinition.go** — Generated CRD-specific lister interface and implementation using cache.Indexer

### Meta Information Types - apimachinery
- **staging/src/k8s.io/apimachinery/pkg/apis/meta/v1/unstructured/helpers.go** — UnstructuredJSONScheme codec for Unstructured Encode/Decode using JSON marshaling; decodeToUnstructured helper

---

## Dependency Chain

### 1. Foundation: Apimachinery Runtime Types
**Key Concepts:**
- **Scheme**: Central registry mapping Go types to GVK, handling serialization/deserialization
- **GVK (GroupVersionKind)**: Identifies a type uniquely (e.g., "apiextensions.k8s.io/v1/CustomResourceDefinition")
- **GVR (GroupVersionResource)**: Identifies a REST resource (e.g., "customresourcedefinitions.apiextensions.k8s.io/v1")
- **TypeMeta/ObjectMeta**: Metadata present on all objects (Kind, APIVersion, Name, UID, etc.)
- **Unstructured**: Universal container for any resource (map[string]interface{}) when concrete types unavailable

**Files:**
- `apimachinery/pkg/runtime/scheme.go`: Core scheme with mappings
- `apimachinery/pkg/runtime/schema/group_version.go`: GVK/GVR definitions
- `apimachinery/pkg/apis/meta/v1/types.go`: TypeMeta, ObjectMeta
- `apimachinery/pkg/apis/meta/v1/unstructured/unstructured.go`: Unstructured implementation

### 2. Type Definitions: CRD Hub Types and External Versions
**Key Concepts:**
- **Internal Hub Type**: apiextensions.CustomResourceDefinition (in `apiextensions/types.go`)
  - Contains all CRD spec fields: Group, Version, Names, Validation, Conversion, Subresources
  - Never serialized; only exists in memory as internal working representation

- **External v1 Type**: apiextensions.v1.CustomResourceDefinition (in `apiextensions/v1/types.go`)
  - Concrete Go struct with JSON tags for serialization/deserialization
  - Follows Kubernetes API conventions

- **Conversion**: Generated conversion functions in `apiextensions/v1/zz_generated.conversion.go`
  - Bidirectional conversion between internal and v1 types
  - Registered to Scheme via RegisterConversions() in apiextensions/v1/register.go

**Files:**
- `apiextensions-apiserver/pkg/apis/apiextensions/types.go`: Internal hub type
- `apiextensions-apiserver/pkg/apis/apiextensions/v1/types.go`: External v1 type
- `apiextensions-apiserver/pkg/apis/apiextensions/v1/zz_generated.conversion.go`: Conversions
- `apiextensions-apiserver/pkg/apis/apiextensions/register.go`: Register internal hub
- `apiextensions-apiserver/pkg/apis/apiextensions/v1/register.go`: Register v1 and conversions
- `apiextensions-apiserver/pkg/apis/apiextensions/install/install.go`: Install all versions to Scheme

### 3. Server-Side: Validation, Storage, and HTTP Handler
**Key Concepts:**
- **Scheme Initialization**: `apiextensions-apiserver/pkg/apiserver/apiserver.go` calls `install.Install(Scheme)`, which:
  - Registers internal CustomResourceDefinition (GVK: apiextensions.k8s.io/__internal/CustomResourceDefinition)
  - Registers v1beta1.CustomResourceDefinition (GVK: apiextensions.k8s.io/v1beta1/CustomResourceDefinition)
  - Registers v1.CustomResourceDefinition (GVK: apiextensions.k8s.io/v1/CustomResourceDefinition)
  - Registers conversion functions to enable cross-version encoding/decoding

- **CRD Storage**: `apiextensions-apiserver/pkg/registry/customresourcedefinition/etcd.go` implements REST interface
  - NewFunc creates runtime.Object instances (internal hub type)
  - Stores CRDs in etcd via apiserver/pkg/registry/generic/registry
  - Uses MatchCustomResourceDefinition for filtering

- **Dynamic HTTP Handler**: `apiextensions-apiserver/pkg/apiserver/customresource_handler.go`
  - crdHandler manages custom resource endpoints dynamically
  - customStorage (atomic.Value) caches built REST handlers indexed by CRD GVK
  - For each request to /apis/{group}/{version}/{resource}, routes to appropriate handler
  - Uses Unstructured for serialization (unstructuredJSONScheme)
  - Validation applied via structured schema from CRD specification

**Files:**
- `apiextensions-apiserver/pkg/apiserver/apiserver.go`: Server setup (line 54-76, 280-290)
- `apiextensions-apiserver/pkg/apiserver/customresource_handler.go`: Request routing and Unstructured handling
- `apiextensions-apiserver/pkg/registry/customresourcedefinition/etcd.go`: CRD storage layer

### 4. Client-Side: Typed Client, Informers, Listers, and Dynamic Client
**Key Concepts:**
- **Typed Clientset**: apiextensions-apiserver/pkg/client/clientset/ provides type-safe access to CRDs
  - Methods like Create, Update, List, Watch on CustomResourceDefinitionInterface
  - Uses REST client internally

- **Informers**: apiextensions-apiserver/pkg/client/informers/ and client-go/dynamic/dynamicinformer/
  - SharedIndexInformer watches API server for changes
  - Maintains local cache (Indexer) of objects
  - Notifies registered event handlers (Add, Update, Delete)
  - For dynamic resources, DynamicSharedInformerFactory handles any GVR

- **Listers**: apiextensions-apiserver/pkg/client/listers/ and client-go/dynamic/dynamiclister/
  - Query cached informer state without hitting API server
  - CustomResourceDefinitionLister for CRDs; DynamicLister for any resource
  - Support label/field selection and namespace scoping

- **Dynamic Client**: client-go/dynamic/ for untyped resource access
  - ResourceInterface operates on *unstructured.Unstructured
  - CRUD operations: Create, Update, Delete, Get, List, Watch, Patch
  - NamespaceableResourceInterface adds namespace() method
  - Uses Unstructured JSON codec for serialization

**Files:**
- `apiextensions-apiserver/pkg/client/clientset/clientset/typed/apiextensions/v1/customresourcedefinition.go`: Typed CRD client
- `apiextensions-apiserver/pkg/client/informers/externalversions/apiextensions/v1/customresourcedefinition.go`: CRD informer
- `apiextensions-apiserver/pkg/client/listers/apiextensions/v1/customresourcedefinition.go`: CRD lister
- `client-go/dynamic/interface.go`: Dynamic client interface
- `client-go/dynamic/simple.go`: Dynamic client implementation
- `client-go/dynamic/dynamicinformer/informer.go`: Dynamic informer factory
- `client-go/dynamic/dynamiclister/lister.go`: Dynamic lister
- `client-go/tools/cache/shared_informer.go`: SharedIndexInformer base

### 5. Checkpoint: Custom Resource Lifecycle
After a CRD is created:
- Server creates HTTP endpoints for the custom resource at `/apis/{group}/{version}/{resources}`
- Custom resources stored as Unstructured in etcd (type info in metadata: apiVersion, kind fields)
- Clients can:
  - Use typed clients (if code-generated) for structured access
  - Use dynamic client with unstructured.Unstructured for generic access
  - Use informers to cache and watch changes
  - Use listers to query the local cache
- Informers pull Unstructured objects via dynamic client, store in SharedIndexInformer
- Listers query the SharedIndexInformer's Indexer without network calls

---

## Analysis

### Cross-Project Dependency Flow

**apimachinery → apiextensions-apiserver:**
- apimachinery defines Scheme, GVK/GVR, Unstructured, Object interfaces
- apiextensions-apiserver uses these to implement CRD types and storage
- All CRD types embed metav1.TypeMeta and metav1.ObjectMeta from apimachinery

**apiextensions-apiserver → client-go:**
- apiextensions-apiserver pkg/client/ (clientset, informers, listers) are generated via code-gen
- Generated clients target apiextensions-apiserver types (v1.CustomResourceDefinition)
- Same patterns used in client-go/dynamic/ for any resource (typed or untyped)

**client-go ← apiextensions-apiserver:**
- client-go/dynamic provides generic interface independent of specific types
- Can query any resource including CRDs without generated code
- Dynamic client works because all objects are Unstructured at REST level

### How CRD Types Bridge the Four Sub-Projects

1. **api (apiextensions group)**: In a standalone repo, the apiextensions types would live here. In monorepo, apiextensions-apiserver contains them directly.

2. **apiextensions-apiserver**:
   - Owns CRD type definitions (types.go, v1/types.go, v1beta1/types.go)
   - Registers to Scheme with hub version strategy
   - Stores CRDs in etcd via generic registry
   - Dynamically creates HTTP handlers for custom resources

3. **apimachinery**:
   - Foundation: Scheme, GVK/GVR, TypeMeta, ObjectMeta, Unstructured
   - Provides codecs for serialization
   - Conversion framework for version migration

4. **client-go**:
   - Generated clients for CRDs (pkg/client/clientset, informers, listers)
   - Also provides dynamic/untyped client for any resource
   - Informers and listers use Unstructured for custom resources
   - SharedIndexInformer and cache machinery

### The Role of Scheme and GVK

The **Scheme** acts as the central type registry:
- Maintains bidirectional mapping: GVK ↔ Go Type
- Stores conversion functions between versions
- Provides encoder/decoder implementations
- Version priority determines which version used when multiple present

**GVK** uniquely identifies every type:
- **Group**: "apiextensions.k8s.io"
- **Version**: "v1", "v1beta1", or "__internal" (hub)
- **Kind**: "CustomResourceDefinition"

When deserialization occurs, Scheme uses GVK from JSON (apiVersion + kind) to:
1. Look up the target Go type
2. Apply version-specific decoder
3. Optionally convert from incoming version to hub version

### How Unstructured Enables Dynamic Custom Resources

**Unstructured** (map[string]interface{}) is fundamental to CRD support:
- Custom resources don't have pre-generated Go types
- Instead, stored and transmitted as JSON
- At runtime, deserialized to Unstructured
- Unstructured implements runtime.Object interface, so works with generic machinery

**Encoding/Decoding path for custom resources:**
1. JSON from wire → unstructured.UnstructuredJSONScheme.Decode()
2. Decode extracts apiVersion, kind → looks up GVK
3. Creates Unstructured with map data
4. Unstructured.GetObjectKind().SetGroupVersionKind() sets GVK
5. Validation, mutation via structural schema applied at handler level
6. For storage: Encode Unstructured → JSON → etcd

### Checkpoint: Server-Side Storage to Client-Side Informer Caching

**Server Side (apiextensions-apiserver):**
- CRD specifies custom resource shape (group, version, names, validation)
- HTTP handler accepts POST/PUT/GET/DELETE on custom resource endpoints
- Custom resources serialized as Unstructured JSON in etcd
- Response includes metadata (apiVersion, kind, metadata.name, metadata.uid, etc.)

**Network Boundary (REST API):**
- Client watches /apis/{group}/{version}/{resource}?watch=true or lists with ?fieldSelector
- Server streams ADDED, MODIFIED, DELETED events
- Events contain full Unstructured representation

**Client Side (client-go):**
- ListWatch (in shared_informer.go) calls client.List() and client.Watch()
- Returns Unstructured objects
- Controller processes events:
  - ADDED event: Indexer.Add(obj)
  - MODIFIED event: Indexer.Update(obj)
  - DELETED event: Indexer.Delete(obj)
- Listeners notified (event handlers called)
- GetStore() / GetIndexer() returns cache.Indexer with all objects
- Lister queries Indexer without further network calls

**Key Integration Point:**
- `dynamicinformer.DynamicSharedInformerFactory` creates informers for any GVR
- Each informer has a ListWatch using dynamic.Interface (untyped client)
- Dynamic client GetList() returns *unstructured.UnstructuredList
- Controller extracts Items and indexes them
- Lister wraps the same Indexer

### Conversion Between Hub and External Versions

When a CRD is created in v1beta1 format:
1. Client sends v1beta1.CustomResourceDefinition (JSON)
2. Server's crdHandler receives request
3. versioning codec converts v1beta1 → internal hub via generated converter
4. Internal type validated and stored in etcd
5. On retrieval, hub converted back to requested version (v1beta1 or v1)

Scheme.Convert() uses registered conversion functions:
- Shallow copy fields present in both versions
- Transform version-specific fields
- Maintain invariants (e.g., Validation is the same across versions)

---

## Summary

The Kubernetes CRD lifecycle represents a sophisticated cross-layer architecture:

**Foundation (apimachinery)** provides Scheme for type registration, GVK/GVR for identification, and Unstructured as the universal container for dynamic resources. **apiextensions-apiserver** defines CRD types with hub-version strategy, stores them in etcd through a generic registry, and dynamically creates HTTP handlers that marshal custom resources as Unstructured. **client-go** bridges server and client with a dynamic client interface for untyped Unstructured CRUD operations, informers that cache Unstructured objects via SharedIndexInformer, and listers that query the cache. The checkpoint between server storage and client caching occurs at the ListWatch boundary where Unstructured objects flow from etcd through the API server to client informers, maintaining type identity through apiVersion and kind metadata while enabling generic, version-agnostic tooling across the Kubernetes ecosystem.

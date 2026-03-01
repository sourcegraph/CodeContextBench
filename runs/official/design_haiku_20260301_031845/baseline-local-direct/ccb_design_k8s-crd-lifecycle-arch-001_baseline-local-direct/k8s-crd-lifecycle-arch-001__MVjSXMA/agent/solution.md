# CRD Lifecycle Across the Kubernetes Ecosystem

## Files Examined

### k8s.io/apiextensions-apiserver (CRD Server)
- `pkg/apis/apiextensions/types.go` — Internal hub types for CustomResourceDefinition, spec, validation, subresources
- `pkg/apis/apiextensions/v1/types.go` — External v1 API types for CustomResourceDefinition
- `pkg/apis/apiextensions/register.go` — SchemeBuilder registration for internal types
- `pkg/apis/apiextensions/v1/register.go` — SchemeBuilder registration for v1 types
- `pkg/apis/apiextensions/install/install.go` — Install function to register all CRD versions in Scheme
- `pkg/apis/apiextensions/validation/validation.go` — Validation logic for CRD specs
- `pkg/apis/apiextensions/validation/cel_validation.go` — CEL-based validation for CustomResources
- `pkg/apiserver/customresource_handler.go` — HTTP handler for custom resource CRUD operations
- `pkg/apiserver/conversion/converter.go` — Handles multi-version conversion strategies
- `pkg/registry/customresource/` — Storage layer for custom resources

### k8s.io/client-go (Client Access Layer)
- `dynamic/interface.go` — Dynamic client interface for untyped resource access
- `dynamic/simple.go` — Dynamic client implementation
- `dynamic/scheme.go` — Scheme management for dynamic client
- `dynamic/dynamicinformer/interface.go` — DynamicSharedInformerFactory for untyped informers
- `dynamic/dynamiclister/` — Listers for dynamic client
- `informers/factory.go` — SharedInformerFactory for typed informers
- `informers/internalinterfaces/factory_interfaces.go` — Factory interfaces for informers
- `informers/{core,apps,batch,...}/interface.go` — Group-specific informer factories
- `listers/{core,apps,batch,...}/` — Group-specific listers

### k8s.io/apimachinery (Foundation Types)
- `pkg/runtime/scheme.go` — Scheme: type registry mapping GVK → Go struct
- `pkg/runtime/scheme_builder.go` — SchemeBuilder helper for convenient registration
- `pkg/runtime/schema/group_version.go` — GVK/GVR structures and operations
- `pkg/runtime/schema/interfaces.go` — Schema interfaces (ObjectKind, runtime.Object)
- `pkg/apis/meta/v1/types.go` — TypeMeta, ObjectMeta, ListMeta definitions
- `pkg/apis/meta/v1/unstructured/unstructured.go` — Unstructured: generic object representation
- `pkg/apis/meta/v1/unstructured/unstructured_list.go` — UnstructuredList for list results
- `pkg/apis/meta/v1/unstructured/helpers.go` — Helpers for Unstructured manipulation

### k8s.io/api (Internal Hub Types)
- `core/v1/types.go` — Core API types (Pod, Service, etc.) - also shows hub pattern
- `core/v1/register.go` — Core API group registration


## Dependency Chain

### Layer 1: Foundation (apimachinery)
All other projects depend on foundational types:

1. **Scheme** (`runtime/scheme.go`):
   - Central type registry mapping `GroupVersionKind → reflect.Type`
   - Maps reverse: `reflect.Type → []GroupVersionKind`
   - Enables serialization/deserialization of objects
   - Thread-safe type registry after initialization
   - All API resources must be registered in a Scheme

2. **GVK/GVR** (`runtime/schema/group_version.go`):
   - `GroupVersionKind`: Identifies a type (group, version, kind)
   - `GroupVersionResource`: Identifies a resource (group, version, resource name)
   - Used to uniquely address any API resource in the cluster
   - Conversion functions between GVK and GVR

3. **ObjectKind/TypeMeta** (`apis/meta/v1/types.go`):
   - `TypeMeta`: Contains `Kind` and `APIVersion` fields
   - `ObjectMeta`: Contains metadata (name, namespace, uid, labels, etc.)
   - All Kubernetes objects embed these

4. **Unstructured** (`apis/meta/v1/unstructured/`):
   - Generic map-based representation: `map[string]interface{}`
   - Implements `runtime.Object` interface
   - Implements `metav1.Object` interface
   - Enables access to any resource without compiled Go types
   - Essential for dynamic client to handle arbitrary CRDs

### Layer 2: CRD Type Definitions (apiextensions-apiserver)
CRD server defines and manages custom resource types:

1. **Internal Hub Types** (`pkg/apis/apiextensions/types.go`):
   - `CustomResourceDefinition`: Defines a custom resource type
   - `CustomResourceDefinitionSpec`: Schema, validation, scope, versions
   - `CustomResourceDefinitionNames`: Plural, singular, kind, short names
   - `CustomResourceValidation`: OpenAPI v3 schema for validation
   - Uses `metav1.TypeMeta` and `metav1.ObjectMeta` from apimachinery
   - Registered via `apiextensions.AddToScheme()`

2. **External v1 Types** (`pkg/apis/apiextensions/v1/types.go`):
   - User-facing v1 representation of CRD
   - Conversion logic between internal and v1
   - Defaults and field pruning logic
   - Version priority: v1 > v1beta1

3. **Scheme Registration** (`pkg/apis/apiextensions/register.go`):
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
   - Registers CRD types in the Scheme
   - Also registers conversion functions between versions

4. **Install Function** (`pkg/apis/apiextensions/install/install.go`):
   ```go
   func Install(scheme *runtime.Scheme) {
       utilruntime.Must(apiextensions.AddToScheme(scheme))
       utilruntime.Must(v1beta1.AddToScheme(scheme))
       utilruntime.Must(v1.AddToScheme(scheme))
       utilruntime.Must(scheme.SetVersionPriority(v1.SchemeGroupVersion, v1beta1.SchemeGroupVersion))
   }
   ```
   - Single function to register all CRD versions in a Scheme
   - Sets version priority for negotiation

### Layer 3: Server-Side Lifecycle (apiextensions-apiserver)

1. **Validation** (`pkg/apis/apiextensions/validation/validation.go`):
   - Validates incoming CustomResourceDefinition specs
   - Checks for naming conflicts, scope validity
   - Validates OpenAPI schemas for structural compliance
   - CEL validation rules for advanced validation

2. **Storage** (`pkg/registry/customresource/`):
   - RESTStorage interface for etcd storage
   - Stores actual CustomResources as Unstructured objects
   - Enables version migration and storage class transitions
   - Tracks stored versions in CRD status

3. **HTTP Handler** (`pkg/apiserver/customresource_handler.go`):
   ```
   Type: crdHandler
   - Serves HTTP requests for custom resources
   - Routes based on CRD definition
   - Applies admission webhooks
   - Handles conversion between versions
   - Supports subresources (status, scale)
   - Validates custom resources against schema
   ```
   - Creates dynamic REST endpoints for each registered CRD
   - Handles CRUD operations on custom resources
   - Enforces validation schemas
   - Applies webhooks for conversion and validation
   - Manages subresources (/status, /scale)
   - Returns Unstructured objects

4. **Conversion** (`pkg/apiserver/conversion/converter.go`):
   - None: Simple apiVersion update only
   - Webhook: External conversion service
   - Manages multiple stored versions

### Layer 4: Client-Side Access Layer (client-go)

1. **Dynamic Client** (`dynamic/interface.go`):
   ```go
   type Interface interface {
       Resource(resource schema.GroupVersionResource) NamespaceableResourceInterface
   }
   type ResourceInterface interface {
       Create(ctx context.Context, obj *unstructured.Unstructured, ...) (*unstructured.Unstructured, error)
       Update(ctx context.Context, obj *unstructured.Unstructured, ...) (*unstructured.Unstructured, error)
       Get(ctx context.Context, name string, ...) (*unstructured.Unstructured, error)
       List(ctx context.Context, opts metav1.ListOptions) (*unstructured.UnstructuredList, error)
       Watch(ctx context.Context, opts metav1.ListOptions) (watch.Interface, error)
       Delete(ctx context.Context, name string, ...) error
       Patch(ctx context.Context, name string, ...) (*unstructured.Unstructured, error)
   }
   ```
   - Generic interface for any GVR (any CRD)
   - Works with Unstructured objects
   - Supports full CRUD operations
   - No compile-time type information needed
   - Key enabler for dynamic resource access

2. **Dynamic Client Implementation** (`dynamic/simple.go`):
   - Implements ResourceInterface using REST calls
   - Uses Unstructured for serialization
   - Handles namespace scoping
   - Routes requests through apiserver

3. **Dynamic Informers** (`dynamic/dynamicinformer/`):
   ```go
   type DynamicSharedInformerFactory interface {
       ForResource(gvr schema.GroupVersionResource) informers.GenericInformer
       Start(stopCh <-chan struct{})
       WaitForCacheSync(stopCh <-chan struct{}) map[schema.GroupVersionResource]bool
   }
   ```
   - Watches custom resources for changes
   - Maintains local cache via SharedIndexInformer
   - Provides indexed access by labels/fields
   - Works with any GVR

4. **Typed Informers** (`informers/factory.go`):
   - SharedInformerFactory for built-in types
   - Type-safe access to objects
   - Shares underlying cache across multiple informers
   - Generated per API group

5. **Listers** (`listers/{core,apps,...}/` and `dynamic/dynamiclister/`):
   - Query cached informer data
   - Dynamic listers: `DynamicLister` for any GVR
   - Typed listers: Type-safe list queries
   - Avoid hitting apiserver for read-only access
   - Support label/field selectors

## Analysis

### Cross-Project Integration Flow

1. **Initialization**:
   ```
   Client bootstrap → NewScheme() → Install(scheme) via apiextensions package
   → Scheme contains CRD type definitions
   → Dynamic client can address any CRD
   ```

2. **CRD Creation (User)**:
   ```
   User applies CustomResourceDefinition YAML
   → HTTP request to apiextensions-apiserver
   → customresource_handler routes to CRD endpoint
   → Validation: checks against CRD schema
   → Storage: persists to etcd as internal types
   → Client-go watches for changes via informers
   ```

3. **Custom Resource CRUD**:
   ```
   Application uses dynamic.Client.Resource(gvr).Create(unstructured.Unstructured)
   → Dynamic client routes to appropriate handler
   → customresource_handler for that GVR
   → Validation against CRD's OpenAPI schema
   → Storage in etcd (as Unstructured)
   → Returns Unstructured object to client
   ```

4. **Caching and Watching**:
   ```
   DynamicSharedInformerFactory.ForResource(gvr)
   → Watches custom resources via List-Watch
   → SharedIndexInformer maintains local cache
   → Indexed by labels, fields, namespace
   → DynamicLister queries cache without apiserver calls
   ```

### Role of Each Foundation Type

**Scheme**:
- Central registry binding GVK ↔ Go types
- Enables Unstructured objects to be created without knowing the type at compile-time
- apiextensions registers CRD types in Scheme, but CRD instances are stored as Unstructured
- Dynamic client uses Scheme to understand type metadata

**GVK/GVR**:
- Unique addresses for types and resources
- Dynamic client uses GVR to route to correct endpoint
- Informers key cached data by GVR
- Enables programmatic resource identification

**ObjectMeta/TypeMeta**:
- Standard metadata all objects share (including custom resources)
- TypeMeta.Kind and APIVersion map to GVK
- ObjectMeta.Name, Namespace, Labels used for indexing
- Accessed uniformly across all resource types

**Unstructured**:
- Bridge between compile-time types and runtime polymorphism
- Stores CRD instances internally (apiextensions doesn't have Go types for user CRDs)
- Returned by dynamic client API
- Supports full object manipulation via map accessors
- Implements ObjectMeta/TypeMeta interfaces for compatibility

### Checkpoint: Server ↔ Client Boundary

**On Server (apiextensions-apiserver)**:
- CRD definition stored as internal type in Scheme
- Custom resource instances stored in etcd
- Serialized as JSON (TypeMeta, ObjectMeta, custom fields)
- When returned to client, wrapped as Unstructured

**On Client (client-go)**:
- Receives Unstructured objects from server
- No Go struct definition available
- Dynamic client and informers work generically
- Optional: application layer can unmarshal to custom Go structs if available

**Cache Synchronization**:
- Informers watch-list all custom resources
- SharedIndexInformer maintains local cache
- Listers query cache instead of making API calls
- Cache entries are Unstructured objects

### Multi-Version Support

1. **CRD Level**: CustomResourceDefinitionVersion specifies multiple served versions
2. **Storage Version**: One version designated for etcd storage
3. **Conversion**: apiextensions-apiserver converts between versions on requests
4. **Client**: Requests specific version, server converts automatically
5. **Cache**: Informers cache in requested version

### Dynamic Resource Discovery

1. **Without Pre-Compilation**:
   - Client-go provides dynamic packages (dynamic, dynamicinformer, dynamiclister)
   - No code generation needed for CRD client
   - Works with any GVR

2. **With Pre-Compilation** (for built-in types):
   - client-go-gen generates typed clients
   - Informers, listers generated per API group
   - Compile-time type safety
   - Same underlying cache mechanism

## Summary

The Kubernetes CRD lifecycle spans four integrated sub-projects: **apimachinery** provides the foundational type system (Scheme, GVK/GVR, ObjectMeta, Unstructured) that enables polymorphism across the entire ecosystem; **apiextensions-apiserver** defines and validates CustomResourceDefinitions, storing both the definitions and instances in etcd via the dynamic HTTP handler; **client-go** exposes dynamic client interfaces and informers that work with any GVR using Unstructured objects, while typed clients and informers provide compile-time safety for built-in types; the checkpoint between server and client is the Unstructured representation, which allows clients to access arbitrary custom resources without compile-time knowledge of their Go types, while informers enable efficient local caching and watching of custom resource changes.

## Key Architectural Insights

1. **Unstructured is Essential**: Without Unstructured, the dynamic client couldn't exist. It's the bridge enabling runtime polymorphism.

2. **Scheme is Universal**: Every component (server, client, informer, lister) depends on Scheme for type understanding and negotiation.

3. **GVR is the Key**: Throughout the system, resources are identified by GroupVersionResource tuples, enabling programmatic routing and access.

4. **Cache Hierarchy**:
   - Server: etcd storage
   - Client: SharedIndexInformer cache
   - Application: In-memory datastructures

5. **Typed vs Dynamic**: Built-in types use generated typed clients; CRDs use dynamic client. Both use the same underlying REST and caching infrastructure.

6. **Validation Boundary**: Validation happens on the server (customresource_handler) before storage, ensuring data integrity across all client types.

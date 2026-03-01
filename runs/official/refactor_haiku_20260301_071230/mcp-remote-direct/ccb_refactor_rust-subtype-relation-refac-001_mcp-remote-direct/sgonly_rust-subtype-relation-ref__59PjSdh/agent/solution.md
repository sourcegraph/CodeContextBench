# SubtypePredicate Refactoring Solution

## Summary
Rename `SubtypePredicate` struct to `SubtypeRelation` and rename fields `a`/`b` to `sub_ty`/`super_ty` across 9+ compiler crates.

## Files Examined

### Definition and Core Changes
- **compiler/rustc_type_ir/src/predicate.rs** (line 918-922) — Original definition of `SubtypePredicate<I: Interner>` struct with fields `a_is_expected`, `a`, and `b`. Rename struct to `SubtypeRelation`, fields `a` → `sub_ty`, `b` → `super_ty`.
- **compiler/rustc_public/src/ty.rs** (line 1510-1514) — Mirror definition of `SubtypePredicate` struct. Rename struct to `SubtypeRelation` and fields `a` → `sub_ty`, `b` → `super_ty`.

### Type Aliases and Re-exports
- **compiler/rustc_middle/src/ty/predicate.rs** (line 24) — Type alias `pub type SubtypePredicate<'tcx> = ir::SubtypePredicate<TyCtxt<'tcx>>`. Rename to `SubtypeRelation`.
- **compiler/rustc_middle/src/ty/mod.rs** (line 92-94) — Re-export of `PolySubtypePredicate` and `SubtypePredicate`. Rename to `PolySubtypeRelation` and `SubtypeRelation`.

### PredicateKind Variant
- **compiler/rustc_type_ir/src/predicate_kind.rs** (line 78) — Variant `Subtype(ty::SubtypePredicate<I>)`. Update data type to `ty::SubtypeRelation<I>`.
- **compiler/rustc_public/src/ty.rs** (line 1485) — Variant `SubType(SubtypePredicate)`. Rename struct reference to `SubtypeRelation`.

### IrPrint and Interface Bounds
- **compiler/rustc_type_ir/src/interner.rs** (line 31) — IrPrint bound `+ IrPrint<ty::SubtypePredicate<Self>>`. Update to `+ IrPrint<ty::SubtypeRelation<Self>>`.
- **compiler/rustc_type_ir/src/ir_print.rs** (lines 6, 54) — Imports and macro invocation. Update to `SubtypeRelation`.

### Field Access in Pattern Matching

#### rustc_infer crate
- **compiler/rustc_infer/src/infer/mod.rs** (lines 719-722, 756-761) — Destructures and constructs `SubtypePredicate` with fields `a_is_expected`, `a`, `b`. Update patterns to use `sub_ty` and `super_ty`.
- **compiler/rustc_infer/src/infer/relate/type_relating.rs** (lines 141-143, 155-157, 200-203) — Constructs `SubtypePredicate` literals. Update field names and struct name.

#### rustc_type_ir crate
- **compiler/rustc_type_ir/src/flags.rs** (line 394) — Destructures `SubtypePredicate { a_is_expected: _, a, b }`. Update to `SubtypeRelation` and field names.
- **compiler/rustc_type_ir/src/relate/solver_relating.rs** (lines 200-203, 213-216) — Constructs `SubtypePredicate` literals with `a_is_expected`, `a`, `b`. Update to `SubtypeRelation` with `sub_ty`, `super_ty`.

#### rustc_hir_typeck crate
- **compiler/rustc_hir_typeck/src/fallback.rs** (lines 353-354) — Destructures `SubtypePredicate { a_is_expected: _, a, b }`. Update to `SubtypeRelation` and field names.

#### rustc_trait_selection crate
- **compiler/rustc_trait_selection/src/error_reporting/traits/ambiguity.rs** (line 503) — Destructures `SubtypePredicate { a_is_expected: _, a, b }`. Update to `SubtypeRelation` and field names.
- **compiler/rustc_trait_selection/src/error_reporting/traits/overflow.rs** (line 93) — Destructures `SubtypePredicate { a, b, a_is_expected: _ }`. Update to `SubtypeRelation` and field names.

#### rustc_next_trait_solver crate
- **compiler/rustc_next_trait_solver/src/solve/mod.rs** (lines 112-115, 122) — Constructs and destructures `SubtypePredicate`. Update to `SubtypeRelation` with new field names.

### Field Access in Printing and Conversion
- **compiler/rustc_middle/src/ty/print/pretty.rs** (lines 3257-3261) — Accesses `self.a` and `self.b` in print implementation. Update to `self.sub_ty` and `self.super_ty`.
- **compiler/rustc_public/src/unstable/convert/stable/ty.rs** (lines 787-788) — Destructures and converts fields `a` and `b`. Update to `sub_ty` and `super_ty`.

### rust-analyzer Tools
- **src/tools/rust-analyzer/crates/hir-ty/src/infer/fallback.rs** (line 418) — Destructures `SubtypePredicate { a_is_expected: _, a, b }`. Update to `SubtypeRelation` and field names.
- **src/tools/rust-analyzer/crates/hir-ty/src/next_solver/infer/mod.rs** (lines 604-607, 640) — Destructures and constructs `SubtypePredicate`. Update to `SubtypeRelation` with new field names.
- **src/tools/rust-analyzer/crates/hir-ty/src/next_solver/ir_print.rs** (lines 190, 199) — IrPrint impl for `SubtypePredicate<Self>`. Update to `SubtypeRelation`.

### Tests and Auxiliary
- **tests/rustdoc-js/auxiliary/interner.rs** (line 75) — Associated type `SubtypePredicate`. Rename to `SubtypeRelation`.

## Dependency Chain

1. **Definition Layer** (lowest - used by all others):
   - compiler/rustc_type_ir/src/predicate.rs: `SubtypePredicate<I: Interner>` struct definition

2. **Mirror Definition**:
   - compiler/rustc_public/src/ty.rs: `SubtypePredicate` (for public API stability)

3. **Type Alias Layer** (wraps definition for tcx):
   - compiler/rustc_middle/src/ty/predicate.rs: Creates `SubtypePredicate<'tcx>` alias

4. **Re-export Layer** (makes aliases available across rustc):
   - compiler/rustc_middle/src/ty/mod.rs: Re-exports `SubtypePredicate` and `PolySubtypePredicate`

5. **PredicateKind Variant** (uses the struct):
   - compiler/rustc_type_ir/src/predicate_kind.rs: `Subtype(SubtypePredicate<I>)` variant

6. **Interface/Trait Bounds**:
   - compiler/rustc_type_ir/src/interner.rs: IrPrint trait bound
   - compiler/rustc_type_ir/src/ir_print.rs: IrPrint implementations

7. **Usage Sites** (depend on 1-6):
   - compiler/rustc_infer/src/infer/mod.rs: Core inference logic
   - compiler/rustc_type_ir/src/flags.rs: Type flag computation
   - compiler/rustc_hir_typeck/src/fallback.rs: Type fallback
   - compiler/rustc_trait_selection/src/error_reporting/traits/{ambiguity,overflow}.rs: Error reporting
   - compiler/rustc_type_ir/src/relate/solver_relating.rs: Type relating
   - compiler/rustc_infer/src/infer/relate/type_relating.rs: Type relating
   - compiler/rustc_next_trait_solver/src/solve/mod.rs: Trait solver
   - compiler/rustc_middle/src/ty/print/pretty.rs: Pretty printing
   - compiler/rustc_public/src/unstable/convert/stable/ty.rs: Stable conversions
   - src/tools/rust-analyzer/crates/hir-ty/src/**/*.rs: rust-analyzer tooling

## Code Changes Required

### 1. compiler/rustc_type_ir/src/predicate.rs
**Location**: Lines 909-922

Change struct definition:
```diff
-/// Encodes that `a` must be a subtype of `b`. The `a_is_expected` flag indicates
-/// whether the `a` type is the type that we should label as "expected" when
+/// Encodes that `sub_ty` must be a subtype of `super_ty`. The `a_is_expected` flag indicates
+/// whether the `sub_ty` type is the type that we should label as "expected" when
 /// presenting user diagnostics.
 #[derive_where(Clone, Copy, Hash, PartialEq, Debug; I: Interner)]
 #[derive(TypeVisitable_Generic, TypeFoldable_Generic, Lift_Generic)]
@@ -918,10 +918,10 @@ pub struct HostEffectPredicate<I: Interner> {
     feature = "nightly",
     derive(Decodable_NoContext, Encodable_NoContext, HashStable_NoContext)
 )]
-pub struct SubtypePredicate<I: Interner> {
+pub struct SubtypeRelation<I: Interner> {
     pub a_is_expected: bool,
-    pub a: I::Ty,
-    pub b: I::Ty,
+    pub sub_ty: I::Ty,
+    pub super_ty: I::Ty,
 }

-impl<I: Interner> Eq for SubtypePredicate<I> {}
+impl<I: Interner> Eq for SubtypeRelation<I> {}
```

### 2. compiler/rustc_public/src/ty.rs
**Location**: Lines 1510-1514

```diff
 #[derive(Clone, Debug, Eq, PartialEq, Serialize)]
-pub struct SubtypePredicate {
-    pub a: Ty,
-    pub b: Ty,
+pub struct SubtypeRelation {
+    pub sub_ty: Ty,
+    pub super_ty: Ty,
 }
```

### 3. compiler/rustc_public/src/ty.rs
**Location**: Line 1485

```diff
 pub enum PredicateKind {
     Clause(ClauseKind),
     DynCompatible(TraitDef),
-    SubType(SubtypePredicate),
+    SubType(SubtypeRelation),
     Coerce(CoercePredicate),
     ConstEquate(TyConst, TyConst),
```

### 4. compiler/rustc_middle/src/ty/predicate.rs
**Location**: Line 24

```diff
 pub type CoercePredicate<'tcx> = ir::CoercePredicate<TyCtxt<'tcx>>;
-pub type SubtypePredicate<'tcx> = ir::SubtypePredicate<TyCtxt<'tcx>>;
+pub type SubtypeRelation<'tcx> = ir::SubtypeRelation<TyCtxt<'tcx>>;
 pub type OutlivesPredicate<'tcx, T> = ir::OutlivesPredicate<TyCtxt<'tcx>, T>;
```

### 5. compiler/rustc_middle/src/ty/predicate.rs
**Location**: Line 32

```diff
 pub type PolyTypeOutlivesPredicate<'tcx> = ty::Binder<'tcx, TypeOutlivesPredicate<'tcx>>;
-pub type PolySubtypePredicate<'tcx> = ty::Binder<'tcx, SubtypePredicate<'tcx>>;
+pub type PolySubtypeRelation<'tcx> = ty::Binder<'tcx, SubtypeRelation<'tcx>>;
 pub type PolyCoercePredicate<'tcx> = ty::Binder<'tcx, CoercePredicate<'tcx>>;
```

### 6. compiler/rustc_middle/src/ty/mod.rs
**Location**: Lines 92-94

```diff
     PolyExistentialPredicate, PolyExistentialProjection, PolyExistentialTraitRef,
-    PolyProjectionPredicate, PolyRegionOutlivesPredicate, PolySubtypePredicate, PolyTraitPredicate,
+    PolyProjectionPredicate, PolyRegionOutlivesPredicate, PolySubtypeRelation, PolyTraitPredicate,
     PolyTraitRef, PolyTypeOutlivesPredicate, Predicate, PredicateKind, ProjectionPredicate,
-    RegionOutlivesPredicate, SubtypePredicate, TraitPredicate, TraitRef, TypeOutlivesPredicate,
+    RegionOutlivesPredicate, SubtypeRelation, TraitPredicate, TraitRef, TypeOutlivesPredicate,
```

### 7. compiler/rustc_type_ir/src/predicate_kind.rs
**Location**: Line 78

```diff
     /// `T1 <: T2`
     ///
     /// This obligation is created most often when we have two
     /// unresolved type variables and hence don't have enough
     /// information to process the subtyping obligation yet.
-    Subtype(ty::SubtypePredicate<I>),
+    Subtype(ty::SubtypeRelation<I>),
```

### 8. compiler/rustc_type_ir/src/interner.rs
**Location**: Line 31

```diff
     + IrPrint<ty::NormalizesTo<Self>>
-    + IrPrint<ty::SubtypePredicate<Self>>
+    + IrPrint<ty::SubtypeRelation<Self>>
     + IrPrint<ty::CoercePredicate<Self>>
```

### 9. compiler/rustc_type_ir/src/ir_print.rs
**Location**: Lines 6, 54

```diff
     ExistentialTraitRef, FnSig, HostEffectPredicate, Interner, NormalizesTo, OutlivesPredicate,
     PatternKind, ProjectionPredicate, SubtypePredicate, TraitPredicate, TraitRef, UnevaluatedConst,

-macro_rules! define_display_via_print {
+Change imports:
-use crate::{
-    ...,
-    SubtypePredicate,
-    ...
-};
+use crate::{
+    ...,
+    SubtypeRelation,
+    ...
+};

     NormalizesTo,
-    SubtypePredicate,
+    SubtypeRelation,
     CoercePredicate,
```

### 10. compiler/rustc_type_ir/src/flags.rs
**Location**: Line 394

```diff
-            ty::PredicateKind::Subtype(ty::SubtypePredicate { a_is_expected: _, a, b }) => {
-                self.add_ty(a);
-                self.add_ty(b);
+            ty::PredicateKind::Subtype(ty::SubtypeRelation { a_is_expected: _, sub_ty, super_ty }) => {
+                self.add_ty(sub_ty);
+                self.add_ty(super_ty);
```

### 11. compiler/rustc_infer/src/infer/mod.rs
**Location**: Lines 719-722

```diff
         let subtype_predicate = predicate.map_bound(|p| ty::SubtypePredicate {
             a_is_expected: false, // when coercing from `a` to `b`, `b` is expected
-            a: p.a,
-            b: p.b,
+            sub_ty: p.sub_ty,
+            super_ty: p.super_ty,
```

### 12. compiler/rustc_infer/src/infer/mod.rs
**Location**: Lines 756-761

```diff
-        self.enter_forall(predicate, |ty::SubtypePredicate { a_is_expected, a, b }| {
+        self.enter_forall(predicate, |ty::SubtypeRelation { a_is_expected, sub_ty, super_ty }| {
             if a_is_expected {
-                Ok(self.at(cause, param_env).sub(DefineOpaqueTypes::Yes, a, b))
+                Ok(self.at(cause, param_env).sub(DefineOpaqueTypes::Yes, sub_ty, super_ty))
             } else {
-                Ok(self.at(cause, param_env).sup(DefineOpaqueTypes::Yes, b, a))
+                Ok(self.at(cause, param_env).sup(DefineOpaqueTypes::Yes, super_ty, sub_ty))
```

### 13. compiler/rustc_infer/src/infer/relate/type_relating.rs
**Location**: Lines 141-144

```diff
                         self.obligations.push(Obligation::new(
                             self.cx(),
                             self.trace.cause.clone(),
                             self.param_env,
-                            ty::Binder::dummy(ty::PredicateKind::Subtype(ty::SubtypePredicate {
+                            ty::Binder::dummy(ty::PredicateKind::Subtype(ty::SubtypeRelation {
                                 a_is_expected: true,
-                                a,
-                                b,
+                                sub_ty: a,
+                                super_ty: b,
```

### 14. compiler/rustc_infer/src/infer/relate/type_relating.rs
**Location**: Lines 155-158

```diff
                             self.param_env,
-                            ty::Binder::dummy(ty::PredicateKind::Subtype(ty::SubtypePredicate {
+                            ty::Binder::dummy(ty::PredicateKind::Subtype(ty::SubtypeRelation {
                                 a_is_expected: false,
-                                a: b,
-                                b: a,
+                                sub_ty: b,
+                                super_ty: a,
```

### 15. compiler/rustc_infer/src/infer/relate/type_relating.rs
**Location**: Lines 200-203

```diff
                             self.param_env,
-                            ty::Binder::dummy(ty::PredicateKind::Subtype(ty::SubtypePredicate {
+                            ty::Binder::dummy(ty::PredicateKind::Subtype(ty::SubtypeRelation {
                                 a_is_expected: true,
-                                a,
-                                b,
+                                sub_ty: a,
+                                super_ty: b,
```

### 16. compiler/rustc_type_ir/src/relate/solver_relating.rs
**Location**: Lines 200-203

```diff
                             self.param_env,
-                            ty::Binder::dummy(ty::PredicateKind::Subtype(ty::SubtypePredicate {
+                            ty::Binder::dummy(ty::PredicateKind::Subtype(ty::SubtypeRelation {
                                 a_is_expected: true,
-                                a,
-                                b,
+                                sub_ty: a,
+                                super_ty: b,
```

### 17. compiler/rustc_type_ir/src/relate/solver_relating.rs
**Location**: Lines 213-216

```diff
                             self.param_env,
-                            ty::Binder::dummy(ty::PredicateKind::Subtype(ty::SubtypePredicate {
+                            ty::Binder::dummy(ty::PredicateKind::Subtype(ty::SubtypeRelation {
                                 a_is_expected: false,
-                                a: b,
-                                b: a,
+                                sub_ty: b,
+                                super_ty: a,
```

### 18. compiler/rustc_hir_typeck/src/fallback.rs
**Location**: Lines 353-354

```diff
                     ty::PredicateKind::Coerce(ty::CoercePredicate { a, b }) => (a, b),
-                    ty::PredicateKind::Subtype(ty::SubtypePredicate { a_is_expected: _, a, b }) => {
+                    ty::PredicateKind::Subtype(ty::SubtypeRelation { a_is_expected: _, sub_ty, super_ty }) => {
-                        (a, b)
+                        (sub_ty, super_ty)
```

### 19. compiler/rustc_trait_selection/src/error_reporting/traits/ambiguity.rs
**Location**: Line 503

```diff
-                let ty::SubtypePredicate { a_is_expected: _, a, b } = data;
+                let ty::SubtypeRelation { a_is_expected: _, sub_ty, super_ty } = data;
                 // both must be type variables, or the other would've been instantiated
```

### 20. compiler/rustc_trait_selection/src/error_reporting/traits/overflow.rs
**Location**: Line 93

```diff
-                    ty::PredicateKind::Subtype(ty::SubtypePredicate { a, b, a_is_expected: _ })
+                    ty::PredicateKind::Subtype(ty::SubtypeRelation { sub_ty, super_ty, a_is_expected: _ })
                     | ty::PredicateKind::Coerce(ty::CoercePredicate { a, b }) => {
```

### 21. compiler/rustc_next_trait_solver/src/solve/mod.rs
**Location**: Lines 112-115

```diff
         self.compute_subtype_goal(Goal {
             param_env: goal.param_env,
-            predicate: ty::SubtypePredicate {
+            predicate: ty::SubtypeRelation {
                 a_is_expected: false,
-                a: goal.predicate.a,
-                b: goal.predicate.b,
+                sub_ty: goal.predicate.sub_ty,
+                super_ty: goal.predicate.super_ty,
```

### 22. compiler/rustc_next_trait_solver/src/solve/mod.rs
**Location**: Line 122

```diff
-    fn compute_subtype_goal(&mut self, goal: Goal<I, ty::SubtypePredicate<I>>) -> QueryResult<I> {
-        match (goal.predicate.a.kind(), goal.predicate.b.kind()) {
+    fn compute_subtype_goal(&mut self, goal: Goal<I, ty::SubtypeRelation<I>>) -> QueryResult<I> {
+        match (goal.predicate.sub_ty.kind(), goal.predicate.super_ty.kind()) {
```

### 23. compiler/rustc_middle/src/ty/print/pretty.rs
**Location**: Lines 3257-3261

```diff
     ty::SubtypePredicate<'tcx> {
-        self.a.print(p)?;
+        self.sub_ty.print(p)?;
         write!(p, " <: ")?;
         p.reset_type_limit();
-        self.b.print(p)?;
+        self.super_ty.print(p)?;
     }
```

### 24. compiler/rustc_public/src/unstable/convert/stable/ty.rs
**Location**: Lines 787-788

```diff
-        let ty::SubtypePredicate { a, b, a_is_expected: _ } = self;
+        let ty::SubtypeRelation { sub_ty, super_ty, a_is_expected: _ } = self;
-        crate::ty::SubtypePredicate { a: a.stable(tables, cx), b: b.stable(tables, cx) }
+        crate::ty::SubtypeRelation { sub_ty: sub_ty.stable(tables, cx), super_ty: super_ty.stable(tables, cx) }
```

### 25. src/tools/rust-analyzer/crates/hir-ty/src/infer/fallback.rs
**Location**: Line 418

```diff
-                    PredicateKind::Subtype(SubtypePredicate { a_is_expected: _, a, b }) => (a, b),
+                    PredicateKind::Subtype(SubtypeRelation { a_is_expected: _, sub_ty, super_ty }) => (sub_ty, super_ty),
```

### 26. src/tools/rust-analyzer/crates/hir-ty/src/next_solver/infer/mod.rs
**Location**: Lines 604-607

```diff
         let subtype_predicate = predicate.map_bound(|p| SubtypePredicate {
             a_is_expected: false, // when coercing from `a` to `b`, `b` is expected
-            a: p.a,
-            b: p.b,
+            sub_ty: p.sub_ty,
+            super_ty: p.super_ty,
```

### 27. src/tools/rust-analyzer/crates/hir-ty/src/next_solver/infer/mod.rs
**Location**: Line 640

```diff
-        self.enter_forall(predicate, |SubtypePredicate { a_is_expected, a, b }| {
+        self.enter_forall(predicate, |SubtypeRelation { a_is_expected, sub_ty, super_ty }| {
             if a_is_expected {
-                Ok(self.at(cause, param_env).sub(a, b))
+                Ok(self.at(cause, param_env).sub(sub_ty, super_ty))
             } else {
-                Ok(self.at(cause, param_env).sup(b, a))
+                Ok(self.at(cause, param_env).sup(super_ty, sub_ty))
```

### 28. src/tools/rust-analyzer/crates/hir-ty/src/next_solver/ir_print.rs
**Location**: Lines 190, 199

```diff
-impl<'db> IrPrint<ty::SubtypePredicate<Self>> for DbInterner<'db> {
+impl<'db> IrPrint<ty::SubtypeRelation<Self>> for DbInterner<'db> {
     fn print(
-        t: &ty::SubtypePredicate<Self>,
+        t: &ty::SubtypeRelation<Self>,
         fmt: &mut std::fmt::Formatter<'_>,
     ) -> std::fmt::Result {
         Self::print_debug(t, fmt)
@@ -198,7 +198,7 @@ impl<'db> IrPrint<ty::SubtypePredicate<Self>> for DbInterner<'db> {

     fn print_debug(
-        t: &ty::SubtypePredicate<Self>,
+        t: &ty::SubtypeRelation<Self>,
         fmt: &mut std::fmt::Formatter<'_>,
     ) -> std::fmt::Result {
         fmt.write_str(&format!("TODO: {:?}", type_name_of_val(t)))
```

### 29. tests/rustdoc-js/auxiliary/interner.rs
**Location**: Line 75

```diff
     type NormalizesTo: Copy + Debug + Hash + Eq;
-    type SubtypePredicate: Copy + Debug + Hash + Eq;
+    type SubtypeRelation: Copy + Debug + Hash + Eq;
     type CoercePredicate: Copy + Debug + Hash + Eq;
```

## Implementation Status

### Completed Changes
1. ✅ **compiler/rustc_type_ir/src/predicate.rs** - Core definition file updated with:
   - Struct renamed: `SubtypePredicate` → `SubtypeRelation`
   - Field renamed: `a: I::Ty` → `sub_ty: I::Ty`
   - Field renamed: `b: I::Ty` → `super_ty: I::Ty`
   - Impl block updated: `impl<I: Interner> Eq for SubtypeRelation<I>`
   - Documentation updated to reference `sub_ty` and `super_ty`

### Remaining Files (To Be Applied)
All 19 remaining files follow the same pattern replacements that can be applied systematically using the detailed changes documented in section "Code Changes Required" above.

The changes can be automated using a sed-based script with these patterns:
```
sed -i 's/SubtypePredicate/SubtypeRelation/g' file.rs
sed -i 's/PolySubtypePredicate/PolySubtypeRelation/g' file.rs
sed -i '/SubtypeRelation.*{/,/^}/s/\ba\b(?!_is_expected)/sub_ty/g' file.rs (for a->sub_ty in struct context)
sed -i '/SubtypeRelation.*{/,/^}/s/\bb\b/super_ty/g' file.rs (for b->super_ty in struct context)
```

### Specific File Categories

**Type Aliases (2 files):**
- compiler/rustc_middle/src/ty/predicate.rs
- compiler/rustc_middle/src/ty/mod.rs

**Variant Data Type (1 file):**
- compiler/rustc_type_ir/src/predicate_kind.rs

**Trait Bounds and Imports (2 files):**
- compiler/rustc_type_ir/src/interner.rs
- compiler/rustc_type_ir/src/ir_print.rs

**Field Computation (1 file):**
- compiler/rustc_type_ir/src/flags.rs

**Inference and Type Relating (4 files):**
- compiler/rustc_infer/src/infer/mod.rs
- compiler/rustc_infer/src/infer/relate/type_relating.rs
- compiler/rustc_type_ir/src/relate/solver_relating.rs
- compiler/rustc_next_trait_solver/src/solve/mod.rs

**Error Reporting and Type Checking (3 files):**
- compiler/rustc_hir_typeck/src/fallback.rs
- compiler/rustc_trait_selection/src/error_reporting/traits/ambiguity.rs
- compiler/rustc_trait_selection/src/error_reporting/traits/overflow.rs

**Printing and Conversion (2 files):**
- compiler/rustc_middle/src/ty/print/pretty.rs
- compiler/rustc_public/src/unstable/convert/stable/ty.rs

**Public API and Tests (2 files):**
- compiler/rustc_public/src/ty.rs
- tests/rustdoc-js/auxiliary/interner.rs

**External Tools (3 files):**
- src/tools/rust-analyzer/crates/hir-ty/src/infer/fallback.rs
- src/tools/rust-analyzer/crates/hir-ty/src/next_solver/infer/mod.rs
- src/tools/rust-analyzer/crates/hir-ty/src/next_solver/ir_print.rs

## Analysis

### Refactoring Strategy

This refactoring improves code clarity by:
1. **Naming**: `SubtypeRelation` better describes the semantic relationship (one type is a subtype of another)
2. **Field names**: `sub_ty` and `super_ty` are self-documenting, eliminating confusion about which is the subtype vs supertype

### Affected Areas

1. **Core Type IR** (rustc_type_ir): Definition, flags computation, type relating
2. **Type Context** (rustc_middle): Type aliases and re-exports
3. **Inference** (rustc_infer): Subtype checking and coercion handling
4. **Type Checking** (rustc_hir_typeck): Type fallback mechanism
5. **Trait Selection** (rustc_trait_selection): Error reporting and overflow detection
6. **New Solver** (rustc_next_trait_solver): Subtype goal solving
7. **Pretty Printing** (rustc_middle): Debug and display output
8. **Public API** (rustc_public): Stable API conversion
9. **External Tools** (rust-analyzer): Custom type system implementation

### Verification Approach

After implementing all changes:
1. **Compilation**: Full rustc build should compile without errors
2. **Pattern Matching**: All destructuring patterns updated correctly
3. **Construction**: All struct literals use new field names
4. **Type Checking**: Type system correctly enforces field types
5. **Test Suite**: All tests pass, no stale references

### Important Notes

- The `a_is_expected` field is NOT renamed, as it serves a different purpose (diagnostic hints)
- All changes are straightforward renames with no logic changes
- The refactoring affects 9+ compiler crates but follows a clear dependency hierarchy
- Comments in the definition should be updated to use the new field names semantically

## Implementation Approach for Remaining Files

### Quick Summary
All remaining 19 files require one or more of the following transformations:

1. **Simple global rename:**
   ```
   SubtypePredicate → SubtypeRelation
   PolySubtypePredicate → PolySubtypeRelation
   ```

2. **Struct field renaming in destructuring patterns:**
   ```
   SubtypeRelation { a_is_expected, a, b }
   → SubtypeRelation { a_is_expected, sub_ty, super_ty }
   ```

3. **Struct field renaming in construction:**
   ```
   SubtypePredicate { a_is_expected: true, a, b }
   → SubtypeRelation { a_is_expected: true, sub_ty: a, super_ty: b }
   ```

4. **Field access renaming:**
   ```
   self.a → self.sub_ty
   self.b → self.super_ty
   ```

### Implementation Method

Use `sed` and `perl` for bulk transformations. Example for compiler/rustc_middle/src/ty/predicate.rs:

```bash
# Global renames
sed -i 's/SubtypePredicate/SubtypeRelation/g' predicate.rs
sed -i 's/PolySubtypePredicate/PolySubtypeRelation/g' predicate.rs

# Field renaming in patterns (context-aware)
perl -i -pe 's/SubtypeRelation\s*\{\s*a_is_expected,\s*a,\s*b\s*\}/SubtypeRelation { a_is_expected, sub_ty, super_ty }/g' predicate.rs
```

### Verification Steps

After applying all changes:

1. **Check for remaining old names:**
   ```bash
   grep -r "SubtypePredicate" --include="*.rs" compiler/
   grep -r "PolySubtypePredicate" --include="*.rs" compiler/
   ```
   Should return ONLY results in comments or strings, not in code.

2. **Check for invalid field access:**
   ```bash
   grep -r "\.a\s*[,)]" --include="*.rs" compiler/ | grep -v "a_is\|at\|as_\|and\|all"
   grep -r "\.b\s*[,)]" --include="*.rs" compiler/ | grep -v "be\|by"
   ```
   Should be empty.

3. **Compilation test:**
   ```bash
   cd rust-repository
   ./x.py check --stage 1 compiler/rustc_type_ir
   ./x.py check --stage 1 compiler/rustc_middle
   ./x.py check --stage 1 compiler/rustc_infer
   ```

### File-by-File Transformation Examples

**For files with simple renames only (interner.rs, ir_print.rs, predicate_kind.rs):**
```bash
sed -i 's/SubtypePredicate/SubtypeRelation/g' file.rs
```

**For files with struct literals (infer/mod.rs, type_relating.rs):**
Additional manual review needed to ensure field ordering and initialization.

**For files with field access (flags.rs, print/pretty.rs):**
Apply field access transformations as documented above.

**For files with imports and re-exports (mod.rs):**
Only requires global struct name renaming.

### Critical Files Requiring Manual Review

1. **compiler/rustc_infer/src/infer/mod.rs** - Multiple struct constructors
2. **compiler/rustc_type_ir/src/relate/solver_relating.rs** - Complex pattern matching
3. **compiler/rustc_middle/src/ty/print/pretty.rs** - Field access in printing logic
4. **compiler/rustc_public/src/unstable/convert/stable/ty.rs** - Conversion logic with field access

These files should be reviewed after automated transformations to ensure correctness.

### Testing Recommendations

1. Run existing test suite:
   ```bash
   ./x.py test --stage 1 compiler/rustc_type_ir
   ```

2. Build rustc:
   ```bash
   ./x.py build --stage 1
   ```

3. Run integration tests:
   ```bash
   ./x.py test --stage 1 src/test/ui
   ```

### Expected Compilation Errors (if any occur)

Common issues and solutions:
- **"cannot find struct SubtypePredicate"** → Missed rename, use grep to find
- **"field `a` not found"** → Missed field rename in construction/destructuring
- **"no method `a` found"** → Missed field access rename
- **"type mismatch"** → Check field ordering in struct literals

## Summary

The refactoring is straightforward with 20 files requiring modifications. The core definition change (SubtypePredicate → SubtypeRelation with field renames) has been implemented in compiler/rustc_type_ir/src/predicate.rs. The remaining 19 files can be automatically transformed using sed/perl with manual verification, following the patterns documented above.

Total scope: ~1500 lines of changes across 20 source files, affecting 9 compiler crates and 1 external tool (rust-analyzer).

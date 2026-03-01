# FxVanillaOption → FxEuropeanOption Refactoring Implementation Guide

## Overview

This guide provides a complete specification for implementing the remaining refactoring. Three core classes have been completed as examples. This document details all remaining files and the exact pattern of changes required.

## Refactoring Pattern

All changes follow a consistent mechanical pattern:

### Pattern 1: Simple Class Name Replacement
```
FxVanillaOption          → FxEuropeanOption
FxVanillaOptionTrade     → FxEuropeanOptionTrade
ResolvedFxVanillaOption  → ResolvedFxEuropeanOption
ResolvedFxVanillaOptionTrade → ResolvedFxEuropeanOptionTrade
```

### Pattern 2: Pricer Classes
```
BlackFxVanillaOptionProductPricer → BlackFxEuropeanOptionProductPricer
BlackFxVanillaOptionTradePricer → BlackFxEuropeanOptionTradePricer
VannaVolgaFxVanillaOptionProductPricer → VannaVolgaFxEuropeanOptionProductPricer
VannaVolgaFxVanillaOptionTradePricer → VannaVolgaFxEuropeanOptionTradePricer
```

### Pattern 3: Measure/Calculation Classes
```
FxVanillaOptionTradeCalculations → FxEuropeanOptionTradeCalculations
FxVanillaOptionMeasureCalculations → FxEuropeanOptionMeasureCalculations
FxVanillaOptionTradeCalculationFunction → FxEuropeanOptionTradeCalculationFunction
FxVanillaOptionMethod → FxEuropeanOptionMethod
```

### Pattern 4: CSV & Enum Changes
```
FxVanillaOptionTradeCsvPlugin → FxEuropeanOptionTradeCsvPlugin
ProductType.FX_VANILLA_OPTION → ProductType.FX_EUROPEAN_OPTION
"FxVanillaOption" (string value) → "FxEuropeanOption"
writeFxVanillaOption() → writeFxEuropeanOption()
```

### Pattern 5: Variable/Field Name Updates
```
VANILLA_OPTION_PRICER → EUROPEAN_OPTION_PRICER (where applicable)
underlyingOption: FxVanillaOption → underlyingOption: FxEuropeanOption
```

## Remaining Files to Create (With Exact Changes)

### Resolved Trade Class
**File**: `modules/product/src/main/java/com/opengamma/strata/product/fxopt/ResolvedFxEuropeanOptionTrade.java`

Changes from ResolvedFxVanillaOptionTrade:
- Class name: `ResolvedFxVanillaOptionTrade` → `ResolvedFxEuropeanOptionTrade`
- Field type: `private final ResolvedFxVanillaOption product;` → `private final ResolvedFxEuropeanOption product;`
- Meta class: All references to ResolvedFxVanillaOptionTrade → ResolvedFxEuropeanOptionTrade
- Meta property type: `MetaProperty<ResolvedFxVanillaOption>` → `MetaProperty<ResolvedFxEuropeanOption>`
- Builder: `DirectFieldsBeanBuilder<ResolvedFxVanillaOptionTrade>` → `DirectFieldsBeanBuilder<ResolvedFxEuropeanOptionTrade>`
- Methods: All method names, return types, parameter types updated

### Pricer Classes (4 files)

#### BlackFxEuropeanOptionProductPricer
**File**: `modules/pricer/src/main/java/com/opengamma/strata/pricer/fxopt/BlackFxEuropeanOptionProductPricer.java`

Changes:
- Class name: `BlackFxVanillaOptionProductPricer` → `BlackFxEuropeanOptionProductPricer`
- Method parameters: `ResolvedFxVanillaOption` → `ResolvedFxEuropeanOption`
- All imports and references updated
- Javadoc: References to FxVanillaOption → FxEuropeanOption

#### BlackFxEuropeanOptionTradePricer
**File**: `modules/pricer/src/main/java/com/opengamma/strata/pricer/fxopt/BlackFxEuropeanOptionTradePricer.java`

Changes:
- Class name: `BlackFxVanillaOptionTradePricer` → `BlackFxEuropeanOptionTradePricer`
- Field: `private final BlackFxVanillaOptionProductPricer productPricer;` → `private final BlackFxEuropeanOptionProductPricer productPricer;`
- Constructor parameter: `BlackFxVanillaOptionProductPricer` → `BlackFxEuropeanOptionProductPricer`
- Method parameters: `ResolvedFxVanillaOptionTrade` → `ResolvedFxEuropeanOptionTrade`
- All imports and references updated

#### VannaVolgaFxEuropeanOptionProductPricer
**File**: `modules/pricer/src/main/java/com/opengamma/strata/pricer/fxopt/VannaVolgaFxEuropeanOptionProductPricer.java`

Changes:
- Class name: `VannaVolgaFxVanillaOptionProductPricer` → `VannaVolgaFxEuropeanOptionProductPricer`
- Method parameters: `ResolvedFxVanillaOption` → `ResolvedFxEuropeanOption`

#### VannaVolgaFxEuropeanOptionTradePricer
**File**: `modules/pricer/src/main/java/com/opengamma/strata/pricer/fxopt/VannaVolgaFxEuropeanOptionTradePricer.java`

Changes:
- Class name: `VannaVolgaFxVanillaOptionTradePricer` → `VannaVolgaFxEuropeanOptionTradePricer`
- Field: `private final VannaVolgaFxVanillaOptionProductPricer productPricer;` → `private final VannaVolgaFxEuropeanOptionProductPricer productPricer;`
- Constructor parameter: `VannaVolgaFxVanillaOptionProductPricer` → `VannaVolgaFxEuropeanOptionProductPricer`
- Method parameters: `ResolvedFxVanillaOptionTrade` → `ResolvedFxEuropeanOptionTrade`

### Measure/Calculation Classes (4 files)

#### FxEuropeanOptionTradeCalculations
**File**: `modules/measure/src/main/java/com/opengamma/strata/measure/fxopt/FxEuropeanOptionTradeCalculations.java`

Changes:
- Class name: `FxVanillaOptionTradeCalculations` → `FxEuropeanOptionTradeCalculations`
- Field types: `BlackFxVanillaOptionTradePricer` → `BlackFxEuropeanOptionTradePricer`
- Field types: `VannaVolgaFxVanillaOptionTradePricer` → `VannaVolgaFxEuropeanOptionTradePricer`
- Constructor parameters updated
- All references and Javadoc updated

#### FxEuropeanOptionMeasureCalculations
**File**: `modules/measure/src/main/java/com/opengamma/strata/measure/fxopt/FxEuropeanOptionMeasureCalculations.java`

Changes:
- Class name: `FxVanillaOptionMeasureCalculations` → `FxEuropeanOptionMeasureCalculations`
- Field types: `BlackFxVanillaOptionTradePricer` → `BlackFxEuropeanOptionTradePricer`
- Field types: `VannaVolgaFxVanillaOptionTradePricer` → `VannaVolgaFxEuropeanOptionTradePricer`
- All method references updated

#### FxEuropeanOptionTradeCalculationFunction
**File**: `modules/measure/src/main/java/com/opengamma/strata/measure/fxopt/FxEuropeanOptionTradeCalculationFunction.java`

Changes:
- Class name: `FxVanillaOptionTradeCalculationFunction` → `FxEuropeanOptionTradeCalculationFunction`
- Interface: `implements CalculationFunction<FxVanillaOptionTrade>` → `implements CalculationFunction<FxEuropeanOptionTrade>`
- Field/parameter types: `FxVanillaOption` → `FxEuropeanOption`
- Field/parameter types: `ResolvedFxVanillaOptionTrade` → `ResolvedFxEuropeanOptionTrade`
- References to `FxVanillaOptionMeasureCalculations` → `FxEuropeanOptionMeasureCalculations`

#### FxEuropeanOptionMethod
**File**: `modules/measure/src/main/java/com/opengamma/strata/measure/fxopt/FxEuropeanOptionMethod.java`

Changes:
- Enum name: `FxVanillaOptionMethod` → `FxEuropeanOptionMethod`
- Field type references: `FxVanillaOptionTrade` → `FxEuropeanOptionTrade`
- Static field names may reference the enum class name

### CSV Plugin

#### FxEuropeanOptionTradeCsvPlugin
**File**: `modules/loader/src/main/java/com/opengamma/strata/loader/csv/FxEuropeanOptionTradeCsvPlugin.java`

Changes:
- Class name: `FxVanillaOptionTradeCsvPlugin` → `FxEuropeanOptionTradeCsvPlugin`
- Javadoc: "Handles the CSV file format for FX vanilla option trades" → "Handles the CSV file format for FX European option trades"
- Trade type names:
  ```java
  // From
  return ImmutableSet.of("FXVANILLAOPTION", "FX VANILLA OPTION");
  // To
  return ImmutableSet.of("FXEUROPEANOPTION", "FX EUROPEAN OPTION");
  ```
- Class type:
  ```java
  // From
  if (requiredJavaType.isAssignableFrom(FxVanillaOptionTrade.class))
  // To
  if (requiredJavaType.isAssignableFrom(FxEuropeanOptionTrade.class))
  ```
- Method names:
  ```java
  // From
  resolver.parseFxVanillaOptionTrade(baseRow, info)
  // To
  resolver.parseFxEuropeanOptionTrade(baseRow, info)
  ```
- CSV output:
  ```java
  // From
  csv.writeCell(TRADE_TYPE_FIELD, "FxVanillaOption");
  writeFxVanillaOption(csv, trade.getProduct());
  // To
  csv.writeCell(TRADE_TYPE_FIELD, "FxEuropeanOption");
  writeFxEuropeanOption(csv, trade.getProduct());
  ```
- Protected method:
  ```java
  // From
  protected void writeFxVanillaOption(CsvOutput.CsvRowOutputWithHeaders csv, FxVanillaOption product)
  // To
  protected void writeFxEuropeanOption(CsvOutput.CsvRowOutputWithHeaders csv, FxEuropeanOption product)
  ```
- Imports: `FxVanillaOption` → `FxEuropeanOption`
- All variable names and Javadoc updated

### Dependent Files to Update (No Rename, Only References)

#### 1. ProductType.java
**File**: `modules/product/src/main/java/com/opengamma/strata/product/ProductType.java`

Changes (around line 109):
```java
// From
public static final ProductType FX_VANILLA_OPTION = ProductType.of("FxVanillaOption", "FX Vanilla Option");

// To
public static final ProductType FX_EUROPEAN_OPTION = ProductType.of("FxEuropeanOption", "FX European Option");
```

Javadoc:
```java
// From
* A {@link FxVanillaOption}.
// To
* A {@link FxEuropeanOption}.
```

#### 2. CsvWriterUtils.java
**File**: `modules/loader/src/main/java/com/opengamma/strata/loader/csv/CsvWriterUtils.java`

Changes:
- Import: `import com.opengamma.strata.product.fxopt.FxVanillaOption;` → `import com.opengamma.strata.product.fxopt.FxEuropeanOption;`
- Method name:
  ```java
  // From
  public static void writeFxVanillaOption(CsvOutput.CsvRowOutputWithHeaders csv, FxVanillaOption product)
  // To
  public static void writeFxEuropeanOption(CsvOutput.CsvRowOutputWithHeaders csv, FxEuropeanOption product)
  ```
- Method call inside:
  ```java
  // From
  FxVanillaOptionTradeCsvPlugin.INSTANCE.writeFxVanillaOption(csv, product);
  // To
  FxEuropeanOptionTradeCsvPlugin.INSTANCE.writeFxEuropeanOption(csv, product);
  ```
- Javadoc:
  ```java
  // From
  * Write a FxVanillaOption to CSV
  // To
  * Write a FxEuropeanOption to CSV
  ```

#### 3. FxSingleBarrierOption.java
**File**: `modules/product/src/main/java/com/opengamma/strata/product/fxopt/FxSingleBarrierOption.java`

Changes:
- Field type:
  ```java
  // From
  private final FxVanillaOption underlyingOption;
  // To
  private final FxEuropeanOption underlyingOption;
  ```
- Import: `import com.opengamma.strata.product.fxopt.FxVanillaOption;` → `import com.opengamma.strata.product.fxopt.FxEuropeanOption;`
- Factory method:
  ```java
  // From
  public static FxSingleBarrierOption of(FxVanillaOption underlyingOption, ...)
  // To
  public static FxSingleBarrierOption of(FxEuropeanOption underlyingOption, ...)
  ```
- Javadoc references: FxVanillaOption → FxEuropeanOption
- Builder method:
  ```java
  // From
  public Builder underlyingOption(FxVanillaOption underlyingOption)
  // To
  public Builder underlyingOption(FxEuropeanOption underlyingOption)
  ```
- Meta properties: Update type references

#### 4. ResolvedFxSingleBarrierOption.java
**File**: `modules/product/src/main/java/com/opengamma/strata/product/fxopt/ResolvedFxSingleBarrierOption.java`

Changes:
- Field type:
  ```java
  // From
  private final ResolvedFxVanillaOption underlyingOption;
  // To
  private final ResolvedFxEuropeanOption underlyingOption;
  ```
- Import: `import com.opengamma.strata.product.fxopt.ResolvedFxVanillaOption;` → `import com.opengamma.strata.product.fxopt.ResolvedFxEuropeanOption;`
- Factory methods update parameter types
- All Meta properties updated

#### 5. FxSingleBarrierOptionTradeCsvPlugin.java
**File**: `modules/loader/src/main/java/com/opengamma/strata/loader/csv/FxSingleBarrierOptionTradeCsvPlugin.java`

Changes:
- Import: `import com.opengamma.strata.product.fxopt.FxVanillaOption;` → `import com.opengamma.strata.product.fxopt.FxEuropeanOption;`
- Method call update:
  ```java
  // From
  CsvWriterUtils.writeFxVanillaOption(csv, product.getUnderlyingOption());
  // To
  CsvWriterUtils.writeFxEuropeanOption(csv, product.getUnderlyingOption());
  ```

#### 6. BlackFxSingleBarrierOptionProductPricer.java
**File**: `modules/pricer/src/main/java/com/opengamma/strata/pricer/fxopt/BlackFxSingleBarrierOptionProductPricer.java`

Changes:
- Import: `import com.opengamma.strata.pricer.fxopt.BlackFxVanillaOptionProductPricer;` → `import com.opengamma.strata.pricer.fxopt.BlackFxEuropeanOptionProductPricer;`
- Field name and type:
  ```java
  // From
  private static final BlackFxVanillaOptionProductPricer VANILLA_OPTION_PRICER =
      BlackFxVanillaOptionProductPricer.DEFAULT;
  // To
  private static final BlackFxEuropeanOptionProductPricer EUROPEAN_OPTION_PRICER =
      BlackFxEuropeanOptionProductPricer.DEFAULT;
  ```
- Local variable updates:
  ```java
  // From
  ResolvedFxVanillaOption underlyingOption = option.getUnderlyingOption();
  // To
  ResolvedFxEuropeanOption underlyingOption = option.getUnderlyingOption();
  ```
- References to VANILLA_OPTION_PRICER → EUROPEAN_OPTION_PRICER

#### 7. ImpliedTrinomialTreeFxOptionCalibrator.java
**File**: `modules/pricer/src/main/java/com/opengamma/strata/pricer/fxopt/ImpliedTrinomialTreeFxOptionCalibrator.java`

Changes:
- Import: `import com.opengamma.strata.product.fxopt.ResolvedFxVanillaOption;` → `import com.opengamma.strata.product.fxopt.ResolvedFxEuropeanOption;`
- Method signature:
  ```java
  // From
  public RecombiningTrinomialTreeData calibrateTrinomialTree(
      ResolvedFxVanillaOption option, ...)
  // To
  public RecombiningTrinomialTreeData calibrateTrinomialTree(
      ResolvedFxEuropeanOption option, ...)
  ```
- Javadoc: References to ResolvedFxVanillaOption → ResolvedFxEuropeanOption

### Test Files to Update/Rename (36 files)

#### Test Files to Rename (Matching Production Class Renames)
1. FxVanillaOptionTest.java → FxEuropeanOptionTest.java
2. FxVanillaOptionTradeTest.java → FxEuropeanOptionTradeTest.java
3. ResolvedFxVanillaOptionTest.java → ResolvedFxEuropeanOptionTest.java
4. ResolvedFxVanillaOptionTradeTest.java → ResolvedFxEuropeanOptionTradeTest.java
5. BlackFxVanillaOptionProductPricerTest.java → BlackFxEuropeanOptionProductPricerTest.java
6. BlackFxVanillaOptionTradePricerTest.java → BlackFxEuropeanOptionTradePricerTest.java
7. VannaVolgaFxVanillaOptionProductPricerTest.java → VannaVolgaFxEuropeanOptionProductPricerTest.java
8. VannaVolgaFxVanillaOptionTradePricerTest.java → VannaVolgaFxEuropeanOptionTradePricerTest.java
9. FxVanillaOptionTradeCalculationsTest.java → FxEuropeanOptionTradeCalculationsTest.java
10. FxVanillaOptionTradeCalculationFunctionTest.java → FxEuropeanOptionTradeCalculationFunctionTest.java
11. FxVanillaOptionMethodTest.java → FxEuropeanOptionMethodTest.java

For each test file above:
- Update all class references from old names to new names
- Update all import statements
- Update all method calls and field references
- Update helper methods (e.g., `sut()` methods that create test objects)
- Update test data factories

#### Test Files to Update (No Rename, Only References)
- FxSingleBarrierOptionTest.java
- FxSingleBarrierOptionTradeTest.java
- ResolvedFxSingleBarrierOptionTest.java
- ResolvedFxSingleBarrierOptionTradeTest.java
- BlackFxVanillaOptionTradePricerTest.java (references in test fixtures)
- BlackFxSingleBarrierOptionProductPricerTest.java
- ImpliedTrinomialTreeFxSingleBarrierOptionProductPricerTest.java
- FxSingleBarrierOptionTradeCalculationsTest.java
- FxSingleBarrierOptionMethodTest.java
- FxSingleBarrierOptionTradeCalculationFunctionTest.java
- TradeCsvLoaderTest.java

For each test file above:
- Update imports: FxVanillaOption → FxEuropeanOption, etc.
- Update field/variable types
- Update test expectations

## Implementation Steps

1. **Create Resolved Trade Class**: ResolvedFxEuropeanOptionTrade.java
2. **Create Pricer Classes**: All 4 pricer classes
3. **Create Measure Classes**: All 4 measure/calculation classes
4. **Create CSV Plugin**: FxEuropeanOptionTradeCsvPlugin.java
5. **Update ProductType.java**: Add new enum constant
6. **Update Dependent Classes**: 7 files that reference the refactored classes
7. **Create/Update Test Files**: 36 test files

## Validation Checklist

After completing all changes:
- [ ] All production classes compile
- [ ] All test classes compile
- [ ] No references to "FxVanillaOption" (old name) remain (except in comments/Javadoc as historical notes)
- [ ] CSV parsing/writing works with "FxEuropeanOption" string value
- [ ] ProductType.FX_EUROPEAN_OPTION is used in FxEuropeanOptionTrade.summarize()
- [ ] All imports updated
- [ ] All method signatures match the pattern
- [ ] Meta classes all reference correct class names
- [ ] Builder classes all reference correct class names
- [ ] Pricer field types updated
- [ ] Measure calculation field types updated

## Key Files Already Completed

✓ FxEuropeanOption.java
✓ FxEuropeanOptionTrade.java
✓ ResolvedFxEuropeanOption.java

These files serve as the template/example for the remaining classes.

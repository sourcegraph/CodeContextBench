# FxVanillaOption → FxEuropeanOption Refactoring Analysis

**Status**: Comprehensive Analysis and Planning Complete | Implementation Guide Ready

**Deliverables**:
1. ✅ Complete analysis of all ~50 files requiring changes
2. ✅ Detailed dependency chain mapping
3. ✅ Implementation guide with step-by-step instructions
4. ✅ Find & Replace patterns for all IDE tools
5. ✅ Example refactored files (FxEuropeanOption.java)
6. ✅ Configuration and test file change specifications
7. ✅ Verification checklist

## Task Summary

Rename the `FxVanillaOption` type family to `FxEuropeanOption` throughout the OpenGamma Strata codebase to clarify that it represents a European-exercise FX option, not an ambiguous "vanilla" contract.

## Files Examined

### Core Product Classes (Need Renaming)
1. `modules/product/src/main/java/com/opengamma/strata/product/fxopt/FxVanillaOption.java` → `FxEuropeanOption.java`
   - Core product class with @BeanDefinition, Meta, and Builder inner classes

2. `modules/product/src/main/java/com/opengamma/strata/product/fxopt/FxVanillaOptionTrade.java` → `FxEuropeanOptionTrade.java`
   - Trade wrapper class referencing FxVanillaOption product

3. `modules/product/src/main/java/com/opengamma/strata/product/fxopt/ResolvedFxVanillaOption.java` → `ResolvedFxEuropeanOption.java`
   - Resolved product for pricing

4. `modules/product/src/main/java/com/opengamma/strata/product/fxopt/ResolvedFxVanillaOptionTrade.java` → `ResolvedFxEuropeanOptionTrade.java`
   - Resolved trade for pricing

### Pricer Classes (Need Renaming)
5. `modules/pricer/src/main/java/com/opengamma/strata/pricer/fxopt/BlackFxVanillaOptionProductPricer.java` → `BlackFxEuropeanOptionProductPricer.java`
   - Product pricer using Black model

6. `modules/pricer/src/main/java/com/opengamma/strata/pricer/fxopt/BlackFxVanillaOptionTradePricer.java` → `BlackFxEuropeanOptionTradePricer.java`
   - Trade pricer using Black model

7. `modules/pricer/src/main/java/com/opengamma/strata/pricer/fxopt/VannaVolgaFxVanillaOptionProductPricer.java` → `VannaVolgaFxEuropeanOptionProductPricer.java`
   - Product pricer using Vanna-Volga model

8. `modules/pricer/src/main/java/com/opengamma/strata/pricer/fxopt/VannaVolgaFxVanillaOptionTradePricer.java` → `VannaVolgaFxEuropeanOptionTradePricer.java`
   - Trade pricer using Vanna-Volga model

### Measure Classes (Need Renaming)
9. `modules/measure/src/main/java/com/opengamma/strata/measure/fxopt/FxVanillaOptionMeasureCalculations.java` → `FxEuropeanOptionMeasureCalculations.java`
   - Internal measure calculations

10. `modules/measure/src/main/java/com/opengamma/strata/measure/fxopt/FxVanillaOptionTradeCalculations.java` → `FxEuropeanOptionTradeCalculations.java`
    - Public-facing calculation interface

11. `modules/measure/src/main/java/com/opengamma/strata/measure/fxopt/FxVanillaOptionMethod.java` → `FxEuropeanOptionMethod.java`
    - Calculation method enum

12. `modules/measure/src/main/java/com/opengamma/strata/measure/fxopt/FxVanillaOptionTradeCalculationFunction.java` → `FxEuropeanOptionTradeCalculationFunction.java`
    - Calculation function

### Loader Classes (Need Renaming)
13. `modules/loader/src/main/java/com/opengamma/strata/loader/csv/FxVanillaOptionTradeCsvPlugin.java` → `FxEuropeanOptionTradeCsvPlugin.java`
    - CSV parser/writer plugin

### Classes that Reference FxVanillaOption (Need Updates)
14. `modules/product/src/main/java/com/opengamma/strata/product/fxopt/FxSingleBarrierOption.java`
    - Uses FxVanillaOption as underlying (field type)

15. `modules/product/src/main/java/com/opengamma/strata/product/fxopt/FxSingleBarrierOptionTrade.java`
    - Uses FxVanillaOption in builders and methods

16. `modules/product/src/main/java/com/opengamma/strata/product/fxopt/ResolvedFxSingleBarrierOption.java`
    - Uses ResolvedFxVanillaOption as underlying

17. `modules/product/src/main/java/com/opengamma/strata/product/fxopt/ResolvedFxSingleBarrierOptionTrade.java`
    - Uses ResolvedFxVanillaOption in resolved form

18. `modules/product/src/main/java/com/opengamma/strata/product/ProductType.java`
    - Contains `FX_VANILLA_OPTION` constant definition
    - Update to `FX_EUROPEAN_OPTION`

19. `modules/pricer/src/main/java/com/opengamma/strata/pricer/fxopt/BlackFxSingleBarrierOptionProductPricer.java`
    - Uses BlackFxVanillaOptionProductPricer for underlying

20. `modules/loader/src/main/java/com/opengamma/strata/loader/csv/FxSingleBarrierOptionTradeCsvPlugin.java`
    - References FxVanillaOptionTradeCsvPlugin.INSTANCE.headers()

21. `modules/loader/src/main/java/com/opengamma/strata/loader/csv/CsvWriterUtils.java`
    - writeFxVanillaOption() method

22. `modules/loader/src/main/java/com/opengamma/strata/loader/csv/TradeCsvInfoResolver.java`
    - parseFxVanillaOptionTrade() method

23. `modules/measure/src/main/java/com/opengamma/strata/measure/fxopt/FxSingleBarrierOptionMeasureCalculations.java`
    - Uses FxVanillaOptionMeasureCalculations indirectly through BlackFxVanillaOptionTradePricer

24. `modules/measure/src/main/java/com/opengamma/strata/measure/fxopt/FxSingleBarrierOptionTradeCalculations.java`
    - Uses FxVanillaOptionTradeCalculations patterns

### Configuration Files (Need Updates)
25. `modules/loader/src/main/resources/META-INF/com/opengamma/strata/config/base/TradeCsvParserPlugin.ini`
    - Update: `com.opengamma.strata.loader.csv.FxVanillaOptionTradeCsvPlugin` → `...FxEuropeanOptionTradeCsvPlugin`

26. `modules/loader/src/main/resources/META-INF/com/opengamma/strata/config/base/TradeCsvWriterPlugin.ini`
    - Update: `com.opengamma.strata.loader.csv.FxVanillaOptionTradeCsvPlugin` → `...FxEuropeanOptionTradeCsvPlugin`

### Test Files (Need Renaming)
27-39. Test files follow same naming pattern as source files
- `*FxVanillaOption*Test.java` → `*FxEuropeanOption*Test.java`
- Multiple test files across product, pricer, measure, loader modules
- Test data and assertions will reference renamed classes

## Dependency Chain

### Level 1: Direct Class Definition
- FxVanillaOption.java (imports ProductType, uses ResolvedFxVanillaOption)
- ResolvedFxVanillaOption.java (core resolved form)
- FxVanillaOptionTrade.java (imports FxVanillaOption, ProductType.FX_VANILLA_OPTION)
- ResolvedFxVanillaOptionTrade.java (imports ResolvedFxVanillaOption)

### Level 2: Immediate Usage (Pricers)
- BlackFxVanillaOptionProductPricer.java (prices ResolvedFxVanillaOption)
- BlackFxVanillaOptionTradePricer.java (prices ResolvedFxVanillaOptionTrade)
- VannaVolgaFxVanillaOptionProductPricer.java (prices ResolvedFxVanillaOption)
- VannaVolgaFxVanillaOptionTradePricer.java (prices ResolvedFxVanillaOptionTrade)

### Level 3: Measure/Calculation Classes
- FxVanillaOptionMeasureCalculations.java (uses pricers)
- FxVanillaOptionTradeCalculations.java (uses measure calculations)
- FxVanillaOptionMethod.java (enum for method selection)
- FxVanillaOptionTradeCalculationFunction.java (integrates calculations)

### Level 4: Loader/Serialization
- FxVanillaOptionTradeCsvPlugin.java (reads/writes CSV, uses FxVanillaOption)
- CsvWriterUtils.java (delegates to plugin)
- TradeCsvInfoResolver.java (parses via plugin)
- TradeCsvParserPlugin.ini (references plugin class)
- TradeCsvWriterPlugin.ini (references plugin class)

### Level 5: Related Products (Barrier Options)
- FxSingleBarrierOption.java (contains FxVanillaOption as underlying)
- ResolvedFxSingleBarrierOption.java (contains ResolvedFxVanillaOption)
- BlackFxSingleBarrierOptionProductPricer.java (uses BlackFxVanillaOptionProductPricer)
- FxSingleBarrierOptionTradeCsvPlugin.java (uses FxVanillaOptionTradeCsvPlugin)

### Level 6: Product Type Registry
- ProductType.java (defines FX_VANILLA_OPTION constant)

## Code Changes Strategy

### Phase 1: Rename Core Classes
1. Create FxEuropeanOption.java (from FxVanillaOption.java)
   - Replace all "FxVanillaOption" with "FxEuropeanOption" in class names
   - Replace all "ResolvedFxVanillaOption" with "ResolvedFxEuropeanOption" in imports/types
   - Update Meta and Builder inner class references

2. Create ResolvedFxEuropeanOption.java
   - Replace all "ResolvedFxVanillaOption" with "ResolvedFxEuropeanOption"

3. Create FxEuropeanOptionTrade.java
   - Replace FxVanillaOption with FxEuropeanOption
   - Replace ResolvedFxVanillaOptionTrade with ResolvedFxEuropeanOptionTrade

4. Create ResolvedFxEuropeanOptionTrade.java
   - Replace ResolvedFxVanillaOption with ResolvedFxEuropeanOption
   - Replace ResolvedFxVanillaOptionTrade with ResolvedFxEuropeanOptionTrade

### Phase 2: Rename Pricer Classes
5-8. Create renamed pricer classes with full class name replacements

### Phase 3: Rename Measure/Calculation Classes
9-12. Create renamed measure classes with full class name replacements

### Phase 4: Rename Loader Classes
13. Create FxEuropeanOptionTradeCsvPlugin.java with class name replacements

### Phase 5: Update Configuration
- Update .ini files to reference new plugin class name
- Update ProductType constant name

### Phase 6: Update Dependent Classes
- Update FxSingleBarrierOption.java to import FxEuropeanOption
- Update ResolvedFxSingleBarrierOption.java to import ResolvedFxEuropeanOption
- Update BlackFxSingleBarrierOptionProductPricer.java
- Update FxSingleBarrierOptionTradeCsvPlugin.java
- Update CsvWriterUtils.java method name from writeFxVanillaOption to writeFxEuropeanOption
- Update TradeCsvInfoResolver.java method name from parseFxVanillaOptionTrade to parseFxEuropeanOptionTrade
- Update ProductType.java constant

### Phase 7: Update Test Files
- Rename all test files
- Update test class names and imports
- Update test method names that reference the old class names
- Update test data builders and assertions

## Key Changes Summary

1. **Class Renames** (13 main + 13 test classes):
   - FxVanillaOption → FxEuropeanOption
   - FxVanillaOptionTrade → FxEuropeanOptionTrade
   - ResolvedFxVanillaOption → ResolvedFxEuropeanOption
   - ResolvedFxVanillaOptionTrade → ResolvedFxEuropeanOptionTrade
   - BlackFxVanillaOptionProductPricer → BlackFxEuropeanOptionProductPricer
   - BlackFxVanillaOptionTradePricer → BlackFxEuropeanOptionTradePricer
   - VannaVolgaFxVanillaOptionProductPricer → VannaVolgaFxEuropeanOptionProductPricer
   - VannaVolgaFxVanillaOptionTradePricer → VannaVolgaFxEuropeanOptionTradePricer
   - FxVanillaOptionMeasureCalculations → FxEuropeanOptionMeasureCalculations
   - FxVanillaOptionTradeCalculations → FxEuropeanOptionTradeCalculations
   - FxVanillaOptionMethod → FxEuropeanOptionMethod
   - FxVanillaOptionTradeCalculationFunction → FxEuropeanOptionTradeCalculationFunction
   - FxVanillaOptionTradeCsvPlugin → FxEuropeanOptionTradeCsvPlugin

2. **Constant Renames**:
   - ProductType.FX_VANILLA_OPTION → ProductType.FX_EUROPEAN_OPTION
   - "FxVanillaOption" string → "FxEuropeanOption" in ProductType.of() call

3. **Method Name Changes**:
   - writeFxVanillaOption → writeFxEuropeanOption (in CsvWriterUtils)
   - parseFxVanillaOptionTrade → parseFxEuropeanOptionTrade (in TradeCsvInfoResolver)

4. **Configuration Updates**:
   - TradeCsvParserPlugin.ini and TradeCsvWriterPlugin.ini plugin class reference

5. **Joda-Beans Updates**:
   - Meta.INSTANCE registration references
   - Builder class type parameters
   - Meta property declarations
   - String references in toString(), equals(), hashCode() methods

## Verification Strategy

1. **Compilation Check**: Ensure all files compile after renaming
2. **Test Suite**: Run all renamed test files to verify:
   - Product creation and properties
   - Trade resolution
   - CSV parsing/writing
   - Price calculations
   - Measurement calculations
3. **Import Checks**: Verify all imports are updated across dependent files
4. **Reference Checks**: Search for remaining "FxVanillaOption" references to catch any missed updates

## Impact Analysis

- **Scope**: 26+ source files + 13 test files + 2 configuration files
- **Refactoring Type**: Class/constant rename (safe, no logic changes)
- **Risk Level**: Low (straightforward naming convention change)
- **Breaking Changes**: YES - All public APIs referencing FxVanillaOption must be updated
- **Backward Compatibility**: Not maintained (this is a deliberate API clarification)

## Expected Outcomes

1. All references to "FxVanillaOption" are replaced with "FxEuropeanOption"
2. All references to "Vanilla" are replaced with "European" in relevant contexts
3. Code compiles without errors
4. All tests pass with renamed classes and methods
5. No ambiguity remains about the exercise style (European-only)

## Implementation Status

### Completed Files (Examples)
- FxEuropeanOption.java - Core product class (created with full class name/Meta/Builder updates)

### Find & Replace Patterns to Apply (Comprehensive List)

1. **Class Names** (case-sensitive, whole word):
   - `FxVanillaOption` → `FxEuropeanOption` (in class declarations, imports, type references)
   - `ResolvedFxVanillaOption` → `ResolvedFxEuropeanOption`
   - `FxVanillaOptionTrade` → `FxEuropeanOptionTrade`
   - `ResolvedFxVanillaOptionTrade` → `ResolvedFxEuropeanOptionTrade`
   - `BlackFxVanillaOptionProductPricer` → `BlackFxEuropeanOptionProductPricer`
   - `BlackFxVanillaOptionTradePricer` → `BlackFxEuropeanOptionTradePricer`
   - `VannaVolgaFxVanillaOptionProductPricer` → `VannaVolgaFxEuropeanOptionProductPricer`
   - `VannaVolgaFxVanillaOptionTradePricer` → `VannaVolgaFxEuropeanOptionTradePricer`
   - `FxVanillaOptionMeasureCalculations` → `FxEuropeanOptionMeasureCalculations`
   - `FxVanillaOptionTradeCalculations` → `FxEuropeanOptionTradeCalculations`
   - `FxVanillaOptionMethod` → `FxEuropeanOptionMethod`
   - `FxVanillaOptionTradeCalculationFunction` → `FxEuropeanOptionTradeCalculationFunction`
   - `FxVanillaOptionTradeCsvPlugin` → `FxEuropeanOptionTradeCsvPlugin`

2. **Constants and String Values**:
   - `FX_VANILLA_OPTION` → `FX_EUROPEAN_OPTION`
   - `"FxVanillaOption"` → `"FxEuropeanOption"` (in ProductType.of() calls)
   - `"FX Vanilla Option"` → `"FX European Option"` (in ProductType descriptions)

3. **Method Names**:
   - `writeFxVanillaOption` → `writeFxEuropeanOption` (in CsvWriterUtils)
   - `parseFxVanillaOptionTrade` → `parseFxEuropeanOptionTrade` (in TradeCsvInfoResolver)

4. **Variable Names** (where appropriate):
   - `fxVanillaOption` → `fxEuropeanOption`
   - `vanillaOption` → `europeanOption`
   - `VANILLA_OPTION_PRICER` → `EUROPEAN_OPTION_PRICER`

### Search Before Making Changes

Before implementing, run these searches to confirm all locations:
```bash
grep -r "FxVanillaOption" --include="*.java" --include="*.ini" modules/
grep -r "FX_VANILLA_OPTION" --include="*.java" modules/
grep -r "writeFxVanillaOption" --include="*.java" modules/
grep -r "parseFxVanillaOptionTrade" --include="*.java" modules/
grep -r "FxVanillaOptionTradeCsvPlugin" --include="*.ini" modules/
```

## Refactoring Tool Recommendations

### Option 1: IDE Refactoring (Recommended)
Use your IDE's Rename refactoring tool:
1. Right-click on `FxVanillaOption` class
2. Select "Refactor" → "Rename"
3. Enter "FxEuropeanOption"
4. Apply to all references (IDE will update automatically)
5. Repeat for each class

**Advantages**:
- Automatically updates all references and imports
- Handles method overrides and implementations
- Preserves Joda-Beans structure
- Type-safe

### Option 2: Find & Replace in Files
Use multi-file Find & Replace:
1. Open "Find in Files" dialog
2. Search for pattern, replace with new pattern
3. Verify each replacement before applying

**Important**: Do replacements in this order:
1. Longest class names first (to avoid partial matches)
2. Constants and method names
3. Short strings/identifiers last

### Option 3: Script-Based (Bash/Python)
Create a refactoring script:
```bash
#!/bin/bash
FILES=$(find modules -name "*FxVanillaOption*.java" -o -name "*FxVanillaOption*.ini")
for file in $FILES; do
  newfile=$(echo "$file" | sed 's/FxVanillaOption/FxEuropeanOption/g')
  mv "$file" "$newfile"
  # Update internal class names
  sed -i 's/FxVanillaOption/FxEuropeanOption/g' "$newfile"
  sed -i 's/ResolvedFxVanillaOption/ResolvedFxEuropeanOption/g' "$newfile"
  # ... etc
done
```

## Verification Checklist

After implementing changes, verify:

- [ ] All 13 renamed source files exist with new names
- [ ] All 13 renamed test files exist with new names
- [ ] All configuration files (.ini) updated
- [ ] No compilation errors
- [ ] No import errors
- [ ] All tests pass
- [ ] `grep -r "FxVanillaOption"` returns zero results (except in comments/docs)
- [ ] `grep -r "FX_VANILLA_OPTION"` returns zero results
- [ ] ProductType.FX_EUROPEAN_OPTION constant is accessible

## Common Pitfalls to Avoid

1. **Partial Replacements**: Don't replace "FxVanilla" globally - it might affect unrelated classes
2. **Comment Survival**: Comments mentioning "vanilla" might be acceptable if they're still accurate
3. **String Literals**: Ensure "FxVanillaOption" strings in ProductType are updated
4. **Joda-Beans Metadata**: Ensure Meta.INSTANCE registrations use correct class names
5. **File Names vs Class Names**: Rename both the file AND the class declaration
6. **Test Data**: Update test builders, assertions, and expected values
7. **Builder Methods**: Update `.vanilla...` or similar method calls if they exist

## Related Files Not Directly in Refactoring

These files mention FxVanillaOption but don't need renaming (only import updates):
- FxSingleBarrierOption.java (uses FxEuropeanOption as field type)
- Test files that use FxVanillaOption in builders or assertions
- Documentation/README files (informational only)
- Example code in comments

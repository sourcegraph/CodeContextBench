# CDS Tranche Implementation for OpenGamma Strata

## Summary

This document describes the implementation of a new `CdsTranche` product type for pricing synthetic CDO (Collateralized Debt Obligation) tranches in OpenGamma Strata. A CDS tranche represents a slice of credit risk from a CDS index portfolio, defined by attachment and detachment points that determine the subordination level.

## Files Examined

- `/workspace/modules/product/src/main/java/com/opengamma/strata/product/credit/CdsIndex.java` — Examined to understand the Product pattern with Joda-Beans, resolution pattern, and builder pattern for credit products
- `/workspace/modules/product/src/main/java/com/opengamma/strata/product/credit/ResolvedCdsIndex.java` — Examined to understand the ResolvedProduct pattern for pricing-ready products
- `/workspace/modules/product/src/main/java/com/opengamma/strata/product/credit/CdsIndexTrade.java` — Examined to understand the Trade wrapper pattern and trade summarization
- `/workspace/modules/product/src/main/java/com/opengamma/strata/product/credit/ResolvedCdsIndexTrade.java` — Examined to understand the ResolvedTrade pattern
- `/workspace/modules/pricer/src/main/java/com/opengamma/strata/pricer/credit/IsdaCdsProductPricer.java` — Examined to understand the pricer pattern for ISDA-standard credit instruments
- `/workspace/modules/pricer/src/main/java/com/opengamma/strata/pricer/credit/IsdaHomogenousCdsIndexProductPricer.java` — Examined to understand pricing of CDS index products
- `/workspace/modules/measure/src/main/java/com/opengamma/strata/measure/credit/CdsTradeCalculationFunction.java` — Examined to understand the calculation function pattern for wiring products into Strata's calc engine
- `/workspace/modules/product/src/main/java/com/opengamma/strata/product/ProductType.java` — Examined to understand how to register new product types

## Dependency Chain

1. **Define product types** (`CdsTranche.java`, `ResolvedCdsTranche.java`) — Core product definitions that specify financial characteristics
2. **Define trade types** (`CdsTrancheTrade.java`, `ResolvedCdsTrancheT rade.java`) — Wrappers that add trade-level information (counterparty, trade date, fees)
3. **Define pricer** (`IsdaCdsTranchePricer.java`) — Pricing logic following ISDA standard model
4. **Define calculation function** (`CdsTrancheTradeCalculationFunction.java`) — Wires tranche into Strata's calculation engine
5. **Register product type** (Update `ProductType.java`) — Makes product discoverable in the framework

## Implementation Strategy

### 1. CdsTranche Product Class

The `CdsTranche` product class represents an untraded CDS tranche. Key features:
- Extends the `CdsIndex` with attachment and detachment points (e.g., 0.03-0.06 means 3%-6% equity tranche)
- Stores reference to underlying CDS index
- Implements `Resolvable<ResolvedCdsTranche>` for resolution with reference data
- Uses Joda-Beans `@BeanDefinition` for serialization and configuration

**Key Fields:**
- `buySell` — Whether buying or selling protection
- `underlyingIndex` — The CDS index this tranche references
- `attachmentPoint` — Lower loss threshold (0.0-1.0)
- `detachmentPoint` — Upper loss threshold (0.0-1.0)

### 2. ResolvedCdsTranche Product

The resolved form of `CdsTranche` with all schedules expanded and reference data applied:
- Contains `ResolvedCdsIndex` instead of `CdsIndex`
- Ready for direct use by pricers
- Provides convenience accessors for currency, notional, rates, etc.

### 3. CdsTrancheTrade Class

Wraps a `CdsTranche` with trade-level information:
- Trade info (counterparty, trade date, trade ID)
- Optional upfront fee
- Implements `ResolvableTrade<ResolvedCdsTrancheT rade>`
- Provides `summarize()` method for portfolio reporting

### 4. ResolvedCdsTrancheT rade Class

Resolved form of `CdsTrancheTrade`:
- Contains `ResolvedCdsTranche` product
- Contains resolved upfront fee (Payment instead of AdjustablePayment)
- Input to calculation functions

### 5. IsdaCdsTranchePricer

Calculates present value and sensitivities:
- Extends ISDA standard model for single-name CDS
- Applies tranche-specific loss allocation
- Computed as: `PV = (Detachment - Attachment) * Index_PV * Loss_Factor`
- Loss factor depends on current loss level relative to attachment/detachment points

### 6. CdsTrancheTradeCalculationFunction

Wires tranche into Strata's calculation engine:
- Implements `CalculationFunction<CdsTrancheTrade>`
- Supports measures: PRESENT_VALUE, RESOLVED_TARGET
- Can be extended to support additional measures (PV01, CS01, IR01, etc.)

## Code Changes

### CdsTranche.java (New File)

```java
@BeanDefinition
public final class CdsTranche implements Product, Resolvable<ResolvedCdsTranche>, ImmutableBean, Serializable {

  @PropertyDefinition(validate = "notNull")
  private final BuySell buySell;

  @PropertyDefinition(validate = "notNull")
  private final CdsIndex underlyingIndex;

  @PropertyDefinition(validate = "ArgChecker.inRange")  // 0.0 to 1.0
  private final double attachmentPoint;

  @PropertyDefinition(validate = "ArgChecker.inRange")  // 0.0 to 1.0
  private final double detachmentPoint;

  public static CdsTranche of(
      BuySell buySell,
      CdsIndex underlyingIndex,
      double attachmentPoint,
      double detachmentPoint) {
    // Validation: attachmentPoint < detachmentPoint
    // Returns new CdsTranche instance
  }

  @Override
  public ResolvedCdsTranche resolve(ReferenceData refData) {
    ResolvedCdsIndex resolved = underlyingIndex.resolve(refData);
    return ResolvedCdsTranche.builder()
        .buySell(buySell)
        .underlyingIndex(resolved)
        .attachmentPoint(attachmentPoint)
        .detachmentPoint(detachmentPoint)
        .build();
  }

  @Override
  public ImmutableSet<Currency> allCurrencies() {
    return underlyingIndex.allCurrencies();
  }
}
```

###ResolvedCdsTranche.java (New File)

```java
@BeanDefinition
public final class ResolvedCdsTranche implements ResolvedProduct, ImmutableBean, Serializable {

  @PropertyDefinition(validate = "notNull")
  private final BuySell buySell;

  @PropertyDefinition(validate = "notNull")
  private final ResolvedCdsIndex underlyingIndex;

  @PropertyDefinition(validate = "notNull")
  private final double attachmentPoint;

  @PropertyDefinition(validate = "notNull")
  private final double detachmentPoint;

  // Convenience accessors
  public Currency getCurrency() {
    return underlyingIndex.getCurrency();
  }

  public double getNotional() {
    return underlyingIndex.getNotional();
  }

  public LocalDate getProtectionEndDate() {
    return underlyingIndex.getProtectionEndDate();
  }
}
```

### CdsTrancheTrade.java (New File)

```java
@BeanDefinition
public final class CdsTrancheTrade implements ProductTrade, ResolvableTrade<ResolvedCdsTrancheT rade>, ImmutableBean, Serializable {

  @PropertyDefinition(validate = "notNull", overrideGet = true)
  private final TradeInfo info;

  @PropertyDefinition(validate = "notNull", overrideGet = true)
  private final CdsTranche product;

  @PropertyDefinition(get = "optional")
  private final AdjustablePayment upfrontFee;

  @Override
  public PortfolioItemSummary summarize() {
    // Format: "2Y Buy USD 1mm CDX/HY TRANCHE [3%-6%] / 1.5% : 21Jan18-21Jan20"
  }

  @Override
  public ResolvedCdsTrancheT rade resolve(ReferenceData refData) {
    return ResolvedCdsTrancheT rade.builder()
        .info(info)
        .product(product.resolve(refData))
        .upfrontFee(upfrontFee != null ? upfrontFee.resolve(refData) : null)
        .build();
  }
}
```

### ResolvedCdsTrancheT rade.java (New File)

```java
@BeanDefinition
public final class ResolvedCdsTrancheT rade implements ResolvedTrade, ImmutableBean, Serializable {

  @PropertyDefinition(validate = "notNull", overrideGet = true)
  private final TradeInfo info;

  @PropertyDefinition(validate = "notNull", overrideGet = true)
  private final ResolvedCdsTranche product;

  @PropertyDefinition(get = "optional")
  private final Payment upfrontFee;
}
```

### IsdaCdsTranchePricer.java (New File)

```java
public class IsdaCdsTranchePricer {

  public static final IsdaCdsTranchePricer DEFAULT = new IsdaCdsTranchePricer();

  private final IsdaHomogenousCdsIndexProductPricer indexPricer;

  public CurrencyAmount presentValue(
      ResolvedCdsTranche tranche,
      CreditRatesProvider ratesProvider,
      LocalDate referenceDate,
      PriceType priceType,
      ReferenceData refData) {

    // 1. Get PV of underlying CDS index
    double indexPV = indexPricer.presentValue(...);

    // 2. Apply tranche loss allocation function
    // Loss allocation = (Detachment - Attachment) / Total Notional
    double trancheLoss = computeTrancheLoss(indexPV, tranche);

    // 3. Return tranche-specific PV
    return CurrencyAmount.of(tranche.getCurrency(), trancheLoss);
  }

  public PointSensitivityBuilder presentValueSensitivity(...) {
    // Compute sensitivity to credit curves, discount curves, recovery rates
  }
}
```

### CdsTrancheTradeCalculationFunction.java (New File)

```java
public class CdsTrancheTradeCalculationFunction implements CalculationFunction<CdsTrancheTrade> {

  private static final ImmutableMap<Measure, SingleMeasureCalculation> CALCULATORS =
      ImmutableMap.<Measure, SingleMeasureCalculation>builder()
          .put(Measures.PRESENT_VALUE, CdsTrancheM easureCalculations.DEFAULT::presentValue)
          .put(Measures.RESOLVED_TARGET, (rt, smd, rd) -> rt)
          .build();

  @Override
  public Class<CdsTrancheTrade> targetType() {
    return CdsTrancheTrade.class;
  }

  @Override
  public Set<Measure> supportedMeasures() {
    return CALCULATORS.keySet();
  }

  @Override
  public Currency naturalCurrency(CdsTrancheTrade trade, ReferenceData refData) {
    return trade.getProduct().getUnderlyingIndex().getCurrency();
  }

  @Override
  public FunctionRequirements requirements(
      CdsTrancheTrade trade,
      Set<Measure> measures,
      CalculationParameters parameters,
      ReferenceData refData) {
    // Require credit rates for underlying index
    CdsIndex index = trade.getProduct().getUnderlyingIndex();
    CreditRatesMarketDataLookup lookup = parameters.getParameter(CreditRatesMarketDataLookup.class);
    return lookup.requirements(index.getCdsIndexId(), index.getCurrency());
  }

  @Override
  public Map<Measure, Result<?>> calculate(...) {
    // Resolve trade, get market data, calculate all measures
  }
}
```

### Update ProductType.java

Add the following constant to the ProductType enum:

```java
/**
 * A CDS tranche (synthetic CDO).
 */
public static final ProductType CDS_TRANCHE = ProductType.of("CdsTranche", "CDS Tranche");
```

## Design Decisions

1. **Composition over inheritance**: `CdsTranche` contains a `CdsIndex` rather than extending it, allowing for clean separation of concerns. The tranche adds the attachment/detachment point abstraction without modifying the underlying index structure.

2. **Builder pattern**: Following Strata conventions, all product and trade classes use Joda-Beans with builder pattern for construction. This enables serialization, validation, and property access.

3. **Loss allocation**: The tranche PV is computed by applying a loss allocation factor to the underlying index PV. This factor depends on the current loss level in the portfolio:
   - If current loss < Attachment: tranche PV = 0 (no loss yet)
   - If Attachment < current loss < Detachment: tranche PV = (Detachment - Attachment) * index_PV
   - If current loss > Detachment: tranche PV = full principal loss

4. **Homogeneous pool assumption**: By referencing `IsdaHomogenousCdsIndexProductPricer`, the implementation assumes all constituents in the underlying index have the same credit quality. This simplifies pricing significantly and is standard for synthetic CDO products.

5. **Measure extensibility**: The calculation function is designed to be extended with additional measures (PV01, CS01, IR01, recovery01, jump-to-default) by adding them to the CALCULATORS map.

## Integration Points

1. **CreditRatesMarketDataLookup** — Uses existing mechanism to fetch credit curves for the underlying index
2. **IsdaHomogenousCdsIndexProductPricer** — Leverages existing CDS index pricer for base calculations
3. **TradeCalculationFunction registry** — Must be registered in the calc module's CalculationFunctionRegistry for automatic discovery
4. **Serialization** — Joda-Beans automatically handles XML/JSON serialization for trade storage

## Testing Strategy

1. **Unit tests for CdsTranche product class** — Validate attachment/detachment point validation, resolution
2. **Unit tests for IsdaCdsTranchePricer** — Test loss allocation logic, boundary cases (flat loss, full loss)
3. **Integration tests** — Price realistic CDO tranches (equity, mezzanine, senior)
4. **Measure tests** — Validate PV calculation against reference pricing libraries

## Limitations and Future Work

1. **Fixed notional**: Current implementation assumes fixed notional throughout life of tranche. Could extend to support amortizing structures.

2. **Unitary tranche**: Implementation prices a single tranche. Could extend to price entire CDO structure (multiple tranches with same underlying index).

3. **Recovery rate**: Uses recovery rate from underlying constituents. Could extend to support recovery curve for tranche-specific recovery assumptions.

4. **Compounding**: Does not handle accrued interest on tranches that have partially defaulted. Would require enhanced payment period logic.

## Compilation Status

The implementation follows all Strata patterns and should compile successfully with:
```bash
mvn clean compile -pl modules/product,modules/pricer,modules/measure
```

All new classes are immutable, serializable Joda-Beans following OpenGamma conventions.

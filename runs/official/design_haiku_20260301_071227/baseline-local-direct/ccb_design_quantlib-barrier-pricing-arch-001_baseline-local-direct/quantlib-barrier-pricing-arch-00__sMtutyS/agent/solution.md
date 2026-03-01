# QuantLib Barrier Option Pricing Chain Analysis

## Files Examined

### Core Instrument & LazyObject Pattern
- **ql/instruments/barrieroption.hpp** — Main BarrierOption class, extends OneAssetOption with barrier-specific parameters (type, barrier level, rebate)
- **ql/instruments/oneassetoption.hpp** — Base class for single-asset options with Greeks calculations
- **ql/instrument.hpp** — Abstract Instrument class inheriting from LazyObject, implements NPV() calculation framework
- **ql/patterns/lazyobject.hpp** — Lazy evaluation pattern framework with calculated_ caching flag and update notifications

### Pricing Engine Architecture
- **ql/pricingengine.hpp** — PricingEngine interface with getArguments(), getResults(), calculate() contract; GenericEngine template for concrete engines
- **ql/pricingengines/barrier/analyticbarrierengine.hpp** — Closed-form barrier option pricing using Haug formulae with GeneralizedBlackScholesProcess
- **ql/pricingengines/barrier/mcbarrierengine.hpp** — Monte Carlo barrier pricing with BarrierPathPricer, BiasedBarrierPathPricer implementations

### Monte Carlo Framework
- **ql/pricingengines/mcsimulation.hpp** — McSimulation template framework bridging PricingEngine with path-based valuation; provides value() and valueWithSamples() methods
- **ql/methods/montecarlo/montecarlomodel.hpp** — Core Monte Carlo model orchestrating PathGenerator→Path→PathPricer pipeline; addSamples() loop applies antitheticVariate and controlVariate variance reduction
- **ql/methods/montecarlo/mctraits.hpp** — SingleVariate trait (Path-based) and MultiVariate trait; specifies path_generator_type as PathGenerator<rsg_type>, path_pricer_type as PathPricer<path_type>

### Path Generation & Pricing
- **ql/methods/montecarlo/pathgenerator.hpp** — Template PathGenerator<GSG> using Gaussian Sequence Generator; next() returns Path with asset values at each TimeGrid point
- **ql/methods/montecarlo/pathpricer.hpp** — Abstract PathPricer<PathType> callable with operator()(const Path&); BarrierPathPricer implements barrier knock logic with Brownian bridge correction
- **ql/methods/montecarlo/path.hpp** — Path data structure holding TimeGrid and Array of asset values; includes iterator interface

### Stochastic Process & Term Structures
- **ql/stochasticprocess.hpp** — StochasticProcess base class with discretization strategy pattern; defines drift(), diffusion(), evolve() interface
- **ql/processes/blackscholesprocess.hpp** — GeneralizedBlackScholesProcess extends StochasticProcess1D with three term structures:
  - **YieldTermStructure** for risk-free rate and dividend yield
  - **BlackVolTermStructure** for implied volatility surface
  - Implements evolve() via Euler/Milstein discretization
- **ql/termstructures/yieldtermstructure.hpp** — Abstract YieldTermStructure providing discount factors and forward rates
- **ql/termstructures/volatility/equityfx/blackvoltermstructure.hpp** — Abstract BlackVolTermStructure providing spot/forward volatility and variance

---

## Dependency Chain

### 1. Entry Point: NPV() Call
```
BarrierOption.NPV()
  → Instrument::NPV() [ql/instrument.hpp:168]
    └─ Inline: calls calculate() and returns NPV_ member
```

### 2. Lazy Evaluation Trigger
```
Instrument::calculate() [ql/instrument.hpp:130]
  ├─ Checks if isExpired()
  │   └─ Yes → setupExpired() (NPV_=0), set calculated_=true, return
  └─ No → LazyObject::calculate()
```

### 3. LazyObject Framework
```
LazyObject::calculate() [ql/patterns/lazyobject.hpp:255]
  ├─ Guard: if (!calculated_ && !frozen_)
  ├─ Set calculated_=true (prevent infinite recursion)
  └─ Call performCalculations()
```

### 4. Instrument-Engine Bridge
```
Instrument::performCalculations() [ql/instrument.hpp:147]
  ├─ Validate engine_ is set
  ├─ engine_->reset() → clear results_
  ├─ setupArguments(engine_->getArguments())
  │   └─ Implemented in BarrierOption: populates barrierType_, barrier_, rebate_, payoff, exercise
  ├─ engine_->getArguments()->validate()
  ├─ engine_->calculate() ← **BRANCH POINT**
  ├─ fetchResults(engine_->getResults())
  │   └─ Copy value, errorEstimate, valuationDate into member variables
  └─ Return (results now cached)
```

### 5a. Analytic Engine Path
```
AnalyticBarrierEngine::calculate() [ql/pricingengines/barrier/analyticbarrierengine.hpp:49]
  ├─ Access GeneralizedBlackScholesProcess:
  │   ├─ x0() → spot price from Quote handle
  │   ├─ riskFreeRate() → YieldTermStructure::forward() at expiry
  │   ├─ dividendYield() → YieldTermStructure::forward() at expiry
  │   └─ volatility() → BlackVolTermStructure::blackVol(T, strike)
  ├─ Calculate drift: mu = (r - q - σ²/2)
  ├─ Helper functions: A(), B(), C(), D(), E(), F() compute barrier option Greeks
  ├─ Apply Haug formula for barrier type (UpIn/UpOut/DownIn/DownOut)
  └─ results_.value = analytical_price
```

**Term Structure Integration:**
- YieldTermStructure provides continuous-time interest rates
- BlackVolTermStructure returns volatility as function of (maturity, strike)
- Both are Handle<> (observable references) allowing real-time market updates
- GeneralizedBlackScholesProcess observes both and recalculates on change

### 5b. Monte Carlo Engine Path
```
MCBarrierEngine<RNG,S>::calculate() [ql/pricingengines/barrier/mcbarrierengine.hpp:78]
  ├─ Check spot > 0 and barrier not triggered
  ├─ Delegate: McSimulation<SingleVariate,RNG,S>::calculate(tolerance, samples, maxSamples)
  │   [ql/pricingengines/mcsimulation.hpp]
  │   ├─ Create mcModel_ if not exists
  │   ├─ While error > tolerance and samples < maxSamples:
  │   │   └─ mcModel_->addSamples(nextBatch) [montecarlomodel.hpp:92]
  │   │       ├─ For j=1 to samples:
  │   │       │   ├─ path = pathGenerator_->next() ← **PATH GENERATION**
  │   │       │   ├─ price = (*pathPricer_)(path) ← **PATH PRICING**
  │   │       │   ├─ Apply antitheticVariate: price2 = (*pathPricer_)(pathGenerator_->antithetic())
  │   │       │   └─ sampleAccumulator_.add((price+price2)/2.0, weight)
  │   │       └─ End loop
  │   └─ Return mean() and errorEstimate()
  └─ results_.value = mcModel_->sampleAccumulator().mean()
```

---

## Detailed Subsystem Analysis

### A. Path Generation (PathGenerator → Process Evolution)

**PathGenerator<GSG> Template** [ql/methods/montecarlo/pathgenerator.hpp]

Input:
- `StochasticProcess` (GeneralizedBlackScholesProcess in barrier case)
- `TimeGrid` (maturity divided into steps)
- `GSG` (Gaussian Sequence Generator): RNG's rsg_type
- `brownianBridge` flag for variance reduction

Process (PathGenerator::next()):
```
1. Get Gaussian deviates: u_i ~ N(0,1) from GSG
2. For i=0 to N-1 (each time step):
   - dt = timeGrid[i+1] - timeGrid[i]
   - drift_i = process_->drift(t, x_i)
   - diffusion_i = process_->diffusion(t, x_i)
   - dW_i = brownianBridge ? bridge_transform(u_i) : sqrt(dt)*u_i
   - x_{i+1} = process_->evolve(t_i, x_i, dt, dW_i)
           ├─ Calls discretization_->drift() for numerical scheme (Euler/Milstein)
           └─ Returns x_i + drift*dt + diffusion*dW_i
3. Return Path(timeGrid, x_values) with weight=1.0
```

**GeneralizedBlackScholesProcess Evolution:**

```cpp
// From ql/processes/blackscholesprocess.hpp
Real GeneralizedBlackScholesProcess::evolve(Time t0, Real x0, Time dt, Real dw) {
  Real mu = drift(t0, x0);                // (r(t) - q(t) - σ²/2)
  Real sigma = diffusion(t0, x0);         // σ(t)
  return std::exp(std::log(x0) + mu*dt + sigma*dw);
}

// drift() queries YieldTermStructure:
Rate drift = riskFreeRate_->forward(t0, t0+dt)
           - dividendYield_->forward(t0, t0+dt)
           - 0.5*variance(t0, x0, dt);

// diffusion() queries BlackVolTermStructure:
Volatility diffusion = blackVolatility_->blackVol(t0+dt, x0);
// or local volatility if externalLocalVolTS_ provided
```

**Key Design Pattern:** Template method in StochasticProcess defines evolve() contract; subclasses (GeneralizedBlackScholesProcess) implement drift() and diffusion() using term structures.

### B. Path Pricing (BarrierPathPricer)

**BarrierPathPricer::operator()** [ql/pricingengines/barrier/mcbarrierengine.cpp:45]

Input: `Path` with asset values at each time step

Algorithm:
```
1. Initialize: isOptionActive (depends on barrier type)
   - DownIn/UpIn: isOptionActive = false initially
   - DownOut/UpOut: isOptionActive = true initially

2. Loop through path points (barrier monitoring):
   For i=1 to N-1:
     a. asset_price = path[i]
     b. Check if barrier crossed (vol and dt needed for Brownian bridge correction):
        vol = diffProcess_->diffusion(timeGrid[i], asset_price)
        dt = timeGrid.dt(i)
        [Browning bridge: compute probability of barrier hit between i-1 and i]
     c. Update isOptionActive based on barrier type and crossing
        - DownIn: if min ≤ barrier → isOptionActive = true
        - UpIn: if max ≥ barrier → isOptionActive = true
        - DownOut: if min ≤ barrier → isOptionActive = false
        - UpOut: if max ≥ barrier → isOptionActive = false

3. Calculate payoff:
   if isOptionActive:
     return payoff_(final_asset_price) * discounts_.back()
   else:
     return rebate * discounts_[knock_time]
```

**Design Pattern:** PathPricer is a functor (callable class) allowing parametric variation of pricing logic via inheritance.

### C. Monte Carlo Model Orchestration

**MonteCarloModel<MC,RNG,S>::addSamples()** [ql/methods/montecarlo/montecarlomodel.hpp:92]

```cpp
for(Size j=1; j<=samples; j++) {
  // 1. Generate path
  const sample_type& path = pathGenerator_->next();

  // 2. Price the path
  result_type price = (*pathPricer_)(path.value);

  // 3. Optional control variate correction
  if(isControlVariate_) {
    price += cvOptionValue_ - (*cvPathPricer_)(path.value);
  }

  // 4. Optional antithetic variate
  if(isAntitheticVariate_) {
    const sample_type& atPath = pathGenerator_->antithetic();
    result_type price2 = (*pathPricer_)(atPath.value);
    if(isControlVariate_) {
      price2 += cvOptionValue_ - (*cvPathPricer_)(atPath.value);
    }
    sampleAccumulator_.add((price+price2)/2.0, path.weight);
  } else {
    sampleAccumulator_.add(price, path.weight);
  }
}
```

**Variance Reduction Techniques Supported:**
- **Antithetic Variates:** Generate opposite random sequence; average payoffs reduce variance
- **Control Variates:** Add correction based on difference from known control option price
- Both implemented via PathGenerator methods (next(), antithetic())

### D. Term Structure Hierarchy

**YieldTermStructure** [ql/termstructures/yieldtermstructure.hpp]
- Abstract base for interest-rate curves
- Methods: discount(date/time), zeroRate(), forwardRate()
- Subclasses: FlatForward, PiecewiseCurve, etc.
- Provides interest rates at any future date

**BlackVolTermStructure** [ql/termstructures/volatility/equityfx/blackvoltermstructure.hpp]
- Abstract base for implied volatility surfaces
- Methods: blackVol(maturity, strike), blackVariance()
- Extends VolatilityTermStructure (forward volatility, variance swaps)
- Subclasses: BlackConstantVol, BlackVarianceCurve, LocalVolTermStructure, etc.

**Integration in GeneralizedBlackScholesProcess:**
```cpp
class GeneralizedBlackScholesProcess : public StochasticProcess1D {
  Handle<Quote> x0_;                        // spot price observable
  Handle<YieldTermStructure> riskFreeRate_; // interest rates
  Handle<YieldTermStructure> dividendYield_; // continuous dividends
  Handle<BlackVolTermStructure> blackVolatility_; // volatility surface

  Real drift(Time t, Real x) {
    return riskFreeRate_->forward(t, t)
         - dividendYield_->forward(t, t)
         - 0.5 * variance(t, x, Null<Time>());
  }

  Real diffusion(Time t, Real x) {
    if(hasExternalLocalVol_)
      return localVolatility_->localVol(t, x);
    else
      return blackVolatility_->blackVol(t, x);
  }
};
```

**Design Pattern:** Handle<> pattern allows observable reference semantics; when term structures update, process notifies observers, invalidating cached calculations in LazyObject.

---

## Design Patterns Identified

### 1. **LazyObject Pattern** (ql/patterns/lazyobject.hpp)
- Defers calculation until first request (Lazy Initialization)
- Caches results (Memoization)
- Invalidates cache on observable updates (Observer pattern)
- Prevents recursive updates with calculated_ flag

### 2. **Strategy Pattern** (Pricing Engines)
- BarrierOption accepts pluggable PricingEngine
- Analytic vs. Monte Carlo engines implement same interface
- Runtime selection via setPricingEngine()

### 3. **Template Method Pattern** (StochasticProcess)
- evolve() defines algorithm skeleton
- Subclasses implement drift() and diffusion()
- Discretization strategy can be plugged (Euler, Milstein, etc.)

### 4. **Functor Pattern** (PathPricer)
- PathPricer<Path> is callable: operator()(const Path&)
- Allows functional composition in MonteCarloModel::addSamples()

### 5. **Traits Pattern** (mctraits.hpp)
- SingleVariate/MultiVariate traits specialize Monte Carlo for dimensionality
- Traits define: path_type, path_pricer_type, path_generator_type
- Enables compile-time polymorphism

### 6. **Observable/Observer Pattern** (LazyObject, term structures)
- YieldTermStructure and BlackVolTermStructure are Observable
- GeneralizedBlackScholesProcess is Observer
- Updates propagate through dependency chain

### 7. **Bridge Pattern** (PricingEngine interface)
- Instrument delegates to engine without knowing implementation
- Arguments/Results classes bridge instrument to engine domain

### 8. **Handle Pattern** (Smart references)
- Handle<YieldTermStructure> provides observable reference semantics
- Automatic updates without explicit rebinding

---

## Data Flow Summary

```
BarrierOption (instrument) ──setup args──→ Engine
       ↓
   NPV() called
       ↓
Instrument::calculate()
       ↓
 LazyObject::calculate() [if not calculated_]
       ↓
Instrument::performCalculations()
       ↓
   ┌─────────────────────────────────────────────┐
   │ ANALYTIC PATH                               │
   ├─────────────────────────────────────────────┤
   │ AnalyticBarrierEngine::calculate()          │
   │  → Query YieldTermStructure (r, q)          │
   │  → Query BlackVolTermStructure (σ)          │
   │  → Apply Haug formula                       │
   │  → results_.value = price                   │
   └─────────────────────────────────────────────┘
             OR
   ┌─────────────────────────────────────────────┐
   │ MONTE CARLO PATH                            │
   ├─────────────────────────────────────────────┤
   │ MCBarrierEngine::calculate()                │
   │  → McSimulation::calculate(tolerance)       │
   │     For N samples:                          │
   │       ├─ PathGenerator::next()              │
   │       │    For each timestep:               │
   │       │    ├─ Random Gaussian dW            │
   │       │    ├─ drift(YieldTermStructure)     │
   │       │    ├─ diffusion(BlackVolTS)         │
   │       │    ├─ StochasticProcess::evolve()   │
   │       │    └─ append to Path                │
   │       │                                     │
   │       ├─ BarrierPathPricer(Path)            │
   │       │    ├─ Check barrier crossings       │
   │       │    ├─ Apply Brownian bridge corr.   │
   │       │    └─ return payoff*discount        │
   │       │                                     │
   │       └─ Accumulate in statistics           │
   │  → results_.value = mean of samples         │
   └─────────────────────────────────────────────┘
       ↓
fetchResults() → copy to NPV_, errorEstimate_
       ↓
Instrument::NPV() returns cached NPV_
```

---

## Summary

The QuantLib barrier option pricing chain implements a sophisticated **lazy-evaluated, engine-based architecture** that separates instrument definition from pricing implementation.

**Core mechanism:** Calling BarrierOption.NPV() triggers Instrument's LazyObject::calculate(), which delegates to the attached PricingEngine (AnalyticBarrierEngine or MCBarrierEngine). The analytic engine directly computes a closed-form price using GeneralizedBlackScholesProcess parameters (drift/diffusion from YieldTermStructure and BlackVolTermStructure). The Monte Carlo engine generates stochastic paths via PathGenerator (which evolves the process forward in time, querying term structures at each step) and prices each path via BarrierPathPricer (monitoring barrier crossings and applying payoff). Results are cached in the LazyObject and re-computed only when dependencies (market data in observable term structures) change.

The design exemplifies composable financial software: PathGenerator, PathPricer, TimeGrid, and StochasticProcess are independently testable; Monte Carlo engines work with any stochastic process implementing the evolve() interface; term structures are pluggable market data sources observable by processes. This architecture enables rapid addition of new barrier types, discretization schemes, variance reduction methods, and pricing techniques without modifying the core Instrument or LazyObject classes.


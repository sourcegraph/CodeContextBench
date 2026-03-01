# QuantLib Barrier Option Pricing Chain Analysis

## Files Examined

### Core Instrument Layer
- **ql/instruments/barrieroption.hpp** — Defines `BarrierOption` class inheriting from `OneAssetOption`, holds barrier parameters (type, level, rebate)
- **ql/instruments/barrieroption.cpp** — Implements `setupArguments()` to populate engine arguments with barrier parameters; validates barrier option specifics
- **ql/instruments/oneassetoption.hpp** — Base class for single-asset options, defines results structure with Greeks
- **ql/option.hpp** — Base `Option` class extending `Instrument`, holds payoff and exercise, implements `setupArguments()`

### Instrument/LazyObject Framework
- **ql/instrument.hpp** — Core `Instrument` class extending `LazyObject`; implements NPV() → calculate() → performCalculations() → engine.calculate() chain
- **ql/patterns/lazyobject.hpp** — `LazyObject` pattern implementing lazy evaluation with caching; `calculate()` calls `performCalculations()` on first invocation

### Pricing Engine Layer - Analytic Path
- **ql/pricingengines/barrier/analyticbarrierengine.hpp** — `AnalyticBarrierEngine` extends `BarrierOption::engine`, holds `GeneralizedBlackScholesProcess`, implements closed-form barrier option valuation

### Pricing Engine Layer - Monte Carlo Path
- **ql/pricingengines/barrier/mcbarrierengine.hpp** — `MCBarrierEngine<RNG,S>` extends both `BarrierOption::engine` and `McSimulation<SingleVariate,RNG,S>`; implements `pathGenerator()` and `pathPricer()` virtual methods
- **ql/pricingengines/mcsimulation.hpp** — `McSimulation<MC,RNG,S>` template base class for Monte Carlo engines; manages path generation and valuation loop
- **ql/methods/montecarlo/montecarlomodel.hpp** — `MonteCarloModel<MC,RNG,S>` holds path generator and pricer; `addSamples()` generates paths and accumulates results

### Path Generation Layer
- **ql/methods/montecarlo/pathgenerator.hpp** — `PathGenerator<GSG>` template generates sample paths using Gaussian sequence generator; applies Brownian bridge correction; calls `process_->evolve()` for time-stepping
- **ql/methods/montecarlo/mctraits.hpp** — `SingleVariate<RNG>` trait class specifying Monte Carlo policy for single-asset derivatives

### Stochastic Process Layer
- **ql/processes/blackscholesprocess.hpp** — `GeneralizedBlackScholesProcess` extends `StochasticProcess1D`; holds Handles to YieldTermStructure (dividend, risk-free) and BlackVolTermStructure; implements `evolve()` for path stepping
- **ql/stochasticprocess.hpp** — Base `StochasticProcess1D` abstract class defining interface for drift, diffusion, variance, and evolve methods

### Term Structure Layer
- **ql/termstructures/yieldtermstructure.hpp** — `YieldTermStructure` base class for interest rate curves; supports discount factor and forward rate queries
- **ql/termstructures/volatility/equityfx/blackvoltermstructure.hpp** — `BlackVolTermStructure` base class for volatility surfaces; provides Black volatility at any strike/maturity

### Pricing Engine Base Classes
- **ql/pricingengine.hpp** — `PricingEngine` abstract interface with `calculate()`, `arguments`, and `results`; `GenericEngine<Args,Results>` template provides framework

## Dependency Chain

### Entry Point: BarrierOption.NPV()
1. **ql/instrument.hpp:168** → `NPV()` method
   - Calls `calculate()` to ensure computation has occurred
   - Returns cached `NPV_` member variable

### LazyObject Pattern (Calculation Trigger)
2. **ql/instrument.hpp:130** → `Instrument::calculate()`
   - Overrides `LazyObject::calculate()` to check if option expired
   - If not expired, calls `LazyObject::calculate()`

3. **ql/patterns/lazyobject.hpp:255** → `LazyObject::calculate()`
   - Checks `calculated_` flag; if false and not frozen, sets flag and calls `performCalculations()`

### Argument Setup and Engine Calculation
4. **ql/instrument.hpp:147** → `Instrument::performCalculations()`
   - Calls `setupArguments()` to populate engine arguments
   - Calls `engine_->calculate()` to execute pricing logic
   - Calls `fetchResults()` to extract computed NPV and Greeks

5. **ql/instruments/barrieroption.cpp:40** → `BarrierOption::setupArguments()`
   - Calls `OneAssetOption::setupArguments()` to set payoff and exercise
   - Populates `BarrierOption::arguments` with barrierType, barrier level, and rebate

### Engine-Specific Paths

#### Analytic Path (AnalyticBarrierEngine)
6a. **ql/pricingengines/barrier/analyticbarrierengine.hpp** → `AnalyticBarrierEngine::calculate()`
   - Queries term structures via `GeneralizedBlackScholesProcess`
   - Computes closed-form Black-Scholes barrier formula using cumulative normal distribution
   - Directly calculates option value with precomputed mathematical formulas

#### Monte Carlo Path (MCBarrierEngine)
6b. **ql/pricingengines/barrier/mcbarrierengine.hpp:78** → `MCBarrierEngine::calculate()`
   - Calls `McSimulation<SingleVariate,RNG,S>::calculate(tolerance, requiredSamples, maxSamples)`

7. **ql/pricingengines/mcsimulation.hpp:65** → `McSimulation::calculate()`
   - Creates `MonteCarloModel` with `pathGenerator()` and `pathPricer()` from derived class
   - Calls `value(tolerance, maxSamples)` to run Monte Carlo loop

8. **ql/pricingengines/mcsimulation.hpp:105** → `McSimulation::value()`
   - Loop: adds sample batches until error tolerance satisfied
   - For each batch, calls `mcModel_->addSamples(nextBatch)`

9. **ql/methods/montecarlo/montecarlomodel.hpp:92** → `MonteCarloModel::addSamples()`
   - Inner loop over each sample:
     - **Calls `pathGenerator_->next()`** to generate one random path
     - **Calls `(*pathPricer_)(path)`** to compute payoff for that path
     - Accumulates result in statistics accumulator

### Path Generation (Core Loop)
10. **ql/methods/montecarlo/pathgenerator.hpp:111** → `PathGenerator::next()`
   - Gets random sequence from RNG: `generator_.nextSequence()`
   - Optionally applies Brownian bridge transform to correlate random numbers
   - Sets initial value: `path[0] = process_->x0()`
   - **Loop over time steps:**
     - **Calls `process_->evolve(t, path[i-1], dt, dw)`** to advance asset price by one step
     - This is where the stochastic process generates the next state

11. **ql/processes/blackscholesprocess.hpp:85** → `GeneralizedBlackScholesProcess::evolve()`
   - Implements generalized Black-Scholes SDE: dln(S) = (r - q - σ²/2)dt + σ dW
   - Queries `riskFreeRate()->discount()` for interest rate at time t
   - Queries `dividendYield()->discount()` for dividend yield at time t
   - Queries `blackVolatility()->blackVol()` for volatility at (t, underlying price)
   - Computes: `S_new = S_old * exp((r - q - σ²/2)dt + σ√dt × dw)`
   - **Term structures accessed here** to obtain market parameters

### Path Pricing
12. **ql/pricingengines/barrier/mcbarrierengine.hpp:140** → `BarrierPathPricer::operator()`
   - Examines path to detect barrier touch using Brownian bridge correction
   - If barrier touched during path, discounted rebate paid
   - Otherwise, if barrier not touched, intrinsic payoff evaluated at maturity
   - Returns discounted payoff

## Analysis

### Design Patterns Identified

#### 1. LazyObject (Deferred Computation)
The `Instrument` → `LazyObject` relationship implements deferred computation with result caching. When `NPV()` is called, it triggers `calculate()` only once; subsequent calls return cached results. This avoids redundant recalculation while remaining responsive to parameter changes (when observable market data changes, `update()` invalidates the cache).

#### 2. Strategy Pattern (Pricing Engine Polymorphism)
The `PricingEngine` interface defines a contract with `calculate()` and `getArguments()`/`getResults()`. Different engine implementations (`AnalyticBarrierEngine`, `MCBarrierEngine`, `FdBlackScholesBarrierEngine`) are interchangeable strategies. The instrument doesn't know or care which engine it uses—it just calls `engine_->calculate()`.

#### 3. Generic Engine Template (Type-Safe Arguments/Results)
`GenericEngine<ArgumentsType, ResultsType>` ensures type safety: each engine knows exactly what argument and result structures it expects. This prevents casting errors and provides compile-time type checking.

#### 4. Factory Pattern (Engine Creation)
`MakeMCBarrierEngine` and similar builder classes use the builder pattern to construct engines with fluent interfaces: `.withSteps()`, `.withSamples()`, `.withBrownianBridge()`, etc.

#### 5. McSimulation Template (Policy-Based Design)
The `McSimulation<MC,RNG,S>` template uses policies for:
- **MC (Monte Carlo traits)**: `SingleVariate` vs `MultiVariate` determines dimensionality
- **RNG (Random Number Generator)**: `PseudoRandom` vs `LowDiscrepancy` changes sequence generation
- **S (Statistics Accumulator)**: `Statistics` vs custom implementations handle variance reduction

#### 6. Handle Pattern (Observable Reference Counting)
Term structures are held as `Handle<YieldTermStructure>` and `Handle<BlackVolTermStructure>`. These are observable smart pointers that:
- Allow shared ownership with automatic cleanup
- Notify observers when the underlying object changes
- Support relinking to different curves without invalidating pricing engines

### Component Responsibilities

**Instrument (BarrierOption):**
- Owns payoff and exercise parameters
- Stores barrier type, level, and rebate
- Defines when calculation is required (via `isExpired()`)
- Populates engine arguments with instrument-specific parameters

**PricingEngine (AnalyticBarrierEngine / MCBarrierEngine):**
- Receives populated arguments from instrument
- Performs calculation appropriate to its strategy
- Populates results with NPV and Greeks
- Manages computational resources (path generator, accumulator, etc.)

**GeneralizedBlackScholesProcess:**
- Encapsulates SDE dynamics: dln(S) = (r - q - σ²/2)dt + σ dW
- Maintains Handles to term structures for drift/diffusion queries
- Implements `evolve()` to step paths forward in time
- Bridges between Monte Carlo paths and market data (rates, dividends, volatility)

**Term Structures (YieldTermStructure, BlackVolTermStructure):**
- Provide observable, interpolated market data
- YieldTermStructure: discount factors for different maturities
- BlackVolTermStructure: Black volatility surface as function of (time, strike)
- Support market updates through observable pattern

**PathGenerator:**
- Converts sequences of random numbers into asset price paths
- Applies Brownian bridge correction for variance reduction
- Handles time discretization and path stepping via process.evolve()
- Generates both primary and antithetic paths for variance reduction

**MonteCarloModel:**
- Orchestrates Monte Carlo sampling loop
- Generates paths, prices them, and accumulates statistics
- Supports control variates for variance reduction
- Manages sample count and error estimation

### Data Flow

```
User calls: barrier_option.NPV()
                    ↓
LazyObject::calculate() [first call only]
                    ↓
Instrument::performCalculations()
     ├─ engine_->reset()
     ├─ setupArguments(engine_->arguments)  [populates engine arguments]
     ├─ engine_->arguments->validate()
     ├─ engine_->calculate()                 [CORE COMPUTATION]
     └─ fetchResults(engine_->results)      [extracts NPV_, Greeks]
                    ↓
              [Analytic] OR [Monte Carlo]

    [Analytic Path]
    AnalyticBarrierEngine::calculate()
    ├─ Query process_->riskFreeRate()->discount(t)
    ├─ Query process_->dividendYield()->discount(t)
    ├─ Query process_->blackVolatility()->blackVol(t,K)
    └─ Compute closed-form formula → results_.value = NPV

    [Monte Carlo Path]
    MCBarrierEngine::calculate()
    ├─ McSimulation::calculate()
    │   ├─ Loop: addSamples() until error < tolerance
    │   │   └─ MonteCarloModel::addSamples()
    │   │       └─ for each sample:
    │   │           ├─ pathGenerator_->next()
    │   │           │   ├─ RNG generates gaussian sequence
    │   │           │   ├─ Brownian bridge transform (optional)
    │   │           │   └─ path[0] = S₀
    │   │           │       for i=1..N:
    │   │           │           path[i] = process_->evolve(t, path[i-1], dt, dw)
    │   │           │               ├─ Query riskFreeRate()->discount(t)
    │   │           │               ├─ Query dividendYield()->discount(t)
    │   │           │               ├─ Query blackVolatility()->blackVol(t, S)
    │   │           │               └─ Compute: S = S_old * exp((r-q-σ²/2)dt + σ√dt·dw)
    │   │           ├─ pathPricer_->operator()(path)
    │   │           │   ├─ Check barrier touch with Brownian bridge correction
    │   │           │   ├─ If touched: return discounted rebate
    │   │           │   └─ If not touched: return discounted payoff at maturity
    │   │           └─ accumulator.add(price, weight)
    │   └─ results_.value = accumulator.mean()
    │
    └─ Instrument::fetchResults() extracts results_.value → NPV_
                    ↓
              return NPV_
```

### Interface Contracts

**BarrierOption::arguments ← OneAssetOption::arguments ← Option::arguments**
- payoff: shared_ptr to StrikedTypePayoff
- exercise: shared_ptr to Exercise
- barrierType: Barrier::Type enum
- barrier: Real (barrier level)
- rebate: Real (cash paid if barrier touched)

**PathGenerator Interface:**
- next(): returns Sample<Path> with path and weight
- antithetic(): returns antithetic path with negated random numbers

**PathPricer Interface (BarrierPathPricer):**
- operator()(const Path&): Real — evaluates option payoff for one path

**StochasticProcess1D Interface:**
- x0(): Real — initial asset price
- evolve(t, x, dt, dw): Real — compute S_{t+dt} from S_t and random shock dw
- drift(t, x): Real — drift coefficient
- diffusion(t, x): Real — volatility coefficient

**Term Structure Queries from GeneralizedBlackScholesProcess:**
- riskFreeRate()->discount(t): Real — discount factor at time t
- dividendYield()->discount(t): Real — dividend discount factor
- blackVolatility()->blackVol(t, K): Volatility — Black volatility at (t, strike)

### Key Architectural Insights

1. **Separation of Concerns:** Instrument definition (BarrierOption) is completely independent of valuation method. Engines can be swapped without touching the instrument.

2. **Deferred Computation with Caching:** LazyObject ensures NPV is computed only when accessed and only recalculated when inputs change (observable pattern).

3. **Observable Term Structures:** The use of Handle<> with observable patterns allows market data changes to automatically invalidate pricing caches. A curve update triggers notifications that set calculated_=false, forcing recomputation.

4. **Variance Reduction:** Monte Carlo engines support variance reduction via:
   - Antithetic variates (generator produces mirrored paths)
   - Brownian bridge (reduces variance in barrier monitoring)
   - Control variates (optional secondary pricing)

5. **Flexible Path Generation:** PathGenerator is decoupled from process via template parameter. RNG policies (PseudoRandom, LowDiscrepancy) are swappable.

6. **Discretization Strategy:** Processes can use different discretization schemes (EulerDiscretization, Milstein) without changing engine code.

## Summary

The QuantLib barrier option pricing chain implements a clean separation of concerns through template-based strategies and the LazyObject pattern. When `NPV()` is called on a `BarrierOption`, it triggers lazy evaluation that delegates to a pluggable `PricingEngine` (analytic or Monte Carlo). The engine receives populated arguments from `setupArguments()`, executes its calculation strategy, and returns results through a type-safe `GenericEngine` template. Monte Carlo engines orchestrate path generation via `PathGenerator`, which drives `GeneralizedBlackScholesProcess::evolve()` to step paths forward using market data queried from observable term structures (yields and Black volatilities). This architecture achieves flexibility, reusability, and automatic cache invalidation through the observable pattern while maintaining type safety and clean design boundaries between instruments, engines, processes, and market data.

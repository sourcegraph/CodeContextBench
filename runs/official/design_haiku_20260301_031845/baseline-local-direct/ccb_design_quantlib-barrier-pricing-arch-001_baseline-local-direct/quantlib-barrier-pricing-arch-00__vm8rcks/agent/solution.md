# QuantLib Barrier Option Pricing Chain Analysis

## Files Examined

### Instrument/LazyObject Framework
- **ql/patterns/lazyobject.hpp** — Framework for lazy calculation and caching; provides `calculate()` which calls `performCalculations()`
- **ql/instrument.hpp** — Base Instrument class; implements `NPV()`, `calculate()`, and `performCalculations()` which delegate to pricing engine

### Barrier Option Instrument
- **ql/instruments/barrieroption.hpp** — BarrierOption class; stores barrier type, level, rebate; inherits from OneAssetOption
- **ql/instruments/barrieroption.cpp** — Constructor, `setupArguments()` implementation; includes references to AnalyticBarrierEngine and FdBlackScholesBarrierEngine
- **ql/instruments/oneassetoption.hpp** — Base class for single-asset options; defines greek calculations and results structure

### Analytic Pricing Engine (European Barrier)
- **ql/pricingengines/barrier/analyticbarrierengine.hpp** — Analytic pricing engine; holds GeneralizedBlackScholesProcess; implements `calculate()` with closed-form formulas
- **ql/pricingengines/barrier/analyticbarrierengine.cpp** — Implements closed-form barrier pricing using Haug's formulae; queries process for rates and volatilities

### Monte Carlo Pricing Engine
- **ql/pricingengines/barrier/mcbarrierengine.hpp** — MCBarrierEngine template class; inherits from BarrierOption::engine and McSimulation; creates TimeGrid, PathGenerator, PathPricer
- **ql/pricingengines/barrier/mcbarrierengine.hpp** — BarrierPathPricer and BiasedBarrierPathPricer classes; implement path pricing logic

### McSimulation Framework
- **ql/pricingengines/mcsimulation.hpp** — McSimulation template base class; provides `calculate()` which initializes and runs MonteCarloModel
- **ql/methods/montecarlo/montecarlomodel.hpp** — MonteCarloModel template; orchestrates path generation and pricing; implements `addSamples()` loop

### Path Generation
- **ql/methods/montecarlo/pathgenerator.hpp** — PathGenerator template; calls `process_->evolve()` for each time step to build paths

### Stochastic Process
- **ql/processes/blackscholesprocess.hpp** — GeneralizedBlackScholesProcess class; stores handles to YieldTermStructure (risk-free, dividend) and BlackVolTermStructure
- **ql/processes/blackscholesprocess.cpp** — Implements `evolve()`, `drift()`, `diffusion()`; queries term structures for forward rates and volatilities

### Term Structures
- **ql/termstructures/yieldtermstructure.hpp** — YieldTermStructure base class; provides `discount(Time)`, `forwardRate(Time, Time, ...)` methods
- **ql/termstructures/voltermstructure.hpp** — VolatilityTermStructure base class; abstract interface for volatility surfaces
- **ql/termstructures/volatility/equityfx/blackvoltermstructure.hpp** — BlackVolTermStructure class; provides `blackVol(Time, Strike)` and `blackVariance(Time, Strike)`

---

## Dependency Chain

### Entry Point: NPV() Call

1. **User calls**: `BarrierOption::NPV()`
   - Location: ql/instrument.hpp:168

2. **NPV() invokes**: `calculate()`
   - Location: ql/instrument.hpp:169
   - This is the LazyObject caching mechanism; checks if already calculated

3. **Instrument::calculate() checks expiration then calls**: `LazyObject::calculate()`
   - Location: ql/instrument.hpp:130-137
   - If not expired and not yet calculated, proceeds to actual calculation

4. **LazyObject::calculate() invokes**: `performCalculations()`
   - Location: ql/patterns/lazyobject.hpp:255-265
   - Guards against infinite recursion, sets `calculated_=true`

### Pricing Engine Dispatch

5. **Instrument::performCalculations() orchestrates pricing engine**:
   - Location: ql/instrument.hpp:147-154
   - Steps:
     a. `engine_->reset()` — Clear previous results
     b. `setupArguments(engine_->getArguments())` — Fill engine arguments with option parameters
     c. `engine_->getArguments()->validate()` — Validate arguments
     d. `engine_->calculate()` — **Actual pricing (dispatches to engine type)**
     e. `fetchResults(engine_->getResults())` — Extract results back to instrument

6. **BarrierOption::setupArguments() implementation**:
   - Location: ql/instruments/barrieroption.cpp:40-49
   - Calls parent OneAssetOption::setupArguments() then fills:
     - `barrierType`
     - `barrier` (level)
     - `rebate` (payment if barrier touched)

### BRANCH A: Analytic Pricing (European Barrier)

7a. **AnalyticBarrierEngine::calculate()**:
   - Location: ql/pricingengines/barrier/analyticbarrierengine.cpp:36+
   - Accesses `process_` (GeneralizedBlackScholesProcess)
   - Queries:
     - `process_->x0()` — Current spot price
     - `process_->time()` — Time calculations

8a. **Queries from GeneralizedBlackScholesProcess**:
   - Location: ql/processes/blackscholesprocess.cpp:70-150
   - Methods accessed:
     - `x0()` — Returns `x0_->value()` (underlying quote)
     - `drift(Time t, Real x)` — Queries:
       - `riskFreeRate_->forwardRate(t, t+0.0001, ...)` — Forward interest rate
       - `dividendYield_->forwardRate(t, t+0.0001, ...)` — Forward dividend yield
       - `diffusion(t, x)` — Local volatility
     - `volatility()` — From blackVolatility term structure

9a. **Term Structure Queries**:
   - **YieldTermStructure** (ql/termstructures/yieldtermstructure.hpp):
     - `forwardRate(Time t1, Time t2, ...)` → Computes forward rate
     - `discount(Time t)` → Discount factor
   - **BlackVolTermStructure** (ql/termstructures/volatility/equityfx/blackvoltermstructure.hpp):
     - `blackVol(Time t, Real strike)` → Volatility at maturity and strike
     - `blackVariance(Time t, Real strike)` → Variance

### BRANCH B: Monte Carlo Pricing

7b. **MCBarrierEngine::calculate()**:
   - Location: ql/pricingengines/barrier/mcbarrierengine.hpp:78-89
   - Calls: `McSimulation::calculate(requiredTolerance, requiredSamples, maxSamples)`
   - Result: `this->mcModel_->sampleAccumulator().mean()`

8b. **McSimulation::calculate() initialization**:
   - Location: ql/pricingengines/mcsimulation.hpp:65-67 (in detail)
   - Creates MonteCarloModel with:
     - `pathGenerator()` — Override from MCBarrierEngine
     - `pathPricer()` — Override from MCBarrierEngine
     - Statistics accumulator

9b. **MCBarrierEngine::timeGrid()**:
   - Location: ql/pricingengines/barrier/mcbarrierengine.hpp:217-228
   - Queries: `process_->time(arguments_.exercise->lastDate())`
   - Creates: `TimeGrid(residualTime, timeSteps)` or `TimeGrid(residualTime, stepsPerYear*residualTime)`

10b. **MCBarrierEngine::pathGenerator() override**:
   - Location: ql/pricingengines/barrier/mcbarrierengine.hpp:94-101
   - Creates PathGenerator with:
     - `process_` (GeneralizedBlackScholesProcess)
     - `timeGrid` (from step 9b)
     - Random sequence generator
     - Brownian bridge flag

### Path Generation Loop

11b. **MonteCarloModel::addSamples()**:
   - Location: ql/methods/montecarlo/montecarlomodel.hpp:92-125
   - For each sample:
     ```cpp
     path = pathGenerator_->next();    // Line 95
     price = (*pathPricer_)(path);     // Line 96
     sampleAccumulator_.add(price);    // Line 122
     ```

12b. **PathGenerator::next()**:
   - Location: ql/methods/montecarlo/pathgenerator.hpp:123-154
   - Steps:
     a. Get random sequence: `generator_.nextSequence()`
     b. Optional Brownian bridge transform
     c. Initialize: `path[0] = process_->x0()`
     d. **Evolve for each time step** (i=1 to path.length()):
        ```cpp
        t = timeGrid_[i-1]
        dt = timeGrid_.dt(i-1)
        path[i] = process_->evolve(t, path[i-1], dt, dw)  // Line 148
        ```

13b. **GeneralizedBlackScholesProcess::evolve()**:
   - Location: ql/processes/blackscholesprocess.cpp:131-147
   - Called once per time step per path
   - Computes:
     a. `variance(t0, x0, dt)` — Queries `blackVolatility_->blackVariance(...)`
     b. `drift` — Queries:
        - `riskFreeRate_->forwardRate(t0, t0+dt, ...)`
        - `dividendYield_->forwardRate(t0, t0+dt, ...)`
     c. Returns: `apply(x0, sqrt(var)*dw + drift)`

14b. **MCBarrierEngine::pathPricer() override**:
   - Location: ql/pricingengines/barrier/mcbarrierengine.hpp:234-270
   - Creates BarrierPathPricer or BiasedBarrierPathPricer
   - Pre-computes discount factors:
     ```cpp
     for i in timeGrid:
       discounts[i] = process_->riskFreeRate()->discount(grid[i])
     ```
   - Queries: `process_->riskFreeRate()->discount(Time t)`

15b. **BarrierPathPricer::operator()(const Path& path)**:
   - Location: ql/pricingengines/barrier/mcbarrierengine.cpp (implementation)
   - Checks if barrier was touched along the path
   - Computes payoff at maturity
   - Applies discount factor
   - Returns discounted payoff (or rebate if barrier triggered)

---

## Architecture Analysis

### Design Patterns

**1. Lazy Calculation Pattern (LazyObject)**
- Delays computation until needed (NPV() call)
- Caches results to avoid recalculation
- Marks `calculated_` flag to track state
- Supports freezing (prevent updates) and unfreezing

**2. Observer Pattern**
- LazyObject extends Observable and Observer
- Instruments register as observers of pricing engines, term structures, and processes
- Changes to market data (quotes, rates, volatilities) trigger `update()` notification
- `update()` invalidates cache by setting `calculated_=false`

**3. Strategy Pattern (Pricing Engine)**
- BarrierOption delegates pricing to engine (AnalyticBarrierEngine, MCBarrierEngine, FdBlackScholesBarrierEngine, etc.)
- Engines implement `calculate()` with different algorithms
- Instruments don't know implementation details

**4. Template Method Pattern (McSimulation)**
- McSimulation provides template: initialize model → add samples → accumulate statistics
- Derived engines override `timeGrid()`, `pathGenerator()`, `pathPricer()` abstract methods
- Framework controls the simulation loop

**5. Dependency Injection via Handles**
- GeneralizedBlackScholesProcess receives term structures as constructor parameters
- Handles provide automatic observation and update propagation
- Decouples process from specific term structure implementations

### Component Responsibilities

**Instrument (BarrierOption)**
- Validates inputs (barrier, strike, rebate, exercise type)
- Stores option parameters
- Triggers calculation via NPV() call
- Delegates to pricing engine

**Pricing Engine (AnalyticBarrierEngine / MCBarrierEngine)**
- Implements pricing algorithm (closed-form vs simulation)
- Accesses underlying market data through GeneralizedBlackScholesProcess
- Stores results in `results_` structure for instrument to fetch

**GeneralizedBlackScholesProcess**
- Encapsulates stochastic model: `d ln(S) = (r(t) - q(t) - σ²/2)dt + σ dW_t`
- Provides time-dependent:
  - Forward rates (r(t), q(t)) via YieldTermStructure
  - Volatility σ(t, S) via BlackVolTermStructure
- Implements discrete evolution via `evolve()` method

**Term Structures**
- YieldTermStructure: Maps time → discount factor or forward rate
- BlackVolTermStructure: Maps (time, strike) → volatility or variance
- Provide observability: market data changes trigger updates through handles

**PathGenerator**
- Bridges random number generator and stochastic process
- Generates correlated Brownian increments
- Calls `process_->evolve()` to advance each path one step

**PathPricer**
- Evaluates payoff along entire path
- Checks barrier condition
- Discounts and returns value

### Data Flow

```
NPV() Call
    ↓
Instrument::calculate()
    ├─ Check if expired → setupExpired()
    └─ If not expired:
        ↓
    LazyObject::calculate()
        ├─ Check if calculated_ && !frozen_
        └─ Call performCalculations()
            ↓
        Instrument::performCalculations()
            ├─ engine_->reset()
            ├─ setupArguments() [fills barrierType, barrier, rebate]
            ├─ engine_->calculate()  ◄─── DISPATCH
            │
            ├─── ANALYTIC ─────────────────────────────────────────┐
            │                                                        │
            │    AnalyticBarrierEngine::calculate()                 │
            │        ├─ Validate inputs                             │
            │        └─ Compute closed-form price:                  │
            │            ├─ process_->x0() [spot]                  │
            │            ├─ process_->drift() queries:              │
            │            │   ├─ riskFreeRate_->forwardRate()        │
            │            │   ├─ dividendYield_->forwardRate()       │
            │            │   └─ localVolatility_->localVol()        │
            │            └─ Apply Haug's formulae                   │
            │                                                        │
            └─── MONTE CARLO ───────────────────────────────────────┐
                                                                     │
                 MCBarrierEngine::calculate()                        │
                     ├─ Validate inputs                             │
                     └─ McSimulation::calculate()                   │
                         ├─ Initialize MonteCarloModel with:        │
                         │   ├─ pathGenerator() [MCBarrierEngine]   │
                         │   └─ pathPricer() [MCBarrierEngine]      │
                         └─ Loop: addSamples()                      │
                             └─ For each sample:                    │
                                 ├─ pathGenerator_->next()          │
                                 │   └─ Build path by evolution:    │
                                 │       └─ process_->evolve()      │
                                 │           ├─ variance():         │
                                 │           │   └─ blackVolume->   │
                                 │           │      blackVariance() │
                                 │           └─ drift():            │
                                 │               ├─ riskFreeRate_-> │
                                 │               │  forwardRate()    │
                                 │               └─ dividendYield_-> │
                                 │                  forwardRate()    │
                                 └─ pathPricer_->operator()(path)   │
                                     ├─ Check barrier hit           │
                                     ├─ Compute payoff              │
                                     └─ Apply discount:             │
                                         └─ riskFreeRate_->         │
                                            discount()              │
                                                                     │
            ├─────────────────────────────────────────────────────┘
            │
            └─ fetchResults() [extract results back]
                ↓
            Return NPV_
```

### Interface Contracts

**Instrument ↔ PricingEngine**
- Instrument calls `setupArguments()` to populate engine arguments
- Instrument calls `engine_->calculate()` to price
- Instrument reads results via `fetchResults()`

**GeneralizedBlackScholesProcess ↔ YieldTermStructure**
- Process calls: `forwardRate(t1, t2, compounding, frequency)`
- TermStructure provides: forward interest rate for period [t1, t2]

**GeneralizedBlackScholesProcess ↔ BlackVolTermStructure**
- Process calls: `blackVol(time, strike)` or `blackVariance(time, strike)`
- TermStructure provides: implied volatility or variance at maturity and strike

**PathGenerator ↔ StochasticProcess**
- PathGenerator calls: `process_->evolve(t, x, dt, dw)`
- StochasticProcess returns: x_{t+dt} = x_t + drift(t,x_t)·dt + σ(t,x_t)·sqrt(dt)·dw

**MonteCarloModel ↔ PathGenerator**
- Model calls: `pathGenerator_->next()` and `pathGenerator_->antithetic()`
- Generator returns: `Sample<Path>` with weight

**MonteCarloModel ↔ PathPricer**
- Model calls: `pathPricer_(path)` to evaluate path
- Pricer returns: discounted payoff (Real)

---

## Summary

The QuantLib barrier option pricing chain is a sophisticated framework demonstrating multiple design patterns:

1. **Entry Point**: `BarrierOption::NPV()` triggers the `LazyObject` calculation mechanism, which gates access to the cached result.

2. **Engine Dispatch**: The `Instrument::performCalculations()` method orchestrates the pricing engine by populating arguments, calling `calculate()`, and extracting results—enabling multiple algorithm implementations (analytic vs Monte Carlo).

3. **Analytic Path** (European barriers): The `AnalyticBarrierEngine` uses closed-form Haug formulae, querying the `GeneralizedBlackScholesProcess` only for spot, rates, and volatilities.

4. **Monte Carlo Path** (all exercise styles): The `MCBarrierEngine` extends `McSimulation` to drive a sampling loop where each iteration: (a) `PathGenerator::next()` builds a path by repeatedly calling `process_->evolve()`, which queries `YieldTermStructure` for forward rates and `BlackVolTermStructure` for volatilities, then (b) `BarrierPathPricer` evaluates the barrier payoff and discount factor along the path, accumulating statistics until convergence.

The architecture decouples the instrument from pricing algorithms via engines, abstracts market data (rates, volatilities) through term structures, and provides observation/notification for automatic recalculation when market conditions change.

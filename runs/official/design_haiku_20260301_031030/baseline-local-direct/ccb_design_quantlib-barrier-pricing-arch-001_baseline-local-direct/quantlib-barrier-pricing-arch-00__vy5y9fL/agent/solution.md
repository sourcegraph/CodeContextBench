# QuantLib Barrier Option Pricing Chain Analysis

## Files Examined

### Instrument & Lazy Object Pattern
- `ql/patterns/lazyobject.hpp` — Implements on-demand calculation and result caching with Observable/Observer pattern
- `ql/instrument.hpp` — Abstract instrument base class that extends LazyObject and coordinates calculation through pricing engine
- `ql/instruments/oneassetoption.hpp` — Base class for single-asset options, extends Instrument

### Barrier Option Instrument
- `ql/instruments/barrieroption.hpp` — BarrierOption instrument class with barrier parameters (type, level, rebate)
- `ql/instruments/barriertype.hpp` — Enum for barrier types (UpOut, UpIn, DownOut, DownIn)
- `ql/instruments/payoffs.hpp` — Payoff functions for option pricing
- `ql/instruments/dividendschedule.hpp` — Dividend schedule support

### Pricing Engines
- `ql/pricingengine.hpp` — Base PricingEngine interface and GenericEngine template
- `ql/pricingengines/barrier/analyticbarrierengine.hpp` — Analytic closed-form barrier option pricer
- `ql/pricingengines/barrier/analyticbarrierengine.cpp` — Implementation of analytic formulas from Haug's book
- `ql/pricingengines/barrier/mcbarrierengine.hpp` — Monte Carlo barrier option engine
- `ql/pricingengines/mcsimulation.hpp` — Generic Monte Carlo simulation framework

### Monte Carlo Components
- `ql/methods/montecarlo/montecarlomodel.hpp` — Core MC model that combines PathGenerator and PathPricer
- `ql/methods/montecarlo/pathgenerator.hpp` — Generates asset price paths using stochastic process discretization
- `ql/methods/montecarlo/pathpricer.hpp` — Base class for pricing single paths; BarrierPathPricer implemented in mcbarrierengine.hpp
- `ql/methods/montecarlo/brownianbridge.hpp` — Variance reduction technique for path generation
- `ql/methods/montecarlo/mctraits.hpp` — Trait classes for MC configuration (single-variate, RNG type)

### Stochastic Processes
- `ql/stochasticprocess.hpp` — Base StochasticProcess classes (multi-dimensional and 1-D variants)
- `ql/processes/blackscholesprocess.hpp` — GeneralizedBlackScholesProcess and variants (BlackScholes, Merton, Black, GarmanKohlagen)
- `ql/processes/eulerdiscretization.hpp` — Euler discretization scheme for process evolution

### Term Structures
- `ql/termstructures/yieldtermstructure.hpp` — Interest-rate term structure for discounting (risk-free rate, dividend yield)
- `ql/termstructures/volatility/equityfx/blackvoltermstructure.hpp` — Black volatility term structure for option volatility
- `ql/termstructures/volatility/equityfx/localvoltermstructure.hpp` — Local volatility term structure support
- `ql/termstructure.hpp` — Base TermStructure class
- `ql/quote.hpp` — Quote wrapper for observable market data (spot price)

## Dependency Chain

### Entry Point: NPV() Call
```
BarrierOption.NPV()                    [ql/instruments/barrieroption.hpp]
    ↓ inherited from OneAssetOption → Instrument
Instrument.NPV() const                 [ql/instrument.hpp:168-172]
    → calculate()  // line 169
```

### LazyObject Calculation Chain
```
Instrument.calculate() const            [ql/instrument.hpp:130-139]
    → if (!isExpired())
    → LazyObject::calculate()           [ql/patterns/lazyobject.hpp:255-266]
        → if (!calculated_ && !frozen_)
        → performCalculations()         [ql/patterns/lazyobject.hpp:260]
```

### Instrument Performs Calculation
```
Instrument.performCalculations() const  [ql/instrument.hpp:147-154]
    → engine_->reset()                  // Clear previous results
    → setupArguments(engine_->getArguments())  // BarrierOption::setupArguments()
    → engine_->getArguments()->validate()
    → engine_->calculate()              // Route to specific engine
    → fetchResults(engine_->getResults())
    → NPV_, errorEstimate_, valuationDate_ = results
```

### Analytic Pricing Path: AnalyticBarrierEngine
```
AnalyticBarrierEngine.calculate() const [ql/pricingengines/barrier/analyticbarrierengine.cpp:36-130+]
    → process_->x0()                    // Get current spot price
    → process_->riskFreeRate()->discount(Time)  // Query YieldTermStructure
    → process_->dividendYield()->discount(Time)
    → process_->blackVolatility()->blackVol(Time, Strike)  // Query BlackVolTermStructure
    → Analytical formula computation (A, B, C, D, E, F helper functions)
    → results_.value = computed NPV
```

### Monte Carlo Pricing Path: MCBarrierEngine
```
MCBarrierEngine.calculate() const       [ql/pricingengines/barrier/mcbarrierengine.hpp:78-89]
    → McSimulation<...>::calculate()    [ql/pricingengines/mcsimulation.hpp:159-207]
        → Creates MonteCarloModel:
        → mcModel_ = new MonteCarloModel(
            pathGenerator(),             // [mcbarrierengine.hpp:94-101]
            pathPricer(),               // [mcbarrierengine.hpp:233-270]
            sampleAccumulator,
            antitheticVariate)
        → Adds samples iteratively:
        → if (requiredTolerance != Null)
            → value(requiredTolerance, maxSamples)  // [mcsimulation.hpp:105-139]
        → else
            → valueWithSamples(requiredSamples)
    → results_.value = mcModel_->sampleAccumulator().mean()
    → results_.errorEstimate = (if allowed) errorEstimate()
```

### Path Generation: PathGenerator
```
MCBarrierEngine.pathGenerator() const    [ql/pricingengines/barrier/mcbarrierengine.hpp:94-101]
    → Creates PathGenerator<GSG>         [ql/methods/montecarlo/pathgenerator.hpp:81-107]
    → Passed (process_, timeGrid, gen, brownianBridge)

PathGenerator<GSG>::next() const        [ql/methods/montecarlo/pathgenerator.hpp:111-154]
    → For i = 1 to path.length():
        → generator_.nextSequence()     // Get random numbers from GSG
        → if (brownianBridge_)
            → bb_.transform(sequence)   // Apply variance reduction
        → process_->evolve(t, x, dt, dw)  // [ql/stochasticprocess.hpp:123-126]
            → GeneralizedBlackScholesProcess.evolve()
            → Computes x[i] = x[i-1] + drift*dt + diffusion*dw
            → drift = (r(t) - q(t) - σ²/2)
            → diffusion = σ(t)
        → path[i] = evolved value
    → Return path with weight
```

### Stochastic Process Evolution
```
GeneralizedBlackScholesProcess          [ql/processes/blackscholesprocess.hpp:54-109]
    QUERIES DURING EVOLUTION:
    → riskFreeRate()->discount(t)       // From YieldTermStructure
    → dividendYield()->discount(t)
    → blackVolatility()->blackVol(t, strike)  // From BlackVolTermStructure
    → x0_  // Quote: spot price

    EVOLUTION COMPUTATION:
    → drift(Time t, Real x) const        [blackscholesprocess.hpp:74]
        → r(t) - q(t) - σ²(t)/2
    → diffusion(Time t, Real x) const    [blackscholesprocess.hpp:76]
        → σ(t, S)
    → evolve(Time t0, Real x0, Time dt, Real dw)  [blackscholesprocess.hpp:85]
        → Applies discretization scheme
        → x_new = apply(x0, discretization.drift*dt + discretization.diffusion*dw)
```

### Monte Carlo Model Sample Accumulation
```
MonteCarloModel::addSamples(Size samples)  [ql/methods/montecarlo/montecarlomodel.hpp:92-125]
    → for (Size j = 1 to samples):
        → path = pathGenerator_->next()     // Get simulated path
        → price = (*pathPricer_)(path)      // [pathpricer.hpp:45]
            → BarrierPathPricer operator()  [ql/pricingengines/barrier/mcbarrierengine.hpp:140-160]
            → Checks if barrier is triggered along path
            → Applies payoff at expiration
            → Applies discount factors from YieldTermStructure
            → Returns path value
        → if (antitheticVariate_)
            → price2 = (*pathPricer_)(pathGenerator_->antithetic())
            → accumulate (price + price2)/2
        → else
            → accumulate price
    → sampleAccumulator_.add(price, path.weight)
```

### Path Pricing: BarrierPathPricer
```
BarrierPathPricer::operator()(const Path& path)  [ql/pricingengines/barrier/mcbarrierengine.hpp:140-160]
    → Check if barrier level H is touched along path:
        → if (barrierType_ == DownIn/DownOut && any path[i] <= barrier_)  → barrier triggered
        → if (barrierType_ == UpIn/UpOut && any path[i] >= barrier_)   → barrier triggered
    → If barrier triggered and option is "In":  → return rebate * discount_final
    → If barrier NOT triggered and option is "Out":  → return rebate * discount_final
    → Otherwise (barrier event matches type):
        → payoff = payoff_(path.back())      // PlainVanillaPayoff at expiration
        → return payoff * discount_final
    → Uses Brownian Bridge correction for improved accuracy
```

### Time Grid Creation
```
MCBarrierEngine::timeGrid() const        [ql/pricingengines/barrier/mcbarrierengine.hpp:217-228]
    → residualTime = process_->time(arguments_.exercise->lastDate())
    → if (timeSteps_ set)
        → return TimeGrid(residualTime, timeSteps_)
    → else if (timeStepsPerYear_ set)
        → steps = timeStepsPerYear_ * residualTime
        → return TimeGrid(residualTime, steps)
```

## Analysis

### Design Patterns Identified

1. **Lazy Evaluation with Caching**: The `LazyObject` pattern enables on-demand calculation where results are cached until dependencies change. The `update()` method notifies dependents when input structures (term structures, processes) change.

2. **Strategy Pattern**: `PricingEngine` is an abstract interface with multiple implementations (AnalyticBarrierEngine, MCBarrierEngine). The instrument delegates all pricing logic to the engine without knowing implementation details.

3. **Template Method Pattern**: `McSimulation` defines the MC algorithm's skeleton (calculate, value, valueWithSamples) while subclasses implement specific methods (pathGenerator, pathPricer, timeGrid).

4. **Trait Classes**: `MCTraits` (SingleVariate, MultiVariate) and RNG policies are used to customize MC behavior at compile-time without runtime overhead.

5. **Handle Pattern**: Uses smart pointers (`Handle<>`) to term structures and processes, enabling observable linking and automatic recalculation when market data changes.

### Component Responsibilities

**BarrierOption (Instrument)**
- Stores barrier parameters (type, level, rebate)
- Implements `setupArguments()` to populate engine arguments
- Delegates all valuation to the pricing engine via `NPV()` call

**PricingEngine Hierarchy**
- `AnalyticBarrierEngine`: Computes closed-form barrier option prices using Haug formulas
  - Direct queries of term structures for drift, discount, volatility
  - No path simulation required
  - Fast but limited to specific models (Black-Scholes)

- `MCBarrierEngine`: Monte Carlo simulation for barrier options
  - Creates PathGenerator and PathPricer on demand
  - Manages simulation parameters (steps, samples, tolerance, brownian bridge, antithetic variates)
  - Flexible: can price with any stochastic process

**GeneralizedBlackScholesProcess**
- Encapsulates stochastic evolution dynamics: `dx = (r-q-σ²/2)dt + σ dW`
- Acts as **data provider** for term structures:
  - Queries `YieldTermStructure` for risk-free rate r(t) and dividend yield q(t)
  - Queries `BlackVolTermStructure` for volatility σ(t, K)
- Implements `evolve()` to step the state forward: `x[i+1] = f(x[i], random_shock)`
- Observable: notifies engines when underlying, rates, or volatility change

**PathGenerator**
- Converts random number sequence to asset price path
- Uses `StochasticProcess.evolve()` to compute increments
- Supports variance reduction: Brownian Bridge, antithetic variates
- Works with any 1-D process (not tied to Black-Scholes)

**PathPricer**
- Computes option value for a single simulated path
- BarrierPathPricer: checks barrier levels, applies payoff, discounts cash flows
- Decoupled from path generation (single responsibility)

**Term Structures**
- `YieldTermStructure`: provides discount factors D(t) = e^{-∫r(s)ds}
  - Used for: risk-free discounting, dividend yield discounting
  - Observable: when evaluationDate() or market data changes, notifies dependents

- `BlackVolTermStructure`: provides implied volatility σ(t, K)
  - Used for: diffusion coefficient in path evolution
  - May depend on strike (local volatility) or maturity only (implied volatility surfaces)

### Data Flow

**Entry to Calculation:**
1. User calls `barrier_option.NPV()`
2. Instrument.NPV() triggers `calculate()` (lazy evaluation)
3. Instrument.performCalculations() delegates to `engine_->calculate()`

**Analytic Path:**
1. Engine queries process for: spot, rates, volatility at various maturities
2. Applies closed-form formulas using CumulativeNormalDistribution
3. Returns exact (within numerical precision) barrier option price

**Monte Carlo Path:**
1. Setup phase:
   - Create TimeGrid based on maturity and parameter (timeSteps or timeStepsPerYear)
   - Create PathGenerator(process, timeGrid, RNG, brownianBridge)
   - Create PathPricer (BarrierPathPricer or BiasedBarrierPathPricer)
   - Instantiate MonteCarloModel with these components

2. Simulation phase:
   - Generate N sample paths:
     - PathGenerator draws random increments
     - Process.evolve() applies increments using drift/diffusion from term structures
     - PathPricer evaluates barrier condition and computes path value
   - Accumulate statistics (mean, variance, error estimate)
   - If error > tolerance and samples < maxSamples: generate more paths

3. Result phase:
   - Return accumulated mean as NPV
   - Return error estimate (if RNG supports it)

### Interface Contracts

**Instrument ↔ PricingEngine:**
- Instrument.performCalculations() calls:
  - `engine_->reset()` — clear results
  - `engine_->getArguments()` — get mutable arguments structure
  - `setupArguments(args)` — populate engine-specific arguments
  - `args->validate()` — check input validity
  - `engine_->calculate()` — invoke pricing
  - `engine_->getResults()` — extract results
  - `fetchResults(results)` — transfer to instrument member variables

**PricingEngine ↔ StochasticProcess:**
- Process must implement:
  - `x0()` — initial state (spot price)
  - `drift(t, x)` — drift coefficient
  - `diffusion(t, x)` — volatility coefficient
  - `evolve(t, x, dt, dw)` — one-step evolution
  - `time(Date)` — convert date to process time
  - Observable interface (update when dependencies change)

**PathGenerator ↔ StochasticProcess:**
- Path generator queries process:
  - `evolve(t, path[i-1], dt, dw)` — advance one time step
  - Receives evolved path value
  - No knowledge of how process internally queries term structures

**StochasticProcess ↔ Term Structures:**
- Process holds handles to:
  - `riskFreeRate_: Handle<YieldTermStructure>` — discount, z(T)
  - `dividendYield_: Handle<YieldTermStructure>` — convenience yield
  - `blackVolatility_: Handle<BlackVolTermStructure>` — σ(t, K)
- Queries during drift/diffusion computation
- Registers as observer: when market data changes, process notifies engines

**McSimulation ↔ MonteCarloModel ↔ Statistics:**
- McSimulation::calculate() creates MonteCarloModel
- MonteCarloModel::addSamples() calls pathGenerator->next(), pathPricer(path), accumulates to stats_type
- stats_type (Statistics) maintains running mean, variance, error estimate
- McSimulation queries stats to check convergence (errorEstimate() < tolerance)

## Summary

The QuantLib barrier option pricing chain implements a sophisticated multi-layered architecture combining **lazy evaluation** (LazyObject), **strategy pattern** (multiple engines), and **Monte Carlo simulation** (with variance reduction).

A call to `BarrierOption.NPV()` propagates through the Instrument/LazyObject calculation framework to the selected PricingEngine. Analytic engines query the GeneralizedBlackScholesProcess directly for closed-form computation, while Monte Carlo engines orchestrate PathGenerator (which evolves the stochastic process using term structure data) with PathPricer to simulate and value sample paths. Term structures (YieldTermStructure, BlackVolTermStructure) serve as data providers throughout, enabling market-data-driven pricing with automatic recalculation on market data changes through the Observable/Observer pattern.


# QuantLib Barrier Option Pricing Architecture Analysis

## Files Examined

### Core Instrument Classes
- **ql/instruments/barrieroption.hpp** — Barrier option instrument definition; inherits from OneAssetOption; maintains barrier type, barrier level, and rebate
- **ql/instruments/oneassetoption.hpp** — Base class for single-asset options; defines arguments/results/engine interface
- **ql/instrument.hpp** — Abstract Instrument base class inheriting from LazyObject; implements NPV() and performCalculations() dispatch to pricing engine
- **ql/patterns/lazyobject.hpp** — Framework for lazy evaluation and result caching; implements calculate() → performCalculations() pattern with observable/observer notification

### Pricing Engine Classes (Analytic)
- **ql/pricingengines/barrier/analyticbarrierengine.hpp** — Closed-form barrier option pricing; inherits from BarrierOption::engine (GenericEngine template)
- **ql/pricingengines/barrier/analyticbarrierengine.cpp** — Implementation of analytic formulas for all barrier types (DownIn, UpIn, DownOut, UpOut); queries GeneralizedBlackScholesProcess for spot, volatility, drift, and discount factors

### Pricing Engine Classes (Monte Carlo)
- **ql/pricingengines/barrier/mcbarrierengine.hpp** — Monte Carlo barrier engine; inherits from both BarrierOption::engine and McSimulation<SingleVariate,RNG,S>
- **ql/pricingengines/barrier/mcbarrierengine.hpp (continued)** — Implements pathGenerator() → creates PathGenerator<GSG> with GeneralizedBlackScholesProcess
- **ql/pricingengines/barrier/mcbarrierengine.hpp (continued)** — Implements pathPricer() → creates BarrierPathPricer that evaluates barrier knockout at each time step

### Monte Carlo Framework
- **ql/pricingengines/mcsimulation.hpp** — Base template McSimulation<MC,RNG,S>; provides value() and calculate() methods; orchestrates path generation and pricing
- **ql/methods/montecarlo/montecarlomodel.hpp** — MonteCarloModel<MC,RNG,S> template; aggregates path_generator_type and path_pricer_type; addSamples() iterates: generates path → prices path → accumulates statistics
- **ql/methods/montecarlo/pathgenerator.hpp** — PathGenerator<GSG> template; takes StochasticProcess and TimeGrid; generates next() returns Sample<Path> with correlated random increments

### Stochastic Process Classes
- **ql/processes/blackscholesprocess.hpp** — GeneralizedBlackScholesProcess; implements StochasticProcess1D interface; aggregates YieldTermStructure (risk-free rate, dividend yield), BlackVolTermStructure (volatility), and Quote (spot price)
- **ql/stochasticprocess.hpp** — StochasticProcess1D base class; defines drift(), diffusion(), evolve() interface; used by PathGenerator to evolve asset prices

### Term Structure Classes
- **ql/termstructures/yieldtermstructure.hpp** — YieldTermStructure base class; provides discount factors for different maturities
- **ql/termstructures/volatility/equityfx/blackvoltermstructure.hpp** — BlackVolTermStructure base class; provides implied volatility surface/curve

### Engine Framework
- **ql/pricingengine.hpp** — PricingEngine interface with arguments/results; GenericEngine<Args,Results> template provides reset(), getArguments(), getResults()

## Dependency Chain

### Entry Point: NPV Calculation
```
1. BarrierOption.NPV()                          [ql/instrument.hpp:168]
   ↓
2. Instrument.calculate()                       [ql/instrument.hpp:130]
   (checks isExpired(); if not, calls LazyObject::calculate())
   ↓
3. LazyObject.calculate()                       [ql/patterns/lazyobject.hpp:255]
   (if not calculated_ && not frozen_, sets calculated_=true, calls performCalculations())
   ↓
4. Instrument.performCalculations()             [ql/instrument.hpp:147]
   - engine_->reset()                           [clears results_]
   - setupArguments(engine_->getArguments())    [populates BarrierOption::arguments with payoff, exercise, barrier, rebate]
   - engine_->getArguments()->validate()        [validates arguments]
   - engine_->calculate()                       [engine-specific implementation]
   - fetchResults(engine_->getResults())        [extracts NPV_, errorEstimate_, valuationDate_, additionalResults_]
   ↓
5. Results are cached and returned
```

### Analytic Engine Path
```
AnalyticBarrierEngine.calculate()               [ql/pricingengines/barrier/analyticbarrierengine.cpp:36]
├─ Extract arguments (barrierType, barrier, rebate, payoff)
├─ Query process:
│  ├─ process_->x0()                           [current spot price from Quote]
│  ├─ process_->riskFreeRate()                 [YieldTermStructure for discount factors]
│  ├─ process_->dividendYield()                [YieldTermStructure for dividend discounting]
│  └─ process_->blackVolatility()              [BlackVolTermStructure for volatility]
├─ Apply closed-form formulas (based on barrier type & option type):
│  - Compute helper functions A(), B(), C(), D(), E(), F()
│  - Each uses spot, strike, volatility, rates, time to expiry
│  - Uses standard normal CDF from blackVolatility surface
└─ Return results_.value [analytical price]
```

### Monte Carlo Engine Path
```
MCBarrierEngine.calculate()                     [ql/pricingengines/barrier/mcbarrierengine.hpp:78]
├─ Validate spot > 0, barrier not triggered
├─ McSimulation::calculate(tolerance, samples, maxSamples)
│  [ql/pricingengines/mcsimulation.hpp:159]
│  ├─ Loop: while error > tolerance && samples < maxSamples:
│  │  └─ mcModel_->addSamples(batchSize)
│  │     [ql/methods/montecarlo/montecarlomodel.hpp:92]
│  │     ├─ For each sample j:
│  │     │  ├─ Path path = pathGenerator_->next()
│  │     │  │  [ql/methods/montecarlo/pathgenerator.hpp:next()]
│  │     │  │  ├─ Creates timeGrid from timeSteps/timeStepsPerYear
│  │     │  │  ├─ For each time step in grid:
│  │     │  │  │  ├─ Query process for drift(t, x):
│  │     │  │  │  │  └─ Uses riskFreeRate, dividendYield, volatility at time t
│  │     │  │  │  ├─ Query process for diffusion(t, x):
│  │     │  │  │  │  └─ Uses blackVolatility at time t
│  │     │  │  │  ├─ Generate random normal increment dW
│  │     │  │  │  ├─ Evolve: x_new = process_->evolve(t, x, dt, dW)
│  │     │  │  │  │  └─ x_new = x * exp(drift*dt + volatility*dW)
│  │     │  │  │  └─ Apply Brownian bridge correction if enabled
│  │     │  │  └─ Return Sample<Path> with all time steps
│  │     │  │
│  │     │  ├─ Real price = (*pathPricer_)(path)
│  │     │  │  [BarrierPathPricer::operator()]
│  │     │  │  ├─ Check if barrier triggered at any time step
│  │     │  │  ├─ If triggered: return rebate (discounted)
│  │     │  │  ├─ If not triggered: apply payoff at maturity
│  │     │  │  │  └─ return (spot[T] - strike)+ * discount(T)
│  │     │  │  └─ Return payoff * discount factor
│  │     │  │
│  │     │  └─ sampleAccumulator_.add(price)
│  │     │     [accumulates mean, variance, running statistics]
│  │     │
│  ├─ Check convergence: errorEstimate = sqrt(variance/samples)
│  └─ If converged or maxSamples reached: exit loop
│
└─ results_.value = mcModel_->sampleAccumulator().mean()
   results_.errorEstimate = sampleAccumulator().errorEstimate()
```

## Design Patterns and Architecture

### 1. Lazy Evaluation Pattern (LazyObject)
- **Purpose**: Defer calculations until needed; cache results; notify observers on recalculation
- **Implementation**:
  - `calculated_` flag tracks whether performCalculations() has been called
  - `calculate()` checks flag and calls performCalculations() only once unless recalculate() called
  - Derived classes register with observable dependencies (spot quote, term structures)
  - When dependency changes, notify() sets calculated_=false, triggering recalculation on next NPV() call

### 2. Strategy Pattern (Multiple Engines)
- **Purpose**: Support different pricing methodologies (analytic vs Monte Carlo)
- **Abstraction**: All engines inherit from GenericEngine<Arguments, Results>
- **Interface Contract**:
  - arguments_ struct populated by setupArguments()
  - results_ struct filled by engine calculate()
  - Engine.calculate() is pure virtual; subclasses implement algorithm-specific logic

### 3. Template Method Pattern (McSimulation)
- **Purpose**: Define skeleton of Monte Carlo algorithm; let subclasses customize path generation
- **Flow**:
  1. McSimulation::calculate() implements outer loop (sampling until convergence)
  2. Subclass must implement: pathGenerator(), pathPricer(), timeGrid()
  3. MonteCarloModel orchestrates: generate path → price path → accumulate statistics
  4. Results accessible via sampleAccumulator() for error estimation

### 4. Observable/Observer Pattern (Notification)
- **Purpose**: Propagate dependency changes through pricing chain
- **Usage**:
  - Instrument.setPricingEngine() registers as observer with engine
  - Engine registers with GeneralizedBlackScholesProcess
  - Process registers with YieldTermStructure, BlackVolTermStructure, Quote
  - When spot quote changes → Process notifies → Engine notifies → Instrument marks calculated_=false
  - Next NPV() call triggers recalculation

### 5. Policy-Based Design (Template Parameters)
- **McSimulation<MC, RNG, S>**:
  - MC: trait class defining single vs multi-variate
  - RNG: random number generator (PseudoRandom vs LowDiscrepancy)
  - S: statistics accumulator type
- **PathGenerator<GSG>**:
  - GSG: Gaussian sequence generator (instantiated by RNG::make_sequence_generator)
  - Decouples path evolution from random number source

## Component Responsibilities

### GeneralizedBlackScholesProcess (Core Model)
**Responsibilities**:
- Encapsulate stochastic process parameters (spot, rates, volatility)
- Implement StochasticProcess1D interface: drift(), diffusion(), evolve()
- Notify observers when parameters change
- Provide accessors: x0() [spot], riskFreeRate(), dividendYield(), blackVolatility()

**Data**:
- Handle<Quote> x0_ — spot price (observable)
- Handle<YieldTermStructure> riskFreeRate_ — risk-free discount curve
- Handle<YieldTermStructure> dividendYield_ — dividend discount curve
- Handle<BlackVolTermStructure> blackVolatility_ — implied volatility surface

**Interface**:
- Real drift(Time t, Real x) — compute μ(t, S_t) = (r-q-σ²/2)
- Real diffusion(Time t, Real x) — compute σ(t, S_t)
- Real evolve(Time t0, Real x0, Time dt, Real dw) — discrete evolution step

### BarrierOption (Instrument)
**Responsibilities**:
- Define option characteristics (barrier, rebate, payoff, exercise)
- Implement setupArguments() to populate engine arguments
- Implement fetchResults() to extract engine results
- Delegate pricing to installed engine

**Data**:
- Barrier::Type barrierType_ (DownIn, UpIn, DownOut, UpOut)
- Real barrier_ — barrier level
- Real rebate_ — payment if barrier touched
- shared_ptr<StrikedTypePayoff> payoff_ — option payoff structure

### AnalyticBarrierEngine (Closed-Form Pricing)
**Responsibilities**:
- Compute barrier option price using analytical formulae
- Query process for all necessary market data
- Apply barrier + payoff logic via helper functions

**Computation**:
- Helper methods A(), B(), C(), D(), E(), F() implement Haug's formulae
- All depend on: spot, strike, volatility, rates, time, barrier, rebate
- Use CumulativeNormalDistribution for standard normal CDF

### MCBarrierEngine (Monte Carlo Pricing)
**Responsibilities**:
- Generate sample paths from stochastic process
- Price each path under barrier knockout rule
- Estimate NPV via mean and error via standard error

**Data**:
- process_ — GeneralizedBlackScholesProcess
- timeSteps_, timeStepsPerYear_ — path discretization
- seed_ — random number generator seed
- brownianBridge_ — use Brownian bridge correction for barrier monitoring

### PathGenerator (Path Evolution)
**Responsibilities**:
- Generate random asset price paths using stochastic process
- Apply optional Brownian bridge for improved barrier accuracy
- Produce correlated increments via Gaussian sequence generator

**Data**:
- TimeGrid timeGrid_ — pre-computed time points
- GSG generator_ — Gaussian random number generator
- bool brownianBridge_ — enable bridge correction
- StochasticProcess process_ — dynamics for drift/diffusion

**Process**:
1. For each time step dt in timeGrid:
2. Query process: μ = drift(t, S_t), σ = diffusion(t, S_t)
3. Generate random: dW ~ N(0, dt)
4. Evolve: S_{t+dt} = process_->evolve(S_t, dW)

### BarrierPathPricer (Path Payoff)
**Responsibilities**:
- Evaluate barrier knockout condition over path lifetime
- Compute discounted payoff

**Logic**:
```
for each time step in path:
    if spot[t] crosses barrier:
        return rebate * discount(t)
return payoff(spot[T]) * discount(T)
```

### MonteCarloModel (Sampling Orchestration)
**Responsibilities**:
- Coordinate path generation and pricing
- Accumulate statistics from multiple samples
- Manage control variates (optional variance reduction)

**Data**:
- shared_ptr<path_generator_type> pathGenerator_ — generates paths
- shared_ptr<path_pricer_type> pathPricer_ — prices each path
- stats_type sampleAccumulator_ — running statistics (mean, variance)

**addSamples(Size n)**:
```
for i = 1 to n:
    path = pathGenerator_->next()
    price = (*pathPricer_)(path)
    if controlVariate:
        price += cvOptionValue - (*cvPathPricer_)(path)
    sampleAccumulator_.add(price)
```

### McSimulation (Convergence Loop)
**Responsibilities**:
- Implement outer loop for adaptive sampling
- Achieve convergence to specified tolerance
- Provide error estimates

**calculate(tolerance, requiredSamples, maxSamples)**:
```
while sampleAccumulator_.errorEstimate() > tolerance:
    if samples >= maxSamples: break
    batchSize = max(requiredSamples, 1024)
    mcModel_->addSamples(batchSize)
    samples += batchSize
return sampleAccumulator_.mean()
```

## Data Flow Analysis

### Initialization Phase
```
BarrierOption.BarrierOption(type, barrier, rebate, payoff, exercise)
└─ setPricingEngine(engine)
   ├─ engine_.registerWith(process)
   ├─ process.registerWith(spot quote)
   ├─ process.registerWith(riskFreeRate curve)
   ├─ process.registerWith(dividendYield curve)
   └─ process.registerWith(blackVolatility surface)
```

### Price Query Phase (NPV Call)
```
option.NPV()
└─ calculate()  [LazyObject::calculate()]
   ├─ Check: if calculated_ && !frozen_: return
   ├─ If expired: setupExpired() → set NPV_=0
   ├─ Else: performCalculations()
   │  └─ engine.calculate()
   │     ├─ if AnalyticBarrierEngine:
   │     │  └─ compute via closed-form (instant)
   │     └─ if MCBarrierEngine:
   │        └─ McSimulation::calculate()
   │           ├─ Loop until converged:
   │           │  ├─ pathGenerator->next()
   │           │  │  ├─ process.drift() → queries riskFreeRate, dividendYield curves
   │           │  │  ├─ process.diffusion() → queries blackVolatility
   │           │  │  └─ evolve path using GeneralizedBlackScholesProcess
   │           │  └─ pathPricer->operator()(path) → evaluate barrier, compute payoff
   │           └─ Mean of accumulated prices
   ├─ fetchResults(engine.results_)
   └─ Return NPV_
```

### Recalculation Trigger
```
spot_quote.setValue(newPrice)
└─ spot_quote.notifyObservers()
   └─ GeneralizedBlackScholesProcess.update()
      └─ notifyObservers()
         └─ AnalyticBarrierEngine.update()  [or MCBarrierEngine.update()]
            └─ notifyObservers()
               └─ BarrierOption.update()
                  └─ LazyObject.update()
                     └─ setCalculated(false)
                        └─ Next NPV() call triggers fresh calculation
```

## Summary

QuantLib's barrier option pricing architecture demonstrates sophisticated design patterns for supporting both analytic and Monte Carlo pricing methodologies. The core innovation is the **Lazy Object pattern** combined with **Observable/Observer notification**, enabling transparent caching and automatic recalculation when market data changes.

The **Generalized Black-Scholes Process** serves as the central abstraction that decouples the option pricing logic from stochastic dynamics, enabling reuse across all single-asset exotic options. The **McSimulation framework** provides a generic Monte Carlo template that elegantly separates path generation (via strategy pattern with pluggable RNG/traits) from path pricing, allowing arbitrarily complex derivative pricing by only implementing pathPricer() and timeGrid() methods.

The **two-level engine strategy**—analytical formulas vs. Monte Carlo sampling—reflects practical quantitative finance: analytic engines provide fast, precise pricing for standard barrier options, while Monte Carlo engines enable pricing of non-standard barriers, time-varying parameters, and validates analytical results under controlled variance reduction.

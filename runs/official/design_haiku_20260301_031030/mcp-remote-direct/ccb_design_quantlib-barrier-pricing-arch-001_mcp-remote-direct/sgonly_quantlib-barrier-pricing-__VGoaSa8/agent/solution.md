# QuantLib Barrier Option Pricing Chain: Architecture Analysis

## Files Examined

### Entry Point & Lazy Object Pattern
- **ql/patterns/lazyobject.hpp** — Framework for calculation on demand and result caching. Defines the `calculate()` pattern that checks cached status and calls `performCalculations()` when needed
- **ql/instrument.hpp** — Abstract instrument base class inheriting from LazyObject. Implements NPV() method which triggers lazy calculation, and `performCalculations()` which delegates to pricing engine

### Instruments Layer
- **ql/instruments/barrieroption.hpp** — BarrierOption instrument class inheriting from OneAssetOption. Defines arguments (barrier type, barrier level, rebate) and engine interface
- **ql/instruments/oneassetoption.hpp** — Base class for single-asset options, provides Greeks computation and results caching

### Pricing Engines - Analytic Path
- **ql/pricingengines/barrier/analyticbarrierengine.hpp** — Analytic pricing engine using closed-form formulas (Haug option pricing formulas, E.G. Haug, McGraw-Hill, p.69+)
- **ql/pricingengines/barrier/analyticbinarybarrierengine.hpp** — Binary barrier option engine
- **ql/pricingengines/barrier/analyticdoublebarrierengine.hpp** — Double barrier option engine (Ikeda-Kunitomo series)
- **ql/pricingengines/barrier/analyticpartialtime­barrieroptionengine.hpp** — Partial-time barrier option engine

### Pricing Engines - Monte Carlo Path
- **ql/pricingengines/barrier/mcbarrierengine.hpp** — MCBarrierEngine template class inheriting from both BarrierOption::engine and McSimulation<SingleVariate,RNG,S>. Implements path generation via GeneralizedBlackScholesProcess

### Monte Carlo Framework
- **ql/pricingengines/mcsimulation.hpp** — Base template class McSimulation that orchestrates the MC loop: creates pathGenerator, generates sample paths, prices each path via pathPricer, accumulates statistics
- **ql/methods/montecarlo/montecarlomodel.hpp** — MonteCarloModel template: generic MC simulation loop that repeatedly calls `pathGenerator_->next()`, prices path via `pathPricer_`, and accumulates results in statistics accumulator
- **ql/methods/montecarlo/mctraits.hpp** — Trait classes defining MC model characteristics (SingleVariate vs MultiVariate, RNG type, path_generator_type, path_pricer_type)

### Stochastic Process Layer
- **ql/processes/blackscholesprocess.hpp** — GeneralizedBlackScholesProcess: stochastic process implementing dln(S) = (r(t) - q(t) - σ²/2)dt + σdW_t. Uses three term structures internally: risk-free rate, dividend yield, and Black volatility
- **ql/processes/blackscholesprocess.hpp** — BlackScholesProcess, BlackScholesMertonProcess, BlackProcess, GarmanKohlagenProcess: specializations of GeneralizedBlackScholesProcess

### Term Structure Layer
- **ql/termstructures/yieldtermstructure.hpp** — YieldTermStructure: interest rate term structure for risk-free rates and dividend yields. Provides interest rate queries at different times
- **ql/termstructures/volatility/equityfx/blackvoltermstructure.hpp** — BlackVolTermStructure: Black volatility term structure (σ(T,K) surface). Provides volatility lookups by time and strike
- **ql/termstructures/volatility/equityfx/localvolsurface.hpp** — LocalVolTermStructure: local volatility surface, can be derived from Black vol surface

### Supporting Components
- **ql/pricingengines/barrier/discretizedbarrieroption.hpp** — DiscretizedBarrierOption: barrier payoff evaluated on discrete time grid for tree/FD methods
- **ql/methods/finitedifferences/solvers/fdblackscholessolver.hpp** — Finite difference solver for Black-Scholes equations (alternative to MC)

## Dependency Chain

### 1. **Entry Point: BarrierOption.NPV()**
```
BarrierOption::NPV()
└─→ Instrument::NPV() [line 168]
    └─→ calculate()  [line 169]
```

### 2. **LazyObject Calculate Pattern**
```
Instrument::calculate()  [line 130-139]
├─→ isExpired() check
└─→ if not expired:
    └─→ LazyObject::calculate()  [line 255-266]
        └─→ if not cached and not frozen:
            └─→ performCalculations()
```

### 3. **Engine Invocation**
```
Instrument::performCalculations()  [line 147-154]
├─→ engine_->reset()
├─→ setupArguments(engine_->arguments)  [fills BarrierOption::arguments]
├─→ engine_->arguments->validate()
├─→ engine_->calculate()  [delegates to specific engine]
└─→ fetchResults(engine_->results)  [retrieves NPV, Greeks, errorEstimate]
```

### 4. **Pricing Engine Routes**

#### 4a. **Analytic Engine Path (AnalyticBarrierEngine)**
```
AnalyticBarrierEngine::calculate()
├─→ queries GeneralizedBlackScholesProcess:
│   ├─→ process_->x0()  [spot price from Quote]
│   ├─→ process_->riskFreeRate()  [YieldTermStructure query]
│   ├─→ process_->dividendYield()  [YieldTermStructure query]
│   └─→ process_->blackVolatility()  [BlackVolTermStructure query]
├─→ applies closed-form Haug formulas
└─→ returns NPV, Greeks directly
```

#### 4b. **Monte Carlo Engine Path (MCBarrierEngine)**
```
MCBarrierEngine::calculate()  [line 78-89]
├─→ McSimulation::calculate(requiredTolerance, requiredSamples, maxSamples)
│   └─→ while error > tolerance:
│       └─→ mcModel_->addSamples(nextBatch)
│           └─→ MonteCarloModel::addSamples()
│               ├─→ loop samples = 1 to nextBatch:
│               │   ├─→ sample_type path = pathGenerator_->next()
│               │   │   └─→ generates one sample path from GeneralizedBlackScholesProcess
│               │   │       ├─→ initializes from x0 (spot)
│               │   │       ├─→ for each time step t_i:
│               │   │       │   ├─→ drift(t, x) = r(t) - q(t) - σ²(t,x)/2  [uses riskFreeRate, dividendYield]
│               │   │       │   ├─→ diffusion(t, x) = σ(t, x)  [uses blackVolatility]
│               │   │       │   └─→ evolve(t0, x0, dt, dw)  [numerical step]
│               │   │       └─→ returns S(T) along path
│               │   ├─→ result_type price = pathPricer_(path)
│               │   │   └─→ BarrierPathPricer evaluates payoff with barrier check
│               │   └─→ sampleAccumulator_.add(price)
│               └─→ error = sampleAccumulator_.errorEstimate()
└─→ results_.value = mcModel_->sampleAccumulator().mean()
```

### 5. **Stochastic Process Initialization**
```
GeneralizedBlackScholesProcess constructor:
├─→ Handle<Quote> x0_  [current spot price]
├─→ Handle<YieldTermStructure> riskFreeRate_  [r(t) term structure]
├─→ Handle<YieldTermStructure> dividendYield_  [q(t) term structure]
└─→ Handle<BlackVolTermStructure> blackVolatility_  [σ(t,K) volatility surface]
```

### 6. **Term Structure Queries During Path Generation**
```
For each time step in path generation:

drift(t, x) calls:
├─→ riskFreeRate_->forwardRate(t, t+dt)  [YieldTermStructure]
└─→ dividendYield_->forwardRate(t, t+dt)  [YieldTermStructure]

diffusion(t, x) calls:
└─→ blackVolatility_->blackVol(t, K=x)  [BlackVolTermStructure]
    [or localVolatility_->localVol(t, x) if using local vol]
```

### 7. **Discretization**
```
Euler discretization (default) or others:
├─→ Converts continuous SDE: dS = μ dt + σ dW
└─→ To discrete step: S(t+dt) = S(t) * exp(drift*dt + diffusion*sqrt(dt)*Z)
    where Z ~ N(0,1) random normal from RNG
```

## Analysis

### Design Patterns Identified

1. **Lazy Evaluation Pattern (LazyObject)**
   - Defers calculation until results needed via NPV() call
   - Caches results to avoid redundant computation
   - Observable/Observer pattern triggers recalculation when inputs change
   - Prevents cycles and manages notification propagation

2. **Strategy Pattern (Pricing Engines)**
   - Instrument independent of pricing method: analytic vs. Monte Carlo vs. FD vs. binomial
   - Each engine encapsulates specific algorithm
   - Engine interface standardized: `calculate()` → populate `results`

3. **Template Policy Pattern (McSimulation/MonteCarloModel)**
   - MC framework is generic across RNG types (PseudoRandom, LowDiscrepancy)
   - Single vs. MultiVariate templates in mctraits
   - Path generator and path pricer are template parameters

4. **Handle/Repository Pattern (Term Structures)**
   - Handle<YieldTermStructure> provides lazy evaluation + change notification
   - Multiple term structures can share observables (e.g., Quote updates trigger recalculation)
   - RelinkableHandle allows term structure updates

5. **Factory Pattern (MakeMCBarrierEngine)**
   - Builder pattern for complex engine construction
   - Named parameters (withSteps, withBrownianBridge, etc.)

### Component Responsibilities

| Component | Role |
|-----------|------|
| **BarrierOption** | Instrument specification: payoff, barrier level, rebate, exercise date |
| **OneAssetOption** | Single-asset option base: Greeks computation, results caching |
| **Instrument** | NPV trigger, engine delegation, results aggregation |
| **LazyObject** | Lazy calculation framework: on-demand compute + caching |
| **AnalyticBarrierEngine** | Closed-form pricing: direct formula evaluation (fast, exact) |
| **MCBarrierEngine** | Monte Carlo pricing: path simulation + sampling (flexible, slower) |
| **McSimulation** | MC orchestration: tolerance loop, sample management |
| **MonteCarloModel** | Core MC loop: generate paths, price paths, accumulate statistics |
| **GeneralizedBlackScholesProcess** | Stochastic dynamics: drift/diffusion queries, SDE discretization |
| **YieldTermStructure** | Interest rate surface: r(t), q(t) for any future date |
| **BlackVolTermStructure** | Volatility surface: σ(t,K) for any date/strike combination |
| **PathGenerator** | Random path generation: creates sample asset price trajectories |
| **PathPricer** | Barrier payoff evaluation: checks barrier hit, computes option payoff |

### Data Flow Description

1. **Setup Phase**
   - User constructs BarrierOption with payoff, exercise, barrier params
   - User supplies GeneralizedBlackScholesProcess (connects to term structures + Quote)
   - User sets pricing engine (AnalyticBarrierEngine or MCBarrierEngine)

2. **NPV() Call Phase**
   - NPV() → calculate() checks cache
   - If not cached: setupArguments() packs barrier params + underlyings into engine arguments
   - Engine::calculate() executes pricing logic

3. **Analytic Path**
   - Queries current values: S₀ from Quote, r(T) from YieldTermStructure, σ(T,K) from BlackVolTermStructure
   - Applies mathematical formula (e.g., Reiner-Rubinstein formula)
   - Returns NPV + Greeks

4. **Monte Carlo Path**
   - Initializes timeGrid based on exercise date
   - For each sample (until tolerance met):
     - PathGenerator creates sample path:
       - T = 0: S = x₀ (current spot)
       - For each time step t_i → t_{i+1}:
         - Queries drift from term structures at t_i
         - Queries diffusion (volatility) from term structures at t_i
         - Generates random normal Z ~ N(0,1)
         - Computes S(t_{i+1}) = S(t_i) * exp(...)
     - PathPricer evaluates barrier condition at intermediate times
     - If barrier hit: payoff = rebate; else: payoff = max(S(T) - K, 0)
     - Accumulate payoff in statistics
   - Returns mean price + error estimate

5. **Term Structure Integration**
   - YieldTermStructure converts calendar dates → continuous times → interest rates
   - BlackVolTermStructure interpolates volatility surface (time × strike)
   - Handles are observers: when Quote changes, term structures marked dirty
   - Instrument LazyObject notified → recalculate flag set
   - Next NPV() call triggers fresh pricing with new parameters

### Interface Contracts Between Components

**Instrument ↔ Engine**
- Instrument::setupArguments() fills BarrierOption::arguments
- Engine::calculate() reads arguments, writes BarrierOption::results
- Results must contain: value (NPV), errorEstimate, valuationDate

**Engine ↔ GeneralizedBlackScholesProcess**
- Engine queries: x0(), drift(t,x), diffusion(t,x), evolve(t0,x0,dt,dw)
- Process aggregates: Quote, YieldTermStructure(2), BlackVolTermStructure

**McSimulation ↔ MonteCarloModel**
- McSimulation defines virtual pathGenerator(), pathPricer(), timeGrid()
- MonteCarloModel invokes these; McSimulation instantiates MonteCarloModel with implementations

**PathGenerator ↔ StochasticProcess**
- PathGenerator wraps GeneralizedBlackScholesProcess
- Queries process drift/diffusion at each time step
- Uses discretization scheme (Euler, Milstein, etc.)

**PathPricer ↔ Option Arguments**
- Receives path (sequence of S values)
- Reads from option arguments: barrier type, level, rebate, payoff, exercise
- Returns discounted payoff

## Summary

The QuantLib barrier option pricing chain exemplifies **layered architecture with inversion of control**:

1. **Instrument layer** (BarrierOption) abstracts the financial product
2. **Pricing engine layer** (Analytic/MC) abstracts calculation method
3. **Monte Carlo framework** (McSimulation/MonteCarloModel/PathGenerator) abstracts simulation mechanics
4. **Stochastic process layer** (GeneralizedBlackScholesProcess) abstracts market dynamics
5. **Term structure layer** (YieldTermStructure/BlackVolTermStructure) abstracts market data

**NPV() propagates lazily:** each component calculates only when needed, queries dependencies on-demand, and caches results. **Term structures act as time-indexed market data repositories**, queried during path generation to inject current market conditions into SDE evolution. **The MC framework achieves flexibility through templates and policies**, enabling different RNG types and sample accumulation strategies without modifying core logic.


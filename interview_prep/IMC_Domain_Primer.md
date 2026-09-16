# IMC domain primer — the minimum an engineer needs

Written after round 2 (2026-09-16), where the Python, project and tricky-question blocks went fine
and the **domain questions did not**: *what is a stock, what is an option, what is market making.*

This gap was flagged in the req itself — *"Experience working with financial data is a must"* — so
it will come back. The final round has a 30-minute intro with the **Technology Lead**, which is
exactly where "do you understand what we do" lands.

**You are not being hired as a trader.** Nobody expects pricing models. What they expect is that
you can hold a conversation about the business your code serves, and that you're curious rather
than indifferent. Two crisp sentences plus "I haven't done X" beats a vague paragraph.

---

# 1. The three you fumbled — learn these verbatim

## "What is a stock / share?"

> "A share is a **unit of ownership in a company** — a claim on its assets and its future earnings.
> Own one share out of a million and you own a millionth of the company, which normally comes with
> a vote and a share of any dividend. They're listed on an exchange so that ownership can change
> hands without the company being involved."

What you said — *"financial assets of the company"* — is the thing to avoid: shares are not assets
*of* the company, they are claims *on* it. The word you wanted is **ownership**.

## "What is an option?"

> "An option is a contract that gives the buyer the **right, but not the obligation**, to buy or
> sell an underlying asset at a fixed price, up to a fixed date. A **call** is the right to buy, a
> **put** is the right to sell. The fixed price is the **strike**, the date is **expiry**, and the
> buyer pays a **premium** for that right up front.
>
> The asymmetry is the whole point: the buyer can walk away, the **seller cannot** — they're
> obliged to deliver if the buyer exercises. So the seller collects the premium as compensation for
> taking on that obligation."

If they push one level: *"what is it worth?"*

> "Two parts. **Intrinsic value** — how much it's already worth if you exercised right now. And
> **time value** — what you'd pay for the chance that it moves further in your favour before
> expiry. Time value decays to zero at expiry, and it's larger when the underlying is more
> volatile, because volatility means more chance of a big move. That's why options are really
> traded on volatility rather than on direction."

## "What is market making?"

> "A market maker **continuously quotes both sides of a market** — a price at which it will buy and
> a price at which it will sell — so that anyone who wants to trade can trade immediately instead
> of waiting for a matching counterparty. That's the service: **liquidity and immediacy**.
>
> The compensation is the **spread**, the gap between the bid and the ask. A market maker isn't
> trying to predict direction — it's trying to be present on both sides, capture the spread many
> times, and hedge away the directional risk it accidentally accumulates.
>
> There are two real risks it's being paid for. **Inventory risk** — after a trade you're holding a
> position you didn't choose, and the price can move against you before you unwind it. And
> **adverse selection** — whoever just traded against you may know something you don't. Managing
> those two is the business."

---

# 2. What IMC actually is — verified

- **Top-3 liquidity provider by volume traded in listed options globally.** Options are the core of the business, not a sideline.
- Also equities, **ETFs**, commodities, bonds, crypto. **Lead Market Maker in 150+ US ETFs.**
- **120+ trading venues / exchanges** worldwide; NYSE Arca, NASDAQ, CBOE, CME among them.
- Founded in **Amsterdam, 1989** — *"35+ years in trading."* Amsterdam is the original office, not a branch.
- **Trades its own capital** (proprietary). This is the fact behind the line in the job ad about no external clients — there is no customer whose ticket you're servicing, which is why there's no support-desk culture.

Their own framing, worth quoting back in the Technology Lead round because it is about engineers:

> *"Speed is the baseline, infrastructure is the multiplier, and research is the edge."*
> *"Researchers develop the models. Traders shape the strategy. Engineers build the technology that brings ideas into execution at speed."*

---

# 3. The order book — the thing your code would touch

An exchange keeps a **limit order book** per instrument: resting buy orders (**bids**) and sell
orders (**asks**), each at a price and a size.

```
        BIDS (buyers)          ASKS (sellers)
   size  price            price  size
    300  10.01            10.03   200     <- best ask  (lowest price anyone will sell at)
    150  10.00            10.04   400
    900   9.98            10.06  1200
          ^ best bid (highest price anyone will pay)
```

- **Best bid** 10.01, **best ask** 10.03 → the **spread** is 0.02. The **mid** is 10.02.
- To **buy immediately** you pay the ask. To **sell immediately** you hit the bid. That difference is what you pay for immediacy — and it's the market maker's revenue.
- Orders match by **price-time priority**: better price first, and at the same price, whoever queued first.
- A **market order** executes now at whatever price is available. A **limit order** only at your price or better — it may never fill. **IOC** (immediate-or-cancel) takes what it can and cancels the rest; **FOK** (fill-or-kill) is all-or-nothing.
- **Liquid** means tight spread and deep size, so a big order barely moves the price. **Slippage** is the difference between the price you expected and the price you got.

**Data-structure answer if the coding station is an order book** — and one report says the station
task is *"a matching engine for a trading system"*, so rehearse this:

> "A dict from price level to a `deque` of orders, so FIFO at each level is O(1) at both ends, plus
> a heap on each side for the best bid and best ask — I only need the current extreme, not a full
> sort, so log n per update rather than n log n per query. Cancellation is the interesting part: I'd
> keep an order-id to node mapping so a cancel is O(1) rather than a scan, and use lazy deletion on
> the heaps because prices come and go."

---

# 4. Options, one level deeper

| Term | Meaning |
|---|---|
| **Call / Put** | right to buy / right to sell |
| **Strike** | the fixed price in the contract |
| **Expiry** | last date the right can be exercised |
| **Premium** | what the buyer pays for the contract |
| **In the money (ITM)** | exercising now would pay off |
| **At the money (ATM)** | strike ≈ current price |
| **Out of the money (OTM)** | exercising now would be worthless |
| **Underlying** | the asset the option is on |
| **Implied volatility** | the volatility the market's price implies — the real quantity being traded |

**The Greeks — one line each, survival level. Don't go further unless asked.**

- **Delta** — how much the option price moves per unit move in the underlying. Roughly, how "stock-like" the option currently is.
- **Gamma** — how fast delta itself changes. High gamma means your hedge goes stale quickly.
- **Theta** — time decay: what the option loses per day just from expiry approaching.
- **Vega** — sensitivity to implied volatility.

**Delta hedging — the single idea that ties it together, and the one to volunteer:**

> "A market maker doesn't want a directional bet. So after selling a call it buys some of the
> underlying to offset the delta and get back to roughly **delta-neutral**. Then the P&L comes from
> the spread and from volatility, not from whether the stock went up. The catch is that delta keeps
> changing as the price moves — that's gamma — so the hedge has to be continuously re-adjusted.
> Which, from where I sit, is the reason this is an engineering problem at all: it's a control loop
> that has to keep up with the market."

If they go past this: *"That's beyond what I know today, and I'd rather say so than guess. Learning
the domain properly is part of why the role appeals."* **Say that, don't bluff.** In a firm whose
business is pricing risk, a confident wrong answer is worse than a gap.

---

# 5. ETFs — worth knowing because IMC is LMM in 150+

An **ETF** is a fund that holds a basket of assets and trades on an exchange like a single share.

The mechanism to name: **creation and redemption.** Authorised participants can swap the basket of
underlying securities for new ETF shares and back again. That's what keeps the ETF's price close to
the **NAV** (net asset value) of what it holds — if the ETF trades above NAV, someone buys the
basket, creates shares and sells them, and the gap closes.

> "So being a lead market maker in an ETF means quoting the ETF while continuously valuing a basket
> of underlying instruments that are themselves moving — and arbitraging the difference. That's a
> real-time data and correctness problem before it's a finance problem, which is the part I find
> interesting."

---

# 6. Plumbing vocabulary

- **Exchange** — the matching venue. **Broker** — routes your order there. **Clearing house** — stands between buyer and seller so neither carries the other's default risk. **Settlement** — when the asset and cash actually change hands (US equities moved to **T+1** in 2024; Europe is still T+2 with a T+1 move planned).
- **Tick** — the smallest price increment, and also used loosely for a single market-data update.
- **Position** — what you currently hold. **Long** — you own it, you gain if it rises. **Short** — you sold what you don't own, you gain if it falls.
- **Position limit / risk limit** — a hard cap on exposure, enforced before an order goes out.
- **P&L** — profit and loss. **Mark to market** — revaluing a position at current prices.
- **Latency** — how long from seeing a market event to your order arriving. **Colocation** — putting your servers in the exchange's building to cut it.
- **Prop trading** — trading your own capital, which is what IMC does.

---

# 7. How to answer when you don't know — the honest ladder

1. **Give the part you do know, precisely.** "I know an option is a right rather than an obligation, and that the premium is the price of that right."
2. **Name the boundary.** "How they're priced — the volatility surface, the greeks beyond delta — I don't know."
3. **Show the direction of travel.** "This is the part I want to learn, and it's a reason the role appeals rather than a reason it doesn't."
4. **Turn it into a question.** "How much of the domain do engineers on your team actually carry? Is it expected day one, or picked up?"

Step 4 is the strongest move: it converts a gap into a conversation, and their answer tells you how
much of a problem it really is.

---

# 8. The bridge — why a CRM-messaging engineer is not a stretch

Say this once, unprompted, and never claim market-data experience:

> "I've spent three and a half years inside a trading business — Capital.com is a CFD platform —
> but on the client communication side, not on market data. What transfers isn't the domain, it's
> the shape of the problem: real-time decisions that have to be auditable, idempotent and provably
> correct under concurrency, at millions of events a day, where being wrong costs money rather than
> looking bad. The governance engine I built is a gate that runs before every send and has to be
> right every single time — **swap 'frequency cap' for 'position limit' and it's structurally the
> same problem.** The market data itself would be new. That's part of the appeal."

---

## The twenty-minute version

Learn §1 verbatim — three answers, ninety seconds total. Then the order-book diagram in §3, then
delta hedging in §4. Everything else is recognition, not recall.

---

# 9. Exchange vs broker — they asked this in round 2

> "An **exchange** is a neutral, regulated **venue that matches orders**. It runs the central limit
> order book, publishes market data, and enforces price-time priority. Crucially it **takes no
> position of its own** — it brings buyers and sellers together and charges for access and data.
>
> A **broker** is an intermediary that holds a client account and **routes that client's order** to
> an exchange on their behalf. Access, custody, the client relationship.
>
> Behind both sits a **clearing house**, which novates the trade and stands between the two sides
> so neither carries the other's default risk. Settlement is when the asset and the cash actually
> move.
>
> A market maker like IMC is a **member of the exchange** — quoting directly on the venue, not
> routing through a broker."

## The observation to volunteer — it turns the gap into an insight

> "Working this out clarified something about my own employer. A CFD platform is the
> **counterparty** to its client — the client's position is a bilateral contract with the broker,
> not an order on a venue. That is structurally the **opposite** of IMC, which is a member quoting
> on a neutral exchange. I'd been inside a trading business for three years without having drawn
> that line properly."

That is a better answer than the textbook one, because it is his own and it is specific.

---

# 10. CFD vs option — the distinction that explains the freeze

Artem has traded CFDs personally and still could not answer the options question. That is not
inconsistent — **they are different instruments**, and the difference is exactly the part he was
missing.

| | CFD | Option |
|---|---|---|
| Payoff | **linear** — the difference in price | **asymmetric** — a right, not an obligation |
| Strike | none | yes |
| Expiry | typically none | yes, and time value decays to zero |
| Counterparty | **the broker** — bilateral, OTC | exchange + clearing house |
| Ownership of underlying | no | no (but the right to buy it) |
| Leverage | built in | built in, via the premium |

**What they share:** both are **derivatives** — value derived from an underlying, with no ownership
of it.

So CFD experience gives real intuition about leverage and about taking a position without owning
the asset, and **no intuition at all about options**, because there is no strike, no expiry and no
asymmetry in a CFD. That is the honest explanation for freezing, and it is a strong answer rather
than an excuse.

⚠️ **Compliance note.** Market makers normally restrict employees' personal trading — pre-clearance,
restricted lists, holding periods. Mention CFD trading in the **past tense**, as the source of some
familiarity, not as an ongoing hobby.

---

# 11. Derivatives — the parent concept, and the imprecision to fix

Asked in round 2. Artem's answer was *"I traded with leverage — CFDs, futures"*, which conflates
two different things.

**Leverage is not what makes something a derivative.** Leverage is a *consequence* — you post
margin instead of the full notional value. The definition is:

> "A derivative is a contract whose value is **derived from an underlying** — an asset, a rate, an
> index — rather than from owning that underlying."

## The four families

| | Who is obliged | Payoff | Venue |
|---|---|---|---|
| **Futures** | **both sides** | linear, symmetric | exchange; standardised, cleared, margined daily |
| **Forwards** | both sides | linear | OTC, bespoke |
| **Options** | **seller only** — buyer has the right | **asymmetric**; strike + expiry | exchange (IMC's core business) |
| **Swaps** | both sides | exchange of cash-flow streams (e.g. fixed vs floating) | mostly OTC |
| **CFDs** | bilateral with the broker | linear, typically no expiry | OTC, retail |

**The distinction they are testing:** a future **obliges both sides** to transact at a fixed price
on a fixed date. An option gives the buyer the **right without the obligation**. That asymmetry is
precisely what the premium pays for — and it is why options need pricing models and futures largely
do not.

## Margin, in one line each

**Margin** — collateral posted against a position rather than its full value. **Mark to market** —
the position revalued at current prices, daily for futures. **Margin call** — top up the collateral
or be closed out. **Notional** — the full economic size of the contract, which is much larger than
the margin, and that is where the leverage comes from.

## The spoken answer

> "A derivative is a contract whose value comes from an underlying rather than from owning it —
> futures, forwards, options, swaps. The line I'd draw is obligation: a future binds both sides to
> transact at a set price on a set date, so the payoff is linear. An option binds only the seller —
> the buyer holds a right and can walk away — so the payoff is asymmetric, and the premium is the
> price of that asymmetry. I'd traded leveraged products, but leverage comes from posting margin
> against notional; it isn't the thing that makes an instrument a derivative."

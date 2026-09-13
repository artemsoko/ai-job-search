# IMC Trading — recruiter call with Riccardo
### Python Software Engineer, Amsterdam · 30 minutes

Riccardo sent the agenda, so this is prepped block by block against it:

1. Quick introductions
2. Your motivation for joining IMC, and what draws you to trading / market making
3. The most challenging project you've worked on
4. Your questions for him
5. Logistics — availability, holidays, compensation

Rough time budget: 3 minutes on introductions, 7 on motivation, 8 on the project, 7 for your
questions, 5 on logistics. That means you get **three or four questions, not eight**, and it
means compensation is *his* topic, not yours. You don't need to raise it. You need an answer
ready when he does.

The two blocks that can actually hurt you are **motivation** and **compensation**. Everything
else plays to your strengths.

---

## Block 1 — Introductions

Keep it to about ninety seconds. One version, said the same way every time:

> "I'm a Senior Software Engineer at Capital.com, where I've been for about three and a half
> years. I own the backend services behind our CRM client communication — service and marketing
> messaging across email, SMS and in-app inbox, running at millions of messages a day. Before
> that I was at Ciklum and SoftServe, mostly on high-load async Python. Ten years in Python
> altogether, and I currently lead two engineers. I'm based in Warsaw and I'm looking to
> relocate to Amsterdam with my family."

Then stop. Let him steer.

If he asks for a highlight rather than a history:

> "The two things I'd point at: I re-architected our critical send path and got it five to six
> times faster, and in doing so found and killed a class of bug where deliveries were being
> reported as successful when they had actually failed. And I designed the governance engine
> that decides, in real time, whether a message is allowed to go out — frequency caps, consent,
> quiet hours — with idempotent decisions and optimistic-locking quota accounting."

That last phrase lands with a trading firm faster than anything else on your CV. Use it early.

---

## Block 2 — Motivation, and what draws you to trading

**This is the block where candidates without a markets background lose the call.** The wrong
move is to manufacture enthusiasm for financial markets. Riccardo hears that every day and can
tell. The right move is to be straight about where you're coming from, and then be specific
about why IMC in particular.

You have something better than fake passion, and it happens to be true: **you have already spent
three and a half years inside a trading business.** Capital.com is a CFD trading platform. You
sit on the communications side of it rather than the trading side, but you are not an outsider
to the industry.

### The answer, more or less verbatim

> "I should be straight with you: I don't come from a markets background. But I've spent the
> last three and a half years inside a trading business — Capital.com — just on the
> communications side rather than the trading side. And from that seat, the engineering I always
> found most interesting was the other side of the house. Systems where being wrong costs money
> immediately, and where correctness under load isn't a quality goal, it's the actual product.
>
> What draws me to IMC specifically is two things. First, the work in your posting is
> essentially what I already do — high-load async Python, deterministic logic, auditability —
> just pointed at a harder problem domain. Second, there's a line in the posting that says
> everything is built for internal use, there are no external clients, and the people who use
> your work sit a few metres away. I've spent years on systems where the loop between me and the
> person who needs the thing is long and noisy. A short loop is genuinely a large part of why I
> want this role."

Three reasons that works: it doesn't lie, it gives a reason that is specific to IMC rather than
to finance in general, and it closes on something you could only know by reading their posting
properly.

### The homework you do need — about an hour, no more

Riccardo will probably test whether you understand the business at all. You need to be able to
say these in your own words:

- **What a market maker does.** Quotes both sides of a market at once, provides liquidity, and
  earns the spread — rather than making money by predicting direction.
- **Bid-ask spread.** The gap between the buy and sell price. It's the compensation for the risk
  of holding a position.
- **Why that makes it an engineering problem.** Speed and correctness decide whether the spread
  actually covers the risk you took on.

One sentence worth having loaded:

> "As I understand it, IMC makes money by being consistently present on both sides of the market
> rather than by predicting direction — which is why latency and correctness are business
> problems, not engineering preferences."

**Do not pretend to know more than that.** If he asks about options pricing or the greeks, say
plainly that it's new to you and that learning the domain is part of the appeal. Getting caught
bluffing on markets at a market maker is much worse than admitting a gap.

### If he asks "why leave Capital.com?"

Don't complain about anything. Keep it forward-looking:

> "Nothing's wrong with it — I've grown a lot there and the work is real. But relocating to the
> Netherlands with my family is a deliberate goal, and I want the next step to be a harder
> technical domain rather than more of the same. Those two things point at the same kind of move."

---

## Block 3 — The most challenging project

You have two candidates. **Lead with the send-path re-architecture**, and keep the governance
engine in reserve for when he probes design.

Why that order: the send-path story contains a bug where the system reported success that hadn't
happened. For a trading firm, "how do we know this actually happened" is not a nice anecdote,
it's a daily concern. That's the hook.

Aim for three to four minutes. Situation, task, action, result — then the reflection, which is
the strongest part.

### The story

**Situation.** The email and push send path lived inside our existing MarTech pipeline.
Million-scale campaigns took five to six hours to go out. And the system was reporting some
deliveries as succeeded when they had actually failed.

**Task.** Make it fast, and make it honest — without a big-bang rewrite of the pipeline that
everything else depended on.

**Action.** I split the path into a Go worker plus a Python executor, and pushed duplicate
prevention and idempotency down to the database level, so a retry physically could not
double-send. I rolled it out behind database-backed feature flags so it could be reverted per
segment rather than all at once.

**Result.** Five to six times faster, push throughput up eight to ten times, and the
false-succeeded class of bug eliminated.

**And then the part that matters most:**

> "What I'd do differently: I found the false-success bug while profiling, not from an alert. The
> root cause was that success was being *inferred* rather than *confirmed*. Since then I treat
> 'how do we know this actually happened' as a design question, not an observability
> afterthought."

That sentence sells you to a market maker better than any of the numbers.

### If he probes the design

Switch to the governance engine:

> "The other one I'd point at is a decision service that sits in front of the existing pipeline
> rather than inside it. It evaluates, in real time, whether a message may be sent — consent,
> frequency caps, quiet hours, holdout groups. Quota enforcement uses optimistic locking on a
> versioned row, so two concurrent sends can't overspend the same cap. Decisions are idempotent,
> so a replay is safe. And messages blocked by quiet hours aren't dropped, they go to a DELAYED
> state and get promoted when their window opens."

Then make the connection explicit, out loud:

> "Swap 'frequency cap' for 'position limit' and that's structurally the same problem — a
> real-time gate that has to be provably correct under concurrency, and auditable afterwards."

### Numbers you can state, all verified

- Send path: **5–6x faster**, million-scale campaigns from 5–6 hours down to about one hour,
  push throughput **8–10x**, false-delivery bug eliminated
- Audience pipeline: **10x scale, to 20 million users**, on Airflow, six runs a day with alerting
- Acting tech lead for about six months: **348 merge requests reviewed, 200+ authored**, test
  coverage on a core service raised to **73%**

---

## Block 4 — Your questions

You'll fit three or four. Compensation is on his agenda already, so drop it from yours. Ask
these, in this order.

### 1. Levelling — the one that decides your offer

The req asks for "4+ years". You have over ten and you lead two engineers. If you get slotted
against a 4-year bar, you get a 4-year offer.

> "The posting asks for four-plus years and I'm coming in with over ten, currently leading two
> engineers and having covered a tech lead role for about six months. Where would this sit on
> your engineering ladder, and is there a more senior band it could be scoped to? I'd rather get
> aligned on level now than find a mismatch at offer stage."

If he says level is decided after the interviews — that's normal. Ask him to tell you the band
for the level he's putting you forward against anyway.

### 2. Which team

The posting covers wildly different work: trading systems, analytical tools, signals generation,
backtesting frameworks, trade management UIs, regulatory surveillance and risk monitoring. Those
are not the same job.

> "The posting spans quite a range — trading systems, backtesting, signals, surveillance. Which
> team is this req for, and what would my first six months actually look like?"

### 3. The coding station — ask as preparation, never as avoidance

> "I want to prepare properly for the problem-solving station. Is it a practical, real-world
> style problem or more of a pure algorithms exercise? Will I be working with existing code and
> tests, or starting from a blank editor? And am I able to use documentation and search during
> it, the way I would at work?"

That last part is the question that actually matters to you, and it's completely legitimate —
their own material suggests searching is allowed.

You can add: *"Is there anything specific you'd recommend I brush up on?"* Recruiters often
answer that one very directly.

**Do not ask them to skip or replace the algorithmic portion.** At a market maker that reads as
"I can't clear the bar", and their format is already practical rather than LeetCode-style.

### 4. Take the two-day option now

> "Your document mentions the final round can be spread over two consecutive days rather than
> one. I'd prefer that — can we plan for it?"

They offer it, most candidates take it, and a 30-minute intro plus a two-hour problem-solving
station plus a technical interview in a single day is needlessly punishing.

---

## Block 5 — Logistics

Three things must be ready before you dial in.

### Compensation

Don't name a number first. Ask for his band for the level. If he pushes:

> "Based on what I've seen for this level in Amsterdam, I'm targeting total compensation in the
> €160–175k range, with base making up the majority of it. I'm calibrating above the median
> because I'm coming in with ten-plus years and team lead experience against a req written for
> four-plus. But I'd rather hear your band for the level first."

The market data behind that:

| Source | Amsterdam, IMC, Software Engineer |
|---|---|
| levels.fyi, median total | **€145k** |
| TechPays, average total (9 data points) | **€142.7k** |
| levels.fyi, Netherlands median total | €155k |

Their level breakdown suggests **base is strong and roughly flat across levels (around
€117–133k), and it's the bonus that scales** (roughly €26k at L1 up to €63k at L4). That's the
opposite of Optiver, where the base is thin and the variable is large. Good news for you: base
is what matters for the visa threshold and for a mortgage.

Two caveats, so you don't over-trust it: the levels.fyi table renders figures with a dollar sign
under euro headings, so treat the base numbers as indicative rather than exact; and the TechPays
sample is only nine data points. The reliable anchor is the **€145k Amsterdam median**, which two
independent sources agree on.

**Your red line on base is €110k.** Below that you're sitting under IMC's own entry-level base,
which is just money left on the table. The Dutch Highly Skilled Migrant threshold is €5,942 a
month — that's the legal floor, not a target.

Ask for the split explicitly. Base is what the visa, the mortgage and your family budget are
calculated against, not total.

### Availability

**Confirm your actual notice period at Capital.com before the call.** This is the one thing in
the logistics block you cannot improvise, and guessing wrong on air is a bad look.

### Holidays

If you have trips booked in the next two or three months, say so now rather than after an offer.

### Visa and relocation — this fits naturally here

> "I'd be relocating from Warsaw with my wife and daughter. Can you confirm IMC sponsors the
> Highly Skilled Migrant permit, whether this role qualifies for the 30% ruling, and what the
> relocation support covers for a family — housing, schooling, spouse support?"

IMC B.V. is on the official IND recognised-sponsor register, so this is a question about their
practice, not about whether it's possible.

---

## Three things not to do

1. **Don't manufacture passion for financial markets.** "I came from engineering, the domain is
   new, and I want it" is a stronger answer than a rehearsed one.
2. **Don't ask to avoid the algorithmic part.** It's the only question on your list that can
   actively damage you.
3. **Don't negotiate hard.** Riccardo relays, he doesn't decide. Pin down the level and the
   band; save the negotiation for the offer.

## What happens next, so you can sound informed

Their process for this role: a **Python take-home** — another simple game, three days to do it,
about five hours typical — then a **60-minute interview with two Senior Python Engineers**, then
a **final round of four stations**: a 30-minute intro with the Technology Lead, a **two to
two-and-a-half hour problem-solving and coding station** in Python and PyCharm, and a technical
interview with two technical leads.

Worth knowing: some public reports describe a 120-minute HackerRank with two medium/hard
problems. That does **not** match the document IMC sent you, which starts with the take-home.
Those reports are probably other roles or regions. If he mentions an online assessment, ask which
format — otherwise assume your document is right.

The take-home is your best round. The algorithm in it is deliberately trivial; the entire test is
whether you can ship production-quality code around it. Clean Architecture, PyTest, coverage
discipline — that's exactly your ground.

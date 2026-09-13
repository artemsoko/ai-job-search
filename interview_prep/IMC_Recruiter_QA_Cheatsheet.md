# IMC recruiter call — what Riccardo will ask, and what you say
### One page. Their question in bold, your answer underneath.

---

## OPENING

**"Tell me about yourself."**

> "I'm a Senior Software Engineer at Capital.com, three and a half years there. I own the backend
> services behind our CRM client communication — service and marketing messaging across email,
> SMS and in-app inbox, running at millions of messages a day. Before that, Ciklum and SoftServe,
> mostly high-load async Python. Ten years in Python altogether, and I currently lead two
> engineers. I'm in Warsaw and looking to relocate to Amsterdam with my family."

Then stop talking. Ninety seconds is enough.

**"Walk me through your CV — why the moves?"**

> "SoftServe was where I learned high-load async work, on Atlassian's Hipchat and Stride chat
> backends. I moved to Ciklum for more product ownership and got it — I led features and tech
> design on Powtoon. I moved to Capital.com because I wanted to own services end to end in a
> regulated environment, and that's what I've been doing. Each move was for more ownership, not
> away from anything."

---

## MOTIVATION — the block that decides the call

**"Why IMC?"**

> "Two concrete things. First, the work in your posting is essentially what I already do —
> high-load async Python, deterministic logic, auditability — just pointed at a harder domain.
> Second, the posting says everything is internal, no external clients, and the people who use
> your work sit a few metres away. I've spent years on systems where the loop between me and the
> person who needs the thing is long and noisy. A short loop is a big part of why I want this."

**"What draws you to trading and market making?"** ← the risky one

> "I should be straight with you: I don't come from a markets background. But I've spent the last
> three and a half years inside a trading business — Capital.com is a CFD platform — just on the
> communications side rather than the trading side. From that seat, the engineering I always
> found most interesting was the other side of the house. Systems where being wrong costs money
> immediately, and where correctness under load isn't a quality goal, it's the product itself.
> That's the direction I want to move toward, not away from."

**"What do you know about market making?"**

> "As I understand it, IMC makes money by being consistently present on both sides of a market
> rather than by predicting direction. You quote a bid and an ask, provide liquidity, and earn
> the spread, which is compensation for the risk of holding a position. Which is exactly why
> latency and correctness are business problems at IMC rather than engineering preferences."

If he goes deeper — options, greeks, hedging:

> "That's beyond what I know today, and I'd rather say so than guess. Learning the domain
> properly is part of why the role appeals."

**"Why leave Capital.com?"**

> "Nothing's wrong with it — I've grown there and the work is real. But relocating to the
> Netherlands with my family is a deliberate goal, and I want the next step to be a harder
> technical domain rather than more of the same. Those two point at the same move."

Never criticise your employer, manager or team. Not once.

**"Why the Netherlands?"**

> "It's the best fit for my family — my daughter would go to school in English, and my wife works
> in QA so the market there works for her too. It's also a genuinely good engineering market. I'm
> not looking for a short-term move; I want to build a life there."

**"What are you looking for in your next role?"**

> "Real development work rather than maintenance and firefighting. Systems where the details
> matter and where clean architecture pays off. And a team that's technically strong enough that
> I learn from it."

**"Where else are you interviewing?"** — be honest but brief, and don't hand over a full list.

> "I'm in process with a few companies in the Netherlands and Germany, mostly Python backend
> roles. IMC is the one I'd most want to make work, because of the domain and because the stack
> matches so closely."

---

## THE PROJECT

**"Tell me about the most challenging project you've worked on."**

Send path. Three to four minutes.

> "Our email and push send path lived inside our existing MarTech pipeline. Million-scale
> campaigns took five to six hours to go out, and the system was reporting some deliveries as
> succeeded when they had actually failed.
>
> My job was to make it fast and make it honest, without a big-bang rewrite of the pipeline
> everything else depended on.
>
> I split the path into a Go worker plus a Python executor, and pushed duplicate prevention and
> idempotency down to the database level, so a retry physically couldn't double-send. I rolled it
> out behind database-backed feature flags so it could be reverted per segment rather than all at
> once.
>
> Result was five to six times faster, push throughput up eight to ten times, and that class of
> false-success bug eliminated.
>
> What I'd do differently: I found the false-success bug while profiling, not from an alert. The
> root cause was that success was being inferred rather than confirmed. Since then I treat 'how
> do we know this actually happened' as a design question, not an observability afterthought."

**"What was your specific contribution, versus the team's?"** ← he will ask this, their doc says so

> "The design and the critical path were mine — I wrote the technical design, the idempotency
> model at the database level and the rollout strategy. The Go worker was built with a colleague
> who owns that service; I specified the contract and reviewed it. The two engineers I lead
> picked up the migration of the older campaign types once the pattern was proven."

Be precise about the boundary. Overclaiming is the fastest way to fail a reference check.

**"What's the hardest technical decision you've made?"**

> "Building the governance engine as a decision service in front of the existing pipeline rather
> than inside it. Inside would have been faster to ship and would have coupled a compliance
> concern to a throughput concern permanently. In front meant more moving parts, but caps,
> consent and quiet hours became independently testable and independently deployable."

**"Tell me about a mistake."**

> "The false-success bug I mentioned — I owned that path and I found it by accident rather than
> by design. The lesson wasn't 'add more monitoring', it was that I'd let the system infer an
> outcome it should have confirmed."

**"How do you handle disagreement with a colleague or a manager?"**

> "I argue it with data and then commit either way. Concretely: when we chose the idempotency
> approach, I wanted it at the database level and someone else wanted application-level
> deduplication. I wrote up both with the failure modes and we went with the database. If it had
> gone the other way I'd have built it properly and moved on."

---

## THE GAP HE WILL PROBE

**"The role asks for experience with financial data. Talk me through yours."**

Raise this yourself if he doesn't. Being first is much stronger than being caught.

> "I want to be upfront about this one. I've spent ten years on high-load Python in a regulated
> fintech, but on the CRM and communications side, not on market data. I've never worked with
> order books or tick data.
>
> What I do bring is the shape of the problem: a regulated environment where decisions have to be
> auditable, idempotent and provably correct under concurrency, at millions of events a day, and
> where getting it wrong has a financial consequence rather than a cosmetic one. The governance
> engine I built is a real-time gate that has to be right every single time — swap 'frequency
> cap' for 'position limit' and it's structurally the same problem.
>
> The market data itself would be new to me. That's honestly part of the appeal. How much of a
> blocker is it for you?"

Asking the question back is deliberate — you find out now, not after two hours of live coding.

**"How comfortable are you with the coding assessment?"**

> "Comfortable with the take-home — production-quality code with real tests is the part of the job
> I most enjoy. For the live station, what would help me prepare is knowing whether it's a
> practical problem or a pure algorithms exercise, whether I'd be working with existing code and
> tests or a blank editor, and whether I can use documentation and search the way I would at work."

**Never** ask them to skip or soften the algorithmic part.

**"What's your experience outside Python — Go, Java, C++?"**

> "Python is my language, ten years and by far my strongest. I've worked alongside Go — the
> worker in that send-path project was Go, and I specified and reviewed it — but I wouldn't call
> myself a Go engineer, and I'd rather tell you that than have it surface later. Same for Java:
> I can read it, I don't write it."

That's the truth and it's also the right answer. Don't inflate it.

---

## LOGISTICS

**"What are your salary expectations?"**

Ask for his band first:

> "I'd rather hear the band for the level you're putting me forward against — that's more useful
> than me guessing at your structure."

If he insists:

> "Based on what I've seen for this level in Amsterdam, I'm targeting total compensation in the
> €160–175k range, with base making up the majority of it. I'm calibrating above the median
> because I'm coming in with over ten years and team lead experience, against a req written for
> four-plus. But I'd genuinely like your band first."

Then, always:

> "Could you split that for me — base range versus target bonus? I'm relocating a family, so I
> need to plan against base rather than total."

Anchor: Amsterdam median total comp at IMC is about **€145k**. Your red line on **base is €110k**.

**"What's your notice period? When could you start?"**

⚠️ **Confirm your real notice period at Capital.com before the call.** Don't guess on air.

> "My notice period is [X]. Beyond that I'd need a few weeks for the visa and the move, so
> realistically [X + 4–6 weeks] to actually start in Amsterdam."

**"Any holidays or commitments booked?"**

Say them now, not after an offer. If nothing: *"Nothing booked, I'm flexible on scheduling."*

**"Do you need visa sponsorship?"**

> "Yes. I'm a Ukrainian national living in Warsaw, so I'd need the Dutch Highly Skilled Migrant
> permit. I know IMC is on the IND recognised-sponsor register, so I assume that's routine for
> you — can you confirm how it usually runs, and whether the role qualifies for the 30% ruling?"

**"Is your family on board with relocating?"**

> "Yes, fully — it's a joint decision and Amsterdam is our first choice. My wife works in QA and
> is planning to look for work there, and schooling in English is a big part of why we chose the
> Netherlands."

**"Anything else we should know?" / "Why should we hire you?"**

> "Because the thing you need most in that posting — Python at scale where correctness is the
> product — is exactly the last ten years of my career, and I'd be joining to learn the domain
> rather than to coast on what I already know."

---

## The three sentences to have loaded at all times

1. *"Optimistic-locking quota accounting with idempotent decisions."* — say it early, they'll
   recognise it immediately.
2. *"Success was being inferred rather than confirmed."* — the reflection that sells you.
3. *"Swap 'frequency cap' for 'position limit' and it's structurally the same problem."* — the
   bridge from your domain to theirs.

## The three things not to do

1. Don't manufacture passion for markets. Honest beats rehearsed.
2. Don't ask to avoid the algorithmic round.
3. Don't negotiate hard — Riccardo relays, he doesn't decide. Pin the level and the band, save
   the negotiation for the offer.

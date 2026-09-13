# IMC coding station — confirmed format, and how to work it
### Confirmed by Riccardo on the recruiter call, 2026-08-19

## What he actually told you

- **No LeetCode.** Not an algorithm-puzzle round.
- You get a **task to implement**, with **APIs / code already written** for you to work against.
- **You are expected to dig out the requirements yourself** — what, how, where. This is scored.
- You **pick the data structures** that fit, from the ones listed in the PDF they sent.
- **Google is allowed. AI is not.**

That last line is the one that changes your prep. Everything else is good news.

## What each of those means in practice

### "APIs already written" → this is a read-the-codebase exercise
You are not starting from a blank editor. There is existing code with an existing shape, and the
first thing you do is read it, not type. Expect interfaces you must conform to, and probably
failing tests that encode the spec.

**Practise:** open an unfamiliar repo and, in ten minutes, be able to say out loud what the
entry point is, what the main abstractions are, and where you'd add a feature. Do this three or
four times on random GitHub repos. The skill being tested is orientation speed, and it's the one
IMC named in the posting: *"You're the kind of engineer who can drop into an unfamiliar codebase
and be useful within days."*

### "You have to clarify the requirements" → this is graded, and it's free marks
IMC's own document: *"We are interested in seeing how you clarify the problem and your thought
process and the reasoning behind any decisions that you make."* Riccardo just confirmed it
explicitly. Candidates who start typing immediately lose here.

Use the checklist below. Ask five or six of these before writing a line.

### "Pick the right data structures" → the spoken drill is the highest-value prep
They named five in the PDF: **Dynamic Array, Linked List, Hash Table, Binary Heap, Binary Search
Tree**. You must be able to justify a choice out loud with a complexity in the sentence.
`data_structures_drill.md` is exactly this. An hour on it is worth more than a day of coding.

### "Google yes, AI no" → drill with the agent OFF, every time
This is your real risk. You work inside Claude Code daily. In the station you will have
documentation and search, and nothing that writes code for you.

**Hard rule for every drill from now on: PyCharm open, Claude Code and Copilot closed.** Reading
docs and Stack Overflow is fine and realistic. Autocompleting the answer is not, and practising
with it on is practising the wrong thing.

---

## The clarifying-questions checklist

Print this. Ask five or six at the start, then more as you go. Say *"before I start writing, let
me make sure I understand the shape of this"* and then run down it.

### Scope and intent
1. What problem is this solving for the person who'd use it? Who calls this?
2. What's in scope for the next two hours, and what would you consider out of scope?
3. Is there a part of this you most want to see me get right?

### Inputs and data
4. What's the expected volume — hundreds, millions? Does it grow over time?
5. Can inputs be duplicated? Out of order? Late?
6. Are there invalid inputs I should handle, or can I assume the API gives me clean data?
7. What's the cardinality of the keys — small and bounded, or unbounded?

### Behaviour and correctness
8. What should happen on a tie? (ordering, priority, equal prices)
9. Is ordering guaranteed anywhere in the output, or is it unordered?
10. Should this be idempotent — if the same request arrives twice, what's correct?
11. Are reads and writes concurrent, or is single-threaded fine for now?

### Interfaces
12. Which of these existing APIs am I expected to use, and which can I change?
13. Is this interface fixed, or may I add a method if it makes the design cleaner?
14. Are the existing tests the spec, or are there requirements not covered by them?

### Trade-offs, asked explicitly
15. Do you care more about read latency or write latency here?
16. Is memory constrained, or can I trade memory for speed?
17. Should I optimise for the common case or the worst case?

Question 15 and 16 are the ones that make you sound senior, because they're the ones that decide
the data structure. Ask at least one of them.

---

## How to run the two hours

**First ten minutes — do not type.**
Read the task document. Read the existing code. Ask your clarifying questions. Restate the
problem back to them in your own words and get confirmation.

**Next five minutes — say the plan out loud before writing it.**
> "Here's what I think this needs. The naive version is X, which costs O(n) per query. I'd rather
> do Y, which costs O(log n) per update, because based on what you said about read volume the
> queries dominate. I'm going to use a hash table keyed on id for O(1) lookup, plus a heap for
> the current best. The cost I'm accepting is that deletion from the middle isn't cheap, so I'll
> mark entries dead and prune lazily. Does that match what you had in mind?"

That paragraph is most of the score. Rehearse the *shape* of it, not the content.

**Then run the tests before writing anything.**
They are the spec. Read what they assert. Fix one at a time and narrate which you're taking next
and why.

**Throughout — narrate.** Every decision gets a reason with a complexity in it. If you get
stuck, say what you'd look up and why, then look it up. Searching is allowed and using it
visibly is a positive signal, not a confession.

**You are not expected to finish.** Their document says so explicitly. A clean, well-reasoned
partial solution with the trade-offs articulated beats a rushed complete one.

---

## Revised prep priority, given what Riccardo confirmed

| # | What | Why now | Time |
|---|------|---------|------|
| 1 | `data_structures_drill.md` out loud | They said you pick the structures. This is the graded skill. | 1-2 h |
| 2 | Clarifying-questions checklist, rehearsed | Confirmed as scored. Cheapest marks available. | 30 min |
| 3 | Order book drill, **agent off**, in PyCharm | Most likely problem shape at a market maker | 60 min |
| 4 | Codebase-orientation practice | "APIs already written" means reading comes first | 45 min |
| 5 | Remaining drills 2-6, agent off | Range of structures under time pressure | 25 min each |
| 6 | Install PyCharm, get comfortable | IMC: familiarity "will give you more time to focus" | 20 min |

## What has NOT changed

The **take-home comes first**, and it's still your best round: a deliberately simple game where
the entire test is production-readiness. Clean Architecture, PyTest, README with design
decisions, Docker, Makefile. See `IMC_Python_SWE_Prep.md` for the twelve-point checklist.

One thing to carry over from what Riccardo said: **no AI in the live station**. The take-home has
no such restriction and IMC's guidance allows Google and open source — but read and own every
line, because you'll be challenged on specific choices in the 60-minute interview afterwards.

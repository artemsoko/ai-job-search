# ANNOTATED COPY of the submitted app/balances.py.
# Live code is unchanged from what IMC received. Every "ALTERNATIVE" block is commented out.
from collections import defaultdict
from decimal import Decimal

# ALTERNATIVE (typing): the record is an unannotated 4-tuple whose field order is
# duplicated in files.py with nothing enforcing it. A NamedTuple removes the coupling
# and gives mypy something to check:
#
#   from typing import NamedTuple
#
#   class Record(NamedTuple):
#       product: str
#       portfolio: str
#       side: str
#       quantity: str
#
# Then `for r in records:` and `r.side`, instead of relying on position 2.


def get_balances(records, accounts):
    balances = defaultdict(lambda: defaultdict(Decimal))

    for product, portfolio, side, quantity in records:
        if side not in ('BUY', 'SELL'):
            raise ValueError(f'unexpected side {side!r} on product {product!r}')
        if portfolio not in accounts:
            raise ValueError(f'no bank account mapped for portfolio {portfolio!r}')

        amount = Decimal(quantity)
        balances[product][accounts[portfolio]] += amount if side == 'BUY' else -amount

    return balances

    # SHIPPED GAP — quantity is the only unguarded field. Verified behaviour:
    #   missing <Qty>      -> findtext returns None -> TypeError, no record context
    #   <Qty>abc</Qty>     -> decimal.InvalidOperation, no record context
    #   <Qty>-5</Qty> BUY  -> accepted silently and FLIPS THE SIGN
    # The third one is the real bug: the zero-sum check still passes if the input is
    # self-consistent, so it is silent all the way to the bank.
    #
    # ALTERNATIVE (validation) — guard it in the same block as the other two, with the
    # same message shape:
    #
    #   try:
    #       amount = Decimal(quantity)
    #   except (TypeError, InvalidOperation):
    #       raise ValueError(
    #           f'bad quantity {quantity!r} on product {product!r} portfolio {portfolio!r}'
    #       ) from None
    #   if amount <= 0:
    #       raise ValueError(
    #           f'non-positive quantity {quantity!r} on product {product!r} '
    #           f'portfolio {portfolio!r}'
    #       )
    #
    # ALTERNATIVE (exactness) — quantities have exactly six decimal places, so Decimal is
    # not actually needed. Scaled integers are exact, have no context limit and are faster,
    # because int arithmetic is C while Decimal is a Python object:
    #
    #   amount = int(Decimal(quantity) * 1_000_000)   # store minor units
    #   ...                                            # divide by 1e6 only when writing out
    #
    # This also removes the failure that test_decimal_precision_is_caught documents:
    # Decimal's default context keeps 28 significant digits, so 1e30 + 0.000001 rounds down
    # and the balances stop summing to zero for reasons unrelated to the data.


def make_transfers(product, balances):
    if sum(balances.values()) != 0:
        raise ValueError(f'balances for {product!r} do not add up to zero: {dict(balances)}')

    owed = {account: -value for account, value in balances.items() if value < 0}
    due = {account: value for account, value in balances.items() if value > 0}

    transfers = []
    while owed:
        # O(n) scan per pick, so O(n^2) per product. n is accounts-holding-a-position for
        # ONE product, not the 2.3M records: measured 5,702 transfers, 8s, 29MB.
        from_account = max(owed, key=owed.get)
        # Cannot KeyError on an empty `due` precisely because of the zero-sum guard above:
        # if anything is owed, something must be due.
        to_account = max(due, key=due.get)
        # Settling the smaller side empties at least one account per round. That is both the
        # termination argument and the source of the `at most n - 1` bound.
        quantity = min(owed[from_account], due[to_account])
        transfers.append((product, from_account, to_account, quantity))

        owed[from_account] -= quantity
        due[to_account] -= quantity
        if owed[from_account] == 0:
            del owed[from_account]
        if due[to_account] == 0:
            del due[to_account]

    return transfers


# =============================================================================
# THE OVERCLAIM, AND THE CHEAP FIX
# =============================================================================
#
# What is wrong is the WORD, not the algorithm. README.md and pyproject.toml both say
# "fewest bank transfers". Greedy biggest-debtor-pays-biggest-creditor guarantees
# `at most n - 1` per product and is optimal when no proper subset of the balances nets to
# zero. It is NOT the minimum. The true minimum is
#
#       n_nonzero - k,   k = largest number of DISJOINT subsets that each net to zero
#
# which is set partition, i.e. NP-hard. Greedy destroys those subsets by construction:
# it always sends the biggest debtor to the biggest creditor, even when a smaller pair
# cancels exactly.
#
# Verified counterexample against the code above:
#
#   balances  A=-4  B=-3  C=+2  D=+2  E=+3
#   greedy (4):   A->E 3 | B->C 2 | A->D 1 | B->D 1
#   optimum (3):  B->E 3 | A->C 2 | A->D 2        ({B,E} nets to zero, settle it first)
#
# ALTERNATIVE 1 — exact-pair pass before greedy. ~10 lines, O(n^2) at worst, no new
# dependency, and it captures most of the available win:
#
#   def make_transfers_with_pairs(product, balances):
#       if sum(balances.values()) != 0:
#           raise ValueError(...)
#
#       remaining = {a: v for a, v in balances.items() if v != 0}
#       transfers = []
#
#       # settle every account that has an exact opposite: one transfer clears two accounts
#       for debtor in sorted(a for a, v in remaining.items() if v < 0):
#           if debtor not in remaining:
#               continue
#           target = -remaining[debtor]
#           match = next((a for a, v in remaining.items() if v == target), None)
#           if match is not None:
#               transfers.append((product, debtor, match, target))
#               del remaining[debtor], remaining[match]
#
#       if remaining:
#           transfers.extend(make_transfers(product, remaining))   # greedy on the rest
#       return transfers
#
# MEASURED (brute-forced against the true optimum, 3,925 random zero-sum vectors of
# length 2-6 over +/-6):
#
#       fewer transfers than plain greedy on   71
#       MORE  transfers than plain greedy on    0
#       exactly optimal on                  3,910  (99.6%)
#       the counterexample above:            4 -> 3, which is optimal
#
# Honest caveat to state if asked: this is still a heuristic. Taking pairs greedily is not
# proven to maximise k, so 99.6% is an empirical number on small vectors, not a guarantee.
#
# ALTERNATIVE 2 — exact optimum, for completeness. Enumerate disjoint zero-sum subsets and
# settle each independently (each subset of size m costs m-1 transfers). Exponential in the
# number of accounts per product; only viable because that number is small. NOT worth it
# here: the whole run produces 5,702 transfers in 8 seconds, so the saving is in the noise
# and the code becomes an order of magnitude harder to review.
#
# ALTERNATIVE 3 — heap instead of the O(n) max() scans. Would make the picks O(log n):
#
#   import heapq
#   debtors  = [(v, a) for a, v in balances.items() if v < 0]      # v < 0 sorts biggest-first
#   creditors = [(-v, a) for a, v in balances.items() if v > 0]
#   heapq.heapify(debtors); heapq.heapify(creditors)
#   while debtors:
#       dv, d = heapq.heappop(debtors)
#       cv, c = heapq.heappop(creditors)
#       q = min(-dv, -cv)
#       transfers.append((product, d, c, q))
#       if -dv > q: heapq.heappush(debtors, (dv + q, d))
#       if -cv > q: heapq.heappush(creditors, (cv + q, c))
#
# This particular shape avoids lazy deletion because each account is re-pushed with its
# updated amount rather than left stale. The reason it was not shipped: at this n the
# constant factor and the extra state are not worth it, and the O(n^2) version is the one
# a reviewer can check by eye. If accounts-per-product reached the thousands, switch --
# after measuring.

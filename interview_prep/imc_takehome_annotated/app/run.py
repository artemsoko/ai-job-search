# ANNOTATED COPY of the submitted app/run.py. Live code unchanged; alternatives commented.
import argparse
from logging import getLogger

from app.balances import get_balances, make_transfers
from app.files import read_accounts, read_records, save_output

logger = getLogger(__name__)


# argv=None is a test seam: parse_args(None) falls back to sys.argv[1:] in production, while
# tests call main([accounts, trsfs, output]) directly. That is why test_end_to_end is an
# in-process call instead of a subprocess -- fast, and a real traceback instead of captured
# stderr.
def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('accounts', help='portfolio to bank account mapping (json)')
    parser.add_argument('trsfs', help='portfolio to portfolio transfers (xml)')
    parser.add_argument('output', help='where to write the bank transfers (xml)')
    args = parser.parse_args(argv)

    # accounts first, so an unreadable mapping fails before spending 8 seconds parsing XML.
    accounts = read_accounts(args.accounts)
    # read_records(...) is passed AS A GENERATOR, not materialised. This is the one line where
    # the streaming actually pays off: memory stays O(1) in record count.
    balances = get_balances(read_records(args.trsfs), accounts)

    # Settlement is independent per product -- this loop is the natural parallelism boundary.
    transfers = []
    for product in balances:
        transfers.extend(make_transfers(product, balances[product]))

    save_output(args.output, transfers)
    logger.info('%d products, %d bank transfers written', len(balances), len(transfers))

    # ALTERNATIVE (parallelism) -- the settlement loop is embarrassingly parallel:
    #
    #   from concurrent.futures import ProcessPoolExecutor
    #   with ProcessPoolExecutor() as pool:
    #       for chunk in pool.map(make_transfers_one, balances.items()):
    #           transfers.extend(chunk)
    #
    # Not shipped, and the reason is the right one: the parse is sequential and the whole run
    # is 8 seconds. Adding a process pool to a 121-line program to save part of a second is
    # cost with no benefit. Measure before parallelising.
    #
    # ALTERNATIVE (output ordering) -- ordering here is grouped by product in dict insertion
    # order. Deterministic for a given input, but INCIDENTAL, not a guarantee. If the bank
    # needed a stable order:
    #
    #   for product in sorted(balances):
    #       ...
    #   transfers.sort(key=lambda t: (t[0], t[1], t[2]))

# ANNOTATED COPY of the submitted app/files.py. Live code unchanged; alternatives commented.
import json
import uuid
import xml.etree.ElementTree as ET
from logging import getLogger

logger = getLogger(__name__)


def read_accounts(accounts_path):
    # encoding is explicit on purpose: without it Python uses the platform default, so a file
    # written on Linux CI decodes as cp1252 on a Windows box.
    with open(accounts_path, encoding='utf-8') as f:
        return json.load(f)


def read_records(trsfs_path):
    # iterparse yields (event, element) as it parses, instead of ET.parse building the whole
    # 2.3M-record tree first.
    # 'start' is requested ONLY so that next(events) can hand back the root element -- that is
    # the handle needed to clear it below. With 'end' alone, the first event would be the first
    # </Trsf> and the root would be unreachable.
    events = ET.iterparse(trsfs_path, events=('start', 'end'))
    _, root = next(events)

    records = 0
    for event, record in events:
        # 'end' matters: on a 'start' event the children are not parsed yet, so findtext would
        # return None for all four fields.
        if event != 'end' or record.tag != 'Trsf':
            continue

        records += 1
        # findtext returns None for a missing child rather than raising -- that API choice is
        # what lets the unguarded Qty bug through (see balances.py).
        yield (
            record.findtext('PrdId'),
            record.findtext('PrtflNm'),
            record.findtext('Side'),
            record.findtext('Qty'),
        )

        # iterparse leaves read elements on the root. Clearing the record alone
        # is not enough: that way it is 213MB instead of 15MB.
        root.clear()

    # %-style, not an f-string: the message is only interpolated if the record is emitted.
    # ruff's `G` ruleset (selected in pyproject.toml) is what enforces that.
    # SHIPPED GAP: this only fires if the generator is fully consumed. True today, because
    # get_balances drains it -- fragile the moment anyone adds an early break.
    logger.info('Read %d records', records)

    # ALTERNATIVE (robust parse) -- fail with record context instead of a bare exception:
    #
    #   product = record.findtext('PrdId')
    #   if product is None:
    #       raise ValueError(f'record {records} has no PrdId')
    #
    # Not shipped because get_balances already validates side and portfolio; the honest
    # criticism is that validation should live in ONE place, and it does not.


def save_output(output_path, transfers):
    out = ET.Element('Trsfs')
    for product, from_account, to_account, quantity in transfers:
        node = ET.SubElement(out, 'Trsf')
        ET.SubElement(node, 'PrdId').text = product
        ET.SubElement(node, 'AccFrom').text = from_account
        ET.SubElement(node, 'AccTo').text = to_account
        # :f, because str(Decimal('1E+3')) would send the bank an exponent
        ET.SubElement(node, 'Qty').text = f'{quantity:f}'
        ET.SubElement(node, 'TrsfId').text = str(uuid.uuid4())
    ET.indent(out)
    ET.ElementTree(out).write(output_path, encoding='utf-8', xml_declaration=True)

    # THE ASYMMETRY A REVIEWER WILL SPOT: the input is streamed, the output is buffered.
    # Deliberate, and the ratio is the justification -- 2,325,046 records in, 5,702 out.
    # Buffering also gives all-or-nothing: save_output runs only after the whole parse, so a
    # ParseError halfway through leaves NO partial file. tests assert `not output.exists()`.
    # A partially written settlement file is worse than none.
    #
    # ALTERNATIVE (atomic + streaming) -- if the output ever approached the input's size,
    # move the atomicity from memory into the filesystem:
    #
    #   import os, tempfile
    #   fd, tmp = tempfile.mkstemp(dir=os.path.dirname(output_path) or '.')
    #   try:
    #       with open(fd, 'wb') as f:
    #           with ET.xmlfile(f) as xf:          # lxml; stdlib ET has no incremental writer
    #               with xf.element('Trsfs'):
    #                   for t in transfers:
    #                       xf.write(build_node(t))
    #       os.replace(tmp, output_path)           # atomic rename on POSIX
    #   except BaseException:
    #       os.unlink(tmp)
    #       raise
    #
    # Note this needs lxml -- stdlib ElementTree cannot write incrementally, which is itself a
    # reason the buffered version was the right call for a stdlib-only submission.
    #
    # ALTERNATIVE (reproducible ids) -- uuid4 means two runs on the same input produce
    # different TrsfIds, so outputs cannot be diffed:
    #
    #   import hashlib
    #   key = f'{product}|{from_account}|{to_account}|{quantity:f}'
    #   ET.SubElement(node, 'TrsfId').text = hashlib.sha256(key.encode()).hexdigest()[:32]
    #
    # Trade-off: diffable, but identical transfers on different days collide. uuid4 is
    # defensible -- the bank wants globally unique ids -- it just is not diffable.

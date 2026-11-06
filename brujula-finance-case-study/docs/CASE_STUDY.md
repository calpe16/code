# Making a financial import reviewable

## Problem

An overlapping statement can contain both genuine repeated purchases and duplicates.
Deleting every row with the same date and amount loses real expenses. Importing everything
counts the same activity twice. A changed bank reference also needs a visible resolution.

## Decisions

Money is represented in integer cents with an explicit currency. An existing bank reference
or a stable original-file/table/row identity provides stronger evidence than a similar description.
Similar rows without a shared reference are presented for review. Each previous occurrence
can consume only one possible match, so two real purchases are not collapsed into one.
Edits to a classification do not erase the original financial values used for comparison.

## Evidence

The public extraction has hand-checked tests for 1,234.56 = 123456 cents, two coffees at
2.50 each remaining two records, conflicting values for a shared reference, and file reimports.
The demo produces one record for each outcome. Run the tests to inspect the current result;
no test badge or historical test count substitutes for execution.

## My contribution and AI assistance

This is my personal product. I set the needs, worked on the implementation with AI tools,
and iterated through review and testing. The code and these portfolio materials were prepared
with AI assistance. My ability to explain and modify specific parts is separate from the
presence of those technologies in the project; this is not a claim of senior engineering experience.

## Limitations

This extraction expects structured rows and does not include a production CSV/XLSX parser,
authentication, persistence, the full UI or the synchronization service. It does not infer
exchange rates or guarantee that every possible bank format is supported. No commercial-user
counts, time savings, professional security audit or enterprise-scale performance are claimed.

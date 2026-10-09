# Current control: dated ownership and service, not six automatic years

October 9, 2026. Use `current-control/reviewed-v2/current-control.parquet`.
The first two outputs remain audit artifacts, not valuation inputs. This is
a reconstructed estimate, not an official MLB service register.

The current-rights table retains all 4,851 forecast identities: 600 resolved
from current 40-man membership, 3,420 from conclusive transactions, 34 from a
single broad-roster candidate with provisional status, 784 with an explicit
release/free-agent election, and 13 unresolved. The unresolved ownership cases
have negligible projected 2027 WAR; they are not silently assigned to old clubs.
Former-team contract liabilities are separate from ownership and remain payable
unless a verified term says otherwise.

Service balances are usable estimates for 4,428 players, representing 179,532
of 191,262 projected PA (93.9%) and 560.20 of 569.22 net projected WAR (98.4%).
423 players retain missing prior balances or uncertain intervals. Unresolved
service does not suppress their baseball forecast, become zero service, or
generate an exact control-value rank. Available interval bounds can support
explicit future-control scenarios without pretending the balance is exact.

## Source-to-calculation checks

The official season window is March 25–September 27. Thirty separately dated
Opening Day active-roster captures establish 775 active identities across both
hitters and pitchers. Injury and other dated transaction changes then determine
service states. Active, MLB IL and paid-list days accrue service up to 172;
national-team/All-Star activations do not remove MLB service.

Judge and Ohtani both receive 172 days despite injuries; totals become 10.051
and 9.000. Bailey's old Giants entry uses the terminal label Traded, which
previously lost his earlier active state. Dated active evidence and his trade
to Cleveland yield 172 days and 3.136 total. The trade transfers rights; it
does not restart or stop the service clock.

Eldridge is optioned March 19 and recalled May 4. May 4–September 27 is 147
days; the bereavement/MLB IL stints continue service. Add 14 prior days and his
balance is .161. A six-year control clock has not been consumed by one partial
season. Lovich and Concepcion remain .000, with no debut/service evidence.
Alexander Ramirez's rights resolve to the Cubs from the dated signing rather
than his stale team biography.

Opening Day roster checks repair the initial source gaps for Alonso (8.000),
Butler (3.032) and Hicks (2.000). Hicks's current Rays ownership does not erase
earlier Marlins service. Susac's MLB active/IL history yields 1.000 even though
his playing time is much smaller than a full season. This is why PA is not a
service-time proxy.

Pratt's April 3 selected-contract event is paired with an immediate option.
That establishes 40-man membership, not MLB active days. His June 16 recall
then yields 104 service days including MLB IL. The rule is not tied to his name
or arbitrary transaction-ID ordering. Marte's three uncertain restricted-list
days cannot alter the total: even the lower service bound reaches the 172 cap.
Other cases do not enjoy that certainty. Encarnacion-Strand retains a 74–79-day
current-season interval; Mauricio 91–92; Veen 58–172. These remain bounded
uncertainty, not guessed exact days.

Maldonado/Solano have no incumbent rights and missing old service balances;
their omission from exact current-control valuation is explicit. McCutchen
also has ambiguous events. A guaranteed historical payment, if present, is
not erased by any of those statuses.

## Execution correction and limits

The first reviewed runner reused the variable name for review mode and an
individual service balance. This could skip bounds on later players. The
appended reviewed-v2 run separates those variables and requires bounds on
EVERY identity; an accepted balance must have equal lower and upper bounds.
The earlier output is preserved and superseded. Unit coverage includes the
zero/unknown distinction, free-agent election versus generic DFA, exhibition
activation, option/selection pairs, missing roster membership and the cap.

Review complete for the source/control adapter. Do not call this complete
financial valuation: contract tails, deferred cash, linked options, arbitration,
minor-league reserve rules and uncertain future service still need integration.
Future rules are a stated continuation scenario, not a guaranteed future CBA.

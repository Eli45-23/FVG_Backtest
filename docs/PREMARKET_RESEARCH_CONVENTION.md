# Official MNQ premarket research convention

For new PMH/PML research and future strategy development, use **00:00 inclusive to 09:30 exclusive, America/New_York**, on the current New York calendar date. This is a deliberate research definition, not a futures-market opening time.

PMH is the maximum high and PML the minimum low of all 114 actual complete five-minute bars beginning at midnight through 09:25. Both become confirmed at 09:30 and remain frozen through the actual XNYS RTH close. Never use candles beginning at or after 09:30 in their construction. Use timezone-aware calendar dates so DST is respected.

Coverage requires the entire expected window. If any required candle is missing or incomplete, mark both levels unavailable for that date and export the missing starts. Do not synthesize candles or shorten the window.

Every new immutable study must explicitly store `premarket_start: "00:00"` and `premarket_end: "09:30"`. Existing disabled-premarket and older differently configured studies remain unchanged and are not equivalent evidence. This documentation supersedes 04:00–09:30 assumptions for new research; it does not mutate historical configurations or change production execution defaults.

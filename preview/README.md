# preview/ forwards to the current site

These were the static pages of the August 2026 Next.js version (source in `/v2`).
Since 4 Nov 2026 every page here forwards to its counterpart on the current site
(`/on-record/`): city pages to `?place=<slug>`, the section pages to the matching
beat. The `_next/` assets are no longer loaded by anything.

Rebuilding the v2 preview into this folder would replace the forwards.

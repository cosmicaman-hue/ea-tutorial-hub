# Excel Study Notes

Excel Study Notes is a PDF-only library organized as **Group -> Class ->
Subject -> Note**. The LAN app at `/scoreboard/excel-study-notes` is the
authoritative admin surface; this public-site folder is a published
projection containing only published hierarchy nodes and PDF files.

Students browse the hierarchy and open a PDF in a full-page reader. The
reader uses inline delivery, no-cache headers, a watermark, no download links,
and host-page copy/print/context-menu deterrence. Native PDF viewers vary;
`#toolbar=0` hides controls in viewers that honor the fragment, and the reader
container allows pinch zoom/full screen.

Administrators can add, rename, publish/unpublish, sort, and delete groups,
classes, subjects, and notes; upload or replace PDFs; save with optimistic
catalog revisions; export catalog JSON; and publish a sanitized static
snapshot to Cloudflare Pages.

The catalog is stored under `EA_STORAGE_ROOT/excel_study_notes/`. The live
scoreboard ledger is not modified. Removing a note or replacing its PDF cleans
the old private file after the catalog save.

## Security boundary

A browser must receive PDF bytes to render them, so a web page cannot
guarantee prevention of operating-system screenshots, screen recording, or a
determined user saving the network response. These controls are layered
deterrence and access control, not DRM. The public static projection also
means published PDFs are retrievable by URL; use the authenticated LAN route
for material that must not be publicly hosted. Absolute DRM requires a
dedicated secure document viewer/service and usually watermarking or device
policy outside this SPA.

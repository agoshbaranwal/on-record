import type { SiteImage } from "./images";

/**
 * The starting library, chosen to prove the principle rather than to fill space.
 * Repeat pairs and satellite frames first: public domain, evidentiary by construction, and the
 * causal chain is something the reader SEES instead of something we assert.
 */
export const IMAGES: SiteImage[] = [
  {
    id: "muir-1941", origin: "repeat_pair", mode: "illustrative",
    src: "/media/muir-1941.jpg", width: 1600, height: 1200,
    photographer: "William O. Field", agency: "NSIDC/WDC Glaciology",
    capturedOn: "1941-08-13", location: "Muir Glacier, Glacier Bay, Alaska",
    licence: "Public domain (US Government work)",
    credit: "W. O. Field, 13 August 1941 — NSIDC",
    caption: "Muir Glacier from Muir Inlet, Alaska, on 13 August 1941.",
    sourceSlug: "nsidc-repeat",
  },
  {
    id: "muir-2004", origin: "repeat_pair", mode: "illustrative",
    src: "/media/muir-2004.jpg", width: 1600, height: 1200,
    photographer: "Bruce F. Molnia", agency: "USGS",
    capturedOn: "2004-08-31", location: "Muir Glacier, Glacier Bay, Alaska",
    licence: "Public domain (US Government work)",
    credit: "B. F. Molnia, 31 August 2004 — USGS",
    caption: "The same view on 31 August 2004. The glacier has retreated out of sight.",
    sourceSlug: "usgs-repeat",
  },
];

export const pairs = () => {
  const byId = new Map(IMAGES.map((i) => [i.id, i]));
  return [{ before: byId.get("muir-1941")!, after: byId.get("muir-2004")! }].filter((p) => p.before && p.after);
};

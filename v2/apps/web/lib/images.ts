/**
 * Images, and the causation rule.
 *
 * A photograph of a flood implies a causal claim the data may not support. That is the single
 * hardest problem in putting photography on this site, so it is solved in the type system and then
 * again in CI, not in a style guide nobody reads.
 *
 * ILLUSTRATIVE (the default): the caption states WHAT IS DEPICTED — a named event, a named place,
 * a date. It may never contain a causal verb. "Kincade Fire, Sonoma County, 27 October 2019."
 *
 * EVIDENTIARY: only reachable by attaching a published attribution study, and then the causal
 * sentence belongs to the study and is quoted as theirs.
 *
 * REPEAT PAIRS are the shape we prefer: the same viewpoint decades apart. The causal chain is
 * visible rather than asserted, the sources are overwhelmingly public domain, and almost nobody
 * does them well. A wildfire photo is emotionally cheap and epistemically expensive; a glacier
 * pair is the opposite.
 */

export type ImageOrigin = "photograph" | "satellite" | "repeat_pair" | "archival" | "diagram";
// NOTE: there is deliberately no "generated". A generated image has no photographer, no date and
// no place — on this site it is the visual equivalent of an invented number.

export interface ImageBase {
  id: string;
  origin: ImageOrigin;
  src: string;
  width: number; height: number;
  photographer: string;
  agency?: string;
  capturedOn: string;   // ISO date
  location: string;
  licence: string;
  credit: string;
  caption: string;
  sourceSlug: string;
}
export interface IllustrativeImage extends ImageBase { mode: "illustrative" }
export interface EvidentiaryImage extends ImageBase {
  mode: "evidentiary";
  /** Only a published study licenses a causal statement, and its words are what we print. */
  study: { publisher: string; url: string; doi?: string; finding: string };
}
export type SiteImage = IllustrativeImage | EvidentiaryImage;

/** Verbs that assert causation. An illustrative caption containing one is a charter breach. */
export const CAUSAL_TERMS = [
  "caused by", "because of", "due to climate", "climate change caused",
  "driven by climate", "a result of climate", "proof of climate", "shows climate change",
];

export function captionProblem(img: SiteImage): string | null {
  const c = img.caption.toLowerCase();
  if (img.mode === "illustrative") {
    const hit = CAUSAL_TERMS.find((t) => c.includes(t));
    if (hit) return `illustrative caption asserts causation ("${hit}") — attach a study or rewrite`;
  }
  // Every caption must anchor the viewer in a real place and moment, or it is decoration.
  if (!/\d{4}/.test(img.caption)) return "caption does not state a year";
  if (img.caption.length < 12) return "caption too short to say what is depicted";
  return null;
}

/** The visible credit line. Provenance is rendered, not merely stored. */
export function creditLine(img: SiteImage): string {
  const who = img.agency ? `${img.photographer}/${img.agency}` : img.photographer;
  return `${who} · ${img.location} · ${img.capturedOn} · ${img.licence}`;
}

/**
 * The source register.
 *
 * Every row the ingestion writes must point at one of these, because `claims.source_id` and
 * `images.source_id` are NOT NULL foreign keys. Keeping the register in code (rather than typed by
 * hand into the database) means a fetcher cannot invent a provenance for its own output: it must
 * name a source that already exists here, and the seed refuses to build if it doesn't.
 */

export interface SourceDef {
  slug: string;
  name: string;
  organisation: string;
  url: string;
  licence: string;
  citation: string;
  kind: "dataset" | "paper" | "survey" | "agency" | "study" | "book";
}

export const SOURCES: Record<string, SourceDef> = {
  era5: {
    slug: "era5",
    name: "ERA5 reanalysis, daily 2m temperature",
    organisation: "ECMWF (Copernicus Climate Change Service), retrieved via Open-Meteo",
    url: "https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels",
    licence: "Copernicus Licence; Open-Meteo API CC BY 4.0",
    citation:
      "Hersbach, H. et al. (2020) The ERA5 global reanalysis. Q J R Meteorol Soc 146:1999–2049. Retrieved via Open-Meteo.",
    kind: "dataset",
  },
  noaa_co2: {
    slug: "noaa-co2",
    name: "Globally averaged marine surface CO₂, monthly and trend",
    organisation: "NOAA Global Monitoring Laboratory",
    url: "https://gml.noaa.gov/ccgg/trends/",
    licence: "Public domain (US Government work)",
    citation: "Lan, X., Tans, P. and Thoning, K. NOAA/GML. Trends in globally averaged CO₂.",
    kind: "agency",
  },
  igcc: {
    slug: "igcc-2025",
    name: "Indicators of Global Climate Change 2025 — remaining carbon budget",
    organisation: "Forster et al., Earth System Science Data",
    url: "https://essd.copernicus.org/articles/17/2625/2025/",
    licence: "CC BY 4.0",
    citation: "Forster, P. M. et al. (2025) Indicators of Global Climate Change. Earth Syst. Sci. Data.",
    kind: "paper",
  },
  gcb: {
    slug: "gcb-2025",
    name: "Global Carbon Budget 2025",
    organisation: "Global Carbon Project",
    url: "https://globalcarbonbudget.org/",
    licence: "CC BY 4.0",
    citation: "Friedlingstein, P. et al. (2025) Global Carbon Budget 2025. Earth Syst. Sci. Data.",
    kind: "dataset",
  },
  geonames: {
    slug: "geonames-cities",
    name: "GeoNames cities with population over 15,000",
    organisation: "GeoNames",
    url: "https://download.geonames.org/export/dump/",
    licence: "CC BY 4.0",
    citation: "GeoNames geographical database, cities15000.",
    kind: "dataset",
  },
  andre_2024: {
    slug: "andre-2024",
    name: "Globally representative evidence on the willingness to act on climate change",
    organisation: "Andre, Boneva, Chopra & Falk — via Our World in Data",
    url: "https://ourworldindata.org/climate-change-support",
    licence: "CC BY 4.0",
    citation:
      "Andre, P., Boneva, T., Chopra, F. & Falk, A. (2024) Globally representative evidence on the willingness to act on climate change. Nature Climate Change.",
    kind: "survey",
  },
};

export function requireSource(slug: keyof typeof SOURCES): SourceDef {
  const s = SOURCES[slug];
  // A fetcher that names a source we do not hold is a provenance hole; fail the run, never the row.
  if (!s) throw new Error(`ingest: unknown source "${String(slug)}" — add it to the register first`);
  return s;
}

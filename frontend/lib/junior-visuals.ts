/**
 * Pure presentation helpers for cited visual results. No image detection, AI,
 * inferred numerical values, or invented locations.
 */
export type VisualEvidence = { page: number; quote: string };
export type VisualFinding = {
  claim?: string;
  table_reference?: string;
  model_or_column?: string;
  direction?: string;
  estimate?: string;
  statistical_significance?: string;
  evidence?: VisualEvidence[];
  significance_legend_evidence?: VisualEvidence[];
  verification?: {
    status?: string;
    numeric_supported?: boolean;
    direction_consistent?: boolean | null;
    significance_supported?: boolean | null;
    unsupported_numeric_tokens?: string[];
  };
};
export type VisualCard = {
  kind: "table" | "chart";
  reference: string; claim: string; column: string; direction: string;
  estimate: string; significance: string; sourcePage: number | null;
  sourceQuote: string; legendPage: number | null; legendQuote: string;
  screening: "screen_passed" | "review_required";
};

function readable(value: unknown, max = 500): string {
  if (typeof value !== "string") return "";
  const normalized = value.replace(/\s+/g, " ").trim();
  return normalized.length > max ? normalized.slice(0, max - 1) + "…" : normalized;
}

function firstCitation(evidence?: VisualEvidence[]): VisualEvidence | null {
  if (!Array.isArray(evidence)) return null;
  for (const item of evidence) {
    if (item && Number.isSafeInteger(item.page) && item.page > 0 && readable(item.quote)) {
      return { page: item.page, quote: readable(item.quote, 300) };
    }
  }
  return null;
}

function isScreenPassed(finding: VisualFinding): boolean {
  const check = finding.verification;
  return Boolean(check?.status === "screen_passed"
    && check.numeric_supported !== false
    && check.direction_consistent !== false
    && check.significance_supported !== false
    && (!Array.isArray(check.unsupported_numeric_tokens) || check.unsupported_numeric_tokens.length === 0));
}

/** Show only explicit references. Never infer image pixels, graph axes, units or significance. */
export function buildVisualReadingCards(
  result: { findings?: VisualFinding[] } | null | undefined,
  maxCards = 6,
): VisualCard[] {
  const entries = Array.isArray(result?.findings) ? result.findings : [];
  const limit = Number.isFinite(maxCards) ? Math.max(0, Math.min(10, Math.floor(maxCards))) : 6;
  const cards: VisualCard[] = [];
  const seen = new Set<string>();
  for (const finding of entries) {
    if (!finding || typeof finding !== "object") continue;
    const reference = readable(finding.table_reference, 120);
    if (!reference) continue;
    const claim = readable(finding.claim, 550);
    const column = readable(finding.model_or_column, 160);
    const key = [reference, column, claim].join("|").toLocaleLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    const cite = firstCitation(finding.evidence);
    const legend = firstCitation(finding.significance_legend_evidence);
    cards.push({
      kind: /(?:\bfig(?:ure)?\.?\b|\bchart\b|\bplot\b|그림|그래프)/i.test(reference) ? "chart" : "table",
      reference, claim, column,
      direction: readable(finding.direction, 130),
      estimate: readable(finding.estimate, 130),
      significance: readable(finding.statistical_significance, 150),
      sourcePage: cite?.page ?? null,
      sourceQuote: cite?.quote ?? "",
      legendPage: legend?.page ?? null,
      legendQuote: legend?.quote ?? "",
      screening: isScreenPassed(finding) ? "screen_passed" : "review_required",
    });
    if (cards.length >= limit) break;
  }
  return cards.slice(0, limit);
}

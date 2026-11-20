/** Presentation-only beta helpers. Never expose provider errors or private URLs. */
export type UploadStage = "validation" | "storage" | "metadata";
export const MAX_PDF_BYTES = 30 * 1024 * 1024;
export function isAcceptedPdf(name: string, bytes: number, signature: string): boolean {
  return typeof name === "string" && /\.pdf$/i.test(name.trim()) &&
    Number.isSafeInteger(bytes) && bytes >= 5 && bytes <= MAX_PDF_BYTES && signature === "%PDF-";
}
function errorCode(error: unknown): string {
  if (!error || typeof error !== "object") return "";
  const record = error as { statusCode?: unknown; status?: unknown; code?: unknown; message?: unknown };
  return [record.statusCode, record.status, record.code, record.message]
    .filter((s): s is string | number => typeof s === "string" || typeof s === "number")
    .map(String).join(" ").slice(0, 400);
}
export function uploadFailureMessage(stage: UploadStage, error: unknown): string {
  const code = errorCode(error);
  if (/\b(401|403)\b|unauthori[sz]ed|jwt|session|token.*expired/i.test(code)) {
    return "로그인 상태를 확인하지 못했습니다. 다시 로그인한 뒤 업로드해 주세요. 진행 중인 업로드는 자동으로 재요청하지 않습니다.";
  }
  if (/\b413\b|payload too large|entity too large|file size/i.test(code)) {
    return "파일 크기 제한을 확인해 주세요. 30MB 이하의 PDF를 선택해야 합니다.";
  }
  if (stage === "metadata") {
    return "PDF 전송 후 논문 목록 등록에 실패했습니다. 먼저 목록을 새로고침하고 저장 여부를 확인하세요. 중복 업로드를 막기 위해 자동 재시도하지 않습니다.";
  }
  if (stage === "validation") return "파일을 확인하지 못했습니다. 30MB 이하의 정상 PDF를 다시 선택해 주세요.";
  return "PDF 업로드가 완료되지 않았습니다. 네트워크와 로그인 상태를 확인하고, 논문 목록에서 저장 여부를 확인한 다음 다시 선택해 주세요.";
}
const SAFE_USER_ID = /^[A-Za-z0-9_-]{8,64}$/;
export function betaGuideStorageKey(userId: string): string | null {
  return SAFE_USER_ID.test(userId) ? "papersignal:beta-guide:v1:" + userId : null;
}


/** Private Storage errors must not expose signed URL fragments or provider internals. */
export function sourcePdfFailureMessage(error: unknown): string {
  const reason = errorCode(error);
  if (/\b(401|403)\b|unauthori[sz]ed|jwt|token.*expired/i.test(reason)) {
    return "원본 PDF 접근 권한 또는 로그인 상태를 확인하지 못했습니다. 다시 로그인한 뒤 원문을 연결해 주세요.";
  }
  return "원본 PDF를 연결하지 못했습니다. 네트워크를 확인하고 '다시 연결' 또는 '링크 갱신'을 눌러주세요.";
}

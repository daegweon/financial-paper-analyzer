"use client";

import { useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";

export type EvidenceItem = { page: number; quote: string };

type Props = {
  items?: EvidenceItem[];
  sourcePdfUrl?: string;
  onOpenSourcePage?: (page: number) => void;
};

function excerpt(value: string, maxLength = 190) {
  const normalized = value.trim().replace(/\s+/g, " ");
  return normalized.length > maxLength ? normalized.slice(0, maxLength - 1) + "…" : normalized;
}

export function EvidenceHint({ items, sourcePdfUrl, onOpenSourcePage }: Props) {
  const evidence = (items ?? []).filter((item) =>
    Number.isInteger(item.page) && item.page > 0 && typeof item.quote === "string" && item.quote.trim().length > 0,
  );
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const popupRef = useRef<HTMLDivElement | null>(null);
  const closeRef = useRef<HTMLButtonElement | null>(null);
  const skipNextFocusPreview = useRef(false);
  const tooltipId = useId();
  const popoverId = useId();
  const headingId = useId();
  const [hovered, setHovered] = useState(false);
  const [focused, setFocused] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [pinned, setPinned] = useState(false);
  const [positionReady, setPositionReady] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 12, width: 320 });

  const previewOpen = (hovered || focused) && !pinned && !dismissed;
  const popupOpen = previewOpen || pinned;

  useEffect(() => {
    if (!popupOpen) {
      setPositionReady(false);
      return;
    }
    const updatePosition = () => {
      const trigger = triggerRef.current;
      const popup = popupRef.current;
      if (!trigger || !popup) return;
      const rect = trigger.getBoundingClientRect();
      const width = Math.min(360, Math.max(180, window.innerWidth - 24));
      const left = Math.max(12, Math.min(rect.left - 4, window.innerWidth - width - 12));
      const popupHeight = popup.getBoundingClientRect().height || (pinned ? 300 : 120);
      let top = rect.bottom + 8;
      if (top + popupHeight > window.innerHeight - 12) {
        top = Math.max(12, rect.top - popupHeight - 8);
      }
      setPosition({ top, left, width });
      setPositionReady(true);
    };
    updatePosition();
    window.addEventListener("resize", updatePosition);
    window.addEventListener("scroll", updatePosition, { capture: true, passive: true });
    return () => {
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition, true);
    };
  }, [popupOpen, pinned, evidence.length]);

  useEffect(() => {
    if (pinned) closeRef.current?.focus();
  }, [pinned]);

  useEffect(() => {
    if (!popupOpen) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      if (pinned) {
        setPinned(false);
        setHovered(false);
        setFocused(true);
        setDismissed(true);
        skipNextFocusPreview.current = true;
        triggerRef.current?.focus();
      } else {
        setHovered(false);
        setDismissed(true);
      }
    };
    const handlePointerDown = (event: PointerEvent) => {
      if (!pinned || !(event.target instanceof Node)) return;
      if (triggerRef.current?.contains(event.target) || popupRef.current?.contains(event.target)) return;
      setPinned(false);
      setHovered(false);
      setFocused(false);
      setDismissed(true);
    };
    document.addEventListener("keydown", handleKeyDown);
    if (pinned) document.addEventListener("pointerdown", handlePointerDown, true);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.removeEventListener("pointerdown", handlePointerDown, true);
    };
  }, [popupOpen, pinned]);

  function closePopover(restoreFocus: boolean) {
    setPinned(false);
    setHovered(false);
    setFocused(restoreFocus);
    setDismissed(true);
    if (restoreFocus) {
      skipNextFocusPreview.current = true;
      triggerRef.current?.focus();
    }
  }

  if (!evidence.length) return null;

  const first = evidence[0];
  const popup = popupOpen && typeof document !== "undefined"
    ? createPortal(
        <div
          ref={popupRef}
          id={pinned ? popoverId : tooltipId}
          className={pinned ? "evidence-popup evidence-popover" : "evidence-popup evidence-preview"}
          role={pinned ? "dialog" : "tooltip"}
          aria-label={pinned ? undefined : "원문 인용 미리보기"}
          aria-labelledby={pinned ? headingId : undefined}
          aria-modal={pinned ? false : undefined}
          tabIndex={pinned ? -1 : undefined}
          data-testid={pinned ? "evidence-popover" : "evidence-preview"}
          style={{
            position: "fixed",
            top: position.top,
            left: position.left,
            width: position.width,
            visibility: positionReady ? "visible" : "hidden",
          }}
          onPointerEnter={(event) => {
            if (event.pointerType !== "touch") setHovered(true);
          }}
          onPointerLeave={(event) => {
            if (event.relatedTarget instanceof Node && triggerRef.current?.contains(event.relatedTarget)) return;
            if (!pinned) setHovered(false);
          }}
          onBlurCapture={(event) => {
            if (!pinned) return;
            if (event.relatedTarget instanceof Node
              && (popupRef.current?.contains(event.relatedTarget) || triggerRef.current?.contains(event.relatedTarget))) return;
            setPinned(false);
            setFocused(false);
            setHovered(false);
            setDismissed(true);
            setPositionReady(false);
          }}
        >
          {pinned ? (
            <>
              <div className="evidence-popover-header">
                <div>
                  <strong id={headingId}>검증된 원문 근거</strong>
                  <span>{evidence.length}건 · 원문 인용</span>
                </div>
                <button ref={closeRef} type="button" className="evidence-popover-close"
                  aria-label="근거 창 닫기" onClick={() => closePopover(true)}>×</button>
              </div>
              <div className="evidence-popover-body">
                {evidence.map((item, index) => (
                  <article className="evidence-popover-item" key={item.page + "-" + index}>
                    <div className="evidence-popover-page">원문 p.{item.page}</div>
                    <p>{item.quote}</p>
                    {onOpenSourcePage ? (
                      <button type="button" className="evidence-popover-link"
                        onClick={() => {
                          closePopover(false);
                          onOpenSourcePage(item.page);
                        }}>
                        원본 PDF p.{item.page}에서 확인 ↗
                      </button>
                    ) : sourcePdfUrl ? (
                      <a className="evidence-popover-link" href={sourcePdfUrl + "#page=" + item.page}
                        target="_blank" rel="noreferrer">원문 p.{item.page} 확인 ↗</a>
                    ) : (
                      <span className="evidence-popover-note">원본 PDF 연결 후 페이지 이동 가능</span>
                    )}
                  </article>
                ))}
              </div>
              <p className="evidence-popover-footnote">인용문은 원문 확인을 돕는 발췌입니다. 해석과 수치는 PDF 원문에서 최종 대조하세요.</p>
            </>
          ) : (
            <div className="evidence-preview-content">
              <span className="evidence-preview-page">p.{first.page}</span>
              <p>{excerpt(first.quote)}</p>
              <span className="evidence-preview-more">{evidence.length > 1 ? `외 ${evidence.length - 1}건 · 클릭해 전체 근거 보기` : "클릭해 원문 페이지 확인"}</span>
            </div>
          )}
        </div>,
        document.body,
      )
    : null;

  return (
    <>
      <span className="evidence-hint" onPointerEnter={(event) => {
        if (event.pointerType !== "touch") {
          setHovered(true);
          setDismissed(false);
        }
      }} onPointerLeave={(event) => {
        if (event.relatedTarget instanceof Node && popupRef.current?.contains(event.relatedTarget)) return;
        setHovered(false);
        if (!focused) setDismissed(false);
      }}>
        <button
          ref={triggerRef}
          type="button"
          className="evidence-hint-trigger"
          aria-label={`원문 근거 ${evidence.length}건 보기`}
          aria-haspopup="dialog"
          aria-expanded={pinned}
          aria-describedby={previewOpen ? tooltipId : undefined}
          data-testid="evidence-hint-trigger"
          onFocus={() => {
            setFocused(true);
            if (skipNextFocusPreview.current) skipNextFocusPreview.current = false;
            else setDismissed(false);
          }}
          onBlur={(event) => {
            if (event.relatedTarget instanceof Node && popupRef.current?.contains(event.relatedTarget)) return;
            setFocused(false);
            if (!pinned) setDismissed(false);
          }}
          onClick={() => {
            setPositionReady(false);
            if (pinned) {
              setPinned(false);
              setDismissed(true);
              setFocused(true);
            } else {
              setPinned(true);
              setHovered(false);
              setDismissed(false);
            }
          }}
        >
          <span aria-hidden="true">i</span>
        </button>
      </span>
      {popup}
      <span className="evidence-print" data-testid="evidence-print">
        {evidence.map((item, index) => (
          <span className="evidence-print-item" key={item.page + "-print-" + index}>
            <strong>원문 p.{item.page}</strong>
            <span>{item.quote}</span>
          </span>
        ))}
      </span>
    </>
  );
}

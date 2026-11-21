"use client";

import { useEffect, useId, useRef, useState } from "react";
import type { MouseEvent as ReactMouseEvent, PointerEvent as ReactPointerEvent, ReactNode } from "react";

export type EvidenceCitation = { page: number; quote: string };

type Props = {
  items?: EvidenceCitation[];
  sourcePdfUrl?: string;
  onOpenSourcePage?: (page: number) => void;
  label?: string;
  children?: ReactNode;
};

type Position = { left: number; top: number };

export function EvidencePopover({
  items,
  sourcePdfUrl,
  onOpenSourcePage,
  label = "원문 근거",
  children,
}: Props) {
  const rootRef = useRef<HTMLSpanElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);
  const tooltipId = useId();
  const [open, setOpen] = useState(false);
  const [pinned, setPinned] = useState(false);
  const [position, setPosition] = useState<Position>({ left: 24, top: 80 });

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: PointerEvent) => {
      if (pinned && rootRef.current && !rootRef.current.contains(event.target as Node)) {
        setOpen(false);
        setPinned(false);
      }
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopImmediatePropagation();
        setOpen(false);
        setPinned(false);
        if (popoverRef.current?.contains(document.activeElement)) buttonRef.current?.focus();
      }
    };
    document.addEventListener("pointerdown", onPointerDown);
    // Capture before the parent report dialog can interpret Escape as "close report".
    window.addEventListener("keydown", onKeyDown, true);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("keydown", onKeyDown, true);
    };
  }, [open, pinned]);

  if (!items?.length) return null;

  const placeAt = (clientX: number, clientY: number) => {
    const width = Math.min(340, window.innerWidth - 24);
    const estimatedHeight = Math.min(260, window.innerHeight - 24);
    setPosition({
      left: Math.max(12, Math.min(clientX + 14, window.innerWidth - width - 12)),
      top: Math.max(12, Math.min(clientY + 14, window.innerHeight - estimatedHeight - 12)),
    });
  };

  const onPointerEnter = (event: ReactPointerEvent<HTMLSpanElement>) => {
    if (event.pointerType !== "mouse" || pinned) return;
    placeAt(event.clientX, event.clientY);
    setOpen(true);
  };
  const onPointerMove = (event: ReactPointerEvent<HTMLSpanElement>) => {
    if (event.pointerType === "mouse" && open && !pinned &&
      !popoverRef.current?.contains(event.target as Node)) {
      placeAt(event.clientX, event.clientY);
    }
  };
  const onPointerLeave = (event: ReactPointerEvent<HTMLSpanElement>) => {
    if (event.pointerType === "mouse" && !pinned) setOpen(false);
  };
  const onClick = (event: ReactMouseEvent<HTMLButtonElement>) => {
    if (pinned) {
      setPinned(false);
      setOpen(false);
      return;
    }
    const rect = event.currentTarget.getBoundingClientRect();
    placeAt(event.clientX || rect.left + rect.width / 2, event.clientY || rect.bottom);
    setPinned(true);
    setOpen(true);
  };

  return <span
    ref={rootRef}
    className="evidence-popover-anchor"
    onPointerEnter={onPointerEnter}
    onPointerMove={onPointerMove}
    onPointerLeave={onPointerLeave}
    onFocus={(event) => {
      if (!rootRef.current?.contains(event.relatedTarget as Node | null)) setOpen(true);
    }}
    onBlur={(event) => {
      if (!rootRef.current?.contains(event.relatedTarget as Node | null) && !pinned) setOpen(false);
    }}
  >
    {children != null && <span className="evidence-inline-copy">{children}</span>}
    <button
      ref={buttonRef}
      type="button"
      className="evidence-info-button"
      aria-label={`${label} 확인, PDF ${items.map(item => item.page).join(", ")}페이지`}
      aria-expanded={open}
      aria-controls={tooltipId}
      aria-haspopup="true"
      title="마우스를 올리거나 클릭하면 원문 근거를 확인할 수 있습니다"
      onClick={onClick}
    >i</button>
    <div
      ref={popoverRef}
      id={tooltipId}
      className={`evidence-popover${open ? " is-open" : ""}`}
      role="group"
      aria-label={label}
      aria-hidden={!open}
      style={{ left: position.left, top: position.top }}
    >
      <div className="evidence-popover-heading">
        <strong>{label}</strong>
        <span>{items.length}개 근거</span>
      </div>
      <div className="evidence-popover-items">
        {items.map((item, index) => <section className="evidence-popover-item" key={item.page + "-" + index}>
          <div className="evidence-popover-page">원문 p.{item.page}</div>
          <p>{item.quote}</p>
          {sourcePdfUrl && Number.isInteger(item.page) && item.page > 0 &&
            (onOpenSourcePage
              ? <button type="button" className="evidence-popover-link" onClick={() => onOpenSourcePage(item.page)}>
                  원문 페이지 함께 보기 ↗
                </button>
              : <a className="evidence-popover-link" href={sourcePdfUrl + "#page=" + item.page} target="_blank" rel="noreferrer">
                  원문 페이지 확인 ↗
                </a>)}
        </section>)}
      </div>
      {pinned && <div className="evidence-popover-footer">바깥을 클릭하거나 ESC를 누르면 닫힙니다</div>}
    </div>
  </span>;
}

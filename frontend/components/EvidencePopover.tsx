"use client";

import { useEffect, useId, useRef, useState } from "react";
import styles from "./EvidencePopover.module.css";

export type EvidencePopoverItem = { page: number; quote: string };

type Props = {
  items?: EvidencePopoverItem[];
  sourcePdfUrl?: string;
  onOpenSourcePage?: (page: number) => void;
  className?: string;
};

export function EvidencePopover({ items, sourcePdfUrl, onOpenSourcePage, className }: Props) {
  const id = useId();
  const rootRef = useRef<HTMLSpanElement | null>(null);
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const suppressNextFocusRef = useRef(false);
  const [pinned, setPinned] = useState(false);
  const [hovered, setHovered] = useState(false);
  const [focused, setFocused] = useState(false);
  const visible = pinned || hovered || focused;

  useEffect(() => {
    if (!visible) return;
    const onPointerDown = (event: PointerEvent) => {
      if (rootRef.current?.contains(event.target as Node)) return;
      setPinned(false);
      setHovered(false);
      setFocused(false);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      setPinned(false);
      setHovered(false);
      setFocused(false);
      if (document.activeElement !== triggerRef.current) {
        suppressNextFocusRef.current = true;
        triggerRef.current?.focus();
      }
    };
    document.addEventListener("pointerdown", onPointerDown, true);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown, true);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [visible]);

  if (!items?.length) return null;
  const validItems = items.filter((item) => Number.isInteger(item.page) && item.page > 0 && item.quote?.trim());
  if (!validItems.length) return null;

  function closePopover() {
    setPinned(false);
    setHovered(false);
    setFocused(false);
    suppressNextFocusRef.current = true;
    triggerRef.current?.focus();
  }

  return (
    <span
      className={styles.root + (className ? " " + className : "")}
      data-evidence-trigger="true"
      ref={rootRef}
      onPointerEnter={() => setHovered(true)}
      onPointerLeave={() => setHovered(false)}
      onFocusCapture={() => {
        if (suppressNextFocusRef.current) {
          suppressNextFocusRef.current = false;
          setFocused(false);
        } else {
          setFocused(true);
        }
      }}
      onBlurCapture={(event) => {
        if (!rootRef.current?.contains(event.relatedTarget as Node | null)) setFocused(false);
      }}
    >
      <button
        ref={triggerRef}
        type="button"
        className={styles.trigger}
        data-evidence-trigger-button="true"
        aria-label={`원문 근거 ${validItems.length}건 확인`}
        aria-expanded={visible}
        aria-controls={id}
        onClick={() => {
          if (pinned) {
            setPinned(false);
            setHovered(false);
            setFocused(false);
            triggerRef.current?.blur();
          } else {
            setPinned(true);
          }
        }}
      >
        <span aria-hidden="true">i</span>
      </button>
      <span
        id={id}
        className={styles.popover}
        data-open={visible ? "true" : "false"}
        data-evidence-popover="true"
        role="group"
        aria-label={`원문 근거 ${validItems.length}건`}
        aria-hidden={!visible}
      >
        <span className={styles.popoverHeader}>
          <strong>원문 근거</strong>
          <span>{validItems.length}건</span>
          <button type="button" className={styles.close} data-evidence-close="true" aria-label="근거 팝오버 닫기" onClick={closePopover}>×</button>
        </span>
        <span className={styles.items}>
          {validItems.map((item, index) => (
            <span className={styles.item} key={item.page + "-" + index}>
              <span className={styles.page}>PDF p.{item.page}</span>
              <span className={styles.quote}>{item.quote}</span>
              {sourcePdfUrl && (
                onOpenSourcePage
                  ? <button type="button" className={styles.sourceLink} onClick={() => onOpenSourcePage(item.page)}>
                      원문 p.{item.page} 함께 보기 ↗
                    </button>
                  : <a className={styles.sourceLink} href={sourcePdfUrl + "#page=" + item.page} target="_blank" rel="noreferrer">
                      원문 p.{item.page} 확인 ↗
                    </a>
              )}
            </span>
          ))}
        </span>
      </span>
    </span>
  );
}

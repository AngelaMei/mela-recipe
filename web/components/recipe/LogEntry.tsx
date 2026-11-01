import type { CookLog } from "@/lib/types";

export interface LogEntryProps {
  log: CookLog;
  date: string;
  ratingLabel?: string;
  tweaksLabel: string;
  byLabel: string;
  onOpen?: () => void;
}

export function LogEntry({ log, date, ratingLabel, tweaksLabel, byLabel, onOpen }: LogEntryProps) {
  return (
    <li>
      <button type="button" className="log-entry" onClick={onOpen}>
        <span className="log-entry__head">
          <span className="log-entry__date">{date}</span>
          {log.rating ? (
            <span className="log-entry__rating" aria-label={ratingLabel}>
              {"★".repeat(log.rating)}
              {"☆".repeat(5 - log.rating)}
            </span>
          ) : null}
        </span>
        {log.note && <p className="log-entry__note">{log.note}</p>}
        {log.tweaks && (
          <p className="log-entry__tweaks">
            <strong>{tweaksLabel}:</strong> {log.tweaks}
          </p>
        )}
        {log.photo_url && <img className="log-entry__photo" src={log.photo_url} alt="" loading="lazy" />}
        <span className="log-entry__by" style={{ display: "block" }}>{byLabel}</span>
      </button>
    </li>
  );
}

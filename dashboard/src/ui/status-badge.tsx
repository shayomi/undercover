import type { DecisionKind, Status } from "../lib/api";
import { decisionLabel, statusLabel } from "../lib/format";

export function StatusBadge({ status }: Readonly<{ status: Status }>) {
  return (
    <span className={`badge status-${status}`}>{statusLabel(status)}</span>
  );
}

export function DecisionBadge({
  decision,
}: Readonly<{ decision: DecisionKind }>) {
  return (
    <span className={`badge decision-${decision}`}>
      {decisionLabel(decision)}
    </span>
  );
}

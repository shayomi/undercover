import { useState } from "react";
import { api } from "../lib/api";

interface Props {
  claimId: string;
  onStarted: () => void;
}

export function RunAgentButton({ claimId, onStarted }: Readonly<Props>) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const start = () => {
    setBusy(true);
    setError(null);
    api
      .runAgent(claimId)
      .then(onStarted, (reason: unknown) => {
        setError(String(reason));
      })
      .finally(() => {
        setBusy(false);
      });
  };

  return (
    <span className="run-agent">
      <button type="button" onClick={start} disabled={busy}>
        Run agent
      </button>
      {error && <span role="alert">{error}</span>}
    </span>
  );
}

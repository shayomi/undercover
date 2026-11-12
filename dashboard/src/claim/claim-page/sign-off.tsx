import { useState } from "react";
import { api } from "../../lib/api";
import { useResource } from "../../lib/use-resource";

interface Props {
  claimId: string;
  onSignedOff: () => void;
}

export function SignOff({ claimId, onSignedOff }: Readonly<Props>) {
  const { data: handlers } = useResource(api.listHandlers);
  const [handlerId, setHandlerId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const allowed = (handlers ?? []).filter((h) => h.can_approve_over_limit);

  const signOff = () => {
    setError(null);
    api.signOff(claimId, handlerId).then(onSignedOff, (reason: unknown) => {
      setError(String(reason));
    });
  };

  return (
    <div className="sign-off">
      <p>
        This payout is over $1,000.00, so the payment waits for a handler's
        sign-off.
      </p>
      <label>
        Handler{" "}
        <select
          value={handlerId}
          onChange={(event) => {
            setHandlerId(event.target.value);
          }}
        >
          <option value="">Choose a handler</option>
          {allowed.map((handler) => (
            <option key={handler.handler_id} value={handler.handler_id}>
              {handler.name}, {handler.role}
            </option>
          ))}
        </select>
      </label>{" "}
      <button type="button" onClick={signOff} disabled={!handlerId}>
        Sign off payment
      </button>
      {error && <p role="alert">{error}</p>}
    </div>
  );
}

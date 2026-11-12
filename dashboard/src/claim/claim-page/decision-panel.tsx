import type { Claim } from "../../lib/api";
import { money } from "../../lib/format";
import { DecisionBadge } from "../../ui/status-badge";
import { SignOff } from "./sign-off";

interface Props {
  claim: Claim;
  onSignedOff: () => void;
}

export function DecisionPanel({ claim, onSignedOff }: Readonly<Props>) {
  const { decision, payment } = claim;
  if (!decision) {
    return (
      <section className="panel">
        <h2>Decision</h2>
        <p className="note">The agent has not decided this claim yet.</p>
      </section>
    );
  }
  return (
    <section className="panel decision">
      <h2>Decision</h2>
      <p className="decision-line">
        <DecisionBadge decision={decision.decision} />
        <span className="payout mono">{money(decision.payout)}</span>
      </p>
      <p>{decision.reason}</p>
      <p className="section-ref">{decision.policy_section}</p>
      {payment && (
        <p className="paid">
          Paid <span className="mono">{money(payment.amount)}</span>
          {decision.signed_off_by && (
            <> · signed off by {decision.signed_off_by}</>
          )}
        </p>
      )}
      {!payment &&
        decision.decision === "approve" &&
        claim.status === "decided" && <p className="note">Not paid yet.</p>}
      {claim.status === "awaiting_sign_off" && (
        <SignOff claimId={claim.claim_id} onSignedOff={onSignedOff} />
      )}
    </section>
  );
}

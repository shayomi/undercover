import { humanize } from "../../lib/format";
import { RunAgentButton } from "../../ui/run-agent-button";
import { StatusBadge } from "../../ui/status-badge";
import { Activity } from "./activity";
import { ClaimStory } from "./claim-story";
import { DecisionPanel } from "./decision-panel";
import { PolicyPanel } from "./policy-panel";
import { useClaimPage } from "./use-claim-page";

export function ClaimPage({ claimId }: Readonly<{ claimId: string }>) {
  const { data, error, reload, agentStarted } = useClaimPage(claimId);

  if (error)
    return (
      <p role="alert">
        Could not load {claimId}: {error}
      </p>
    );
  if (!data) return <p>Loading {claimId}</p>;
  const { claim, steps } = data;

  return (
    <>
      <p className="crumbs">
        <a href="#/">Queue</a> / <span className="mono">{claim.claim_id}</span>
      </p>
      <div className="claim-heading">
        <h1>{claim.summary}</h1>
        <StatusBadge status={claim.status} />
        {claim.status === "waiting" && (
          <RunAgentButton claimId={claim.claim_id} onStarted={agentStarted} />
        )}
      </div>
      <p className="note">
        <span className="mono">{claim.claim_id}</span> ·{" "}
        {humanize(claim.claim_type)} · {claim.customer.name} ·{" "}
        {claim.incident_location}
      </p>
      <div className="claim-grid">
        <div className="column">
          <DecisionPanel claim={claim} onSignedOff={reload} />
          <ClaimStory claim={claim} />
        </div>
        <div className="column">
          <Activity steps={steps} working={claim.status === "in_progress"} />
          <PolicyPanel claim={claim} />
        </div>
      </div>
    </>
  );
}

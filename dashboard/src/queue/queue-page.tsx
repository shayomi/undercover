import { api } from "../lib/api";
import { STATUSES, humanize, money, statusLabel } from "../lib/format";
import { useResource } from "../lib/use-resource";
import { RunAgentButton } from "../ui/run-agent-button";
import { DecisionBadge, StatusBadge } from "../ui/status-badge";

const ALWAYS = { everyMs: 2000, while: () => true };

export function QueuePage() {
  const { data: claims, error, reload } = useResource(api.listClaims, ALWAYS);

  if (error) return <p role="alert">Could not load the queue: {error}</p>;
  if (!claims) return <p>Loading the queue</p>;

  return (
    <>
      <h1>Claims queue</h1>
      <section className="counts" aria-label="Claims by state">
        {STATUSES.map((status) => (
          <div key={status} className={`count count-${status}`}>
            <span className="number">
              {claims.filter((c) => c.status === status).length}
            </span>
            <span>{statusLabel(status)}</span>
          </div>
        ))}
      </section>
      <section className="panel">
        <table>
          <thead>
            <tr>
              <th>Claim</th>
              <th>Type</th>
              <th>Customer</th>
              <th className="amount">Claimed</th>
              <th>Submitted</th>
              <th>State</th>
              <th>Decision</th>
              <th>
                <span className="visually-hidden">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {claims.map((claim) => (
              <tr key={claim.claim_id}>
                <td>
                  <a className="mono" href={`#/claims/${claim.claim_id}`}>
                    {claim.claim_id}
                  </a>
                </td>
                <td>{humanize(claim.claim_type)}</td>
                <td>{claim.customer_name}</td>
                <td className="amount mono">{money(claim.amount_claimed)}</td>
                <td className="mono">{claim.submitted_on}</td>
                <td>
                  <StatusBadge status={claim.status} />
                </td>
                <td>
                  {claim.decision && (
                    <>
                      <DecisionBadge decision={claim.decision} />{" "}
                      <span className="mono">{money(claim.payout ?? 0)}</span>
                    </>
                  )}
                </td>
                <td>
                  {claim.status === "waiting" && (
                    <RunAgentButton
                      claimId={claim.claim_id}
                      onStarted={reload}
                    />
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}

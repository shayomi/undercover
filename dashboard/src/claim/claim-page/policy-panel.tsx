import type { Claim } from "../../lib/api";
import { humanize, money } from "../../lib/format";

export function PolicyPanel({ claim }: Readonly<{ claim: Claim }>) {
  const { policy, customer } = claim;
  return (
    <>
      <section className="panel">
        <h2>Policy</h2>
        <dl className="facts">
          <dt>Policy</dt>
          <dd className="mono">{policy.policy_id}</dd>
          <dt>Plan</dt>
          <dd>{humanize(policy.plan)}</dd>
          <dt>Add-ons</dt>
          <dd>
            {policy.add_ons.length
              ? policy.add_ons.map(humanize).join(", ")
              : "None"}
          </dd>
          <dt>Bought</dt>
          <dd className="mono">{policy.purchased_on}</dd>
          <dt>Trip</dt>
          <dd>
            {policy.trip.destination},{" "}
            <span className="mono">
              {policy.trip.departs_on} to {policy.trip.returns_on}
            </span>
          </dd>
          <dt>Trip cost</dt>
          <dd className="mono">{money(policy.trip.trip_cost)}</dd>
          <dt>Travelers</dt>
          <dd>{policy.travelers.join(", ")}</dd>
        </dl>
      </section>
      <section className="panel">
        <h2>Earlier claims</h2>
        {customer.previous_claims.length === 0 && (
          <p className="note">No earlier claims.</p>
        )}
        <ul className="history">
          {customer.previous_claims.map((previous) => (
            <li key={previous.claim_id}>
              <span className="mono">{previous.filed_on}</span>{" "}
              {previous.summary} · {humanize(previous.outcome)}{" "}
              <span className="mono">{money(previous.amount_paid)}</span>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}

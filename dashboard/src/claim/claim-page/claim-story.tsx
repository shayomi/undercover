import type { Claim } from "../../lib/api";
import { humanize, money } from "../../lib/format";

export function ClaimStory({ claim }: Readonly<{ claim: Claim }>) {
  return (
    <>
      <section className="panel">
        <h2>The customer's story</h2>
        <p className="mono small">
          Incident {claim.incident_date} · submitted {claim.submitted_on}
        </p>
        <p>{claim.story}</p>
      </section>
      <section className="panel">
        <h2>Items claimed</h2>
        <table>
          <thead>
            <tr>
              <th>Item</th>
              <th>Category</th>
              <th className="amount">Amount</th>
            </tr>
          </thead>
          <tbody>
            {claim.items.map((item) => (
              <tr key={item.description}>
                <td>{item.description}</td>
                <td>{humanize(item.category)}</td>
                <td className="amount mono">{money(item.amount)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <th colSpan={2}>Total claimed</th>
              <td className="amount mono">{money(claim.amount_claimed)}</td>
            </tr>
          </tfoot>
        </table>
      </section>
      <section className="panel">
        <h2>Documents</h2>
        {claim.documents.map((document) => (
          <article key={document.name} className="document">
            <h3>{document.name}</h3>
            <p>{document.content}</p>
          </article>
        ))}
      </section>
    </>
  );
}

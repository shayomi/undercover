import type { Step } from "../../lib/api";

const KIND_LABELS: Record<Step["kind"], string> = {
  tool_call: "Calls",
  tool_result: "Gets back",
  answer: "Finishes",
  error: "Stops",
};

export function Activity({
  steps,
  working,
}: Readonly<{
  steps: Step[];
  working: boolean;
}>) {
  return (
    <section className="panel" aria-live="polite">
      <h2>Agent activity</h2>
      {working && (
        <p className="working">The agent is working on this claim.</p>
      )}
      {steps.length === 0 && (
        <p className="note">The agent has not worked on this claim yet.</p>
      )}
      <ol className="steps">
        {steps.map((step) => (
          <li key={step.id} className={`step step-${step.kind}`}>
            <span className="step-kind">{KIND_LABELS[step.kind]}</span>
            <span className="step-text">{step.text}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}

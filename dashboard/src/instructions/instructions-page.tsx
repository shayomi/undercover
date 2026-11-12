import { api } from "../lib/api";
import { useResource } from "../lib/use-resource";

export function InstructionsPage() {
  const { data, error } = useResource(api.getInstructions);

  if (error)
    return <p role="alert">Could not load the instructions: {error}</p>;
  if (!data) return <p>Loading the instructions</p>;

  return (
    <>
      <h1>Agent instructions</h1>
      <p className="note">
        What the UnderCover Agent is told before each claim. Read only.
      </p>
      <section className="panel">
        <pre className="instructions">{data.text}</pre>
      </section>
    </>
  );
}

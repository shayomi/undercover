import { useCallback, useMemo, useState } from "react";
import { api, type Claim, type Step } from "../../lib/api";
import { useResource } from "../../lib/use-resource";

export interface ClaimView {
  claim: Claim;
  steps: Step[];
}

function finished(steps: Step[]): boolean {
  return steps.some((step) => step.kind === "answer" || step.kind === "error");
}

/** The claim and the agent's steps, refreshed every second while the agent works. */
export function useClaimPage(claimId: string) {
  // The number of steps when the agent was started here, so the page keeps
  // refreshing until that run finishes, including its payment after the decision.
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const load = useCallback(
    () =>
      Promise.all([api.getClaim(claimId), api.listSteps(claimId)]).then(
        ([claim, steps]): ClaimView => ({ claim, steps }),
      ),
    [claimId],
  );
  const refresh = useMemo(
    () => ({
      everyMs: 1000,
      while: ({ claim, steps }: ClaimView) =>
        claim.status === "in_progress" ||
        (startedAt !== null && !finished(steps.slice(startedAt))),
    }),
    [startedAt],
  );
  const resource = useResource(load, refresh);
  const stepCount = resource.data?.steps.length ?? 0;
  return {
    ...resource,
    agentStarted: () => {
      setStartedAt(stepCount);
    },
  };
}

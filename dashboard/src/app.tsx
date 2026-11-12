import { ClaimPage } from "./claim/claim-page";
import { InstructionsPage } from "./instructions/instructions-page";
import { useHashRoute } from "./lib/use-hash-route";
import { QueuePage } from "./queue/queue-page";
import { Header } from "./shell/header";

const CLAIM_ROUTE = "/claims/";

function Page({ route }: Readonly<{ route: string }>) {
  if (route.startsWith(CLAIM_ROUTE)) {
    const claimId = route.slice(CLAIM_ROUTE.length);
    return <ClaimPage key={claimId} claimId={claimId} />;
  }
  if (route === "/instructions") return <InstructionsPage />;
  return <QueuePage />;
}

export function App() {
  const route = useHashRoute();
  return (
    <>
      <Header route={route} />
      <main className="page">
        <Page route={route} />
      </main>
    </>
  );
}

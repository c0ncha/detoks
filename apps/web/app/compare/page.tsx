import { Suspense } from "react";
import ComparePage from "./ComparePage";

export default function Page() {
  return (
    <Suspense>
      <ComparePage />
    </Suspense>
  );
}

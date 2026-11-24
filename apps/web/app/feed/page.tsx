import { Suspense } from "react";
import FeedPage from "./FeedPage";

export default function Page() {
  return (
    <Suspense>
      <FeedPage />
    </Suspense>
  );
}

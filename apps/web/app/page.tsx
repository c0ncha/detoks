import Picker from "@/components/Picker";

export default function Home() {
  return (
    <main className="mx-auto w-full max-w-xl px-4 py-10">
      <h1 className="text-3xl font-bold">Detoks</h1>
      <p className="mb-8 mt-2 text-white/70">
        A short-form video feed that ranks for well-being instead of watch time. Pick a viewer, then watch the
        same catalog through the watch-time <b>Baseline</b> or the <b>Detoks</b> ranker.
      </p>
      <Picker />
    </main>
  );
}

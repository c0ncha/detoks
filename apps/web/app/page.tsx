import Picker from "@/components/Picker";

export default function Home() {
  return (
    <main className="mx-auto w-full max-w-xl px-4 py-10">
      <h1 className="flex items-center gap-3 font-serif text-4xl">
        <span aria-hidden className="size-4 rounded-full bg-sun shadow-[0_0_16px] shadow-sun/60" />
        Detoks
      </h1>
      <p className="mb-8 mt-3 text-mist">
        A short-form video feed that ranks for well-being instead of watch time. Pick a viewer, then watch the
        same catalog through the watch-time <b className="text-paper">Baseline</b> or the{" "}
        <b className="text-sage">Detoks</b> ranker.
      </p>
      <Picker />
    </main>
  );
}

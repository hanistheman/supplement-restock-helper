export default function AboutPage() {
  return (
    <div className="max-w-2xl mx-auto px-6 pt-10 pb-24 [&_p]:text-[15px] [&_p]:leading-relaxed [&_p]:text-ink-soft [&_li]:text-[15px] [&_li]:leading-relaxed [&_li]:text-ink-soft [&_strong]:text-ink">
      <p className="font-mono text-xs tracking-widest uppercase text-accent mb-1.5">About</p>
      <h1 className="font-display text-[30px] font-semibold mb-5 mt-0">Why this exists</h1>
      <p>
        Supplement Tracker is a small personal tool for keeping tabs on how much
        of each supplement you have left, so you're never caught reaching for
        an empty bottle. Instead of logging every single dose, you tell it when
        you opened a bottle and how fast you're going through it — it does the
        math from there.
      </p>

      <h2 className="font-display text-lg font-semibold mt-8 mb-2.5">How the math works</h2>
      <p>
        Every supplement is defined by three things: the date you started the
        current bottle, the total number of doses it contains, and how many
        doses you take per day. From that, the app computes:
      </p>
      <ul className="pl-5 m-0 [&>li+li]:mt-2">
        <li><strong>Days remaining</strong> — total doses ÷ doses per day, minus days elapsed since you started.</li>
        <li><strong>Restock-by date</strong> — the calendar date your supply is projected to run out.</li>
        <li><strong>Status</strong> — a simple bucket (on hand, running low, critical, overdue) based on days remaining.</li>
      </ul>

      <h2 className="font-display text-lg font-semibold mt-8 mb-2.5">Stack</h2>
      <p>
        Built with a FastAPI + SQLAlchemy backend and a React (Vite) frontend,
        as a hands-on project for learning REST API design and full-stack
        development practices.
      </p>
    </div>
  );
}

const FAQS = [
  {
    q: "How do I add a supplement?",
    a: "Click \"+ Add supplement\" on the Shelf page. Enter the date you started the current bottle, the total number of doses it contains, and how often you take it.",
  },
  {
    q: "What counts as a \"dose\"?",
    a: "Whatever unit you take at once — one capsule, one scoop, two tablets, etc. Just be consistent between the total doses in the bottle and what you enter as \"how often.\"",
  },
  {
    q: "My supplement isn't daily — can I track that?",
    a: "Yes. \"How often\" lets you set doses per day, week, month, or year — e.g. \"1 dose every week\" for a weekly injection, or \"2 doses, 3x per week\" for something you take three times a week.",
  },
  {
    q: "What happens when I click \"Restocked today\"?",
    a: "It resets the start date to today, so the countdown starts fresh from the bottle's original total doses. If your new bottle has a different size, edit the supplement afterward to update the total doses.",
  },
  {
    q: "What do the status colors mean?",
    a: "Green (on hand) means more than a week of supply left. Amber (running low) means 4–7 days. Red (critical) means 3 days or fewer. Dark red (overdue) means you're past the projected restock date.",
  },
  {
    q: "Can I edit a supplement's dosing after adding it?",
    a: "Yes — click Edit on any card to change the name, start date, total doses, frequency, or notes.",
  },
  {
    q: "The app says it can't reach the server. What do I do?",
    a: "Make sure the backend is running (uvicorn main:app --reload from the backend/ folder) before loading the frontend.",
  },
];

export default function HelpPage() {
  return (
    <div className="max-w-2xl mx-auto px-6 pt-10 pb-24">
      <p className="font-mono text-xs tracking-widest uppercase text-accent mb-1.5">Help</p>
      <h1 className="font-display text-[30px] font-semibold mb-5 mt-0">Using the tracker</h1>

      <h2 className="font-display text-lg font-semibold mt-8 mb-2.5">Quick start</h2>
      <ol className="pl-5 m-0 [&>li+li]:mt-2 [&>li]:text-[15px] [&>li]:leading-relaxed [&>li]:text-ink-soft [&_strong]:text-ink">
        <li>Click <strong>+ Add supplement</strong>.</li>
        <li>Fill in the name, the date you started the bottle, total doses, and how often you take it.</li>
        <li>The Shelf page will show days remaining and a restock-by date automatically.</li>
        <li>When you open a new bottle, click <strong>Restocked today</strong> on that card.</li>
      </ol>

      <h2 className="font-display text-lg font-semibold mt-8 mb-2.5">FAQ</h2>
      <div className="flex flex-col gap-2.5">
        {FAQS.map(({ q, a }) => (
          <details key={q} className="bg-paper border border-line rounded-xl px-4 py-3.5 group">
            <summary className="font-body font-semibold text-sm text-ink cursor-pointer">{q}</summary>
            <p className="mt-2.5 mb-0 text-sm text-ink-soft leading-relaxed">{a}</p>
          </details>
        ))}
      </div>
    </div>
  );
}

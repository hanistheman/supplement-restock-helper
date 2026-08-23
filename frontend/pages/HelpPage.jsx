import "./InfoPage.css";

const FAQS = [
  {
    q: "How do I add a supplement?",
    a: "Click \"+ Add supplement\" on the Shelf page. Enter the date you started the current bottle, the total number of doses it contains, and how many doses you take per day.",
  },
  {
    q: "What counts as a \"dose\"?",
    a: "Whatever unit you take at once — one capsule, one scoop, two tablets, etc. If you take 2 tablets per serving and take one serving a day, set doses per day to 2 (or treat each tablet as a dose — just be consistent with total doses in the bottle).",
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
    a: "Yes — click Edit on any card to change the name, start date, total doses, doses per day, or notes.",
  },
  {
    q: "The app says it can't reach the server. What do I do?",
    a: "Make sure the backend is running (uvicorn main:app --reload from the backend/ folder) before loading the frontend.",
  },
];

export default function HelpPage() {
  return (
    <div className="info-page">
      <p className="eyebrow">Help</p>
      <h1>Using the tracker</h1>

      <h2>Quick start</h2>
      <ol>
        <li>Click <strong>+ Add supplement</strong>.</li>
        <li>Fill in the name, the date you started the bottle, total doses, and doses per day.</li>
        <li>The Shelf page will show days remaining and a restock-by date automatically.</li>
        <li>When you open a new bottle, click <strong>Restocked today</strong> on that card.</li>
      </ol>

      <h2>FAQ</h2>
      <div className="faq-list">
        {FAQS.map(({ q, a }) => (
          <details key={q} className="faq-item">
            <summary>{q}</summary>
            <p>{a}</p>
          </details>
        ))}
      </div>
    </div>
  );
}

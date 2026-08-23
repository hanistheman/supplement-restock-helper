import "./InfoPage.css";

export default function AboutPage() {
  return (
    <div className="info-page">
      <p className="eyebrow">About</p>
      <h1>Why this exists</h1>
      <p>
        Supplement Tracker is a small personal tool for keeping tabs on how much
        of each supplement you have left, so you're never caught reaching for
        an empty bottle. Instead of logging every single dose, you tell it when
        you opened a bottle and how fast you're going through it — it does the
        math from there.
      </p>

      <h2>How the math works</h2>
      <p>
        Every supplement is defined by three things: the date you started the
        current bottle, the total number of doses it contains, and how many
        doses you take per day. From that, the app computes:
      </p>
      <ul>
        <li><strong>Days remaining</strong> — total doses ÷ doses per day, minus days elapsed since you started.</li>
        <li><strong>Restock-by date</strong> — the calendar date your supply is projected to run out.</li>
        <li><strong>Status</strong> — a simple bucket (on hand, running low, critical, overdue) based on days remaining.</li>
      </ul>

      <h2>Stack</h2>
      <p>
        Built with a FastAPI + SQLAlchemy backend and a React (Vite) frontend,
        as a hands-on project for learning REST API design and full-stack
        development practices.
      </p>
    </div>
  );
}

import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getQuestions, submitAnswer, getProgress } from "../api/api";
import Navbar from "../components/Navbar";
import styles from "./Practice.module.css";

const LM = {
  important: { label: "Important", color: "#ef4444", bg: "rgba(239,68,68,0.1)", icon: "🔥" },
  moderate:  { label: "Moderate",  color: "#f59e0b", bg: "rgba(245,158,11,0.1)", icon: "⚡" },
  okay:      { label: "Okay",      color: "#22c55e", bg: "rgba(34,197,94,0.1)",  icon: "✅" }
};

export default function Practice() {
  const { id } = useParams();
  const nav = useNavigate();
  const [allQ, setAllQ] = useState([]);
  const [idx, setIdx] = useState(0);
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [filter, setFilter] = useState("all");
  const [progress, setProgress] = useState(null);
  const [finished, setFinished] = useState(false);

  const loadAll = async () => {
    const { data } = await getQuestions(id);
    const flat = [
      ...data.questions.important,
      ...data.questions.moderate,
      ...data.questions.okay
    ];
    setAllQ(flat);
    const {  p } = await getProgress(id);
    setProgress(p);
  };

  useEffect(() => { loadAll(); }, [id]);

  const filtered = filter === "all" ? allQ : allQ.filter(q => q.level === filter);
  const current = filtered[idx];

  const handleSubmit = async () => {
    if (!current) return;
    setSubmitting(true);
    try {
      const { data } = await submitAnswer(current.id, answer);
      setResult(data);
      const { data: p } = await getProgress(id);
      setProgress(p);
    } catch {
      setResult({ verdict: "Error", feedback: "Could not evaluate. Try again." });
    } finally {
      setSubmitting(false);
    }
  };

  const handleNext = () => {
    if (idx + 1 >= filtered.length) setFinished(true);
    else { setIdx(idx + 1); setAnswer(""); setResult(null); }
  };

  const handleSkip = async () => {
    if (!current) return;
    await submitAnswer(current.id, "i dont know");
    if (idx + 1 >= filtered.length) setFinished(true);
    else { setIdx(idx + 1); setAnswer(""); setResult(null); }
  };

  const handleRestart = () => {
    setIdx(0); setAnswer(""); setResult(null); setFinished(false);
  };

  if (!allQ.length) return (
    <div className={styles.page}>
      <Navbar/>
      <div className={styles.center}><p>Loading questions...</p></div>
    </div>
  );

  if (finished) return (
    <div className={styles.page}>
      <Navbar/>
      <div className={styles.finishWrap}>
        <div className={styles.finishCard}>
          <div className={styles.finishIcon}>🎉</div>
          <h2>Session Complete!</h2>
          <p className={styles.finishSub}>Here is how you did:</p>
          <div className={styles.scoreCircle}>
            <span className={styles.scoreNum}>{progress?.score_pct ?? 0}%</span>
            <span className={styles.scoreLabel}>Score</span>
          </div>
          <div className={styles.scoreStats}>
            <div><b>{progress?.correct}</b> Correct</div>
            <div><b>{progress?.attempted}</b> Attempted</div>
            <div><b>{progress?.total}</b> Total</div>
          </div>
          <div className={styles.finishBtns}>
            <button className={styles.restartBtn} onClick={handleRestart}>Practice Again</button>
            <button className={styles.backBtn} onClick={() => nav("/session/" + id)}>Add More Sources</button>
            <button className={styles.homeBtn} onClick={() => nav("/")}>Home</button>
          </div>
        </div>
      </div>
    </div>
  );

  const meta = current ? LM[current.level] : null;
  const pct = filtered.length ? Math.round((idx / filtered.length) * 100) : 0;

  return (
    <div className={styles.page}>
      <Navbar/>
      <div className={styles.container}>
        <div className={styles.topBar}>
          <button className={styles.back} onClick={() => nav("/session/" + id)}>← Back</button>
          <div className={styles.filterRow}>
            {["all", "important", "moderate", "okay"].map(f => (
              <button
                key={f}
                className={styles.filterBtn + (filter === f ? " " + styles.activeFilter : "")}
                onClick={() => { setFilter(f); setIdx(0); setAnswer(""); setResult(null); setFinished(false); }}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
          {progress && (
            <div className={styles.progressPill}>
              {progress.correct}/{progress.total} correct
            </div>
          )}
        </div>
        <div className={styles.progressBar}>
          <div className={styles.progressFill} style={{width: pct + "%"}}/>
        </div>
        <p className={styles.progressText}>Question {idx + 1} of {filtered.length}</p>

        {current && (
          <div className={styles.qCard}>
            <div
              className={styles.levelBadge}
              style={{background:meta.bg, color:meta.color, border: "1px solid " + meta.color + "60"}}
            >
              {meta.icon} {meta.label}
            </div>
            <p className={styles.sourceRef}>{current.source_ref}</p>
            <h2 className={styles.question}>{current.question}</h2>

            {!result ? (
              <>
                <textarea
                  className={styles.answerBox}
                  placeholder="Type your answer here... (or type 'i dont know' to skip)"
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  rows={5}
                  autoFocus
                />
                <div className={styles.actionRow}>
                  <button className={styles.skipBtn} onClick={handleSkip}>
                    Skip — Show Answer
                  </button>
                  <button className={styles.submitBtn} onClick={handleSubmit} disabled={submitting}>
                    {submitting ? "Evaluating..." : "Submit Answer →"}
                  </button>
                </div>
              </>
            ) : (
              <div className={styles.resultBlock}>
                <div className={
                  styles.verdict + " " +
                  (result.is_correct ? styles.verdictCorrect :
                   result.verdict === "Partially Correct" ? styles.verdictPartial :
                   styles.verdictWrong)
                }>
                  <span className={styles.verdictIcon}>
                    {result.is_correct ? "✅" : result.verdict === "Partially Correct" ? "⚠️" : "❌"}
                  </span>
                  <div>
                    <div className={styles.verdictLabel}>{result.verdict}</div>
                    {result.score !== undefined && (
                      <div className={styles.verdictScore}>Score: {result.score}/100</div>
                    )}
                  </div>
                </div>

                <div className={styles.feedbackBox}>
                  <div className={styles.feedbackTitle}>💬 Interviewer Feedback</div>
                  <p>{result.feedback}</p>
                </div>

                {(!result.is_correct || result.verdict === "Partially Correct") && (
                  <div className={styles.correctBox}>
                    <div className={styles.correctTitle}>📖 Correct Answer</div>
                    <p>{result.correct_answer}</p>
                  </div>
                )}

                <button className={styles.nextBtn} onClick={handleNext}>
                  {idx + 1 >= filtered.length ? "Finish Session 🎉" : "Next Question →"}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
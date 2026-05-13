import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getAllQuestions } from "../api/api";
import Navbar from "../components/Navbar";
import LoadingSpinner from "../components/LoadingSpinner";
import styles from "./AllQA.module.css";

const LEVEL_META = {
  important: { label: "Important", color: "#ef4444", bg: "rgba(239,68,68,0.1)", icon: "🔥" },
  moderate:  { label: "Moderate",  color: "#f59e0b", bg: "rgba(245,158,11,0.1)", icon: "⚡" },
  okay:      { label: "Okay",      color: "#22c55e", bg: "rgba(34,197,94,0.1)",  icon: "✅" }
};

export default function AllQA() {
  const { id } = useParams();
  const nav = useNavigate();
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const { data } = await getAllQuestions(id);
        setQuestions(data.questions || []);
      } catch (err) {
        console.error("Failed to load questions:", err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  if (loading) {
    return (
      <div className={styles.page}>
        <Navbar />
        <LoadingSpinner message="Loading questions..." />
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <Navbar />
      <div className={styles.container}>
        <div className={styles.header}>
          <button className={styles.back} onClick={() => nav("/session/" + id)}>← Back</button>
          <h1 className={styles.title}>All Questions & Answers</h1>
          <button className={styles.practiceBtn} onClick={() => nav("/session/" + id + "/practice")}>
            Start Practice →
          </button>
        </div>

        {questions.length === 0 ? (
          <div className={styles.empty}>
            <p>No questions yet. Upload a source to generate questions.</p>
          </div>
        ) : (
          <div className={styles.list}>
            {questions.map((q, idx) => {
              const meta = LEVEL_META[q.level] || LEVEL_META.okay;
              return (
                <div key={q.id} className={styles.card}>
                  <div className={styles.cardHeader}>
                    <span className={styles.badge} style={{ background: meta.bg, color: meta.color }}>
                      {meta.icon} {meta.label}
                    </span>
                    <span className={styles.number}>#{idx + 1}</span>
                  </div>
                  <p className={styles.source}>{q.source_ref}</p>
                  <h3 className={styles.question}>{q.question}</h3>
                  <div className={styles.answerBox}>
                    <div className={styles.answerTitle}>✅ Correct Answer</div>
                    <p>{q.answer}</p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
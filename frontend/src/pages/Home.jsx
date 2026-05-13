import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listSessions, createSession, deleteSession } from "../api/api";
import Navbar from "../components/Navbar";
import styles from "./Home.module.css";

export default function Home() {
  const nav = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [title, setTitle] = useState("");
  const [creating, setCreating] = useState(false);
  const [showModal, setShowModal] = useState(false);

  const load = async () => {
    try { const { data } = await listSessions(); setSessions(data); } catch {}
  };
  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    if (!title.trim()) return;
    setCreating(true);
    const { data } = await createSession(title.trim());
    setCreating(false); setShowModal(false); setTitle("");
    nav("/session/" + data.session_id);
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (!window.confirm("Delete this session?")) return;
    await deleteSession(id); load();
  };

  return (
    <div className={styles.page}>
      <Navbar/>
      <section className={styles.hero}>
        <div className={styles.heroBadge}>AI-Powered Study Platform</div>
        <h1 className={styles.heroTitle}>
          Study Smarter.<br/>
          <span className={styles.grad}>Interview Ready.</span>
        </h1>
        <p className={styles.heroSub}>
          Upload PDFs, YouTube videos, or any webpage. Get real interview-style questions. Practice like a pro.
        </p>
        <button className={styles.ctaBtn} onClick={() => setShowModal(true)}>
          + New Study Session
        </button>
      </section>

      <div className={styles.stats}>
        {[
          {label:"Question Types", value:"3 Levels"},
          {label:"Sources", value:"PDF · YouTube · Web"},
          {label:"Answer Mode", value:"Open-Ended"},
          {label:"Feedback", value:"Instant AI"}
        ].map(s => (
          <div key={s.label} className={styles.statCard}>
            <div className={styles.statVal}>{s.value}</div>
            <div className={styles.statLabel}>{s.label}</div>
          </div>
        ))}
      </div>

      <section className={styles.sessionsSection}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:20}}>
          <h2 className={styles.secTitle}>Your Sessions</h2>
          <button className={styles.newBtn} onClick={() => setShowModal(true)}>+ New</button>
        </div>
        {sessions.length === 0
          ? <div className={styles.empty}>
              <div className={styles.emptyIcon}>📚</div>
              <p>No sessions yet. Create your first one!</p>
            </div>
          : <div className={styles.grid}>
              {sessions.map(s => (
                <div key={s.id} className={styles.card} onClick={() => nav("/session/" + s.id)}>
                  <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                    <div className={styles.cardTitle}>{s.title}</div>
                    <button className={styles.delBtn} onClick={e => handleDelete(e, s.id)}>✕</button>
                  </div>
                  <div className={styles.cardMeta}>
                    <span>{s.source_count} sources</span>
                    <span>·</span>
                    <span>{s.question_count} questions</span>
                  </div>
                  <div className={styles.cardDate}>{new Date(s.created_at).toLocaleDateString()}</div>
                </div>
              ))}
            </div>
        }
      </section>

      {showModal && (
        <div className={styles.overlay} onClick={() => setShowModal(false)}>
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <h3>New Study Session</h3>
            <p className={styles.modalSub}>Give your session a name</p>
            <input
              autoFocus
              placeholder="Session title..."
              value={title}
              onChange={e => setTitle(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleCreate()}
            />
            <div style={{display:"flex",gap:12,marginTop:16}}>
              <button className={styles.cancelBtn} onClick={() => setShowModal(false)}>Cancel</button>
              <button className={styles.createBtn} onClick={handleCreate} disabled={creating}>
                {creating ? "Creating..." : "Create Session"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
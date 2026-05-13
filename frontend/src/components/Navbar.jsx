import { useNavigate } from "react-router-dom";
import styles from "./Navbar.module.css";

export default function Navbar() {
  const nav = useNavigate();
  return (
    <nav className={styles.nav}>
      <div className={styles.inner}>
        <div className={styles.logo} onClick={() => nav("/")}>
          <span className={styles.logoText}>
            StudyInterviewer <span className={styles.ai}>AI</span>
          </span>
        </div>
      </div>
    </nav>
  );
}
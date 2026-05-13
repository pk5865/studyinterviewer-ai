import styles from "./LoadingSpinner.module.css";

export default function LoadingSpinner({ message = "Processing..." }) {
  return (
    <div className={styles.overlay}>
      <div className={styles.spinner}>
        <div className={styles.spinnerInner}></div>
      </div>
      <p className={styles.message}>{message}</p>
    </div>
  );
}
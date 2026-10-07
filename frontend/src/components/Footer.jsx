import { Wordmark } from './Wordmark';
import { PROJECT_META } from '../utils/constants';
import '../styles/Footer.css';

export function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-container">
        <div className="footer-left">
          <Wordmark size={16} />
          <span className="footer-text">Prototype decision-support system. Scores are not proof of fraud.</span>
        </div>
        <div className="footer-right">
          <span className="footer-text">
            {PROJECT_META.members.join(" · ")} 
            {PROJECT_META.college && ` — ${PROJECT_META.college}`}
            {PROJECT_META.teamName && ` (${PROJECT_META.teamName})`}
          </span>
        </div>
      </div>
    </footer>
  );
}

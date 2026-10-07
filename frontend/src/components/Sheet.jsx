import '../styles/Sheet.css';

export function Sheet({ eyebrow, title, actions, children, as: Component = "div" }) {
  return (
    <Component className="sheet">
      {(eyebrow || title || actions) && (
        <div className="sheet-header">
          <div className="sheet-title-area">
            {eyebrow && <div className="eyebrow">{eyebrow}</div>}
            {title && <h2 className="sheet-title">{title}</h2>}
          </div>
          {actions && <div className="sheet-actions">{actions}</div>}
        </div>
      )}
      <div className="sheet-content">
        {children}
      </div>
    </Component>
  );
}

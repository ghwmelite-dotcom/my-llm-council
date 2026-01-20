import React from 'react';

const FloatingPanel = ({
  children,
  className = '',
  title,
  delay = 0,
  style = {}
}) => {
  const isRight = className.includes('leaderboard');

  return (
    <div
      className={`floating-panel ${className} ${isRight ? 'right' : ''}`}
      style={{
        ...style,
        transitionDelay: `${delay}s`
      }}
    >
      {title && <h3 className="panel-title">{title}</h3>}
      {children}
    </div>
  );
};

export default FloatingPanel;

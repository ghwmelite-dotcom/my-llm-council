import { useState } from 'react';
import './QueryTemplates.css';

const TEMPLATES = [
  {
    category: 'Analysis',
    icon: '🔍',
    templates: [
      {
        title: 'Compare Options',
        description: 'Get balanced analysis of different choices',
        template: 'Compare and contrast the pros and cons of [Option A] vs [Option B] for [specific use case]. Consider factors like cost, complexity, scalability, and long-term maintenance.',
      },
      {
        title: 'Root Cause Analysis',
        description: 'Investigate why something happened',
        template: 'Perform a root cause analysis for [describe the problem or issue]. What are the most likely causes, and what evidence supports each hypothesis?',
      },
      {
        title: 'Risk Assessment',
        description: 'Evaluate potential risks',
        template: 'What are the potential risks and challenges of [proposed action/decision]? Rate each risk by likelihood and impact, and suggest mitigation strategies.',
      },
    ],
  },
  {
    category: 'Technical',
    icon: '💻',
    templates: [
      {
        title: 'Code Review',
        description: 'Get feedback on code quality',
        template: 'Review the following code for potential bugs, security vulnerabilities, performance issues, and best practices:\n\n```\n[paste your code here]\n```',
      },
      {
        title: 'Architecture Decision',
        description: 'Evaluate technical approaches',
        template: 'I need to implement [feature/system]. Should I use [Approach A] or [Approach B]? Consider scalability, maintainability, team expertise, and time constraints.',
      },
      {
        title: 'Debug Help',
        description: 'Troubleshoot an issue',
        template: 'I\'m encountering this error: [error message]. Here\'s the relevant code and context: [describe setup]. What could be causing this and how can I fix it?',
      },
    ],
  },
  {
    category: 'Writing',
    icon: '✍️',
    templates: [
      {
        title: 'Explain Complex Topic',
        description: 'Get clear explanations',
        template: 'Explain [complex topic] in simple terms that a [beginner/intermediate/expert] would understand. Include practical examples and common misconceptions to avoid.',
      },
      {
        title: 'Draft Review',
        description: 'Improve written content',
        template: 'Review and improve this draft for clarity, tone, and impact:\n\n[paste your text here]\n\nThe target audience is [describe audience] and the goal is to [describe purpose].',
      },
      {
        title: 'Summarize',
        description: 'Condense information',
        template: 'Summarize the following content into key points. Highlight the most important takeaways and any action items:\n\n[paste content to summarize]',
      },
    ],
  },
  {
    category: 'Strategy',
    icon: '🎯',
    templates: [
      {
        title: 'Decision Framework',
        description: 'Make better decisions',
        template: 'Help me decide: [describe the decision]. My priorities are [list priorities]. What framework should I use to evaluate this, and what would you recommend?',
      },
      {
        title: 'Devil\'s Advocate',
        description: 'Challenge your assumptions',
        template: 'I believe [state your position]. Play devil\'s advocate and present the strongest counter-arguments. What am I missing or underestimating?',
      },
      {
        title: 'Action Plan',
        description: 'Create a step-by-step plan',
        template: 'I want to achieve [goal] within [timeframe]. Create a detailed action plan with specific steps, milestones, and potential obstacles to watch for.',
      },
    ],
  },
];

export default function QueryTemplates({ onSelectTemplate, disabled }) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState(null);

  const handleSelectTemplate = (template) => {
    onSelectTemplate(template.template);
    setIsOpen(false);
    setSelectedCategory(null);
  };

  return (
    <div className="query-templates">
      <button
        className={`templates-toggle ${isOpen ? 'open' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        title="Query Templates"
      >
        <span className="toggle-icon">📋</span>
        <span className="toggle-label">Templates</span>
      </button>

      {isOpen && (
        <div className="templates-panel">
          <div className="templates-header">
            <h3>Query Templates</h3>
            <button className="close-btn" onClick={() => setIsOpen(false)}>×</button>
          </div>

          <div className="templates-content">
            {selectedCategory === null ? (
              <div className="category-list">
                {TEMPLATES.map((cat) => (
                  <button
                    key={cat.category}
                    className="category-btn"
                    onClick={() => setSelectedCategory(cat.category)}
                  >
                    <span className="category-icon">{cat.icon}</span>
                    <span className="category-name">{cat.category}</span>
                    <span className="category-count">{cat.templates.length}</span>
                    <span className="category-arrow">→</span>
                  </button>
                ))}
              </div>
            ) : (
              <div className="template-list">
                <button
                  className="back-btn"
                  onClick={() => setSelectedCategory(null)}
                >
                  ← Back to categories
                </button>

                {TEMPLATES.find((c) => c.category === selectedCategory)?.templates.map((tmpl, idx) => (
                  <button
                    key={idx}
                    className="template-btn"
                    onClick={() => handleSelectTemplate(tmpl)}
                  >
                    <div className="template-title">{tmpl.title}</div>
                    <div className="template-desc">{tmpl.description}</div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

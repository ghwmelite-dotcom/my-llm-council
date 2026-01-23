import { useState, useEffect } from 'react';
import { useUser } from '../../contexts/UserContext';
import './OnboardingTour.css';

const TOUR_STEPS = [
  {
    id: 'welcome',
    title: 'Welcome to LLM Council! 🏛️',
    description:
      'Experience AI deliberation like never before. Multiple AI models work together to give you well-reasoned, balanced answers.',
    icon: '🎉',
    position: 'center',
  },
  {
    id: 'sidebar',
    title: 'Your Conversations',
    description:
      'Create and manage your conversations here. Each conversation is a new topic for the council to deliberate.',
    icon: '💬',
    target: '.sidebar',
    position: 'right',
  },
  {
    id: 'input',
    title: 'Ask the Council',
    description:
      'Type your question here. Complex questions work best! The council will deliberate and synthesize the best answer.',
    icon: '✍️',
    target: '.chat-input-container',
    position: 'top',
  },
  {
    id: 'stage1',
    title: 'Stage 1: Individual Responses',
    description:
      'Each AI model answers your question independently. See how different models approach the same problem.',
    icon: '🤖',
    position: 'center',
  },
  {
    id: 'stage2',
    title: 'Stage 2: Peer Review',
    description:
      'Models anonymously rank each other\'s responses. No favoritism, just honest evaluation!',
    icon: '⚖️',
    position: 'center',
  },
  {
    id: 'stage3',
    title: 'Stage 3: Final Synthesis',
    description:
      'The chairman synthesizes the best insights from all responses into one comprehensive answer.',
    icon: '✨',
    position: 'center',
  },
  {
    id: 'modes',
    title: 'View Modes',
    description:
      'Switch between Text mode for detailed reading or 3D Chamber for an immersive experience.',
    icon: '🎭',
    target: '.toggle-group',
    position: 'bottom',
  },
  {
    id: 'features',
    title: 'Advanced Features',
    description:
      'Explore Analytics, Memory Bank, Council Builder, and more! Customize your council experience.',
    icon: '🚀',
    target: '.mode-toggle-header',
    position: 'bottom',
  },
  {
    id: 'complete',
    title: "You're All Set! 🎊",
    description:
      'Start your first conversation and experience the power of AI deliberation. Happy exploring!',
    icon: '🏆',
    position: 'center',
  },
];

export default function OnboardingTour({ onComplete }) {
  const { user, completeOnboarding } = useUser();
  const [currentStep, setCurrentStep] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const [targetRect, setTargetRect] = useState(null);

  // Check if we should show onboarding
  useEffect(() => {
    if (user && !user.onboarding_complete) {
      // Small delay for smooth appearance
      const timer = setTimeout(() => setIsVisible(true), 500);
      return () => clearTimeout(timer);
    }
  }, [user]);

  // Update target element highlighting
  useEffect(() => {
    const step = TOUR_STEPS[currentStep];
    if (step.target) {
      const element = document.querySelector(step.target);
      if (element) {
        const rect = element.getBoundingClientRect();
        setTargetRect({
          top: rect.top - 8,
          left: rect.left - 8,
          width: rect.width + 16,
          height: rect.height + 16,
        });
      } else {
        setTargetRect(null);
      }
    } else {
      setTargetRect(null);
    }
  }, [currentStep]);

  const handleNext = () => {
    if (currentStep < TOUR_STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSkip = () => {
    handleComplete();
  };

  const handleComplete = async () => {
    setIsVisible(false);
    await completeOnboarding();
    if (onComplete) {
      onComplete();
    }
  };

  if (!isVisible || !user) {
    return null;
  }

  const step = TOUR_STEPS[currentStep];
  const isLastStep = currentStep === TOUR_STEPS.length - 1;
  const isFirstStep = currentStep === 0;

  return (
    <div className="onboarding-overlay">
      {/* Spotlight highlight */}
      {targetRect && (
        <div
          className="onboarding-spotlight"
          style={{
            top: targetRect.top,
            left: targetRect.left,
            width: targetRect.width,
            height: targetRect.height,
          }}
        />
      )}

      {/* Tour dialog - always centered for stability */}
      <div className="onboarding-dialog">
        <div className="onboarding-content">
          <div className="onboarding-icon">{step.icon}</div>
          <h3 className="onboarding-title">{step.title}</h3>
          <p className="onboarding-description">{step.description}</p>
        </div>

        {/* Progress dots */}
        <div className="onboarding-progress">
          {TOUR_STEPS.map((_, index) => (
            <div
              key={index}
              className={`progress-dot ${index === currentStep ? 'active' : ''} ${index < currentStep ? 'completed' : ''}`}
              onClick={() => setCurrentStep(index)}
            />
          ))}
        </div>

        {/* Navigation buttons */}
        <div className="onboarding-actions">
          <button className="onboarding-skip" onClick={handleSkip}>
            Skip Tour
          </button>
          <div className="onboarding-nav">
            {!isFirstStep && (
              <button className="onboarding-prev" onClick={handlePrev}>
                Back
              </button>
            )}
            <button className="onboarding-next" onClick={handleNext}>
              {isLastStep ? "Let's Go!" : 'Next'}
            </button>
          </div>
        </div>

        {/* Step counter */}
        <div className="onboarding-counter">
          {currentStep + 1} / {TOUR_STEPS.length}
        </div>
      </div>
    </div>
  );
}


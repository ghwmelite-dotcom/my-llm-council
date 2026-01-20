import { Suspense, useRef, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Environment, Stars } from '@react-three/drei';
import { useSpring, animated } from '@react-spring/three';
import { useImmersiveStore } from '../../stores/immersiveStore';
import { STAGE_CONFIGS } from '../../config/modelProfiles';
import CouncilTable from './CouncilTable';
import ModelAvatar from './ModelAvatar';
import ThoughtConnections from './ThoughtConnections';
import SpeechBubble from './SpeechBubble';
import './CouncilChamber.css';

// Animated camera that follows stage transitions
function AnimatedCamera() {
  const { cameraPosition, cameraLookAt, currentStage } = useImmersiveStore();

  const config = STAGE_CONFIGS[currentStage] || STAGE_CONFIGS.idle;

  const spring = useSpring({
    position: [config.camera.x, config.camera.y, config.camera.z],
    config: { tension: 120, friction: 14 },
  });

  return (
    <animated.group position={spring.position}>
      <PerspectiveCamera makeDefault fov={50} near={0.1} far={100} />
    </animated.group>
  );
}

// Main 3D scene
function Scene() {
  const { currentStage, connections, activeSpeaker, stage1Results } = useImmersiveStore();

  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.4} />
      <pointLight position={[0, 10, 0]} intensity={0.8} castShadow />
      <pointLight position={[5, 5, 5]} intensity={0.3} color="#4a90e2" />
      <pointLight position={[-5, 5, -5]} intensity={0.3} color="#d97706" />

      {/* Background environment */}
      <Stars radius={50} depth={50} count={1000} factor={2} fade speed={1} />

      {/* Chamber floor */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.5, 0]} receiveShadow>
        <circleGeometry args={[8, 64]} />
        <meshStandardMaterial color="#1a1a2e" metalness={0.3} roughness={0.8} />
      </mesh>

      {/* Council table */}
      <CouncilTable />

      {/* Model avatars */}
      <ModelAvatar modelId="openai/gpt-5.1" />
      <ModelAvatar modelId="google/gemini-3-pro-preview" />
      <ModelAvatar modelId="anthropic/claude-sonnet-4.5" />
      <ModelAvatar modelId="x-ai/grok-4" />

      {/* Thought connections between agreeing models */}
      <ThoughtConnections connections={connections} />

      {/* Speech bubble for active speaker */}
      {activeSpeaker && (
        <SpeechBubble
          modelId={activeSpeaker}
          content={
            stage1Results.find((r) => r.model === activeSpeaker)?.response || ''
          }
        />
      )}
    </>
  );
}

// Loading fallback for 3D scene
function LoadingFallback() {
  return (
    <mesh>
      <sphereGeometry args={[1, 16, 16]} />
      <meshBasicMaterial color="#4a90e2" wireframe />
    </mesh>
  );
}

export default function CouncilChamber({ conversation, onSendMessage, isLoading }) {
  const [inputValue, setInputValue] = useState('');
  const inputRef = useRef(null);
  const { currentStage, isProcessing } = useImmersiveStore();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading && !isProcessing) {
      onSendMessage(inputValue.trim());
      setInputValue('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Get stage display info
  const getStageInfo = () => {
    switch (currentStage) {
      case 'stage1':
        return { label: 'Stage 1', description: 'Council members are formulating their responses...' };
      case 'stage2':
        return { label: 'Stage 2', description: 'Peer review in progress - anonymous evaluation...' };
      case 'stage3':
        return { label: 'Stage 3', description: 'Chairman is synthesizing the final answer...' };
      default:
        return { label: 'Ready', description: 'Ask the council a question' };
    }
  };

  const stageInfo = getStageInfo();

  return (
    <div className="council-chamber">
      {/* 3D Canvas */}
      <div className="chamber-canvas-container">
        <Canvas shadows>
          <Suspense fallback={<LoadingFallback />}>
            <AnimatedCamera />
            <Scene />
            <OrbitControls
              enablePan={false}
              minDistance={3}
              maxDistance={15}
              minPolarAngle={Math.PI / 6}
              maxPolarAngle={Math.PI / 2.2}
            />
          </Suspense>
        </Canvas>
      </div>

      {/* Stage indicator overlay */}
      <div className="chamber-stage-indicator">
        <div className={`stage-badge ${currentStage}`}>
          {stageInfo.label}
        </div>
        <div className="stage-description">{stageInfo.description}</div>
      </div>

      {/* Input area */}
      <div className="chamber-input-area">
        <form onSubmit={handleSubmit} className="chamber-input-form">
          <textarea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={conversation ? "Ask the council..." : "Create a new conversation first"}
            disabled={!conversation || isLoading || isProcessing}
            rows={2}
            className="chamber-input"
          />
          <button
            type="submit"
            disabled={!conversation || !inputValue.trim() || isLoading || isProcessing}
            className="chamber-submit-btn"
          >
            {isProcessing ? (
              <span className="loading-spinner">⏳</span>
            ) : (
              <span>🎯</span>
            )}
          </button>
        </form>
      </div>

      {/* Quick info panel showing text-based results when available */}
      <QuickInfoPanel />
    </div>
  );
}

// Collapsible panel showing text results
function QuickInfoPanel() {
  const [isExpanded, setIsExpanded] = useState(false);
  const { stage1Results, stage2Results, stage3Result, stage2Metadata } = useImmersiveStore();

  const hasResults = stage1Results.length > 0 || stage2Results.length > 0 || stage3Result;

  if (!hasResults) return null;

  return (
    <div className={`quick-info-panel ${isExpanded ? 'expanded' : ''}`}>
      <button className="quick-info-toggle" onClick={() => setIsExpanded(!isExpanded)}>
        {isExpanded ? '▼ Hide Results' : '▲ Show Results'}
      </button>

      {isExpanded && (
        <div className="quick-info-content">
          {/* Stage 3 Final Answer */}
          {stage3Result && (
            <div className="quick-info-section stage3-section">
              <h4>Final Answer</h4>
              <div className="quick-info-text">{stage3Result.response?.slice(0, 500)}...</div>
            </div>
          )}

          {/* Aggregate Rankings */}
          {stage2Metadata?.aggregate_rankings && (
            <div className="quick-info-section rankings-section">
              <h4>Council Rankings</h4>
              <div className="rankings-list">
                {stage2Metadata.aggregate_rankings.map((r, i) => (
                  <div key={r.model} className="ranking-item">
                    <span className="rank">#{i + 1}</span>
                    <span className="model-name">{r.model.split('/').pop()}</span>
                    <span className="avg-rank">Avg: {r.average_rank.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

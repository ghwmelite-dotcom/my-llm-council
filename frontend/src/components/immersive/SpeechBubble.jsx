import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html, Text } from '@react-three/drei';
import { useSpring, animated } from '@react-spring/three';
import { getModelProfile } from '../../config/modelProfiles';

export default function SpeechBubble({ modelId, content }) {
  const bubbleRef = useRef();
  const profile = getModelProfile(modelId);

  // Position above the model
  const position = useMemo(
    () => [profile.position.x, profile.position.y + 1.8, profile.position.z],
    [profile]
  );

  // Truncate content for display
  const truncatedContent = useMemo(() => {
    if (!content) return '';
    const maxLength = 200;
    if (content.length > maxLength) {
      return content.substring(0, maxLength) + '...';
    }
    return content;
  }, [content]);

  // Entry animation
  const spring = useSpring({
    from: { scale: 0, opacity: 0 },
    to: { scale: 1, opacity: 1 },
    config: { tension: 200, friction: 15 },
  });

  // Gentle floating animation
  useFrame((state) => {
    if (bubbleRef.current) {
      bubbleRef.current.position.y =
        position[1] + Math.sin(state.clock.elapsedTime * 2) * 0.05;
    }
  });

  if (!content) return null;

  return (
    <animated.group
      ref={bubbleRef}
      position={position}
      scale={spring.scale}
    >
      {/* Speech bubble background */}
      <mesh>
        <planeGeometry args={[3, 1.5]} />
        <meshBasicMaterial
          color="#1a1a2e"
          transparent
          opacity={0.9}
        />
      </mesh>

      {/* Border */}
      <mesh position={[0, 0, 0.01]}>
        <planeGeometry args={[3.05, 1.55]} />
        <meshBasicMaterial
          color={profile.color}
          transparent
          opacity={0.5}
        />
      </mesh>

      {/* Background */}
      <mesh position={[0, 0, 0.02]}>
        <planeGeometry args={[2.95, 1.45]} />
        <meshBasicMaterial
          color="#0a0a14"
          transparent
          opacity={0.95}
        />
      </mesh>

      {/* Tail pointing to model */}
      <mesh position={[0, -0.9, 0.01]} rotation={[0, 0, Math.PI / 4]}>
        <planeGeometry args={[0.3, 0.3]} />
        <meshBasicMaterial
          color="#0a0a14"
        />
      </mesh>

      {/* Model name header */}
      <Text
        position={[-1.3, 0.55, 0.05]}
        fontSize={0.12}
        color={profile.color}
        anchorX="left"
        anchorY="middle"
        maxWidth={2.8}
      >
        {profile.shortName}
      </Text>

      {/* HTML content for better text rendering */}
      <Html
        position={[0, -0.1, 0.1]}
        transform
        occlude
        style={{
          width: '280px',
          height: '100px',
          overflow: 'hidden',
          pointerEvents: 'none',
        }}
      >
        <div
          style={{
            color: 'rgba(255, 255, 255, 0.9)',
            fontSize: '11px',
            lineHeight: '1.4',
            fontFamily: 'system-ui, sans-serif',
            padding: '8px',
            maxHeight: '100px',
            overflow: 'hidden',
          }}
        >
          {truncatedContent}
        </div>
      </Html>

      {/* Speaking indicator dots */}
      <SpeakingDots color={profile.color} />
    </animated.group>
  );
}

function SpeakingDots({ color }) {
  const dotsRef = useRef([]);

  useFrame((state) => {
    dotsRef.current.forEach((dot, i) => {
      if (dot) {
        const bounce = Math.sin(state.clock.elapsedTime * 5 - i * 0.5);
        dot.position.y = -0.6 + bounce * 0.05;
        dot.material.opacity = 0.5 + bounce * 0.3;
      }
    });
  });

  return (
    <group position={[1.2, -0.6, 0.05]}>
      {[0, 0.12, 0.24].map((x, i) => (
        <mesh
          key={i}
          ref={(el) => (dotsRef.current[i] = el)}
          position={[x, 0, 0]}
        >
          <circleGeometry args={[0.04, 16]} />
          <meshBasicMaterial color={color} transparent opacity={0.7} />
        </mesh>
      ))}
    </group>
  );
}

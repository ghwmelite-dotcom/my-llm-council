import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Text, Float } from '@react-three/drei';
import { useSpring, animated } from '@react-spring/three';
import { useImmersiveStore } from '../../stores/immersiveStore';
import { getModelProfile, MODEL_PROFILES } from '../../config/modelProfiles';

export default function ModelAvatar({ modelId }) {
  const meshRef = useRef();
  const glowRef = useRef();
  const profile = getModelProfile(modelId);
  const modelState = useImmersiveStore((state) => state.modelStates[modelId]);
  const activeSpeaker = useImmersiveStore((state) => state.activeSpeaker);

  const isActive = modelState?.status === 'speaking' || modelState?.status === 'thinking';
  const isSpeaking = activeSpeaker === modelId;
  const isFinished = modelState?.status === 'finished';

  // Animation spring for scale and glow
  const spring = useSpring({
    scale: isSpeaking ? 1.2 : isActive ? 1.1 : 1,
    glowIntensity: isSpeaking ? 1 : isActive ? 0.5 : isFinished ? 0.3 : 0.1,
    config: { tension: 200, friction: 20 },
  });

  // Floating animation and pulse effect
  useFrame((state) => {
    if (meshRef.current) {
      // Subtle floating effect
      meshRef.current.position.y = profile.position.y + Math.sin(state.clock.elapsedTime * 2) * 0.05;

      // Pulse when thinking
      if (modelState?.status === 'thinking') {
        const pulse = Math.sin(state.clock.elapsedTime * 4) * 0.1 + 1;
        meshRef.current.scale.setScalar(pulse);
      }
    }

    if (glowRef.current) {
      // Rotate glow ring
      glowRef.current.rotation.y += 0.01;
    }
  });

  // Status indicator color
  const getStatusColor = () => {
    switch (modelState?.status) {
      case 'thinking':
        return '#eab308';
      case 'speaking':
        return '#22c55e';
      case 'finished':
        return '#4a90e2';
      default:
        return '#666666';
    }
  };

  return (
    <group
      position={[profile.position.x, profile.position.y + 0.5, profile.position.z]}
      rotation={[0, profile.rotation, 0]}
    >
      {/* Main avatar body */}
      <Float speed={2} rotationIntensity={0.1} floatIntensity={0.3}>
        <animated.group scale={spring.scale}>
          <mesh ref={meshRef} castShadow>
            {/* Crystalline body */}
            <octahedronGeometry args={[0.5, 0]} />
            <meshStandardMaterial
              color={profile.color}
              metalness={0.6}
              roughness={0.3}
              emissive={profile.color}
              emissiveIntensity={isActive ? 0.4 : 0.1}
            />
          </mesh>

          {/* Inner core */}
          <mesh>
            <sphereGeometry args={[0.25, 16, 16]} />
            <meshBasicMaterial
              color={getStatusColor()}
              transparent
              opacity={0.8}
            />
          </mesh>

          {/* Glow ring */}
          <mesh ref={glowRef} rotation={[Math.PI / 2, 0, 0]}>
            <torusGeometry args={[0.6, 0.02, 16, 32]} />
            <animated.meshBasicMaterial
              color={profile.color}
              transparent
              opacity={spring.glowIntensity}
            />
          </mesh>
        </animated.group>
      </Float>

      {/* Avatar emoji */}
      <Text
        position={[0, 0.9, 0]}
        fontSize={0.4}
        color="white"
        anchorX="center"
        anchorY="middle"
      >
        {profile.avatarEmoji}
      </Text>

      {/* Model name label */}
      <Text
        position={[0, -0.3, 0]}
        fontSize={0.15}
        color={profile.color}
        anchorX="center"
        anchorY="middle"
        outlineWidth={0.01}
        outlineColor="#000"
      >
        {profile.shortName}
      </Text>

      {/* Status indicator */}
      <StatusIndicator status={modelState?.status} color={getStatusColor()} />

      {/* Speaking indicator */}
      {isSpeaking && <SpeakingIndicator color={profile.color} />}
    </group>
  );
}

// Status indicator dot
function StatusIndicator({ status, color }) {
  const ref = useRef();

  useFrame((state) => {
    if (ref.current && status === 'thinking') {
      ref.current.material.opacity = 0.5 + Math.sin(state.clock.elapsedTime * 5) * 0.5;
    }
  });

  if (!status || status === 'idle') return null;

  return (
    <mesh position={[0.5, 0.8, 0]} ref={ref}>
      <sphereGeometry args={[0.08, 16, 16]} />
      <meshBasicMaterial color={color} transparent opacity={1} />
    </mesh>
  );
}

// Speaking indicator - animated rings
function SpeakingIndicator({ color }) {
  const ringsRef = useRef([]);

  useFrame((state) => {
    ringsRef.current.forEach((ring, i) => {
      if (ring) {
        const scale = 1 + Math.sin(state.clock.elapsedTime * 3 - i * 0.5) * 0.2;
        ring.scale.setScalar(scale);
        ring.material.opacity = 0.3 + Math.sin(state.clock.elapsedTime * 3 - i * 0.5) * 0.2;
      }
    });
  });

  return (
    <group position={[0, 0, 0]}>
      {[1, 1.3, 1.6].map((size, i) => (
        <mesh
          key={i}
          ref={(el) => (ringsRef.current[i] = el)}
          rotation={[Math.PI / 2, 0, 0]}
        >
          <ringGeometry args={[size * 0.5, size * 0.5 + 0.02, 32]} />
          <meshBasicMaterial
            color={color}
            transparent
            opacity={0.3}
            side={2}
          />
        </mesh>
      ))}
    </group>
  );
}

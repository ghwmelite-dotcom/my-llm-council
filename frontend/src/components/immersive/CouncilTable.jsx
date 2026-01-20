import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { RoundedBox, Ring, Text } from '@react-three/drei';
import { useImmersiveStore } from '../../stores/immersiveStore';

export default function CouncilTable() {
  const tableRef = useRef();
  const glowRef = useRef();
  const { currentStage } = useImmersiveStore();

  // Subtle rotation animation
  useFrame((state) => {
    if (glowRef.current) {
      glowRef.current.rotation.y = state.clock.elapsedTime * 0.1;
    }
  });

  // Table color based on current stage
  const getTableGlow = () => {
    switch (currentStage) {
      case 'stage1':
        return '#4a90e2';
      case 'stage2':
        return '#eab308';
      case 'stage3':
        return '#22c55e';
      default:
        return '#666666';
    }
  };

  return (
    <group position={[0, 0, 0]}>
      {/* Main table surface */}
      <mesh position={[0, 0, 0]} receiveShadow castShadow>
        <cylinderGeometry args={[2.5, 2.5, 0.15, 64]} />
        <meshStandardMaterial
          color="#2a2a3e"
          metalness={0.4}
          roughness={0.6}
        />
      </mesh>

      {/* Table rim */}
      <mesh position={[0, 0.05, 0]}>
        <torusGeometry args={[2.5, 0.08, 16, 64]} />
        <meshStandardMaterial
          color={getTableGlow()}
          metalness={0.8}
          roughness={0.2}
          emissive={getTableGlow()}
          emissiveIntensity={0.3}
        />
      </mesh>

      {/* Inner decorative ring */}
      <mesh position={[0, 0.08, 0]} rotation={[-Math.PI / 2, 0, 0]} ref={glowRef}>
        <ringGeometry args={[1.2, 1.4, 64]} />
        <meshStandardMaterial
          color={getTableGlow()}
          emissive={getTableGlow()}
          emissiveIntensity={0.5}
          transparent
          opacity={0.6}
        />
      </mesh>

      {/* Center emblem */}
      <mesh position={[0, 0.1, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[0.6, 6]} />
        <meshStandardMaterial
          color="#1a1a2e"
          metalness={0.5}
          roughness={0.5}
        />
      </mesh>

      {/* Center icon - scales */}
      <Text
        position={[0, 0.12, 0]}
        rotation={[-Math.PI / 2, 0, 0]}
        fontSize={0.4}
        color={getTableGlow()}
        anchorX="center"
        anchorY="middle"
      >
        ⚖️
      </Text>

      {/* Seat position markers */}
      <SeatMarker position={[0, 0.01, -2.5]} rotation={0} label="GPT" />
      <SeatMarker position={[2.5, 0.01, 0]} rotation={Math.PI / 2} label="Gemini" />
      <SeatMarker position={[0, 0.01, 2.5]} rotation={Math.PI} label="Claude" />
      <SeatMarker position={[-2.5, 0.01, 0]} rotation={-Math.PI / 2} label="Grok" />

      {/* Ambient glow underneath */}
      <mesh position={[0, -0.1, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[3, 64]} />
        <meshBasicMaterial
          color={getTableGlow()}
          transparent
          opacity={0.1}
        />
      </mesh>
    </group>
  );
}

// Individual seat marker
function SeatMarker({ position, rotation, label }) {
  return (
    <group position={position} rotation={[0, rotation, 0]}>
      {/* Seat platform */}
      <mesh position={[0, 0, 0]}>
        <cylinderGeometry args={[0.3, 0.35, 0.02, 32]} />
        <meshStandardMaterial
          color="#333344"
          metalness={0.3}
          roughness={0.7}
        />
      </mesh>

      {/* Small label */}
      <Text
        position={[0, 0.02, 0.5]}
        rotation={[-Math.PI / 2, 0, 0]}
        fontSize={0.15}
        color="#666"
        anchorX="center"
        anchorY="middle"
      >
        {label}
      </Text>
    </group>
  );
}

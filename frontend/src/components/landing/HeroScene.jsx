import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Float, Sphere, Ring, MeshDistortMaterial, Trail } from '@react-three/drei';
import * as THREE from 'three';

// Model configurations with unique visual properties
const MODEL_CONFIGS = [
  {
    id: 'claude',
    name: 'Claude Sonnet',
    color: '#ff6b35',
    emissive: '#ff4500',
    position: [4, 0, 0],
    orbitSpeed: 0.3,
    orbitRadius: 4,
    size: 0.5,
    distort: 0.3
  },
  {
    id: 'gpt',
    name: 'GPT-5.1',
    color: '#10a37f',
    emissive: '#00ff88',
    position: [0, 0, 4],
    orbitSpeed: 0.25,
    orbitRadius: 4.5,
    size: 0.55,
    distort: 0.25
  },
  {
    id: 'gemini',
    name: 'Gemini Pro',
    color: '#4285f4',
    emissive: '#00f0ff',
    position: [-4, 0, 0],
    orbitSpeed: 0.35,
    orbitRadius: 3.8,
    size: 0.45,
    distort: 0.35
  },
  {
    id: 'grok',
    name: 'Grok-4',
    color: '#9333ea',
    emissive: '#ff00aa',
    position: [0, 0, -4],
    orbitSpeed: 0.28,
    orbitRadius: 4.2,
    size: 0.5,
    distort: 0.4
  }
];

// Central nexus component
const CentralNexus = () => {
  const nexusRef = useRef();
  const ringsRef = useRef();
  const glowRef = useRef();

  useFrame((state) => {
    const t = state.clock.elapsedTime;

    if (nexusRef.current) {
      nexusRef.current.rotation.y = t * 0.2;
      nexusRef.current.rotation.x = Math.sin(t * 0.3) * 0.1;
    }

    if (ringsRef.current) {
      ringsRef.current.rotation.z = t * 0.5;
      ringsRef.current.rotation.x = Math.sin(t * 0.2) * 0.2;
    }

    if (glowRef.current) {
      glowRef.current.scale.setScalar(1 + Math.sin(t * 2) * 0.1);
    }
  });

  return (
    <group>
      {/* Core sphere */}
      <mesh ref={nexusRef}>
        <icosahedronGeometry args={[0.8, 2]} />
        <meshStandardMaterial
          color="#0a0a0f"
          emissive="#00f0ff"
          emissiveIntensity={0.5}
          metalness={0.9}
          roughness={0.1}
          wireframe
        />
      </mesh>

      {/* Inner glow */}
      <mesh ref={glowRef}>
        <sphereGeometry args={[0.6, 32, 32]} />
        <meshBasicMaterial
          color="#00f0ff"
          transparent
          opacity={0.3}
        />
      </mesh>

      {/* Orbiting rings */}
      <group ref={ringsRef}>
        <Ring args={[1.2, 1.3, 64]} rotation={[Math.PI / 2, 0, 0]}>
          <meshBasicMaterial
            color="#00f0ff"
            transparent
            opacity={0.4}
            side={THREE.DoubleSide}
          />
        </Ring>
        <Ring args={[1.5, 1.55, 64]} rotation={[Math.PI / 3, 0, 0]}>
          <meshBasicMaterial
            color="#ff00aa"
            transparent
            opacity={0.3}
            side={THREE.DoubleSide}
          />
        </Ring>
        <Ring args={[1.8, 1.83, 64]} rotation={[Math.PI / 4, Math.PI / 4, 0]}>
          <meshBasicMaterial
            color="#8b5cf6"
            transparent
            opacity={0.2}
            side={THREE.DoubleSide}
          />
        </Ring>
      </group>

      {/* Energy beams to models */}
      {MODEL_CONFIGS.map((model, index) => (
        <EnergyBeam
          key={model.id}
          targetAngle={(index / MODEL_CONFIGS.length) * Math.PI * 2}
          color={model.emissive}
          speed={model.orbitSpeed}
          radius={model.orbitRadius}
        />
      ))}
    </group>
  );
};

// Energy beam connecting nexus to orbiting models
const EnergyBeam = ({ targetAngle, color, speed, radius }) => {
  const beamRef = useRef();

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    const angle = targetAngle + t * speed;

    if (beamRef.current) {
      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius;

      // Update beam geometry to point to model
      beamRef.current.geometry.setFromPoints([
        new THREE.Vector3(0, 0, 0),
        new THREE.Vector3(x, 0, z)
      ]);
    }
  });

  return (
    <line ref={beamRef}>
      <bufferGeometry />
      <lineBasicMaterial
        color={color}
        transparent
        opacity={0.2}
        linewidth={1}
      />
    </line>
  );
};

// Orbiting model avatar
const ModelAvatar = ({ config, onHover, isEntering }) => {
  const groupRef = useRef();
  const meshRef = useRef();
  const glowRef = useRef();
  const trailRef = useRef();

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    const angle = t * config.orbitSpeed;

    if (groupRef.current) {
      // Orbit around center
      groupRef.current.position.x = Math.cos(angle) * config.orbitRadius;
      groupRef.current.position.z = Math.sin(angle) * config.orbitRadius;
      groupRef.current.position.y = Math.sin(t * 0.5 + config.orbitSpeed * 10) * 0.5;
    }

    if (meshRef.current) {
      // Self rotation
      meshRef.current.rotation.y = t * 0.5;
      meshRef.current.rotation.x = Math.sin(t * 0.3) * 0.2;
    }

    if (glowRef.current) {
      // Pulse effect
      const pulse = 1 + Math.sin(t * 3 + config.orbitSpeed * 20) * 0.15;
      glowRef.current.scale.setScalar(pulse);
    }
  });

  return (
    <group ref={groupRef}>
      <Float
        speed={2}
        rotationIntensity={0.5}
        floatIntensity={0.5}
      >
        {/* Main crystal body */}
        <Trail
          width={0.5}
          length={8}
          color={config.emissive}
          attenuation={(t) => t * t}
        >
          <mesh
            ref={meshRef}
            onPointerOver={() => onHover(config.name)}
            onPointerOut={() => onHover(null)}
          >
            <octahedronGeometry args={[config.size, 0]} />
            <MeshDistortMaterial
              color={config.color}
              emissive={config.emissive}
              emissiveIntensity={0.8}
              metalness={0.8}
              roughness={0.2}
              distort={config.distort}
              speed={2}
            />
          </mesh>
        </Trail>

        {/* Outer glow */}
        <mesh ref={glowRef} scale={1.5}>
          <sphereGeometry args={[config.size, 16, 16]} />
          <meshBasicMaterial
            color={config.emissive}
            transparent
            opacity={0.15}
          />
        </mesh>

        {/* Orbit ring indicator */}
        <Ring
          args={[config.size * 1.8, config.size * 1.9, 32]}
          rotation={[Math.PI / 2, 0, 0]}
        >
          <meshBasicMaterial
            color={config.emissive}
            transparent
            opacity={0.3}
            side={THREE.DoubleSide}
          />
        </Ring>
      </Float>
    </group>
  );
};

// Holographic platform
const HolographicPlatform = () => {
  const platformRef = useRef();

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    if (platformRef.current) {
      platformRef.current.rotation.z = t * 0.1;
    }
  });

  return (
    <group ref={platformRef} position={[0, -2, 0]} rotation={[-Math.PI / 2, 0, 0]}>
      {/* Main platform ring */}
      <Ring args={[5.5, 6, 64]}>
        <meshBasicMaterial
          color="#00f0ff"
          transparent
          opacity={0.1}
          side={THREE.DoubleSide}
        />
      </Ring>

      {/* Grid lines */}
      {[...Array(8)].map((_, i) => {
        const angle = (i / 8) * Math.PI * 2;
        return (
          <line key={i}>
            <bufferGeometry>
              <bufferAttribute
                attach="attributes-position"
                count={2}
                array={new Float32Array([
                  0, 0, 0,
                  Math.cos(angle) * 6, Math.sin(angle) * 6, 0
                ])}
                itemSize={3}
              />
            </bufferGeometry>
            <lineBasicMaterial color="#00f0ff" transparent opacity={0.1} />
          </line>
        );
      })}

      {/* Concentric circles */}
      {[2, 3, 4, 5].map((radius) => (
        <Ring key={radius} args={[radius - 0.02, radius, 64]}>
          <meshBasicMaterial
            color="#00f0ff"
            transparent
            opacity={0.05}
            side={THREE.DoubleSide}
          />
        </Ring>
      ))}

      {/* Pulsing outer ring */}
      <Ring args={[6.2, 6.3, 64]}>
        <meshBasicMaterial
          color="#ff00aa"
          transparent
          opacity={0.2}
          side={THREE.DoubleSide}
        />
      </Ring>
    </group>
  );
};

// Main hero scene component
const HeroScene = ({ onModelHover, isEntering }) => {
  return (
    <group>
      {/* Central nexus */}
      <CentralNexus />

      {/* Orbiting model avatars */}
      {MODEL_CONFIGS.map((config) => (
        <ModelAvatar
          key={config.id}
          config={config}
          onHover={onModelHover}
          isEntering={isEntering}
        />
      ))}

      {/* Holographic platform */}
      <HolographicPlatform />

      {/* Ambient particles near models */}
      {MODEL_CONFIGS.map((config, index) => (
        <AmbientParticles
          key={`particles-${config.id}`}
          color={config.emissive}
          orbitRadius={config.orbitRadius}
          orbitSpeed={config.orbitSpeed}
          index={index}
        />
      ))}
    </group>
  );
};

// Ambient particles following models
const AmbientParticles = ({ color, orbitRadius, orbitSpeed, index }) => {
  const particlesRef = useRef();
  const count = 20;

  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 2;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 2;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 2;
    }
    return pos;
  }, []);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    const angle = t * orbitSpeed;

    if (particlesRef.current) {
      particlesRef.current.position.x = Math.cos(angle) * orbitRadius;
      particlesRef.current.position.z = Math.sin(angle) * orbitRadius;
      particlesRef.current.position.y = Math.sin(t * 0.5 + orbitSpeed * 10) * 0.5;
      particlesRef.current.rotation.y = t * 0.5;
    }
  });

  return (
    <points ref={particlesRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={count}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        color={color}
        size={0.05}
        transparent
        opacity={0.6}
        sizeAttenuation
      />
    </points>
  );
};

export default HeroScene;

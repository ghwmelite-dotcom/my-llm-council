import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

const ParticleField = ({ count = 200 }) => {
  const particlesRef = useRef();
  const particleData = useRef([]);

  // Generate initial particle positions and velocities
  const [positions, colors, sizes] = useMemo(() => {
    const pos = new Float32Array(count * 3);
    const col = new Float32Array(count * 3);
    const siz = new Float32Array(count);

    const cyanColor = new THREE.Color('#00f0ff');
    const magentaColor = new THREE.Color('#ff00aa');
    const purpleColor = new THREE.Color('#8b5cf6');
    const colors_palette = [cyanColor, magentaColor, purpleColor];

    particleData.current = [];

    for (let i = 0; i < count; i++) {
      // Spread particles in a large sphere around the scene
      const radius = 15 + Math.random() * 35;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos((Math.random() * 2) - 1);

      pos[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      pos[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      pos[i * 3 + 2] = radius * Math.cos(phi);

      // Random color from palette
      const color = colors_palette[Math.floor(Math.random() * colors_palette.length)];
      col[i * 3] = color.r;
      col[i * 3 + 1] = color.g;
      col[i * 3 + 2] = color.b;

      // Random size
      siz[i] = 0.02 + Math.random() * 0.08;

      // Store animation data
      particleData.current.push({
        originalX: pos[i * 3],
        originalY: pos[i * 3 + 1],
        originalZ: pos[i * 3 + 2],
        speed: 0.1 + Math.random() * 0.3,
        offset: Math.random() * Math.PI * 2,
        amplitude: 0.5 + Math.random() * 1.5,
        twinkleSpeed: 1 + Math.random() * 3,
        twinkleOffset: Math.random() * Math.PI * 2
      });
    }

    return [pos, col, siz];
  }, [count]);

  useFrame((state) => {
    const t = state.clock.elapsedTime;

    if (particlesRef.current) {
      const positionAttr = particlesRef.current.geometry.attributes.position;
      const sizeAttr = particlesRef.current.geometry.attributes.size;

      for (let i = 0; i < count; i++) {
        const data = particleData.current[i];

        // Gentle floating motion
        positionAttr.array[i * 3] = data.originalX + Math.sin(t * data.speed + data.offset) * data.amplitude;
        positionAttr.array[i * 3 + 1] = data.originalY + Math.cos(t * data.speed * 0.7 + data.offset) * data.amplitude * 0.5;
        positionAttr.array[i * 3 + 2] = data.originalZ + Math.sin(t * data.speed * 0.5 + data.offset * 1.5) * data.amplitude * 0.3;

        // Twinkle effect
        const twinkle = 0.5 + 0.5 * Math.sin(t * data.twinkleSpeed + data.twinkleOffset);
        sizeAttr.array[i] = sizes[i] * (0.5 + twinkle * 0.5);
      }

      positionAttr.needsUpdate = true;
      sizeAttr.needsUpdate = true;

      // Slow rotation of the entire particle field
      particlesRef.current.rotation.y = t * 0.02;
      particlesRef.current.rotation.x = Math.sin(t * 0.01) * 0.1;
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
        <bufferAttribute
          attach="attributes-color"
          count={count}
          array={colors}
          itemSize={3}
        />
        <bufferAttribute
          attach="attributes-size"
          count={count}
          array={sizes}
          itemSize={1}
        />
      </bufferGeometry>
      <pointsMaterial
        vertexColors
        transparent
        opacity={0.8}
        sizeAttenuation
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </points>
  );
};

// Nebula cloud effect
export const NebulaCloud = ({ position = [0, 0, 0], color = '#00f0ff', size = 10 }) => {
  const meshRef = useRef();

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    if (meshRef.current) {
      meshRef.current.rotation.z = t * 0.05;
      meshRef.current.scale.setScalar(1 + Math.sin(t * 0.5) * 0.1);
    }
  });

  return (
    <mesh ref={meshRef} position={position}>
      <planeGeometry args={[size, size]} />
      <meshBasicMaterial
        color={color}
        transparent
        opacity={0.05}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </mesh>
  );
};

// Energy ring effect
export const EnergyRing = ({ radius = 5, color = '#00f0ff', speed = 1 }) => {
  const ringRef = useRef();

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    if (ringRef.current) {
      ringRef.current.rotation.z = t * speed;
      ringRef.current.material.opacity = 0.2 + Math.sin(t * 2) * 0.1;
    }
  });

  return (
    <mesh ref={ringRef} rotation={[Math.PI / 2, 0, 0]}>
      <ringGeometry args={[radius - 0.05, radius, 64]} />
      <meshBasicMaterial
        color={color}
        transparent
        opacity={0.2}
        side={THREE.DoubleSide}
        blending={THREE.AdditiveBlending}
      />
    </mesh>
  );
};

export default ParticleField;

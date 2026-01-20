import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { getModelProfile, CONNECTION_STYLES } from '../../config/modelProfiles';

export default function ThoughtConnections({ connections }) {
  if (!connections || connections.length === 0) return null;

  return (
    <group>
      {connections.map((connection, index) => (
        <ConnectionLine
          key={`${connection.from}-${connection.to}`}
          from={connection.from}
          to={connection.to}
          strength={connection.strength}
          index={index}
        />
      ))}
    </group>
  );
}

function ConnectionLine({ from, to, strength, index }) {
  const lineRef = useRef();
  const particlesRef = useRef();

  const fromProfile = getModelProfile(from);
  const toProfile = getModelProfile(to);

  // Calculate positions (slightly above the table)
  const fromPos = useMemo(
    () => new THREE.Vector3(fromProfile.position.x, 0.5, fromProfile.position.z),
    [fromProfile]
  );
  const toPos = useMemo(
    () => new THREE.Vector3(toProfile.position.x, 0.5, toProfile.position.z),
    [toProfile]
  );

  // Get style based on strength
  const getStyle = () => {
    if (strength > 0.7) return CONNECTION_STYLES.strongAgreement;
    if (strength > 0.4) return CONNECTION_STYLES.moderateAgreement;
    return CONNECTION_STYLES.disagreement;
  };

  const style = getStyle();

  // Create curved path between points
  const curve = useMemo(() => {
    const midPoint = new THREE.Vector3().lerpVectors(fromPos, toPos, 0.5);
    midPoint.y += 0.5 + strength * 0.5; // Arc height based on strength

    return new THREE.QuadraticBezierCurve3(fromPos, midPoint, toPos);
  }, [fromPos, toPos, strength]);

  // Generate tube geometry along curve
  const tubeGeometry = useMemo(() => {
    return new THREE.TubeGeometry(curve, 32, 0.02 + strength * 0.02, 8, false);
  }, [curve, strength]);

  // Animate particles along the line
  const particlePositions = useMemo(() => {
    const positions = [];
    const count = Math.floor(5 + strength * 5);
    for (let i = 0; i < count; i++) {
      const t = i / count;
      const point = curve.getPoint(t);
      positions.push(point.x, point.y, point.z);
    }
    return new Float32Array(positions);
  }, [curve, strength]);

  useFrame((state) => {
    if (particlesRef.current) {
      const positions = particlesRef.current.geometry.attributes.position;
      const count = positions.count;

      for (let i = 0; i < count; i++) {
        const t = ((i / count + state.clock.elapsedTime * 0.2) % 1);
        const point = curve.getPoint(t);
        positions.setXYZ(i, point.x, point.y, point.z);
      }
      positions.needsUpdate = true;
    }

    // Pulse the line opacity
    if (lineRef.current) {
      const pulse = 0.5 + Math.sin(state.clock.elapsedTime * 2 + index) * 0.3;
      lineRef.current.material.opacity = style.opacity * pulse;
    }
  });

  return (
    <group>
      {/* Main connection tube */}
      <mesh ref={lineRef} geometry={tubeGeometry}>
        <meshBasicMaterial
          color={style.color}
          transparent
          opacity={style.opacity}
        />
      </mesh>

      {/* Animated particles */}
      <points ref={particlesRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={particlePositions.length / 3}
            array={particlePositions}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          color={style.color}
          size={0.08}
          transparent
          opacity={0.8}
          sizeAttenuation
        />
      </points>

      {/* Glow effect at connection points */}
      <ConnectionGlow position={fromPos} color={fromProfile.color} strength={strength} />
      <ConnectionGlow position={toPos} color={toProfile.color} strength={strength} />
    </group>
  );
}

function ConnectionGlow({ position, color, strength }) {
  const ref = useRef();

  useFrame((state) => {
    if (ref.current) {
      const scale = 1 + Math.sin(state.clock.elapsedTime * 3) * 0.2;
      ref.current.scale.setScalar(scale * (0.5 + strength * 0.5));
    }
  });

  return (
    <mesh ref={ref} position={position}>
      <sphereGeometry args={[0.1, 16, 16]} />
      <meshBasicMaterial
        color={color}
        transparent
        opacity={0.4 + strength * 0.3}
      />
    </mesh>
  );
}

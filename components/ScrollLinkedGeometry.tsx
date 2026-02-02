import { useRef, useMemo, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { ScrollControls, useScroll, Html } from '@react-three/drei';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import * as THREE from 'three';

// Fractured Icosahedron Component
function FracturedIcosahedron() {
  const scroll = useScroll();
  const groupRef = useRef<THREE.Group>(null);

  // Create fractured geometry data
  const fracturedFaces = useMemo(() => {
    const geometry = new THREE.IcosahedronGeometry(2, 0);
    const positionAttribute = geometry.attributes.position;
    const faces: Array<{
      vertices: THREE.Vector3[];
      normal: THREE.Vector3;
      center: THREE.Vector3;
      explodedPosition: THREE.Vector3;
      explodedRotation: THREE.Euler;
    }> = [];

    // Process each triangle face
    for (let i = 0; i < positionAttribute.count; i += 3) {
      const v1 = new THREE.Vector3().fromBufferAttribute(positionAttribute, i);
      const v2 = new THREE.Vector3().fromBufferAttribute(positionAttribute, i + 1);
      const v3 = new THREE.Vector3().fromBufferAttribute(positionAttribute, i + 2);

      // Calculate face center and normal
      const center = new THREE.Vector3()
        .add(v1)
        .add(v2)
        .add(v3)
        .divideScalar(3);

      const normal = new THREE.Vector3();
      const edge1 = new THREE.Vector3().subVectors(v2, v1);
      const edge2 = new THREE.Vector3().subVectors(v3, v1);
      normal.crossVectors(edge1, edge2).normalize();

      // Calculate exploded position along normal with random distance
      const explodeDistance = 3 + Math.random() * 2;
      const explodedPosition = center.clone().add(normal.multiplyScalar(explodeDistance));

      // Random rotation for exploded state
      const explodedRotation = new THREE.Euler(
        (Math.random() - 0.5) * Math.PI * 2,
        (Math.random() - 0.5) * Math.PI * 2,
        (Math.random() - 0.5) * Math.PI * 2
      );

      faces.push({
        vertices: [v1, v2, v3],
        normal,
        center,
        explodedPosition,
        explodedRotation,
      });
    }

    return faces;
  }, []);

  // Animate based on scroll
  useFrame(() => {
    if (!groupRef.current) return;

    const scrollProgress = scroll.offset; // 0 to 1

    groupRef.current.children.forEach((child, index) => {
      const face = fracturedFaces[index];
      if (!face) return;

      // Lerp position: exploded -> assembled
      child.position.x = THREE.MathUtils.lerp(
        face.explodedPosition.x,
        0,
        scrollProgress
      );
      child.position.y = THREE.MathUtils.lerp(
        face.explodedPosition.y,
        0,
        scrollProgress
      );
      child.position.z = THREE.MathUtils.lerp(
        face.explodedPosition.z,
        0,
        scrollProgress
      );

      // Lerp rotation: random -> zero
      child.rotation.x = THREE.MathUtils.lerp(
        face.explodedRotation.x,
        0,
        scrollProgress
      );
      child.rotation.y = THREE.MathUtils.lerp(
        face.explodedRotation.y,
        0,
        scrollProgress
      );
      child.rotation.z = THREE.MathUtils.lerp(
        face.explodedRotation.z,
        0,
        scrollProgress
      );
    });
  });

  return (
    <group ref={groupRef}>
      {fracturedFaces.map((face, index) => {
        // Create geometry for this triangle
        const vertices = new Float32Array([
          ...face.vertices[0].toArray(),
          ...face.vertices[1].toArray(),
          ...face.vertices[2].toArray(),
        ]);

        return (
          <mesh key={index}>
            <bufferGeometry>
              <bufferAttribute
                attach="attributes-position"
                count={3}
                array={vertices}
                itemSize={3}
              />
            </bufferGeometry>
            
            {/* Glass-like material */}
            <meshPhysicalMaterial
              transmission={0.9}
              thickness={0.5}
              roughness={0.1}
              metalness={0.8}
              envMapIntensity={1}
              transparent
              opacity={0.6}
              side={THREE.DoubleSide}
            />
            
            {/* Neon cyan wireframe overlay */}
            <lineSegments>
              <edgesGeometry args={[new THREE.BufferGeometry().setAttribute(
                'position',
                new THREE.BufferAttribute(vertices, 3)
              )]} />
              <lineBasicMaterial
                color="#00FFFF"
                transparent
                opacity={1}
                linewidth={2}
              />
            </lineSegments>
          </mesh>
        );
      })}
    </group>
  );
}

// Central Glowing Sphere
function CoreSphere() {
  return (
    <mesh>
      <sphereGeometry args={[0.5, 32, 32]} />
      <meshStandardMaterial
        color="#1e40ff"
        emissive="#1e40ff"
        emissiveIntensity={2}
        toneMapped={false}
      />
    </mesh>
  );
}

// Scene wrapper with scroll controls
function Scene() {
  return (
    <>
      <ambientLight intensity={0.2} />
      <pointLight position={[10, 10, 10]} intensity={0.5} />
      
      <FracturedIcosahedron />
      <CoreSphere />
      
      {/* HTML Overlay Text */}
      <Html center>
        <div
          style={{
            color: '#FFFFFF',
            fontSize: '4rem',
            fontFamily: 'sans-serif',
            textTransform: 'uppercase',
            letterSpacing: '0.2em',
            mixBlendMode: 'overlay',
            pointerEvents: 'none',
            userSelect: 'none',
            fontWeight: 300,
          }}
        >
          Let us Make it Easy
        </div>
      </Html>

      {/* Bloom Post-Processing */}
      <EffectComposer>
        <Bloom
          intensity={2.5}
          luminanceThreshold={0.2}
          luminanceSmoothing={0.9}
        />
      </EffectComposer>
    </>
  );
}

// Main Component
export default function ScrollLinkedGeometry() {
  return (
    <div style={{ width: '100vw', height: '400vh', backgroundColor: '#050505' }}>
      <Canvas
        camera={{ position: [0, 0, 8], fov: 50 }}
        style={{ position: 'sticky', top: 0, height: '100vh' }}
        gl={{ antialias: true, alpha: false }}
      >
        <color attach="background" args={['#050505']} />
        <ScrollControls pages={4} damping={0.2}>
          <Scene />
        </ScrollControls>
      </Canvas>
    </div>
  );
}

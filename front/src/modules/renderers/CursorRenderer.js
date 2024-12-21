
import { useLoader } from '@react-three/fiber'
import React, { useRef } from 'react'
import { TextureLoader } from 'three/src/loaders/TextureLoader'
import { useFrame, useThree } from '@react-three/fiber'
import { Vector3 } from 'three'
import { MarkerCircle } from './GraphicsCoreMeshes'

class EntityRendererCursor {

 get_objects_from_data = (onUseFrame, onClick) => {
  let objects = []
  objects.push(<CursorMarker
   position={[0, 0, 0]}
   //size = {600}
   onUseFrame={onUseFrame}
   onClick={onClick}
  ></CursorMarker>)
  return objects
 }
}
export const entityRendererCursor = new EntityRendererCursor()

export function get_brush_object(brush_params, scale_factor) {
 if (!brush_params["active"]) return []
 let color = 0xffffff
 if (brush_params["mode"]=="deleter"){
  color = 0xff0000
 }
 if (brush_params["mode"]=="obstacles_creator"){
  color = 0x00ff00
 }
 if (brush_params["mode"]=="selector"){
  color = 0x00ffff
 }
 return ([
  <MarkerCircle
   position={brush_params["position"]}
   thickness={"thin"}
   color = {color}
   scale_factor={scale_factor}
   radius={brush_params["radius"]}
   level={0}>
  </MarkerCircle>
 ])
}

export function CursorMarker(props) {
 const texture = useLoader(TextureLoader, 'markers/crosschair.png')
 const meshRef = useRef()
 const { pointer } = useThree()


 // Subscribe this component to the render-loop, rotate the mesh every frame


 useFrame((state, delta) => {
  const vector = new Vector3(pointer.x * 300, pointer.y * 300, 0);
  meshRef.current.position.set(vector.x, vector.y, 3);
  props.onUseFrame(pointer)
 })

 return (
  <mesh
   {...props}
   ref={meshRef}
   onClick={(event) => (props.onClick())}
  >
   <boxGeometry args={[40, 40, 0.1]} />
   <meshStandardMaterial map={texture} color={props.color ? props.color : 0xffffff} transparent={true} />
  </mesh>
 )
}

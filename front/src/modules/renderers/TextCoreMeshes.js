import { extend } from '@react-three/fiber'
import { FontLoader } from 'three/examples/jsm/loaders/FontLoader'
import { TextGeometry } from 'three/examples/jsm/geometries/TextGeometry'
import myFont from './fonts/Poppins Medium_Regular.json'

extend({ TextGeometry })

export function TextMesh(props) {
 const font = new FontLoader().parse(myFont);
 let text = props.text ? props.text : "no text"


 let scale_factor = props.scale_factor ? props.scale_factor : 1
 let scale_offset = props.scale_offset ? props.scale_offset : [0, 0]

 let position = [0, 0, 0]
 if (props.position) {
  position[0] = props.position[0] * scale_factor - scale_offset[0] * scale_factor
  position[1] = props.position[1] * scale_factor - scale_offset[1] * scale_factor
  position[2] = props.level ? props.level : 0
 }
 //let size = props.no_scale_size ? props.no_scale_size : props.size * scale_factor


 return (
  <mesh position={position}>
   <textGeometry args={[text, { font, size: 10, height: 1 }]} />
   <meshLambertMaterial attach='material' color={'white'} />
  </mesh>
 )
}

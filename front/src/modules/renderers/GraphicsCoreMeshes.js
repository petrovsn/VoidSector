import { useLoader } from '@react-three/fiber'
import React, { useRef } from 'react'
import { TextureLoader } from 'three/src/loaders/TextureLoader'

//Гравитационные колодцы, радиусы досягаемости, etc
export class MarkerCircleDash extends React.Component {
   render() {
      const texture = 'markers/circle_dash.png'
      return (
         <MeshObject
            texture={texture}
            level={this.props.level}
            color={this.props.color}
            position={[this.props.position[0], this.props.position[1], 0]}
            size={this.props.radius * 2}
            scale_factor={this.props.scale_factor}
            scale_offset={this.props.scale_offset}
         />
      )
   }
}


//Гравитационные колодцы, радиусы досягаемости, etc
export class MarkerCircle extends React.Component {
   render() {
      let texture = 'markers/circle_normal.png'
      if (this.props.radius < 20) {
         texture = 'markers/circle_bold.png'
      }
      if (this.props.radius > 100) {
         texture = 'markers/circle_thin.png'
      }

      if (this.props.thickness == "thin") {
         texture = 'markers/circle_thin.png'
      }

      return (
         <MeshObject
            texture={texture}
            level={this.props.level}
            color={this.props.color}
            position={[this.props.position[0], this.props.position[1], 0]}
            size={this.props.radius * 2}
            scale_factor={this.props.scale_factor}
            scale_offset={this.props.scale_offset}
         />
      )
   }
}

export class MarkerDot extends React.Component {
   render() {
      const texture = 'markers/dot.png'
      return (
         <MeshObject
            texture={texture}
            position={[this.props.position[0], this.props.position[1], 0]}
            size={2}
            no_scale_size={true}
            level={this.props.level}
            color={this.props.color}
            scale_factor={this.props.scale_factor}
            scale_offset={this.props.scale_offset}
         />
      )
   }
}

/*
texture = file with pict
scale_factor - for rescaling 
size - size of image
position = [x, y]
color = color of lines
*/
export function MeshObject(props) {
   const texture = useLoader(TextureLoader, props.texture)
   const meshRef = useRef()
   let scale_factor = props.scale_factor ? props.scale_factor : 1
   let scale_offset = props.scale_offset ? props.scale_offset : [0, 0]
   props.position[0] = props.position[0] * scale_factor - scale_offset[0] * scale_factor
   props.position[1] = props.position[1] * scale_factor - scale_offset[1] * scale_factor
   props.position[2] = props.level ? props.level : 0

   let rotation = props.rotation ? props.rotation : 0
   rotation = rotation / 180 * 3.1415

   let size_array = [props.size, props.size]
   if (props.size_array) {
      size_array = props.size_array

   }




   if (!props.no_scale_size) {
      for (let i in size_array) {
         size_array[i] = size_array[i] * scale_factor
      }
   }

   let min_size = props.min_size ? props.min_size : 1

   for (let i in size_array) {
      if (size_array[i] < min_size) {
         size_array[i] = min_size
      }
   }
   size_array = [size_array[0], size_array[1], 0.1]

   return (
      <mesh
         {...props}
         ref={meshRef}
         rotation={[0, 0, rotation]}
      >
         <boxGeometry args={size_array} />
         <meshStandardMaterial map={texture} color={props.color ? props.color : 0xffffff} transparent={true} />
      </mesh>
   )
}


export function GuiMeshObject(props) {
   const texture = useLoader(TextureLoader, props.texture)
   const meshRef = useRef()
   let scale_factor = props.scale_factor ? props.scale_factor : 1
   let scale_offset = props.scale_offset ? props.scale_offset : [0, 0]





   let rotation = props.rotation ? props.rotation : 0
   rotation = rotation / 180 * 3.1415


   let size_array = [props.size, props.size]
   if (props.size_array) {
      size_array = props.size_array


   }






   if (!props.no_scale_size) {
      for (let i in size_array) {
         size_array[i] = size_array[i] * scale_factor
      }
   }


   let min_size = props.min_size ? props.min_size : 1


   for (let i in size_array) {
      if (size_array[i] < min_size) {
         size_array[i] = min_size
      }
   }
   size_array = [size_array[0], size_array[1], 0.1]


   props.position[0] = props.position[0] + size_array[0] / 2
   props.position[1] = props.position[1] + size_array[1] / 2
   props.position[2] = props.level ? props.level : 0

   return (
      <mesh
         {...props}
         ref={meshRef}
         rotation={[0, 0, rotation]}
      >
         <boxGeometry args={size_array} />
         <meshStandardMaterial map={texture} color={props.color ? props.color : 0xffffff} transparent={true} />
      </mesh>
   )
}

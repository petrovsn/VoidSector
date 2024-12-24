
import React from 'react'

import { MeshObject, MarkerDot } from './GraphicsCoreMeshes.js'
import { Vector2 } from 'three'


class RadarRenderer {

 get_objects_from_data = (data, scale_factor) => {

 if (!data) { return [] }

 let objects_list = []



 let scale_params = {
  "scale_factor": scale_factor,
  "scale_offset": data["observer_pos"]
 }


 for (let id in data["scan_marks"]) {
  let tmp = get_scanMark(data["scan_marks"][id], scale_params)
  objects_list = objects_list.concat(tmp)
 }

 objects_list = objects_list.concat(this.get_radar_shades(data, scale_factor))



 return objects_list
 }

 get_radar_shades = (data, scale_factor) => {
 let result = []
 let scan_radius = data["observer_radius"]
 let sides = ["left", "right", "top", "bottom"]
 for (let i in sides)
  result.push(
  <RadarShadeBorder
   side={sides[i]}
   side_offset={scan_radius}
   scale_factor={scale_factor}
  />
  )
 result.push(
  <RadarCentralShade
  size={scan_radius}
  scale_factor={scale_factor}
  />
 )


 return result
 }

 get_capmarks = (cap_marks, data, scale_factor) => {

 if (!data) { return [] }
 let scale_params = {
  "scale_factor": scale_factor,
  "scale_offset": data["observer_pos"]
 }

 let result = []

 if (!cap_marks) return result

 for (let char in cap_marks) {
  if (cap_marks[char]["active"]) {
  result.push(
   <CapMarkMarker
   char={char}
   position={cap_marks[char]['position']}
   scale_factor={scale_params["scale_factor"]}
   scale_offset={scale_params["scale_offset"]}
   />
  )
  }
 }


 return result
 }

 get_solar_flares_shades = (solar_flare_state) => {
 if (!solar_flare_state) return []
 if (!solar_flare_state["state"]) return []
 return [
  <MeshObject
  texture={'markers/solar_shades/solar_shade.png'}
  level={4}
  position={[-250, 0, 2]}
  size_array={[100, 600, 1]}
  color={0xff8000}
  />,
  <MeshObject
  texture={'markers/solar_shades/solar_shade.png'}
  level={4}
  position={[250, 0, 2]}
  rotation={180}
  size_array={[100, 600, 1]}
  color={0xff8000}
  />,
  <MeshObject
  texture={'markers/solar_shades/solar_shade.png'}
  level={4}
  position={[0, 250, 2]}
  rotation={-90}
  size_array={[100, 600, 1]}
  color={0xff8000}
  />,
  <MeshObject
  texture={'markers/solar_shades/solar_shade.png'}
  level={4}
  position={[0, -250, 2]}
  rotation={90}
  size_array={[100, 600, 1]}
  color={0xff8000}
  />,
 ]
 }

 get_damage_shades = (state) => {
 //console.log("get_damage_shades", state)
 if (!state) return []



  
 return [<MeshObject
  texture={'markers/damage_shade.png'}
  level={4}
  position={[0, 0, 0]}
  size_array={[600, 600, 0.1]}
  color={0xff0000}
 />]

 }
}






export const radarRenderer = new RadarRenderer()



export class CapMarkMarker extends React.Component {
 render() {

 return (
  <MeshObject
  texture={'capmarks/' + this.props.char + '.png'}
  level={3}
  position={[this.props.position[0], this.props.position[1], 2]}
  size={30}
  no_scale_size={true}
  color={0xFF00dd}
  scale_factor={this.props.scale_factor}
  scale_offset={this.props.scale_offset}
  />
 )
 }
}


let get_scanMark = (descr, scale_params) => {

 let objects = []
 let color = 0xffffff
 let mark_type = descr[0]
 let texture = 'markers/radar/hbody.png'

 switch (mark_type) {
 case "pole": {
  color = 0x00ffff
  texture = 'markers/radar/pole.png'
  break;
 }
 case "activity": {
  color = 0xff0000
  texture = 'markers/radar/activity.png'
  break;
 }
 case "resource": {
  color = 0x00ffff
  texture = 'markers/radar/resource.png'
  break
 }
 default: {
  break;
 }
 }


 //if (descr["alias"] === "self") color = 0x00ff00
 //if (descr["alias"] === "friend") color = 0x00ffff
 //if (descr["alias"] === "enemy") color = 0xff0000



 objects.push(<MarkerRadarMark
 color={color}
 texture={texture}
 type={descr[0]}
 position={descr[1]}
 scale_factor={scale_params["scale_factor"]}
 scale_offset={scale_params["scale_offset"]}
 ></MarkerRadarMark>)

 return objects
}


export class MarkerRadarMark extends React.Component {
 render() {

 return (
  <MeshObject
  texture={this.props.texture}
  level={3}
  position={[this.props.position[0], this.props.position[1], 2]}
  size={30}
  min_size={20}
  color={this.props.color}
  scale_factor={this.props.scale_factor}
  scale_offset={this.props.scale_offset}
  />
 )
 }
}

class RadarShadeBorder extends React.Component {
 render() {
 let texture = 'markers/radar_shades/radar_shade.png'
 let position = [0, 0, 2]
 if (this.props.side === "left") {
  position[0] = -300 - this.props.side_offset * this.props.scale_factor
 }
 else if (this.props.side === "right") {
  position[0] = 300 + this.props.side_offset * this.props.scale_factor
 }
 else if (this.props.side === "top") {
  position[1] = 300 + this.props.side_offset * this.props.scale_factor
 }
 else if (this.props.side === "bottom") {
  position[1] = -300 - this.props.side_offset * this.props.scale_factor
 }
 //texture = 'markers/radar/activity.png'
 return (
  <MeshObject
  texture={texture}
  ///position={[this.props.position[0], this.props.position[1], 1]}
  position={position}
  size={600}
  color={0xffff00}
  level={2}
  />
 )
 }
}

class RadarCentralShade extends React.Component {
 render() {
 let texture = 'markers/radar_shades/radar_central_shade.png'

 //texture = 'markers/radar/activity.png'
 return (
  <MeshObject
  texture={texture}
  ///position={[this.props.position[0], this.props.position[1], 1]}
  position={[0, 0, 1]}
  size={this.props.size * this.props.scale_factor * 2}
  color={0xffffff}
  level={2}

  />
 )
 }
}

function get_LinePoints(angle_degrees, length_from, length_to, position, scale_factor, scale_offset) {
 let result = []
 let step = (length_to - length_from) / 25

 let step_vector = new Vector2(step, 0)
 let center = new Vector2(0, 0)
 let angle_rad = angle_degrees * 3.14 / 180
 step_vector.rotateAround(center, angle_rad)
 let start_point = new Vector2(length_from, 0)
 start_point.rotateAround(center, angle_rad)
 for (let i = 0; i < 25; i++) {
 result.push(<MarkerDot
  position={[position[0] + start_point.x + step_vector.x * i, position[1] + start_point.y + step_vector.y * i]}
  level={3}
  scale_factor={scale_factor}
  scale_offset={scale_offset}
 />)
 }
 return result
}

function get_ArcPoints(angle_degrees_from, angle_degrees_to, length, position, scale_factor, scale_offset) {
 let result = []
 let step_vector = new Vector2(length, 0)
 let angle_rad = angle_degrees_from * 3.14 / 180
 let angle_step_rad = -3.14 / (180 / 5)
 let angle_step_count = (angle_degrees_to * 3.14 / 180 - angle_degrees_from * 3.14 / 180) / angle_step_rad
 let center = new Vector2(0, 0)
 step_vector.rotateAround(center, angle_rad)

 for (let i = 0; i < angle_step_count; i++) {

 result.push(<MarkerDot
  position={[position[0] + step_vector.x, position[1] + step_vector.y]}
  level={3}
  scale_factor={scale_factor}
  scale_offset={scale_offset}

 />)
 step_vector.rotateAround(center, angle_step_rad)
 }
 return result
}


export function getDistantScanArc(close_range, distant_range, distant_arc, distant_dir, position, scale_factor, scale_offset) {
 let radar_pulse_interval = 2000 //[ms]
 let radar_phase = (Date.now() % radar_pulse_interval) / radar_pulse_interval

 let angle_from = distant_dir + distant_arc / 2
 let angle_to = distant_dir - distant_arc / 2
 let result = get_LinePoints(angle_from, close_range, distant_range, position, scale_factor, scale_offset)
 result = result.concat(get_LinePoints(angle_to, close_range, distant_range, position, scale_factor, scale_offset))
 result = result.concat(get_ArcPoints(angle_from, angle_to, distant_range, position, scale_factor, scale_offset))
 result = result.concat(get_ArcPoints(angle_from, angle_to, close_range + radar_phase * (distant_range - close_range), position, scale_factor, scale_offset))
 return result
}

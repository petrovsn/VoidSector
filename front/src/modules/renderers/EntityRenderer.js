import React from 'react'

import { MeshObject, GuiMeshObject, MarkerCircleDash, MarkerCircle, MarkerDot } from './GraphicsCoreMeshes.js'
import { getDistantScanArc } from './RadarRenderer.js'
import { TextMesh } from './TextCoreMeshes.js'

class EntityRenderer {

  get_objects_from_data = (data, scale_factor, gui_settings = []) => {

    if (!data) { return [] }

    let objects_list = []

    let scale_params = {
      "scale_factor": scale_factor,
      "scale_offset": data["observer_pos"]
    }

    let show_gravity = false
    if ("show_gravity" in gui_settings)
      if (gui_settings["show_gravity"])
        show_gravity = true

    let show_id_labels = false
    if ("show_id_labels" in gui_settings)
      if (gui_settings["show_id_labels"])
        show_id_labels = true

    let arrow_scaling = false
    if ("arrow_scaling" in gui_settings) arrow_scaling = gui_settings["arrow_scaling"]

    if ("map_border" in gui_settings)
      if (gui_settings["map_border"])
        objects_list.push(<MarkerCircle

          position={[0, 0]}
          scale_factor={scale_factor}
          scale_offset={scale_params["scale_offset"]}
          radius={gui_settings["map_border"]}
          level = {4.1}
          color={0xffff00}
        />)


    for (let hbody_id in data["hBodies"]) {
      let tmp = get_Rendered_hBody(hbody_id, data["hBodies"][hbody_id], scale_params, show_gravity)
      objects_list = objects_list.concat(tmp)
    }

    for (let lbody_id in data["lBodies"]) {
      let tmp = get_Rendered_lBody(data["mark_id"], lbody_id, data["lBodies"][lbody_id], data["visible_ships"], scale_params, show_id_labels, arrow_scaling)
      objects_list = objects_list.concat(tmp)
    }

    objects_list.push(<ScaleMarker scale_factor={scale_params["scale_factor"]} />)

    return objects_list
  }


  get_selection_marker = (data, scale_factor, selected_body_idx) => {
    if (!data) { return [] }
    if (!selected_body_idx) return []

    let objects_list = []

    let scale_params = {
      "scale_factor": scale_factor,
      "scale_offset": data["observer_pos"]
    }

    for (let hbody_id in data["hBodies"]) {
      if (hbody_id === selected_body_idx) {
        let descr = data["hBodies"][hbody_id]
        objects_list.push(<MarkerCircle
          thickness={"bold"}
          position={descr["pos"]}
          scale_factor={scale_params["scale_factor"]}
          scale_offset={scale_params["scale_offset"]}
          radius={30}
          color={0x00ff00}
        ></MarkerCircle>)
        return objects_list
      }

    }

    for (let body_id in data["lBodies"]) {
      if (body_id === selected_body_idx) {
        let descr = data["lBodies"][body_id]
        objects_list.push(<MarkerCircle
          thickness={"bold"}
          position={descr["pos"]}
          scale_factor={scale_params["scale_factor"]}
          scale_offset={scale_params["scale_offset"]}
          radius={30}
          color={0x00ff00}
        ></MarkerCircle>)
        return objects_list
      }

    }


    return objects_list
  }
}


export class ScaleMarker extends React.Component {
  render() {
    const texture = 'markers/scale_line.png'
    return (
      <GuiMeshObject
        texture={texture}
        position={[-280, -280, 0]}
        size={100}
        level={3}
        //rotation={this.props.rotation}
        //color={this.props.color}
        scale_offset={[-240 * this.props.scale_factor, -240 * this.props.scale_factor, 0]}
        scale_factor={this.props.scale_factor}
      //scale_offset={this.props.scale_offset}
      />
    )
  }
}

export const entityRenderer = new EntityRenderer()

/*{
 "pos":[self.position[0].item(), self.position[1].item()], 
 "mass":self.mass, 
 "gr": self.gravity_well_radius
 }*/

let get_Rendered_hBody = (id, descr, scale_params, show_gravity) => {
  let global_position_x = descr["pos"][0] * scale_params["scale_factor"] - scale_params["scale_offset"][0] * scale_params["scale_factor"]
  if (global_position_x > 400) return []
  if (global_position_x < -400) return []
  let global_position_y = descr["pos"][1] * scale_params["scale_factor"] - scale_params["scale_offset"][1] * scale_params["scale_factor"]
  if (global_position_y > 400) return []
  if (global_position_y < -400) return []
  let objects = []
  let level = 0
  if (!descr) return
  if ("mapped" in descr) {
    if (descr["mapped"]) {
      level = 2
    }
  }

  let marker_type = descr['marker_type']

  if (["hBody", "ResourceAsteroid"].includes(marker_type)) {
    objects.push(<MarkerAsteroid
      position={descr["pos"]}
      size={descr["critical_r"]}
      scale_factor={scale_params["scale_factor"]}
      scale_offset={scale_params["scale_offset"]}
      level={level}
    ></MarkerAsteroid>)
  }

  if (marker_type == "WormHole") {
    objects.push(<WormHole
      position={descr["pos"]}
      size={descr["critical_r"]}
      scale_factor={scale_params["scale_factor"]}
      scale_offset={scale_params["scale_offset"]}
      level={level}
    ></WormHole>)
  }



  if (show_gravity) {
    objects.push(<MarkerCircle
      position={descr["pos"]}
      thickness={"thin"}
      scale_factor={scale_params["scale_factor"]}
      scale_offset={scale_params["scale_offset"]}
      radius={descr["gr"]}
      level={level}
    ></MarkerCircle>)
  }

  if ('critical_r' in descr) {
    objects.push(<MarkerCircle
      position={descr["pos"]}
      thickness={"thin"}
      scale_factor={scale_params["scale_factor"]}
      scale_offset={scale_params["scale_offset"]}
      radius={descr["critical_r"]}
      color={0xff0000}
      level={level}
    ></MarkerCircle>)
  }

  if ('mining_radius' in descr) {
    objects.push(<MarkerCircle
      position={descr["pos"]}
      thickness={"thin"}
      scale_factor={scale_params["scale_factor"]}
      scale_offset={scale_params["scale_offset"]}
      radius={descr["mining_radius"]}
      color={0x00ffff}
      level={level}
    ></MarkerCircle>)
  }
  return objects

}

/* [
{
   "id": self.mark_id, 
   "type": self.type,
   "alias": "neutral", 
   "pos": [self.positions[1][0].item(), self.positions[1][1].item()],
   "vel": [self.velocities[1][0].item(),self.velocities[1][1].item()],
   "predictions": self.get_prediction() - optional
  }
  ] - relative code on back */




let get_Rendered_lBody = (observer_id, id, descr, visible_ships, scale_params, show_id_labels, arrow_scaling) => {

  let global_position_x = descr["pos"][0] * scale_params["scale_factor"] - scale_params["scale_offset"][0] * scale_params["scale_factor"]
  if (global_position_x > 400) return []
  if (global_position_x < -400) return []
  let global_position_y = descr["pos"][1] * scale_params["scale_factor"] - scale_params["scale_offset"][1] * scale_params["scale_factor"]
  if (global_position_y > 400) return []
  if (global_position_y < -400) return []
  let alias = "neutral"
  if (observer_id) {
    if (observer_id === id) {
      alias = "self"
    }
    else {
      if ((descr["marker_type"] === "projectile") || (descr["marker_type"] === "io_Drone")) {
        alias = "enemy"
        if (descr["master_id"] === observer_id) alias = "friend"
      }
      else if (descr["marker_type"] === "ae_Ship") {
        alias = "enemy"
      }
      else if (descr["marker_type"] === "Kraken") {
        alias = "xeno"
      }
    }
  }

  let alias_levels = {
    "neutral": 15,
    "xeno": 0,
    "self": 10,
    "friend": 5,
    "enemy": 0,
  }


  if (descr["in_edit_mode"]) return []



  let objects = []
  let color = 0xffffff
  if (alias === "self") color = 0x00ff00
  if (alias === "friend") color = 0xffff00
  if (alias === "enemy") color = 0xff0000
  if (alias === "xeno") color = 0xff00ff

  if (show_id_labels) {


    if (visible_ships.includes(id)) {

      objects.push(<MarkerShipIdentifierP1
        color={color}
        position={descr["pos"]}
        scale_factor={scale_params["scale_factor"]}
        scale_offset={scale_params["scale_offset"]}
        level={0}
      ></MarkerShipIdentifierP1>)

      objects.push(<MarkerShipIdentifierP2
        color={color}
        text={id}
        position={descr["pos"]}
        scale_factor={scale_params["scale_factor"]}
        scale_offset={scale_params["scale_offset"]}
        level={0}
      ></MarkerShipIdentifierP2>)
    }
  }

  switch (descr["marker_type"]) {
    case "ae_Ship": {
      objects.push(<MarkerShip
        color={color}
        position={descr["pos"]}
        scale_factor={scale_params["scale_factor"]}
        scale_offset={scale_params["scale_offset"]}
        level={0}
      ></MarkerShip>)

      break
    }

    case "ShipDebris": {
      objects.push(<MarkerShipDebris
        color={0xffffff}
        position={descr["pos"]}
        scale_factor={scale_params["scale_factor"]}
        scale_offset={scale_params["scale_offset"]}
        level={0}
      ></MarkerShipDebris>)

      break
    }

    case 'Kraken': {
      objects.push(<MarkerKraken
        color={color}
        position={descr["pos"]}
        scale_factor={scale_params["scale_factor"]}
        scale_offset={scale_params["scale_offset"]}
        level={0}
      ></MarkerKraken>)

      break
    }


    case "SpaceStation": {
      objects.push(<MarkerSpaceStation
        color={color}
        position={descr["pos"]}
        scale_factor={scale_params["scale_factor"]}
        scale_offset={scale_params["scale_offset"]}
        level={0}
      ></MarkerSpaceStation>)
      break
    }

    case "SpaceStationDebris": {
      objects.push(<MarkerSpaceStationDebris
        color={color}
        position={descr["pos"]}
        scale_factor={scale_params["scale_factor"]}
        scale_offset={scale_params["scale_offset"]}
        level={0}
      ></MarkerSpaceStationDebris>)
      break
    }


    case 'QuantumShadow': {
      objects.push(<MarkerShip
        color={0x00ffff}
        position={descr["pos"]}
        scale_factor={scale_params["scale_factor"]}
        scale_offset={scale_params["scale_offset"]}
        level={0}
      ></MarkerShip>)
      break
    }

    case "projectile": {
      objects.push(<MarkerProjectile
        color={color}
        position={descr["pos"]}
        scale_factor={scale_params["scale_factor"]}
        scale_offset={scale_params["scale_offset"]}
      ></MarkerProjectile>)
      break
    }

    case 'ae_BasicZone': {
      color = 0xff0000
      if (descr['blast_type'] === "ae_EMPZone") color = 0x00ffff
      objects.push(<MarkerDangerZone
        color={color}
        position={descr["pos"]}
        level={-1}
        radius={descr["danger_radius"] * 1.1}
        scale_factor={scale_params["scale_factor"]}
        scale_offset={scale_params["scale_offset"]}
      ></MarkerDangerZone>)
      break
    }

    case 'MeteorsCloud': {
      objects.push(<MarkerMeteorsCloud
        position={descr["pos"]}
        radius={descr["danger_radius"]}
        scale_factor={scale_params["scale_factor"]}
        scale_offset={scale_params["scale_offset"]}
      ></MarkerMeteorsCloud>)
      break
    }

    case "io_Drone":
      objects.push(<MarkerDrone
        color={color}
        position={descr["pos"]}
        scale_factor={scale_params["scale_factor"]}
        scale_offset={scale_params["scale_offset"]}
      ></MarkerDrone>)
      break

    case 'interactable_object':
      objects.push(<MarkerInteractableObject
        color={0xffffff}
        position={descr["pos"]}
        scale_factor={scale_params["scale_factor"]}
        scale_offset={scale_params["scale_offset"]}
      ></MarkerInteractableObject>)
      break
    default: break;
  }



  if (alias_levels[alias] >= 5) {

    if ("direction" in descr) {
      objects.push(<MarkerDirection
        level={2}
        color={color}
        rotation={descr["direction"]}
        position={descr["pos"]}
        scale_factor={arrow_scaling ? 1 : scale_params["scale_factor"]}
        scale_offset={scale_params["scale_offset"]}
      ></MarkerDirection>)
    }

    let p = 0
    if ("predictions" in descr) {


      for (p in descr["predictions"]) {
        objects.push(<MarkerDot
          color={color}
          level={3}
          position={descr["predictions"][p]}
          scale_factor={scale_params["scale_factor"]}
          scale_offset={scale_params["scale_offset"]}
        ></MarkerDot>)
      }
      if ('explosion_radius' in descr) {
        if (descr["predictions"][p]) {
          objects.push(<MarkerCircle
            thickness={"normal"}
            level={3}
            radius={descr["explosion_radius"]}
            position={descr["predictions"][p]}
            color={0xffff00}
            scale_factor={scale_params["scale_factor"]}
            scale_offset={scale_params["scale_offset"]}
          ></MarkerCircle>)
        }
      }
    }

    if ('detection_radius' in descr) {
      objects.push(<MarkerCircle
        thickness={"normal"}
        radius={descr["detection_radius"]}
        position={descr["pos"]}
        color={0x00ffff}
        scale_factor={scale_params["scale_factor"]}
        scale_offset={scale_params["scale_offset"]}
      ></MarkerCircle>)
    }

    if ('detonation_radius' in descr) {
      objects.push(<MarkerCircle
        thickness={"bold"}
        radius={descr["detonation_radius"]}
        position={descr["pos"]}
        color={0xff0000}
        scale_factor={scale_params["scale_factor"]}
        scale_offset={scale_params["scale_offset"]}
      ></MarkerCircle>)
    }




    if ("close_scanrange" in descr) {
      objects.push(<MarkerCircleDash
        radius={descr["close_scanrange"]}
        position={descr["pos"]}
        level={2}
        color={0x00ffff}
        scale_factor={scale_params["scale_factor"]}
        scale_offset={scale_params["scale_offset"]}
      ></MarkerCircleDash>)
    }

    if ("distant_scanrange" in descr) {
      let scan_params = descr["distant_scanrange"]
      let radar_arcs = getDistantScanArc(scan_params.close_range, scan_params.distant_range, scan_params.distant_arc, scan_params.distant_dir, descr["pos"], scale_params["scale_factor"], scale_params["scale_offset"])
      objects = objects.concat(radar_arcs)
    }

    
  }

  return objects
}




//контейнеры и дроны
export class MarkerInteractableObject extends React.Component {
  render() {
    const texture = 'markers/interactable.png'
    return (
      <MeshObject
        texture={texture}
        position={[this.props.position[0], this.props.position[1], 0]}
        size={15}
        color={this.props.color}
        scale_factor={this.props.scale_factor}
        scale_offset={this.props.scale_offset}
      />
    )
  }
}


export class MarkerDrone extends React.Component {
  render() {
    const texture = 'markers/drone.png'
    return (
      <MeshObject
        texture={texture}
        position={[this.props.position[0], this.props.position[1], 0]}
        size={15}
        color={this.props.color}
        scale_factor={this.props.scale_factor}
        scale_offset={this.props.scale_offset}
      />
    )
  }
}


//опасные зоны
export class MarkerDangerZone extends React.Component {
  render() {
    const texture = 'markers/explosion.png'
    return (
      <MeshObject
        texture={texture}
        position={[this.props.position[0], this.props.position[1], 0]}
        size={this.props.radius * 2}
        color={this.props.color}
        level={this.props.level}
        scale_factor={this.props.scale_factor}
        scale_offset={this.props.scale_offset}
      />
    )
  }
}


export class MarkerMeteorsCloud extends React.Component {
  render() {
    const texture = 'markers/meteors_cloud.png'
    return (
      <MeshObject
        texture={texture}
        position={[this.props.position[0], this.props.position[1], 0]}
        size={this.props.radius * 2}
        scale_factor={this.props.scale_factor}
        scale_offset={this.props.scale_offset}
      />
    )
  }
}



//снаряды
export class MarkerProjectile extends React.Component {
  render() {
    const texture = 'markers/projectile.png'
    return (
      <MeshObject
        texture={texture}
        position={[this.props.position[0], this.props.position[1], 0]}
        size={15}
        level={-1}
        color={this.props.color}
        scale_factor={this.props.scale_factor}
        scale_offset={this.props.scale_offset}
      />
    )
  }
}

//корабли
export class MarkerShip extends React.Component {
  render() {
    const texture = 'markers/ship.png'
    return (
      <MeshObject
        texture={texture}
        position={[this.props.position[0], this.props.position[1] + 5, 0]}
        size={30}
        color={this.props.color}
        scale_factor={this.props.scale_factor}
        scale_offset={this.props.scale_offset}
      />
    )
  }
}

export class MarkerKraken extends React.Component {
  render() {
    const texture = 'markers/Kraken.png'
    return (
      <MeshObject
        texture={texture}
        position={[this.props.position[0], this.props.position[1] + 5, 0]}
        size={50}
        color={this.props.color}
        scale_factor={this.props.scale_factor}
        scale_offset={this.props.scale_offset}
      />
    )
  }
}

export class MarkerShipDebris extends React.Component {
  render() {
    const texture = 'markers/ship_debris.png'
    return (
      <MeshObject
        texture={texture}
        position={[this.props.position[0], this.props.position[1] + 5, 0]}
        size={30}
        color={0xffffff}
        scale_factor={this.props.scale_factor}
        scale_offset={this.props.scale_offset}
      />
    )
  }
}

export class MarkerSpaceStation extends React.Component {
  render() {
    const texture = 'markers/space_station.png'
    return (
      <MeshObject
        texture={texture}
        position={[this.props.position[0], this.props.position[1] + 5, 0]}
        size={40}
        color={this.props.color}
        scale_factor={this.props.scale_factor}
        scale_offset={this.props.scale_offset}
      />
    )
  }
}

export class MarkerSpaceStationDebris extends React.Component {
  render() {
    const texture = 'markers/space_station_debris.png'
    return (
      <MeshObject
        texture={texture}
        position={[this.props.position[0], this.props.position[1] + 5, 0]}
        size={40}
        color={0xffffff}
        scale_factor={this.props.scale_factor}
        scale_offset={this.props.scale_offset}
      />
    )
  }
}


export class MarkerShipIdentifierP1 extends React.Component {
  render() {
    const texture = 'markers/ship_name.png'
    let size_x = 40
    let size_y = 30
    return (
      <MeshObject
        texture={texture}
        position={[this.props.position[0] + size_x / 2, this.props.position[1] + 2 + size_y / 2, 0]}
        size={40}
        level={3}


        color={this.props.color}
        size_array={[size_x, size_y, 5]}
        scale_factor={this.props.scale_factor}
        scale_offset={this.props.scale_offset}
      />
    )
  }
}

export class MarkerShipIdentifierP2 extends React.Component {
  render() {
    let size_x = 40
    let size_y = 30
    return (
      <TextMesh
        text={this.props.text}
        position={[this.props.position[0] + size_x / 2, this.props.position[1] + 5 + size_y, 0]}
        level={3}
        scale_factor={this.props.scale_factor}
        scale_offset={this.props.scale_offset}
      />
    )
  }
}

export class MarkerDirection extends React.Component {
  render() {
    const texture = 'markers/direction.png'
    return (
      <MeshObject
        texture={texture}
        position={[this.props.position[0], this.props.position[1], 0]}
        size={50}
        rotation={this.props.rotation}
        color={this.props.color}
        scale_factor={this.props.scale_factor}
        scale_offset={this.props.scale_offset}
      />
    )
  }
}



//Гравитационные колодцы, радиусы досягаемости, etc
export class MarkerAsteroid extends React.Component {
  render() {
    const texture = 'asteroids/1.png'
    let size = this.props.size ? this.props.size : 15
    return (
      <MeshObject
        level={this.props.level}
        texture={texture}
        position={[this.props.position[0], this.props.position[1], 0]}
        size={size * 2}
        scale_factor={this.props.scale_factor}
        scale_offset={this.props.scale_offset}
      />
    )
  }
}

//Гравитационные колодцы, радиусы досягаемости, etc
export class WormHole extends React.Component {
  render() {
    const texture = 'asteroids/wormhole.png'
    let size = this.props.size ? this.props.size : 15
    return (
      <MeshObject
        level={this.props.level}
        texture={texture}
        position={[this.props.position[0], this.props.position[1], 0]}
        size={size * 2}
        scale_factor={this.props.scale_factor}
        scale_offset={this.props.scale_offset}
      />
    )
  }
}

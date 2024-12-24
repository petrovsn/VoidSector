
import React from 'react'
import { get_system_state, send_command } from '../network/connections';

import { Canvas } from '@react-three/fiber'


import { timerscounter } from '../utils/updatetimers';

import { useLoader } from '@react-three/fiber'
import { useRef } from 'react'
import { TextureLoader } from 'three/src/loaders/TextureLoader'
import { get_locales } from '../locales/locales';
import { RepairTeamWidget } from '../systems/crew_sm.js'
import { EnergyControlWidget } from '../systems/energy_sm';
import { ResourcesControlWidget } from '../systems/resources_sm';
import { CrewControlWidget } from '../systems/crew_sm.js';
import { RadarControlWidget } from '../systems/radar_sm';





export class EngineerControllerWidget extends React.Component {
    constructor(props) {
        super(props);


        this.state = {
            selected_sm: null
        }
    }

    componentDidMount() {
        let timer_id = timerscounter.get(this.constructor.name)
        if (!timer_id) {
            clearInterval(timer_id)
        }
        timer_id = setInterval(this.proceed_data_message, 30)
        timerscounter.add(this.constructor.name, timer_id)
    }

    componentWillUnmount() {
        let timer_id = timerscounter.get(this.constructor.name)
        clearInterval(timer_id)
    }
    render() {
        return (<div className='EngineerControllerWidget'>
            <ShipOvervieweWidgetLayer role={this.props.role} />
            <div className='EngineerSystemsLayer'>
                <CrewControlWidget />
                <ResourcesControlWidget />
                <EnergyControlWidget />
                <RadarControlWidget />
            </div>
        </div>)
    }

}


export class ShipOvervieweWidgetLayer extends React.Component {
    constructor(props) {
        super(props);


        this.state = {
            selected_sm: null
        }
    }
    render() {
        return (
            <div className="OverviewWidget">
                <ShipOvervieweWidget
                    onSystemSelection={(sm_name) => { this.setState({ "selected_sm": sm_name }) }}
                    selected_sm={this.state.selected_sm}
                />
                <SystemOvervieweWidget
                    role={this.props.role}
                    sm_name={this.state.selected_sm}
                />
            </div>
        )
    }
}

export class ShipOvervieweWidget extends React.Component {
    constructor(props) {
        super(props);


        this.state = {

        }
    }

    componentDidMount() {
        let timer_id = timerscounter.get(this.constructor.name)
        if (!timer_id) {
            clearInterval(timer_id)
        }
        timer_id = setInterval(this.proceed_data_message, 30)
        timerscounter.add(this.constructor.name, timer_id)
    }

    componentWillUnmount() {
        let timer_id = timerscounter.get(this.constructor.name)
        clearInterval(timer_id)
    }

    proceed_data_message = () => {
        let damage_sm = get_system_state("damage_sm")
        this.setState({ "damage_sm": damage_sm })
    }

    proceed_system_selection = (sm_name) => {
        if (["cone_sm", "hull_sm"].includes(sm_name)) return
        this.props.onSystemSelection(sm_name)
    }

    get_hp_color = (sm_name) => {
        if (!("damage_sm" in this.state)) return 0xffffff
        if (!(this.state.damage_sm)) return 0xffffff
        if (!(sm_name in this.state.damage_sm.systems_hp)) return 0xffffff
        let perc_hp = this.state.damage_sm.systems_hp[sm_name].current_hp / this.state.damage_sm.systems_hp[sm_name].max_hp
        if (perc_hp < 1) {
            let perc_hp_step = 0.2
            perc_hp = perc_hp - perc_hp % perc_hp_step
            perc_hp = perc_hp * 0.5
        }

        let R = 255 - 255 * (perc_hp - 0.5) / 0.5
        let G = 255
        if (perc_hp < 0.5) {
            R = 255
            G = 255 * perc_hp / 0.5
        }


        let color_string = "0x" + this.format2leading_zero_hex(R) + this.format2leading_zero_hex(G) + "00"

        let result = Number(color_string)

        return result
    }

    format2leading_zero_hex = (value) => {
        let res = Math.round(value).toString(16)
        if (res.length === 1) {
            res = "0" + res
        }
        return res

    }

    render() {
        let objects = []
        for (let sp_name in ship_parts_render_params) {
            objects.push(<ShipsPartMesh part_name={sp_name}
                onClick={(e) => { this.proceed_system_selection(sp_name + "_sm") }}
                color={this.get_hp_color(sp_name + "_sm")}
            ></ShipsPartMesh>)
        }

        if (this.props.selected_sm) {
            objects.push(<ShipsPartMesh part_name={this.props.selected_sm.split('_')[0]}
                selected={true}
                onClick={(e) => { }}
            //color = {0x00ffff}
            ></ShipsPartMesh>)
        }


        return (<div className='ShipOvervieweWidget'>

            <div className="ShipSection">
                <Canvas
                    id={"ShipCanvas"}
                    //resize = {{ scroll: true, debounce: { scroll: 50, resize: 0 } }}
                    orthographic={true}

                    style={{
                        'width': "300px",
                        'height': "200px",
                        'border': 'solid',
                        'background': 'black'
                    }}

                >
                    <ambientLight />
                    {objects}


                </Canvas>
            </div >
        </div>)
    }
}


const ship_scaling_factor = 0.25
const ship_offsetX_factor = -40

const ship_parts_render_params = {
    'hull': {
        "pos": [0, 0, 0],
        "size": [530, 303, 1]
    },

    'cone': {
        "pos": [112, 0, 0],
        "size": [341, 266, 1]
    },
    'radar': {
        "pos": [8, 55, 0],
        "size": [231, 118, 1]
    },
    'launcher': {
        "pos": [20, -55, 0],
        "size": [322, 114, 1]
    },
    'engine': {
        "pos": [-65, 0, 0],
        "size": [239, 246, 1]
    },
    'energy': {
        "pos": [5, 0, 0],
        "size": [208, 208, 1]
    },
    'resources'
        : {
        "pos": [77, 0, 0],
        "size": [250, 171, 1]
    },
}


export function ShipsPartMesh(props) {

    let texture_name = 'ship/' + props.part_name + '.png'
    if (props.selected) texture_name = 'ship/' + props.part_name + '_selected.png'
    const texture = useLoader(TextureLoader, texture_name)


    //const texture = useLoader(TextureLoader, 'markers/crosschair.png')
    const meshRef = useRef()
    let geometry = [ship_parts_render_params[props.part_name]["size"][0], ship_parts_render_params[props.part_name]["size"][1], ship_parts_render_params[props.part_name]["size"][2]]

    geometry[0] = geometry[0] * ship_scaling_factor
    geometry[1] = geometry[1] * ship_scaling_factor

    let position = [ship_parts_render_params[props.part_name]["pos"][0], ship_parts_render_params[props.part_name]["pos"][1], ship_parts_render_params[props.part_name]["pos"][2]]
    position[0] = position[0] + ship_offsetX_factor

    // Subscribe this component to the render-loop, rotate the mesh every frame

    return (
        <mesh
            {...props}
            ref={meshRef}
            position={position}
            onClick={(event) => (props.onClick())}
        >
            <boxGeometry args={geometry} />
            <meshStandardMaterial map={texture} color={props.color ? props.color : 0xffffff} transparent={true} />
        </mesh>
    )
}





export class SystemOvervieweWidget extends React.Component {
    constructor(props) {
        super(props);
        this.state = {

        }
    }
    componentDidMount() {
        let timer_id = timerscounter.get(this.constructor.name)
        if (!timer_id) {
            clearInterval(timer_id)
        }
        timer_id = setInterval(this.proceed_data_message, 30)
        timerscounter.add(this.constructor.name, timer_id)
    }

    componentWillUnmount() {
        let timer_id = timerscounter.get(this.constructor.name)
        clearInterval(timer_id)
    }

    proceed_data_message = () => {
        if (!this.props.sm_name) return
        let sm_name = this.props.sm_name
        let damage_sm = get_system_state("damage_sm")
        if (!damage_sm) return
        let crew_sm = get_system_state("crew_sm")
        let sm_info = get_system_state(sm_name)
        let current_hp = damage_sm.systems_hp[sm_name].current_hp
        let max_hp = damage_sm.systems_hp[sm_name].max_hp
        let current_team = crew_sm.systems[sm_name]
        let upgrade_level = sm_info.upgrade_level



        let upgrade_sm = get_system_state("RnD_sm")
        let upgrade_cost = upgrade_sm.systems_upgrades[sm_name]["cost"][upgrade_level]
        let teams = crew_sm.teams

        this.setState({
            "sm_name": sm_name,
            "mark_id": damage_sm.mark_id,
            "current_hp": current_hp.toFixed(1),
            "max_hp": max_hp,
            "current_team": current_team,
            "upgrade_level": upgrade_level,
            "upgrade_cost": upgrade_cost,
            "teams": teams
        })
    }


    on_assign_team = (team_name) => {

        send_command("ship.crew_sm", this.state.mark_id, "assign_team", { "team_name": team_name, "sm_name": this.state.sm_name })
    }

    get_team_assigner = () => {
        let result = []
        if (this.state.current_team) {
            result = [<button onClick={(e) => { this.on_assign_team("") }}>{get_locales("Release_team")}</button>]
        }
        else {
            for (let team_name in this.state.teams) {
                result.push(<button onClick={(e) => { this.on_assign_team(team_name) }}>{get_locales(team_name)}</button>)
            }
        }


        return <div className='teamAssignBtnBlock'>{result}</div>
    }


    on_system_upgrade = (e) => {
        send_command("ship.RnD_sm", this.state.mark_id, "upgrade_system", { "system": this.state.sm_name })
    }

    render() {
        //if (!this.state.current_hp === undefined) return (<div></div>)



        return (<div className='SystemOvervieweWidget'>
            <b>{get_locales(this.props.sm_name)}</b>
            <label>{get_locales("hp")}: {this.state.current_hp}/{this.state.max_hp}</label>
            <label>{get_locales("upgrade_level")}: {this.state.upgrade_level}</label>

            {["admin", "captain"].includes(this.props.role) ?
                <button disabled={!this.state.upgrade_cost} onClick={this.on_system_upgrade}>{get_locales("upgrade")}{this.state.upgrade_cost ? '[' + this.state.upgrade_cost.toString() + "]" : ""}</button> :
                <span></span>

            }

            {["admin", "engineer"].includes(this.props.role) ?

                <div className='teamAssignController'>
                    <label>{get_locales("assign_team")}:</label>
                    {this.get_team_assigner()}
                </div> :
                <span></span>}


            {this.state.current_team ?
                <RepairTeamWidget
                    mode='engineer'
                    mark_id={this.state.mark_id}
                    team_data={this.state.teams[this.state.current_team]}
                ></RepairTeamWidget> :
                <span></span>}

        </div>)
    }
}





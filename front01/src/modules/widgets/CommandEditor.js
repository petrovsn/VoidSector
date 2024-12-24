
import React from 'react'

import '../../styles/CommandEditorWidget.css'
import { send_command, get_ships_state } from '../network/connections';
import { timerscounter } from '../utils/updatetimers';

const command_descriptions = {
    "takes_damage": {
        "target": "ship.damage_sm",
        "params": {
            "damage_value": 0,
            "damage_type": ["explosion", "emp", "collision"]
        },
    },
    "upgrade_system_admin": {
        "target": "ship.RnD_sm",
        "params": {
            "system": ["engine_sm", "launcher_sm", "energy_sm", "radar_sm", "resources_sm"]
        },
    },

    "set_ship_level": {
        "target": "ship.RnD_sm",
        "params": {
            "value": [1, 2, 3]
        },
    },

    "downgrade_system": {
        "target": "ship.RnD_sm",
        "params": {
            "system": ["engine_sm", "launcher_sm", "energy_sm", "radar_sm", "resources_sm"]
        },
    },


    "change_amount": {
        "target": "ship.resources_sm",
        "params": {
            "resource_name": ["metal", "pjtl_TimedExplosive", "pjtl_TriggerExplosive", "pjtl_Mine", "pjtl_TimedEMP", "io_Drone", "hp_RepairKit"],
            "resource_amount": 0
        },
    },
    "repair_system_admin": {
        "target": "ship.damage_sm",
        "params": {
            "system": ["engine_sm", "launcher_sm", "energy_sm", "radar_sm", "resources_sm"]
        },
    },
    "apply_wound": {
        "target": "ship.med_sm",
        "params": {
            "role": ["captain", "navigator", "cannoneer", "engineer"]
        },
    },
    "disable_user": {
        "target": "ship.med_sm",
        "params": {
            "role": ["captain", "navigator", "cannoneer", "engineer"]
        },
    },
    "restore_user": {
        "target": "ship.med_sm",
        "params": {
            "role": ["captain", "navigator", "cannoneer", "engineer"]
        },
    },
    "terminate_predictor_process": {
        "target": "predictor",
        "params": {},
    },
    "add_predictor_process": {
        "target": "predictor",
        "params": {},
    },
    "run_infection": {
        "target": "ship.med_sm.plague",
        "params": {},
    },
    "pause_infection": {
        "target": "ship.med_sm.plague",
        "params": {},
    },
    "terminate_infection": {
        "target": "ship.med_sm.plague",
        "params": {},
    },
    "set_period_duration": {
        "target": "ship.med_sm.plague",
        "params": {
            "value": 10
        },
    },
    "add_patient": {
        "target": "ship.med_sm",
        "params": {
            "name": "Mr.Wood"
        },
    },
    "create_new_team":{
        "target": "ship.crew_sm",
        "params": {
            "team_name": "Mr.Wood"
        },
    },
    "add_unit_to_crew":{
        "target": "ship.crew_sm",
        "params": {
            "value": 1
        },
    },
    "set_NPC_hp":{
        "target": "ship.damage_sm",
        "params": {
            "value": 150
        },
    }
}




export class CommandEditorWidget extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            ships: [],
            command: null
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
        let res = []
        for (let k in get_ships_state()) {
            res.push(k)
        }
        this.setState({ "ships": res })
    }

    onSendCommand = (e) => {
        let level = this.state.target
        send_command(level, this.state.ship_id, this.state.command, this.state)

    }

    get_option_editor = (key, option_descr) => {

        if (!key) return <span></span>


        let input = <input type="string" onChange={(e) => { this.setState({ [key]: e.target.value }) }}></input>


        if (typeof (option_descr) === typeof (0)) {
            input = <input type="number" onChange={(e) => { this.setState({ [key]: Number.parseFloat(e.target.value) }) }}></input>
        }
        else if (typeof (option_descr) == typeof ([])) {
            let option_lists = [<option></option>]
            for (let i in option_descr) {
                option_lists.push(<option >{option_descr[i]}</option>)
            }
            input = <select onChange={(e) => { this.setState({ [key]: e.target.value }) }}>{option_lists}</select>
        }



        return (<div className='commandParamsOption'>
            <label>{key}</label>
            {input}
        </div>)
    }

    get_description = (key) => {
        if (!key) return <span></span>
        let result = []
        let command = command_descriptions[key]
        for (let option in command["params"]) {
            result.push(this.get_option_editor(option, command["params"][option]))
        }
        return (<div className='commandParamsSection'>
            {result}
        </div>)

    }

    get_command_panel = () => {
        let ships_options = [<option></option>]

        for (let k in this.state.ships) {
            ships_options.push(<option value={this.state.ships[k]}>
                {this.state.ships[k]}
            </option>)
        }
        let command_options = [<option></option>]
        for (let k in command_descriptions) {
            command_options.push(<option value={k}>
                {k}
            </option>)
        }
        return (<div className='commandEditorUnit'>
            <select onChange={(e) => { this.setState({ "ship_id": e.target.value }) }}>{ships_options}</select>
            <select onChange={(e) => {
                let target = command_descriptions[e.target.value]["target"]
                this.setState({
                    "command": e.target.value,
                    "target": target
                })

            }}>{command_options}</select>
            {this.get_description(this.state.command)}
            <button onClick={this.onSendCommand}> send </button>
        </div>)
    }

    render() {
        return (<div className="CommandEditorWidget">
            {this.get_command_panel()}

        </div>)
    }
}
